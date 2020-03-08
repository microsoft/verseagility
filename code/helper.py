import os
import configparser
import logging
import pandas as pd
import re
import json
import spacy
from flair.models import SequenceTagger

# from azure.keyvault import KeyVaultClient
# from azure.common.credentials import ServicePrincipalCredentials

############################################
#####   Logging
############################################

def get_logger(level='info', location = None, excl_az_storage=True):
    '''Get runtime logger'''
    global logger

    # Exceptions
    if excl_az_storage:
        logging.getLogger("azure.storage.common.storageclient").setLevel(logging.WARN)

    # Level
    if level == 'info':
        _level = logging.INFO
    elif level == 'debug':
        _level = logging.DEBUG
    elif level == 'warning':
        _level = logging.WARNING

    # Format
    logging.basicConfig(format = '%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
                    datefmt = '%m/%d/%Y %H:%M:%S',
                    level = _level)

    # Location
    if location is None:
        logger = logging.getLogger(__name__)
    else:
        logger = logging.getLogger(location)

    return logger

def get_context():
    '''Get AML Run Context for Logging to AML Services'''
    try:
        from azureml.core import Run
        run = Run.get_context()
    except Exception as e:
        logger.warning(f'[WARNING] Azure ML not loaded. Nothing will be logged. {e}')
        run = ''
    return run

############################################
#####   Config
############################################

def get_project_config(fn):
    if os.path.isfile(f'./project/{fn}'):
        with open(f'./project/{fn}', encoding='utf-8') as fp:
            params = json.load(fp)
    elif os.path.isfile(f'../project/{fn}'):
        with open(f'../project/{fn}', encoding='utf-8') as fp:
            params = json.load(fp)
    elif os.path.isfile(f'config.json'):
        ## Training Config
        with open('config.json', encoding='utf-8') as fp:
            params = json.load(fp)
    elif os.path.isfile(f'./code/config.json'):
        ## Inference Config
        with open('./code/config.json', encoding='utf-8') as fp:
            params = json.load(fp)
    else: 
        raise Exception(f'Project parameters not found -> {fn}')
    return params

# def get_config():
#     #TODO: remove this, new use: keys to env, settings to params
#     # Get config
#     run_config = configparser.ConfigParser()
#     run_config.read('./code/config.ini')
#     if 'path' not in run_config:
#         run_config.read('./config.ini')
#     if 'path' not in run_config:
#         run_config.read('../config.ini')
#     if 'path' not in run_config:
#         logger.warning('[ERROR] Could not find correct config.ini.')
#     return run_config

############################################
#####   Azure
############################################

# def get_credentials():
#     '''Retrieve Service Principal Credentials'''
#     credentials = ServicePrincipalCredentials(
#         client_id = run_config['sp']['client_id'],
#         secret = run_config['sp']['secret'],
#         tenant = run_config['sp']['tenant']
#     )
#     return credentials

# def get_secret():
#     '''Retrieve Secret from KeyVault'''
#     client = KeyVaultClient(get_credentials())
#     vault_url = run_config['keyvault']['url']
#     vault_name = run_config['keyvault']['name_data']
#     return client.get_secret(vault_url, vault_name, "").value

############################################
#####   ML Frameworks
############################################

# (available) Model lookup
## complete list here: https://huggingface.co/transformers/pretrained_models.html
farm_model_lookup = {
    'bert': {
        'xx':'bert-base-multilingual-cased',
        'en':'bert-base-cased',
        'de':'bert-base-german-cased',
        'fr':'camembert-base',
        'cn':'bert-base-chinese'
        },
    'roberta' : {
        'en' : 'roberta-base'
    },
    'xlm-roberta' : {
        'xx' : 'xlm-roberta-base'
    },
    'albert' : {
        'en' : 'albert-base-v2'
    },
    'distilbert' : {
        'xx' : 'distilbert-base-multilingual-cased',
        'de' : 'distilbert-base-german-cased'
    }
}

def get_farm_model(model_type, language):
    ml = None
    mt = farm_model_lookup.get(model_type)
    if mt is not None:
        ml = mt.get(language)
    if ml is None:
        ml = mt.get('xx')
    if ml is None:
        raise Exception('No Transformer/FARM model found')
    return ml

spacy_model_lookup = {
    'en':'en_core_web_sm',
    'de':'de_core_news_sm',
    'fr':'fr_core_news_sm',
    'es':'es_core_news_sm',
    'it':'it_core_news_sm',
    'xx':'xx_ent_wiki_sm'
}

