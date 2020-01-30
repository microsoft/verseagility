"""
TRAIN CLASSIFICATION MODEL

Before running train, you need to run prepare.py with the respective task.

Example (in the command line):
> cd to root dir
> conda activate nlp
> python code/classification.py --task 1 --model_type bert --use_cuda

"""
from pathlib import Path
import json
import argparse

from farm.data_handler.data_silo import DataSilo
from farm.data_handler.processor import TextClassificationProcessor
from farm.modeling.optimization import initialize_optimizer
from farm.infer import Inferencer
from farm.modeling.adaptive_model import AdaptiveModel
from farm.modeling.language_model import LanguageModel, Roberta, Albert, DistilBert
from farm.modeling.prediction_head import TextClassificationHead, MultiLabelTextClassificationHead
from farm.modeling.tokenization import Tokenizer, RobertaTokenizer, AlbertTokenizer
from farm.train import Trainer, EarlyStopping
from farm.utils import set_all_seeds, MLFlowLogger, initialize_device_settings
from farm.eval import Evaluator
from sklearn.metrics import (matthews_corrcoef, recall_score, precision_score,
                         f1_score, mean_squared_error, r2_score)
from farm.metrics import simple_accuracy, register_metrics

# Custom functions
import sys
sys.path.append('./code')
import helper as he
import data as dt
import custom as cu

# Logger
logger = he.get_logger(location=__name__)
aml_run = he.get_context()

def doc_classification(task, model_type, n_epochs, batch_size, embeds_dropout, evaluate_every, 
                        use_cuda, max_seq_len, learning_rate, do_lower_case, register_model):
    language = cu.params.get('language')
    # Check task
    if cu.tasks.get(str(task)).get('type') != 'classification':
        raise Exception('NOT A CLASSIFICATION TASK') 
    
    # Data
    dt_task = dt.Data(task=task)

    # Settings
    set_all_seeds(seed=42)
    use_amp = None
    device, n_gpu = initialize_device_settings(use_cuda=use_cuda, use_amp=use_amp)
    lang_model = he.farm_model_lookup.get(model_type).get(language)
    save_dir = dt_task.model_dir.replace('model_type', model_type)
    label_list = dt_task.load('fn_label', header=None)[0].to_list()
    
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
        do_lower_case = do_lower_case
    )

    # The evaluation on the dev-set can be done with one of the predefined metrics or with a
    # metric defined as a function from (preds, labels) to a dict that contains all the actual
    # metrics values. The function must get registered under a string name and the string name must
    # be used.
    def mymetrics(preds, labels):
        acc = simple_accuracy(preds, labels)
        f1macro = f1_score(y_true=labels, y_pred=preds, average="macro")
        f1micro = f1_score(y_true=labels, y_pred=preds, average="micro")
        # AML log
        try:
            aml_run.log('acc', acc.get('acc'))
            aml_run.log('acc_backup', acc)
            aml_run.log('f1macro', f1macro)
            aml_run.log('f1micro', f1micro)
        except:
            pass
        return {"acc": acc, "f1_macro": f1macro, "f1_micro": f1micro}
    register_metrics('mymetrics', mymetrics)
    metric = 'mymetrics'

    processor = TextClassificationProcessor(tokenizer=tokenizer,
                                            max_seq_len=max_seq_len,
                                            data_dir=dt_task.data_dir,
                                            label_list=label_list,
                                            metric=metric,
                                            label_column_name="label",
                                            train_filename=dt_task.fn_lookup['fn_train'],
                                            test_filename=dt_task.fn_lookup['fn_test']
                                            )



    # 3. Create a DataSilo that loads several datasets (train/dev/test), provides DataLoaders for them and calculates a few descriptive statistics of our datasets
    data_silo = DataSilo(
        processor=processor,
        batch_size=batch_size
    )

    # 4. Create an AdaptiveModel
    # a) which consists of a pretrained language model as a basis
    language_model = LanguageModel.load(lang_model)

    # b) and a prediction head on top that is suited for our task => Text classification
    prediction_head = TextClassificationHead(num_labels=len(processor.tasks["text_classification"]["label_list"]),
                                            class_weights=data_silo.calculate_class_weights(task_name="text_classification"))

    model = AdaptiveModel(
        language_model=language_model,
        prediction_heads=[prediction_head],
        embeds_dropout_prob=embeds_dropout, 
        lm_output_types=["per_sequence"],
        device=device
    )

    # 5. Create an optimizer
    model, optimizer, lr_schedule = initialize_optimizer(
        model=model,
        n_batches=len(data_silo.loaders["train"]),
        n_epochs=n_epochs,
        device=device,
        learning_rate=learning_rate,
        use_amp=use_amp
    )

    # 6. Feed everything to the Trainer, which keeps care of growing our model into powerful plant and evaluates it from time to time
    # Also create an EarlyStopping instance and pass it on to the trainer

    # An early stopping instance can be used to save the model that performs best on the dev set
    # according to some metric and stop training when no improvement is happening for some iterations.
    earlystopping = EarlyStopping(
        metric="f1_macro", mode="max",  # use f1_macro from the dev evaluator of the trainer
        # metric="loss", mode="min",   # use loss from the dev evaluator of the trainer
        save_dir=save_dir,  # where to save the best model
        patience=1    # number of evaluations to wait for improvement before terminating the training
    )

    trainer = Trainer(
        model=model,
        optimizer=optimizer,
        data_silo=data_silo,
        epochs=n_epochs,
        n_gpu=n_gpu,
        lr_schedule=lr_schedule,
        evaluate_every=evaluate_every,
        device=device,
        early_stopping=earlystopping
    )

    # 7. Let it grow
    trainer.train()

    # 8. Store it:
    # NOTE: if early stopping is used, the best model has been stored already in the directory
    # defined with the EarlyStopping instance
    # The model we have at this moment is the model from the last training epoch that was carried
    # out before early stopping terminated the training
    model.save(save_dir)
    processor.save(save_dir)

