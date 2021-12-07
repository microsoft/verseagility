"""Custom use case specific functions"""

import pandas as pd
import json
import re

# Custom function
import sys
sys.path.append('./src')
import helper as he

logger = he.get_logger(location=__name__)

############################################
#####   PROJECT PARAMS
############################################

# Load parameters from config
params = he.get_project_config('mbio_en.config.json')
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
    return he.validate_concat(data.subject, data.body)

def load_label(data, task):
    if task == 1:
        #label = data.label_classification_simple # TODO: changed load label
        label = data.label
    elif task == 2:
        label = data.label_classification_multi
    return label

## QA
def load_qa(data):
    return he.validate_concat(data.subject, data.body), data.label_answer_body.values

def filter_qa(data):
    # Filter by marked as answer
    data = data[data.label_answer_markedAsAnswer == 'true'].reset_index(drop=True).copy()
    if len(data) == 0:
        data = data[data.label_answer_markedAsAnswer == 'true'].reset_index(drop=True).copy()
    logger.warning(f'Data Length : {len(data)}  \t- after marked as answer ')
    # Filter by UpVotes
    data = data[data['label_answer_upvotes'] > 1].reset_index(drop=True).copy()
    logger.warning(f'Data Length : {len(data)}  \t- after min upvotes of 2')
    return data

