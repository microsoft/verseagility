import pandas as pd

from spacy.matcher import PhraseMatcher
from spacy.tokens import Span
from flair.data import Sentence

import re

# Custom functions
import sys
sys.path.append('./code')
import custom as cu
import data as dt
import helper as he


# Custom FLAIR element for spacy pipeline
class FlairMatcher(object):
    name = "flair"

    def __init__(self, path):
        self.tagger = he.load_flair_model(path=path)

    def __call__(self, doc):
        matches = self.tagger.predict(Sentence(doc.text))
        for match in matches[0].get_spans('ner'):
            _match = match.to_dict()
            span = doc.char_span(_match.get('start_pos'), _match.get('end_pos'), label=_match.get('type'))
            doc.ents = list(doc.ents) + [span]
        return doc

class NER():
    def __init__(self, inference=False):
        dt_ner = dt.Data(inference=inference) #TODO: missing task?
        # Load default model
        self.nlp = he.load_spacy_model(language=cu.params.get('language'), disable=['ner','parser','tagger'])
        
        # Add flair pipeline
        flair_matcher = FlairMatcher(dt_ner.fn_lookup['fn_ner_flair'])
        self.nlp.add_pipe(flair_matcher)

        # Load phrase matcher
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        matcher_items = pd.read_csv(dt_ner.fn_lookup['fn_ner_list'], encoding='utf-8', sep = '\t')
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
                'flair'
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