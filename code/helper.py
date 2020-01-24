import configparser
import logging
# from azure.keyvault import KeyVaultClient
# from azure.common.credentials import ServicePrincipalCredentials

import pandas as pd
import re
import spacy
from flair.models import SequenceTagger

############################################
#####   Logging
############################################

def get_logger(level='info', location = None, excl_az_storage=True):
    '''Get runtime logger'''
    # Location
    if location is None:
        logger = logging.getLogger(__name__)
    else:
        logger = logging.getLogger(location)
    
    # Exceptions
    if excl_az_storage:
        logging.getLogger("azure.storage.common.storageclient").setLevel(logging.WARN)

    # Level
    if level == 'info':
        _level = logging.INFO
    elif level == 'debug':
        _level = logging.DEBUG
    elif level == 'warning':
        _level = logging.WARN

    # Format
    logging.basicConfig(format = '%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
                    datefmt = '%m/%d/%Y %H:%M:%S',
                    level = _level)

    return logger

logger = get_logger(location=__name__)

def get_context():
    '''Get AML Run Context for Logging to AML Services'''
    try:
        from azureml.core import Run
        run = Run.get_context()
    except Exception as e:
        logger.info(f'[WARNING] Azure ML not loaded. Nothing will be logged. {e}')
        run = ''
    return run

############################################
#####   Config
############################################

def get_config():
    # Get config
    run_config = configparser.ConfigParser()
    run_config.read('./code/config.ini')
    if 'path' not in run_config:
        run_config.read('./config.ini')
    if 'path' not in run_config:
        run_config.read('../config.ini')
    if 'path' not in run_config:
        logger.info('[ERROR] Could not find correct config.ini.')
    return run_config

run_config = get_config()

############################################
#####   Azure
############################################

def get_credentials():
    '''Retrieve Service Principal Credentials'''
    credentials = ServicePrincipalCredentials(
        client_id = run_config['sp']['client_id'],
        secret = run_config['sp']['secret'],
        tenant = run_config['sp']['tenant']
    )
    return credentials

def get_secret():
    '''Retrieve Secret from KeyVault'''
    client = KeyVaultClient(get_credentials())
    vault_url = run_config['keyvault']['url']
    vault_name = run_config['keyvault']['name_data']
    return client.get_secret(vault_url, vault_name, "").value

############################################
#####   ML Frameworks
############################################

spacy_model_lookup = {
    'en':'en_core_web_sm',
    'de':'de_core_news_sm',
    'it':'it_core_news_sm',
    'xx':'xx_ent_wiki_sm'
}

flair_model_lookup = {
    'en' : 'ner-ontonotes-fast', 
    'de' : 'ner-multi-fast',
    'xx' : 'ner-multi-fast'
}

def load_spacy_model(language='xx', disable=[]):
    try:
        nlp = spacy.load(spacy_model_lookup[language], disable=disable)
    except OSError:
        logging.info(f'[INFO] Download spacy language model for {language}')
        from spacy.cli import download
        download(spacy_model_lookup[language])
        nlp = spacy.load(spacy_model_lookup[language], disable=disable)
    return nlp

def load_flair_model(path=None, language='xx', task='ner'):
    if task == 'ner':
        if path is None:
            model = SequenceTagger.load(flair_model_lookup.get(language))
        else:
            model = SequenceTagger.load(path)
    else:
        logging.info(f'FLAIR MODEL TASK NOT SUPPORTED --> {task}')
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

    for n, (sub, des) in enumerate(zip(col1, col2)):
        try:
            if sub in des[:len(sub)]:
                text_concat.append(des[:max_len])
            else:
                new_line = sub + '. ' + des
                text_concat.append(new_line[:max_len])
        except Exception as e:
            logger.info(f'[WARNING] Validate Concat - {e}')
            if 'float' in str(e):
                text_concat.append(str(des))
            else:
                text_concat.append(des[:max_len])
    return text_concat

def remove_short(data, column='text_clean', min_length = 5):
    """
    Function to remove texts that fall below quality threshold based on character lenght.
    """
    return data[data[column].str.len() > min_length].reset_index(drop=True).copy()

############################################
#####   Other
############################################

def append_ner(v, s, e, l, t=''):
    return dict(value=str(v), start=int(s), end=int(e), label=str(l), source=str(t))

############################################
#####   Cryptography
############################################

def decrypt(token, dataframe=False):
    ''' Decrypt symetric object using Fernet '''
    secret = get_secret()
    f = Fernet(bytes(secret, encoding='utf-8'))
    token = f.decrypt(token)
    if dataframe:
        _data = StringIO(str(token, 'utf-8'))
        return pd.read_csv(_data, sep='\t', error_bad_lines=False, warn_bad_lines=False,  encoding='utf-8')
    else:
        return token

def decrypt_and_save(fn):
    with open(fn, "rb") as text_file:
        token = text_file.read()
    content = StringIO(str(decrypt(token), 'utf-8'))
    df = pd.read_csv(content, sep='\t', error_bad_lines=False, warn_bad_lines=False,  encoding='utf-8')
    df.to_csv(fn.replace('.enc', '.txt'), sep='\t', encoding='utf-8', index=False) #TODO: match encrypt fn out

def encrypt(token, dataframe=False):
    ''' Encrypt symetric object using Fernet '''
    secret = get_secret()
    f = Fernet(bytes(secret, encoding='utf-8'))
    if dataframe:
        token = bytes(to_csv_string(token), encoding='utf-8')
    return f.encrypt(token)

def encrypt_and_save(fn, data, file_type='.txt'):
    data = encrypt(bytes(data, encoding='utf-8'))
    fn_new = fn.replace(file_type, '.enc')
    with open(fn_new, "wb") as text_file:
        text_file.write(data)