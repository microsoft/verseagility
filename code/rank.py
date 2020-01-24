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
    'historical' : 0, # currently only 0 is supported
    'textblocks' : 1,
    'historical_thread' : 2
}

class Rank():
    def __init__(self, task, rank_type='historical', inference=False):
        self.dt_rank = dt.Data(task=task, inference=inference)
        # Load bm25
        with open(self.dt_rank.fn_lookup['fn_rank'], 'rb') as fh:  
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
            logger.info(f'[INFO] Reduced answer selection to {len(_data)} from {len(self.data)}.')
        
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
                    default=1,
                    type=int,
                    help="Task where: \
                            -task 1 : classification subcat \
                            -task 2 : classification cat \
                            -task 3 : ner \
                            -task 4 : qa")
    args = parser.parse_args()

    # Load data
    cl = pr.Clean(task=args.task)
    data = cl.dt.load('fn_clean')

    # Split tokenized data
    #TODO: improve tokenizer
    toks = [t.split(' ') for t in data.question_clean.to_list()]

    # Create BM25 Object
    bm = bm25.BM25(toks)

    # Dump objects
    with open(cl.dt.fn_lookup['fn_rank'], 'wb') as fp:
        pickle.dump(bm, fp)
        pickle.dump(data, fp)
    logger.info('Create and stored BM25 object.')

if __name__ == "__main__":
    create_bm25()