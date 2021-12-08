"""
General helper file with functions relevant across use cases.

"""
import logging
log = logging.getLogger(__name__)

import os
import platform
import configparser
from pathlib import Path
import pandas as pd
import json
import spacy

try:
    from azure.common.credentials import ServicePrincipalCredentials
    from azure.keyvault import KeyVaultClient
except Exception as e:
    log.warning(f'Azure KeyVault is not installed, \
        but may not be needed for local development or training. Details: {e}')

try:
    from azureml.core import Run
    from azureml.core.authentication import ServicePrincipalAuthentication
    from azureml.core import Workspace
except Exception as e:
    log.warning(f'Azure Machine Learning is not installed, \
        but may not be needed for local development or endpoint deployment. Details: {e}')

############################################
#####   Logging
############################################

def get_logger(level='info', location = None, excl_az_storage=True):
    """Get runtime logger"""
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
    """Get AML Run Context for Logging to AML Services"""
    try:
        run = Run.get_context()
    except Exception as e:
        logger.warning(f'[WARNING] Azure ML not loaded. Nothing will be logged. {e}')
        run = ''
    return run

############################################
#####   Config
############################################

def get_repo_dir():
    """Get repository root directory"""
    root_dir = './'
    if os.path.isdir(Path(__file__).parent.parent / 'src'):
        root_dir = f"{(Path(__file__).parent.parent).resolve()}/"
    elif os.path.isdir('../src'):
        root_dir = '../'
    elif os.path.isdir('./src'):
        root_dir = './'
    else:
        log.warning('Root repository directory not found. This may \
            be an issue when trying to load from /assets or the local config.ini.')
    return root_dir

def get_project_config(fn):
    """Load project configration from repository directory and parse it"""
    _fn1 = f"{get_repo_dir()}/project/{fn}"
    _fn2 = f"{get_repo_dir()}/src/config.json"
    if os.path.isfile(_fn1):
        with open(_fn1, encoding='utf-8') as fp:
            params = json.load(fp)
    elif os.path.isfile(_fn2):
        ## Inference Config
        with open(_fn2, encoding='utf-8') as fp:
            params = json.load(fp)
    else: 
        raise Exception(f'Project parameters not found -> {fn}')
    return params

def get_config(section = None):
    """Load local config file"""
    run_config = configparser.ConfigParser()
    run_config.read(get_repo_dir() + 'config.ini')
    if len(run_config) == 1:
        run_config = None
    elif section is not None:
        run_config = run_config[section]
    return run_config

def get_requirements(req_type = 'deploy'):
    """Load pip requirements, for training and deployment"""
    # Load requirements file
    reqs = [line.rstrip('\n') for line in 
            open(get_repo_dir() + 'requirements.txt', 
            encoding='utf-8') if line[:2] is not '# ']
    # Filter only relevant part
    if req_type == 'deploy':
        reqs = reqs[:reqs.index('##LOCAL ONLY')]
    elif req_type == 'train':
        reqs = reqs[:reqs.index('##DEPLOY ONLY')]
    elif req_type == 'data':
        reqs = reqs[:reqs.index('##TRAIN ONLY')]
    return reqs

############################################
#####   Secret Management
############################################

def _get_sp_credentials():
    """Retrieve Service Principal Credentials"""
    credentials = ServicePrincipalCredentials(
        client_id   = get_secret('sp-client-id'),
        secret      = get_secret('sp-secret'),
        tenant      = get_secret('sp-tenant-id'),
        resource    = 'https://vault.azure.net/'
    )
    return credentials

def _get_kv_secret(name):
    """ Retrieve Secret from KeyVault"""
    client = KeyVaultClient(_get_sp_credentials())
    vault_url = get_secret('keyvault-url')
    return client.get_secret(vault_url, name, "").value

def get_secret(name, section = 'environ'):
    """Get KeyVault Secret
    
    Order of trials:
    - config.ini (local)
    - ENV variable (deployment)
    - KeyVault direct (deployment)
    - KeyVault via AML (training)
    """
    secret = None
    config = get_config(section = section)

    if config is not None and name in config:
        # Get secret from local config
        secret = config[name]
    elif name in os.environ:
        # Get secret from environment variable
        secret = os.environ[name]
    elif 'sp-tenant-id' in os.environ:
        # Get via KeyVault
        secret = _get_kv_secret(name)
    else:
        # Get via AML linked KeyVault
        run_context = get_aml_context()
        if run_context is not None:
            secret = run_context.get_secret(name = name)

    if secret is None:
        raise Exception(f'The secret {name} was not found via the helper.')
    
    return secret

