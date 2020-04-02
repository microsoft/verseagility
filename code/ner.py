import pandas as pd
import re
from pathlib import Path
import logging
import requests
import os

from spacy.matcher import PhraseMatcher
from spacy.tokens import Span

from flair.data import Sentence

from farm.data_handler.data_silo import DataSilo
from farm.data_handler.processor import NERProcessor
from farm.modeling.optimization import initialize_optimizer
from farm.infer import Inferencer
from farm.modeling.adaptive_model import AdaptiveModel
from farm.modeling.language_model import LanguageModel
from farm.modeling.prediction_head import TokenClassificationHead
from farm.modeling.tokenization import Tokenizer
from farm.train import Trainer
from farm.utils import set_all_seeds, MLFlowLogger, initialize_device_settings

from azure.ai.textanalytics import TextAnalyticsClient, TextAnalyticsApiKeyCredential

# Custom functions
import sys
sys.path.append('./code')
import custom as cu
import data as dt
import helper as he


# Custom FLAIR element for spacy pipeline
class FlairMatcher(object):
    name = "flair"
    ##TODO: run on stored headless models
    def __init__(self, path):
        self.tagger = he.load_flair_model(path=path)

    def __call__(self, doc):
        matches = self.tagger.predict(Sentence(doc.text))
        for match in matches[0].get_spans('ner'):
            _match = match.to_dict()
            span = doc.char_span(_match.get('start_pos'), _match.get('end_pos'), label=_match.get('type'))
            doc.ents = list(doc.ents) + [span]
        return doc

class TextAnalyticsMatcher(object):
    name = "textanalytics"
    def __init__(self):
        self.key = he.get_secret('text-analytics-key')
        self.endpoint = f"https://{he.get_secret('text-analytics-name')}.cognitiveservices.azure.com/"
        self.ta_credential = TextAnalyticsApiKeyCredential(self.key)
        self.text_analytics_client = TextAnalyticsClient(
                endpoint=self.endpoint, credential=self.ta_credential)
        
    def __call__(self, doc):
        text = doc.text
        result = self.text_analytics_client.recognize_entities(inputs=[text])[0]
        for entity in result.entities:
            span = doc.char_span(entity.grapheme_offset, entity.grapheme_offset + entity.grapheme_length, label=entity.category)
            doc.ents = list(doc.ents) + [span]
        return doc

class CustomNER():
    def init(self):
        pass

    def ner(self, task, model_type, n_epochs, batch_size, evaluate_every, use_cude):
        aml_run = he.get_context()
        # Check task
        if cu.tasks.get(str(task)).get('type') != 'ner':
            raise Exception('NOT A NER TASK') 
        language = cu.params.get('language')
        
        # Data
        dt_task = dt.Data(task=task)

        set_all_seeds(seed=42)
        device, n_gpu = initialize_device_settings(use_cuda=True)
        lang_model = he.get_farm_model(model_type, language)
        save_dir = dt_task.get_path('model_dir')
        # ner_labels = dt_task.load('fn_label', header=None)[0].to_list() TODO:
        ner_labels = ["[PAD]", "X", "O", "B-MISC", "I-MISC", "B-PER", "I-PER", "B-ORG", "I-ORG", "B-LOC", "I-LOC", "B-OTH", "I-OTH"]

        # n_epochs = 4
        # batch_size = 32
        # evaluate_every = 750
        # lang_model =  "xlm-roberta-large"

        # AML log
        try:
            aml_run.log('task', task)
            aml_run.log('language', language)
            aml_run.log('n_epochs', n_epochs)
            aml_run.log('batch_size', batch_size)
            aml_run.log('lang_model', lang_model)
            aml_run.log_list('label_list', label_list)
        except:
            pass

        # 1.Create a tokenizer
        tokenizer = Tokenizer.load(
            pretrained_model_name_or_path=lang_model,
            do_lower_case=False)

        # 2. Create a DataProcessor that handles all the conversion from raw text into a pytorch Dataset
        processor = NERProcessor(
            tokenizer=tokenizer, max_seq_len=128, 
            data_dir=dt_task.data_dir, metric="seq_f1", 
            label_list=ner_labels
        )

        # 3. Create a DataSilo that loads several datasets (train/dev/test), provides DataLoaders for them and calculates a few descriptive statistics of our datasets
        data_silo = DataSilo(processor=processor, batch_size=batch_size)

        # 4. Create an AdaptiveModel
        # a) which consists of a pretrained language model as a basis
        language_model = LanguageModel.load(lang_model)
        # b) and a prediction head on top that is suited for our task => NER
        prediction_head = TokenClassificationHead(num_labels=len(ner_labels))

        model = AdaptiveModel(
            language_model=language_model,
            prediction_heads=[prediction_head],
            embeds_dropout_prob=0.1,
            lm_output_types=["per_token"],
            device=device,
        )

        # 5. Create an optimizer
        model, optimizer, lr_schedule = initialize_optimizer(
            model=model,
            learning_rate=1e-5,
            n_batches=len(data_silo.loaders["train"]),
            n_epochs=n_epochs,
            device=device,
        )

        # 6. Feed everything to the Trainer, which keeps care of growing our model into powerful plant and evaluates it from time to time
        trainer = Trainer(
            model=model,
            optimizer=optimizer,
            data_silo=data_silo,
            epochs=n_epochs,
            n_gpu=n_gpu,
            lr_schedule=lr_schedule,
            evaluate_every=evaluate_every,
            device=device,
        )

        # 7. Let it grow
        trainer.train()

        # 8. Hooray! You have a model. Store it:
        model.save(save_dir)
        processor.save(save_dir)


