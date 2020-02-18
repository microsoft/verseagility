""" 
#TODO: replace with python step functions
Finetuning the model for sub category classification.

Task 1 - forum entry classification
Task 2 - ner (MS products)
Task 3 - qa ranking
Task 4 - urgency / priority

INPUT:
- language
- task
- raw data filename

STEPS:
1. Load and prepare data
2. Clean data for each task (incl splits)
3. Train for each task
3.a classification, by use case
3.b ner, by use case (should be single model..)
3.c qa, by use case (prepare BM25 in v1)

OUTPUT:
- status
"""
import argparse
import mlflow
from farm.utils import MLFlowLogger

# Custom functions
import sys
sys.path.append('./code')
import prepare
import classification
# import ner
# import rank

# from azureml.core import Run

def main():
    parser = argparse.ArgumentParser()

    ## Run arguments
    parser.add_argument("--task", 
                    default=1,
                    type=int,
                    help="Task where: \
                            -task 1 : classification subcat \
                            -task 2 : classification cat \
                            -task 3 : ner \
                            -task 4 : qa") 
    parser.add_argument('--run_prepare',
                    action='store_true',
                    help="ONLY FOR train.py, wether to run prepare.py")                 
    ### PREPARE
    parser.add_argument('--do_format',
                    action='store_true',
                    help="Avoid reloading and normalizing data")
    parser.add_argument("--split", 
                    default=0.9,
                    type=float,
                    help="Train test split. Dev split is taken from train set.")    
    parser.add_argument("--min_cat_occurance", 
                    default=300,
                    type=int,
                    help="Min occurance required by category.") 
    parser.add_argument("--min_char_length", 
                    default=20,
                    type=int,
                    help="") 

    ### CLASSIFICATION
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
                    default=3,
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
                    default=3e-5,
                    type=float,
                    help='')  
    parser.add_argument('--do_lower_case',
                        action='store_true',
                        help="")
    parser.add_argument('--register_model',
                        action='store_true',
                        help="Register model in AML")
    args = parser.parse_args()

    # Run prepare
    if args.run_prepare:
        prepare.main(args.task, args.do_format, args.split, args.min_cat_occurance, args.min_char_length)
    
    # Run train
    classification.doc_classification(task=args.task, model_type=args.model_type, n_epochs=args.n_epochs, 
                                    batch_size=args.batch_size, embeds_dropout=args.embeds_dropout, evaluate_every=args.evaluate_every, 
                        use_cuda=args.use_cuda, max_seq_len=args.max_seq_len, learning_rate=args.learning_rate, do_lower_case=args.do_lower_case, 
                        register_model=args.register_model)

if __name__ == "__main__":
    main()