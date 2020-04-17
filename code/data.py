"""
Helper function for data management

All directories, files and model assets 
should pass via the data_manager.

Add custom directories and files to 
the dir_lookup and fn_lookup objects.
"""
import pandas as pd
import numpy as np
import pickle
import json
import os
import logging
from pathlib import Path
from azure.cosmos import cosmos_client

# Custom functions
import sys
sys.path.append('../code')
import helper as he
import custom as cu

logger = he.get_logger(location=__name__)

try:
    from azureml.core import Run, Dataset, Model, Workspace
    from azureml.core.authentication import InteractiveLoginAuthentication
except Exception as e:
    logging.warning(f'AML not installed -> {e}')

try:
    from azure.storage.blob import BlockBlobService
except Exception as e:
    logging.warning(f'Azure Storage Account not installed -> {e}')

def get_repo_dir():
    """Get repository root directory"""
    root_dir = './'
    if os.path.isdir(Path(__file__).parent.parent / 'code'):
        root_dir = f"{str((Path(__file__).parent.parent).resolve())}/"
    elif os.path.isdir('../code'):
        root_dir = '../'
    elif os.path.isdir('./code'):
        root_dir = './'
    else:
        logging.warning('ROOT FOLDER NOT FOUND.')
    return root_dir

def get_asset_dir():
    """Get assets directory"""
    assets_dir = ''
    if os.path.isdir(Path(__file__).parent.parent / 'assets'):
        assets_dir = f"{str((Path(__file__).parent.parent).resolve() / 'assets')}/"
    elif os.path.isdir('../assets'):
        assets_dir = '../assets/'
    elif os.path.isdir('./assets'):
        assets_dir = './assets/'
    else:
        logging.warning(f'ASSETS FOLDER NOT FOUND. {os.getcwd()}')
    return assets_dir

def get_local_dir():
    """Get the local data repository, as specified in the local config"""
    try:
        data_dir = he.get_config().get('data', 'dir')
    except Exception as e:
        logging.warning(f'No config.ini found ({e}), using repository root as default dir.')
        data_dir = None
    return data_dir

