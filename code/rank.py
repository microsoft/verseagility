import os
import pandas as pd
import re
import argparse
import pickle

from gensim.summarization import bm25

# Custom functions
import sys
sys.path.append('./code')
import helper as he
import prepare as pr
import custom as cu
import data as dt

logger = he.get_logger(location=__name__)

rank_type_lookup = {
    'historical' : 0, #NOTE: currently only 0 is supported
    'textblocks' : 1,
    'historical_thread' : 2
}

class Rank():
    def __init__(self, task, rank_type='historical', inference=False):
        self.dt_rank = dt.Data(task=task, inference=inference)
        # Load bm25
        with open(self.dt_rank.get_path('fn_rank', dir = 'model_dir'), 'rb') as fh:  
            self.bm = pickle.load(fh)
            self.data = pickle.load(fh)

    def bm25_score(self, tok):
        """Calculate the BM25 score for each document, based on new text"""
        return pd.Series(self.bm.get_scores(document = tok))

    def run(self, toks, cats=None, ans_thresh=0, top=3):
        """Run BM25 scoring on new text input"""
        
        # Run BM25
        scores = self.bm25_score(toks)

        # Prepare Scores
        _data = self.data.copy()
        _data['score'] = scores
        score_indexes = scores.sort_values(ascending = False).index
        _data = _data.iloc[score_indexes].reset_index(drop=True)
        # Filter by classified label
        if cats is not None and cats != '':
            #TODO: does not work for lists
            _data = _data[_data.appliesTo.str.contains(cats)].reset_index(drop=True)
            logger.warning(f'[INFO] Reduced answer selection to {len(_data)} from {len(self.data)}.')
        
        # BM25 Score threshold
        _data = _data[_data.score > ans_thresh].reset_index(drop=True)
        _data['score'] = _data['score'].apply(lambda x: f'{x:.2f}')
        return _data.head(top)

    def inference_from_dicts(self, dicts):
        """Used for inference
        NOTE: expects one input, one output given
        """
        return self.run(dicts[0]['text'], cats=dicts[0]['cat'])[['question_clean','answer_text_clean','appliesTo','score']].to_dict(orient='records')

def create_bm25():
    """Function to create or update BM25 object"""
    # Run arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", 
                    default=4,
                    type=int,
                    help="Task where: \
                            -task 1 : classification subcat \
                            -task 2 : classification cat \
                            -task 3 : ner \
                            -task 4 : qa")
    parser.add_argument('--register_model',
                        action='store_true',
                        help="")
    parser.add_argument('--download_train',
                        action='store_true',
                        help="")
    args = parser.parse_args()

    # Load data
    cl = pr.Clean(task=args.task, download_train=args.download_train)
    data = cl.dt.load('fn_clean', dir = 'data_dir')

    # Split tokenized data
    toks = data.question_clean.apply(cl.transform_by_task).to_list()

    # Create BM25 Object
    bm = bm25.BM25(toks)

    # Dump objects
    with open(cl.dt.get_path('fn_rank', 'model_dir'), 'wb') as fp:
        pickle.dump(bm, fp)
        pickle.dump(data, fp)
    logger.warning('[INFO] Created and stored BM25 object.')

    # Upload
    if args.register_model:
        cl.dt.upload('model_dir', destination = 'model')

if __name__ == "__main__":
    create_bm25()