def load_spacy_model(language='xx', disable=[]):
    try:
        nlp = spacy.load(spacy_model_lookup[language], disable=disable)
    except OSError:
        logging.warning(f'[INFO] Downloading spacy language model for {language}')
        from spacy.cli import download
        download(spacy_model_lookup[language])
        nlp = spacy.load(spacy_model_lookup[language], disable=disable)
    return nlp

flair_model_lookup = {
    'en' : 'ner-ontonotes-fast', 
    'de' : 'ner-multi-fast',
    'xx' : 'ner-multi-fast'
}
flair_model_file_lookup = {
    'en' : 'en-ner-ontonotes-fast-v0.4.pt', 
    'de' : 'ner-multi-fast.pt',
    'xx' : 'ner-multi-fast.pt'
}

def get_flair_model(language, object_type):
    if object_type == 'model':
        lookup = flair_model_lookup
    elif object_type == 'fn':
        lookup = flair_model_file_lookup
    m = lookup.get(language)
    if m is None:
        m = lookup.get('xx')
    return m

def load_flair_model(path=None, language='xx', task='ner'):
    if task == 'ner':
        if path is None:
            model = SequenceTagger.load(get_flair_model(language, 'model'))
        else:
            model = SequenceTagger.load(path)
    else:
        logging.warning(f'FLAIR MODEL TASK NOT SUPPORTED --> {task}')
        model = None
    return model

############################################
#####   Dataframe
############################################

def csv_to_string(df):
    return df.to_csv(sep="\t", encoding="utf-8", index=False)

def validate_concat(col1, col2, max_len=1000):
    """
    Determine if concatination is needed, by checking for dublicate in subject and body.
    Max length of sequence (text) is set. Characters surpassing max_len are cut-off. 
    """
    text_concat = []
    if isinstance(col1, str):
        col1, col2 = [col1], [col2]

    for __, (sub, des) in enumerate(zip(col1, col2)):
        try:
            if sub in des[:len(sub)]:
                text_concat.append(des[:max_len])
            else:
                new_line = sub + '. ' + des
                text_concat.append(new_line[:max_len])
        except Exception as e:
            logger.warning(f'[WARNING] Validate Concat - {e}')
            if 'float' in str(e):
                text_concat.append(str(des))
            else:
                text_concat.append(des[:max_len])
    return text_concat

def remove_short(data, column='text_clean', min_char_length = 5):
    """
    Function to remove texts that fall below quality threshold based on character lenght.
    """
    return data[data[column].str.len() > min_char_length].reset_index(drop=True).copy()

############################################
#####   Other
############################################

def append_ner(v, s, e, l, t=''):
    return dict(value=str(v), start=int(s), end=int(e), label=str(l), source=str(t))

############################################
#####   Cryptography
############################################

# def decrypt(token, dataframe=False):
#     ''' Decrypt symetric object using Fernet '''
#     secret = get_secret()
#     f = Fernet(bytes(secret, encoding='utf-8'))
#     token = f.decrypt(token)
#     if dataframe:
#         _data = StringIO(str(token, 'utf-8'))
#         return pd.read_csv(_data, sep='\t', error_bad_lines=False, warn_bad_lines=False,  encoding='utf-8')
#     else:
#         return token

# def decrypt_and_save(fn):
#     with open(fn, "rb") as text_file:
#         token = text_file.read()
#     content = StringIO(str(decrypt(token), 'utf-8'))
#     df = pd.read_csv(content, sep='\t', error_bad_lines=False, warn_bad_lines=False,  encoding='utf-8')
#     df.to_csv(fn.replace('.enc', '.txt'), sep='\t', encoding='utf-8', index=False) #TODO: match encrypt fn out

# def encrypt(token, dataframe=False):
#     ''' Encrypt symetric object using Fernet '''
#     secret = get_secret()
#     f = Fernet(bytes(secret, encoding='utf-8'))
#     if dataframe:
#         token = bytes(to_csv_string(token), encoding='utf-8')
#     return f.encrypt(token)

# def encrypt_and_save(fn, data, file_type='.txt'):
#     data = encrypt(bytes(data, encoding='utf-8'))
#     fn_new = fn.replace(file_type, '.enc')
#     with open(fn_new, "wb") as text_file:
#         text_file.write(data)