class Data():
    def __init__(self,  
                    task            =   1,
                    version         =   1,
                    inference       =   False,
                    download_source =   False, #TODO:
                    download_train  =   False
                ):
        """Initiatlize data manager with task and directory specifics"""
        # Parameters
        self.project_name = cu.params.get('name')
        self.task = task
        self.language = cu.params.get('language')
        self.version = version
        self.env = cu.params.get('environment')

        # Directories
        ##NOTE: if data and model files are separate per task, 
        ## add {self.task} to directory
        self.data_dir = f'{self.project_name}-data'
        self.model_dir = f'{self.project_name}-model-{self.task}'
        self.raw_dir = f'raw'
        self.intermediate_dir = f'intermediate_{self.task}'
        self.train_dir = f'train_{self.task}'
        if 'AZUREML_MODEL_DIR' in os.environ:
            ### AzureML deployed run
            _base = os.environ['AZUREML_MODEL_DIR']
            _dir = f"{_base}/{self.model_dir}/"
            if os.path.isdir(_dir):
                ### Deployed with multiple model objects in AML
                self.root_dir = f'{_base}/'
                self.model_dir = f'{self.model_dir}/{os.listdir(_dir)[0]}/{self.model_dir}/'
                # NOTE: get's latest version of model
            else:
                ### Deployed with single model objects in AML
                self.root_dir = f"{_base}/"
        else:
            self.root_dir = f"{os.path.abspath(cu.params.get('data_dir'))}/"
            os.makedirs(f"{self.root_dir}{self.data_dir}", exist_ok=True)
            os.makedirs(f"{self.root_dir}{self.data_dir}/{self.raw_dir}", exist_ok=True)
            os.makedirs(f"{self.root_dir}{self.data_dir}/{self.intermediate_dir}", exist_ok=True)
            os.makedirs(f"{self.root_dir}{self.data_dir}/{self.train_dir}", exist_ok=True)
            os.makedirs(f"{self.root_dir}{self.model_dir}", exist_ok=True)
        
        logging.info(f'[INFO] Root directory: {self.root_dir}')
        logging.info(f'[INFO] Data directory: {self.data_dir}')
        logging.info(f'[INFO] Model directory: {self.model_dir}')
        
        ###############################################################
        ### CUSTOOMIZE DIRECTORY & FILE PATHS HERE
        ###############################################################
        # Lookup
        ## Directory
        self.dir_lookup = {
            'repo_dir'          : get_repo_dir(),
            'asset_dir'         : get_asset_dir(),
            'root_dir'          : self.root_dir,
            'data_dir'          : self.data_dir,
            'raw_dir'           : f"{self.data_dir}/{self.raw_dir}",
            'intermediate_dir'  : f"{self.data_dir}/{self.intermediate_dir}",
            'train_dir'         : f"{self.data_dir}/{self.train_dir}",
            'model_dir'         : self.model_dir
        }
        ## Filename
        self.fn_lookup = {
            'fn_source'     : f"{self.project_name}-source.json",
            'fn_prep'       : f'data-l{self.language}.txt',
            'fn_train'      : f'train-l{self.language}-t{self.task}.txt',
            'fn_clean'      : f'clean-l{self.language}-t{self.task}.txt',
            'fn_test'       : f'test-l{self.language}-t{self.task}.txt',
            'fn_label'      : f'label-l{self.language}-t{self.task}.txt',
            'fn_rank'       : f'data-l{self.language}-t{self.task}.pkl',
            'fn_ner_list'   : f'ner.txt',
            'fn_ner_flair'  : f'{he.get_flair_model(self.language, "fn")}',
            'fn_names'      : f'names.txt',
            'fn_stopwords'  : f'stopwords-{self.language}.txt',
        }
        #############################END###############################

        # Load AML
        try:
            # if he.get_config() is not None:
            #     auth = None
            #     self.ws = Workspace.get(name=he.get_secret('aml-ws-name'), 
            #         subscription_id=he.get_secret('aml-ws-sid'), 
            #         resource_group=he.get_secret('aml-ws-rg'),
            #         auth=auth)
            # else:
            run = Run.get_context()
            self.ws = run.experiment.workspace
        except Exception as e:
            logging.warning(f'[WARNING] AML Workspace not loaded -> {e}.')

        # Load Storage Account
        try:
            blob_connection_string = '' 
            self.bbs = BlockBlobService(connection_string=blob_connection_string)
        except Exception as e:
            logging.warning(f'[WARNING] Storage account not loaded -> {e}')

    def get_path(self, fn, dir = 'root_dir'):
        """Resolve standardized file and directory paths"""
        # Resolve fn
        if fn in self.fn_lookup:
            fn = self.fn_lookup.get(fn)
        elif fn in self.dir_lookup:
            if 'root_dir' in fn:
                dir = None
            fn = self.dir_lookup.get(fn)

        # Append directory
        if dir is not None:
            if dir == 'repo_dir':
                fn = f"{self.dir_lookup.get('repo_dir')}{fn}"
            elif dir == 'asset_dir':
                fn = f"{self.dir_lookup.get('asset_dir')}{fn}"
            elif dir == 'root_dir':
                fn = f"{self.root_dir}{fn}"
            elif dir in ['data_dir', 'raw_dir','intermediate_dir', 'train_dir','model_dir']:
                fn = f"{self.root_dir}{self.dir_lookup.get(dir)}/{fn}"
        return fn

    def _get_blob_fn(self, fn, dir):
        if dir == 'train_dir':
            fn = f'{self.train_dir}/{fn}'
        elif dir == 'raw_dir':
            fn = f'{self.raw_dir}/{fn}'
        elif dir == 'intermediate_dir':
            fn = f'{self.intermediate_dir}/{fn}'
        return fn

    ##### DOWNLOAD #####
    def _download_blob(self, fn, fp, container):
        """Download from blob storage account"""
        self.bbs.get_blob_to_path(container, fn, fp)

    def _download_datastore(self, fn, dir = 'data_dir'):
        """Download from AML Data Store"""
        Dataset.get_by_name(workspace=self.ws, name=fn).download(target_path=self.get_path(dir), overwrite=True)
    
    def _download_model(self, fn, dir = 'model_dir'):
        """Download from AML Model Management"""
        Model(self.ws, name=fn).download(self.get_path(dir))

    def download(self, fn, 
                        dir = 'root_dir',
                        container=None, 
                        source='datastore'):
        """Download file from online storage"""
        fp = self.get_path(fn, dir = dir)
        fn = self.get_path(fn, dir = None)

        if source == 'blob':
            if container is None:
                container = self.project_name
            fn = self._get_blob_fn(fn, dir)
            self._download_blob(fn, fp, container)
        elif source == 'datastore':
            self._download_datastore(fn, dir = dir)
        elif source == 'model':
            self._download_model(fn, dir = dir)
        else:
            logging.warning(f'[ERROR] Source <{source}> does not exist. Cannot download file.')
        logging.info(f'[INFO] Downloaded data {fn} from {source}')

    ##### UPLOAD #####
    def _upload_blob(self, fn, fp, container):
        """Upload to blob storage"""
        self.bbs.create_container(container, fail_on_exist = False)
        self.bbs.create_blob_from_path(container, fn, fp)

    def _upload_dataset(self, fn, fp):
        """Upload dataset to AzureML Datastore
        Note:
        -only works for single file or directory
        -not meant for model assets, see _upload_model
        """
        datastore = self.ws.get_default_datastore()

        if isinstance(fp, list) or os.path.isfile(fp):
            if not isinstance(fp, list):
                fp = [fp]
            datastore.upload_files(fp,
                                target_path = fn,
                                overwrite = True,
                                show_progress = True)
        elif os.path.isdir(fp):
            datastore.upload(src_dir = str(fp),
                        target_path = fn,
                        overwrite = True,
                        show_progress = True)
        else:
            raise Exception(f'File type not determined for {fp}, could not upload to datastore.')
        ds = Dataset.File.from_files([(datastore, fn)])
        ds.register(workspace = self.ws,
                    name = fn,
                    description = f'Data set for {self.task}',
                    create_new_version = True)

    def _upload_model(self, fn, fp):
        """Upload model assets to AzureML Models
        
        NOTE: expects folder.
        """
        Model.register( workspace   = self.ws,
                        model_name  = fn[:31],
                        model_path  = fp,
                        description='Model assets',
                        tags={'task' : self.task,
                            'language': cu.params.get('language'), 
                            'environment': cu.params.get('environment')}
                    )

    def upload(self,    fn, 
                        destination, 
                        dir = 'root_dir', 
                        container = None):
        """Upload any data or assets to the cloud"""
        fp = self.get_path(fn, dir = dir)
        fn = self.get_path(fn, dir = None)

        if destination == 'dataset':
            self._upload_dataset(fn, fp)
        elif destination == 'model':
            self._upload_model(fn, fp)
        elif destination == 'blob':
            if container is None:
                container = self.project_name
            fn = self._get_blob_fn(fn, dir)
            self._upload_blob(fn, fp, container)
        else:
            raise Exception(f'[ERROR] Destination <{destination}> does not exist. Can not upload file(s).')
        logging.info(f'[INFO] Upload of {fn} to <{destination}> completed.')

    ##### I/O #####
    def save(self, data, fn, file_type = 'dataframe', dir = 'root_dir', 
                sep = '\t', encoding = 'utf-8', header = True, index = False):
        """Data saver
        
        Save/dump supported data types in standardized manner.
        """
        fn = self.get_path(fn, dir=dir)
        if file_type == 'dataframe':
            data.to_csv(fn, sep=sep, encoding=encoding, index=index, header=header)
        elif file_type == 'list':
            with open(fn, 'w', encoding=encoding) as f:
                f.writelines(data)
        elif file_type == 'json':
            with open(fn, 'w', encoding=encoding) as f:
                json.dump(data, f)
        elif file_type == 'numpy':
            np.save(fn, data)
        elif file_type == 'pickle':
            with open(fn, 'wb') as f:
                pickle.dump(data, f)
        else:
            raise Exception(f'[ERROR] - file type ({file_type}) not supported in data saver. {fn} not saved.')
        logging.info(f'SAVED: {fn}')

    def load(self, fn, file_type = 'dataframe', dir = 'root_dir',
                    sep = '\t', encoding = 'utf-8', header = 'infer', low_memory = True, dtype = None):
        """Data loader
        
        Load/read supported data types in standardized manner.
        """
        fn = self.get_path(fn, dir=dir)
        if file_type == 'dataframe':
            data = pd.read_csv(fn, sep=sep, encoding=encoding, header=header, low_memory=low_memory, dtype=dtype)
        elif file_type == 'list':
            data = [line.rstrip('\n') for line in open(fn, encoding=encoding)]
        elif file_type == 'json':
            with open(fn, encoding=encoding) as f:
                data = json.load(f)
        elif file_type == 'numpy':
            data = np.load(fn, allow_pickle=True)
        elif file_type == 'pickle':
            with open(fn, 'rb') as f:
                data = pickle.load(f)
        elif file_type == 'parquet':
            data = pd.read_parquet(fn)
        else:
            raise Exception(f'[ERROR] - file type ({file_type}) not supported in data loader. {fn} not loaded.')
        logging.info(f'LOADED: {fn}')
        return data