def run():
    # Run arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", 
                    default=1,
                    type=int,
                    help="Task where: \
                            -task 1 : classification subcat \
                            -task 2 : classification cat \
                            -task 3 : ner \
                            -task 4 : qa")
    parser.add_argument("--model_type", 
                    default='bert',
                    type=str,
                    help="Available model types: \
                            -bert: en/de/... \
                            -roberta: en \
                            -albert: en \
                            -distilbert : de")
    parser.add_argument('--use_cuda',
                        action='store_true',
                        help="Use CUDA for training")
    parser.add_argument('--n_epochs',
                    default=5,
                    type=int,
                    help='')  
    parser.add_argument('--batch_size',
                    default=32,
                    type=int,
                    help='')  
    parser.add_argument('--embeds_dropout',
                    default=0.2,
                    type=float,
                    help='')
    parser.add_argument('--evaluate_every',
                    default=100,
                    type=int,
                    help='')  
    parser.add_argument('--max_seq_len',
                    default=128,
                    type=int,
                    help='')  
    parser.add_argument('--learning_rate',
                    default=0.5e-5,
                    type=float,
                    help='')  
    parser.add_argument('--do_lower_case',
                        action='store_true',
                        help="")
    parser.add_argument('--register_model',
                        action='store_true',
                        help="Register model in AML")
    args = parser.parse_args()

    # Params
    max_seq_len     = args.max_seq_len
    learning_rate   = args.learning_rate
    do_lower_case   = args.do_lower_case
    task            = args.task
    model_type      = args.model_type
    n_epochs        = args.n_epochs
    batch_size      = args.batch_size
    embeds_dropout  = args.embeds_dropout
    evaluate_every  = args.evaluate_every
    use_cuda        = args.use_cuda
    register_model  = args.register_model

    doc_classification(task, model_type, n_epochs, batch_size, embeds_dropout, evaluate_every, use_cuda, max_seq_len, learning_rate, do_lower_case, register_model)

if __name__ == "__main__":
    run()