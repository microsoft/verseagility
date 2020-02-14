"""Custom use case specific functions"""

import pandas as pd
import json
import re

# Custom function
import sys
sys.path.append('./code')
import helper as he

logger = he.get_logger(location=__name__)

############################################
#####   PROJECT PARAMS
############################################

# Load parameters from config
params = he.get_project_config('msforum_de.config.json') #TODO: select parameters
tasks = params.get('tasks')
logger.warning(f'[INFO] *** Project target lang \t-> {params.get("language")} \t***')
logger.warning(f'[INFO] *** Project target env \t-> {params.get("environment")} \t***')

############################################
#####   Data Preparation
############################################

def prepare_source(data):
    """Normalize source data for use in downstram tasks. 
    NOTE: should be task agnostic"""
    data_norm = pd.json_normalize(data, sep='_').to_dict(orient='records')
    return pd.read_json(json.dumps(data_norm))

def remove(line): 
    line = re.sub(r'Original Title\:', '', line)
    return line

def get_placeholder(line):
    line = re.sub(r'KB[0-9]{6}', ' PU ', line)
    return line

## CLASSIFICATION
def load_text(data):
    return he.validate_concat(data.question_title, data.question_text)

def load_label(data, task):
    if task == 1:
        label = data.appliesTo.apply(lambda x: x.split(',')[0])
    elif task == 2:
        label = data.appliesTo.apply(lambda x: x.split(',')[-1])
    return label

## QA
def load_qa(data):
    return he.validate_concat(data.question_title, data.question_text), data.answer_text.values

def filter_qa(data):
    # Filter by marked as answer
    _temp = data[data.answer_markedAsAnswer == 'true'].reset_index(drop=True).copy()
    if len(_temp) == 0:
        _temp = data[data.answer_markedAsAnswer == True].reset_index(drop=True).copy()
    logger.warning(f'Data Length : {len(_temp)}  \t- after marked as answer ')
    # Filter by UpVotes
    # _temp = _temp[_temp['answer_upvotes'] > 1].reset_index(drop=True).copy() #TODO: evaluate
    logger.warning(f'Data Length : {len(_temp)}  \t- after min upvotes of 2')
    return _temp