############################################
#####   Fetch from CosmosDB
############################################

def get_data():
    # Query for CosmosDB
    CONFIG = {
        "ENDPOINT": f"https://{he.get_secret('cosmos-db-name')}.documents.azure.com:443/",
        "PRIMARYKEY": he.get_secret('cosmos-db-key'),
        "DATABASE": "data", 
        "CONTAINER": "documents"
    }
    CONTAINER_LINK = f"dbs/{CONFIG['DATABASE']}/colls/{CONFIG['CONTAINER']}"
    FEEDOPTIONS = {}
    FEEDOPTIONS["enableCrossPartitionQuery"] = True
    QUERY = {
        "query": f"SELECT * from c where c.status = 'train' and CONTAINS(c.language, '{cu.params.get('language')}')"
    }
    # Initialize the Cosmos client
    client = cosmos_client.CosmosClient(
        url_connection=CONFIG["ENDPOINT"], auth={"masterKey": CONFIG["PRIMARYKEY"]}
    )
    # Query for some data
    results = client.QueryItems(CONTAINER_LINK, QUERY, FEEDOPTIONS)
    return results

def get_label(obj, task):
    out = dict()
    for o in obj:
        if 'class' in task:
            _key = f"{task}_{o.get('task_type')}"
            _value = o.get('version')[0].get('value')
            out[_key] = _value
        elif 'answer' in task:
            for k in o.keys():
                _key = f'{task}_{k}'
                _value = o.get(k)
                out[_key] = _value
    return out