class NER():
    def __init__(self, task, inference=False):
        dt_ner = dt.Data(task=task, inference=inference)
        # Load default model
        self.nlp = he.load_spacy_model(language=cu.params.get('language'), disable=['ner','parser','tagger'])
        
        # Add flair pipeline #TODO: excluding FALIR for now, to be compared with text analytics
        # flair_matcher = FlairMatcher(dt_ner.get_path('fn_ner_flair'))
        # self.nlp.add_pipe(flair_matcher)
        
        # Text Analytics
        ta_matcher = TextAnalyticsMatcher()
        self.nlp.add_pipe(ta_matcher)

        # Load phrase matcher
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        matcher_items = pd.read_csv(dt_ner.get_path('fn_ner_list', dir='asset_dir'), encoding='utf-8', sep = '\t')
        for product in matcher_items['key'].drop_duplicates():
            _values = matcher_items[matcher_items['key'] == product]
            patterns = [self.nlp.make_doc(v) for v in _values.value]
            self.matcher.add(product, None, *patterns)

    def get_doc(self, text):
        return self.nlp(text)

    def get_spacy(self, doc):
        ents = []
        for ent in doc.ents:
            ents.append(he.append_ner(
                ent.text, 
                ent.start_char, 
                ent.end_char, 
                ent.label_,
                'spacy'
            ))
        return ents

    def get_rules(self, text):
        #TODO: move regex to custom or config
        ents = []
        ## Get error codes
        matches = re.finditer(r'\b(((o|0)(x|\*))|(800))\S*', text, re.IGNORECASE) 
        for match in matches:
            ents.append(he.append_ner(text[match.span()[0]:match.span()[1]], match.span()[0], match.span()[1] ,'ERROR CODE', 'regex'))
        return ents

    def get_list(self, doc):
        mats = []
        for match_id, start, end in self.matcher(doc):
            mats.append(he.append_ner(
                doc[start:end],
                start,
                end,
                self.nlp.vocab.strings[match_id],
                'list'
            ))
        return mats

    def run(self, text, remove_duplicate=True):
        # Text to document object
        doc = self.get_doc(text)
        # Process
        mats = self.get_list(doc)
        rules = self.get_rules(text)
        ents = self.get_spacy(doc)

        # Handle duplicates, keep first
        #TODO: improve to consider any overlaps 
        #TODO: BUG: unify positions
        entity_list = list(mats) + list(rules) + list(ents)
        entity_list_clean = []
        for ent in entity_list:
            if ''.join(ent['value'].lower().split()) not in [''.join(x['value'].lower().split()) for x in entity_list_clean]:
                entity_list_clean.append(ent)
        return entity_list_clean

    def inference_from_dicts(self, dicts):
        """Used for inference
        NOTE: expects one input, one output given
        """
        return self.run(dicts[0]['text'])