############################################
#####   Azure Machine Learning
############################################

def get_aml_context():
    """Get Azure Machine Learning Run context"""
    try:
        run = Run.get_context()
        run.experiment #NOTE: this raises an error when not loaded
    except Exception:
        run = None
    return run

def get_aml_ws():
    """Get Azure Machine Learning Workspace object"""
    ws = get_aml_context()
    config = get_config(section = 'environ')

    if ws is not None:
        # Fetch from context
        ws = ws.experiment.workspace
    elif config is not None and platform.system() == 'Windows':
        # Fetch via config
        try:
            # Authenticate via Interactive
            ws = Workspace.get(name = get_secret('aml-ws-name'),
                    resource_group  = get_secret('aml-ws-rg'),
                    auth            = None,
                    subscription_id = get_secret('aml-ws-sid'))
            # NOTE: alt. if tenant is not correct:
            # auth = InteractiveLoginAuthentication(tenant_id=he.get_secret('tenant_id'))
        except Exception as e:
            log.warning(f'[WARNING] Unable to get AML workspace via config file. {e}')
    else:
        # Fetch via SP
        try:
            # Authenticate via SP
            sp = ServicePrincipalAuthentication(tenant_id           = get_secret('sp-tenant-id'),
                                        service_principal_id        = get_secret('sp-client-id'),
                                        service_principal_password  = get_secret('sp-secret'))
            # Get workspace
            ws = Workspace.get(name = get_secret('aml-ws-name'),
                    resource_group  = get_secret('aml-ws-rg'),
                    auth            = sp,
                    subscription_id = get_secret('aml-ws-sid'))
        except Exception as e:
            log.warning(f'[WARNING] Unable to get AML workspace via Service Principal. {e}')
    return ws

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
        'en' : 'roberta-base',
        'de' : 'roberta-base',
        'fr' : 'roberta-base',
        'es' : 'roberta-base',
        'it' : 'roberta-base'
        # All languages for roberta because of multi_classificaiton
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

spacy_model_lookup = {
    'en':'en_core_web_sm',
    'de':'de_core_news_sm',
    'fr':'fr_core_news_sm',
    'es':'es_core_news_sm',
    'it':'it_core_news_sm',
    'xx':'xx_ent_wiki_sm'
}

def load_spacy_model(language='xx', disable=[]):
    """Load spacy models depending on language"""
    try:
        nlp = spacy.load(spacy_model_lookup[language], disable=disable)
    except OSError:
        logging.warning(f'[INFO] Downloading spacy language model for {language}')
        from spacy.cli import download
        download(spacy_model_lookup[language])
        nlp = spacy.load(spacy_model_lookup[language], disable=disable)
    return nlp

def get_flair_model(language, object_type):
    if object_type == 'model':
        lookup = flair_model_lookup
    elif object_type == 'fn':
        lookup = flair_model_file_lookup
    m = lookup.get(language)
    if m is None:
        m = lookup.get('xx')
    return m

def get_farm_model(model_type, language):
    ml = None
    mt = farm_model_lookup.get(model_type)
    if mt is not None:
        ml = mt.get(language)
    if ml is None:
        ml = mt.get('xx')
    if ml is None:
        raise Exception(f'No Transformer/FARM model found. model = {model_type}, lang = {language}')
    return ml


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
#     """ Decrypt symetric object using Fernet """
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
#     """ Encrypt symetric object using Fernet """
#     secret = get_secret()
#     f = Fernet(bytes(secret, encoding='utf-8'))
#     if dataframe:
#         token = bytes(to_csv_string(token), encoding='utf-8')
#     return f.encrypt(token)

# def encrypt_and_save(fn, data, file_type='.txt'):
#     data = encrypt(bytes(data, encoding='utf-8'))
#     fn_new = fn.replace(file_type, '.enc')
#     with open(fn_new, "wb") as text_file:
#         text_file.write(data)#


def get_best_argument(details, argument):
    args_list = details['runDefinition']['arguments']
    for i, a in enumerate(args_list):
        if argument in a :
            return args_list[i + 1]