def get_dataset(cl, source="cdb"):
    # Transform request result
    if source == "cdb":
        results = get_data()
        data = cu.prepare_source(results)
        if 'label_classification' in data.columns:
            lbl_class = data.label_classification.apply(lambda x: get_label(x, 'label_classification')).to_list()
            data = pd.concat([data, pd.DataFrame(lbl_class)], axis = 1)
        #TODO: temporary workaround for data
        data['label_classification_multi'] = data['label_classification_simple']
        data['label_classification_simple'] = data['label_classification_simple'].apply(lambda x: x.split(',')[0])
        ##end temp workaround
        if 'label_ner' in data.columns:
            label_ner = data.label_answer.apply(lambda x: get_label(x, 'label_ner')).to_list()
            data = pd.concat([data, pd.DataFrame(label_ner)], axis = 1)
        if 'label_answer' in data.columns:
            lbl_answer = data.label_answer.apply(lambda x: get_label(x, 'label_answer')).to_list()
            data = pd.concat([data, pd.DataFrame(lbl_answer)], axis = 1)
    elif source == "datastore":
        if not os.path.isfile(cl.dt.get_path('fn_source')):
            cl.dt.download('fn_source', dir = 'root_dir', source = 'datastore')
        data = cl.dt.process(data_type=cu.params.get('prepare').get('data_type'))
    cl.dt.save(data, 'fn_prep', dir = 'data_dir')
    return data