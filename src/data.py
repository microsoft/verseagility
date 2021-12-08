"""
Helper function for data management

All directories, files and model assets 
should pass via the data_manager.

Add custom directories and files to 
the dir_lookup and fn_lookup objects.

"""
import logging
log = logging.getLogger(__name__)

import pandas as pd
import numpy as np
import pickle
import json
import os
from pathlib import Path
from azure.cosmos import cosmos_client
from azureml.core import Workspace, Dataset

# Custom functions
import sys
sys.path.append('../src')
import helper as he
import custom as cu

try:
    from azureml.core import Run, Dataset, Model, Workspace
    from azureml.core.authentication import InteractiveLoginAuthentication
except Exception as e:
    log.warning(f'Azure Machine Learning is not installed, \
        but may not be needed for local development or endpoint deployment. Details: {e}')

try:
    from azure.storage.blob import BlockBlobService
except Exception as e:
    log.warning(f'Azure Storage Account (2.1.0) not installed, \
        but may not be needed for local development or endpoint deployment. Details: {e}')
    #TODO:  Azure Storage Account package needs to be upgraded to v12. This will break the 
    #       current implementation.

def get_repo_dir():
    """Get repository root directory"""
    root_dir = './'
    if os.path.isdir(Path(__file__).parent.parent / 'src'):
        root_dir = f"{str((Path(__file__).parent.parent).resolve())}/"
    elif os.path.isdir('../src'):
        root_dir = '../'
    elif os.path.isdir('./src'):
        root_dir = './'
    else:
        log.warning('ROOT FOLDER NOT FOUND.')
    return root_dir

def get_asset_dir():
    """Get assets directory"""
    asset_dir = ''
    if os.path.isdir(Path(__file__).parent.parent / 'assets'):
        asset_dir = f"{str((Path(__file__).parent.parent).resolve() / 'assets')}/"
    elif os.path.isdir('../assets'):
        asset_dir = '../assets/'
    elif os.path.isdir('./assets'):
        asset_dir = './assets/'
    else:
        log.warning(f'ASSETS FOLDER NOT FOUND. {os.getcwd()}')
    return asset_dir

def get_local_dir():
    """Get the local data repository, as specified in the local config"""
    try:
        run_config = he.get_config(section='data')
        data_dir = run_config['dir']
    except Exception as e:
        log.info(f'No config.ini found ({e}), using repository root as default dir.')
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
            _base = "azureml-models" 
            #NOTE: this input changes everytime, therefore hardcoded
            # os.environ['AZUREML_MODEL_DIR']
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
        
        log.info(f'[INFO] Root directory: {self.root_dir}')
        log.info(f'[INFO] Data directory: {self.data_dir}')
        log.info(f'[INFO] Model directory: {self.model_dir}')
        
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
        self.ws = he.get_aml_ws()

        # Load Storage Account
        try:
            blob_connection_string = he.get_secret('storage-connection-string')
            self.bbs = BlockBlobService(connection_string = blob_connection_string)
        except Exception as e:
            log.warning(f'[WARNING] Connection to Storage Account not established, \
                but may not be needed for local development or endpoint deployment. Details: {e}')

    def get_path(self, 
                fn, 
                dir = 'root_dir'
            ):
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
        """Get relative file path for Storage Account"""
        if dir == 'train_dir':
            fn = f'{self.train_dir}/{fn}'
        elif dir == 'raw_dir':
            fn = f'{self.raw_dir}/{fn}'
        elif dir == 'intermediate_dir':
            fn = f'{self.intermediate_dir}/{fn}'
        return fn

    def _trim_model_name(self, fn):
        """Trim Model Name to Max Length of AML MM"""
        return fn[:31]
    
    ##### DOWNLOAD #####
    def _download_blob(self, fn, fp, container):
        """Download from blob storage account"""
        self.bbs.get_blob_to_path(container, fn, fp)

    def _download_datastore(self, fn, dir = 'data_dir'):
        """Download from AML Data Store"""
        Dataset.get_by_name(workspace = self.ws, name = fn).download(target_path = self.get_path(dir), overwrite = True)
    
    def _download_model(self, fn, dir = 'model_dir', version = None):
        """Download from AML Model Management"""
        _model = Model(self.ws, name = fn, version = version)
        _model.download(self.get_path(dir), exist_ok = True)
        log.info(f'MODEL INFO: name = {_model.name}, version = {_model.version}')

    def download(self, fn, 
            dir = 'root_dir',
            container=None,
            source='datastore'
            ):
        """Download file from online storage"""
        fp = self.get_path(fn, dir = dir)
        fn = self.get_path(fn, dir = None)

        if source == 'blob':
            if container is None:
                container = self.project_name
            fn = self._get_blob_fn(fn, dir)
            log.debug(f'Starting blob download: {fn}, in {container}')
            self._download_blob(fn, fp, container)
        elif source == 'datastore':
            self._download_datastore(fn, dir = dir)
        elif source == 'model':
            log.debug(f'Starting model download: {self._trim_model_name(fn)}, in {dir}')
            self._download_model(self._trim_model_name(fn), dir = dir)
        else:
            raise Exception(f'[ERROR] Source <{source}> does not exist. \
                Cannot download file {fn}.')
        log.info(f'DOWNLOADED: {fn} FROM: {source}')

    ##### UPLOAD #####
    def _upload_blob(self, fn, fp, container):
        """Upload to blob storage"""
        self.bbs.create_container(container, fail_on_exist = False)
        self.bbs.create_blob_from_path(container, fn, fp)

    def _upload_datastore(self, fn, fp):
        """Upload dataset to AzureML Datastore
        Note:
        -only works for sinlge/multiple file(s) or single directory
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
            raise Exception(f'File type not determined for {fp}. \
                Could not upload to datastore.')
        ds = Dataset.File.from_files([(datastore, fn)])
        ds.register(workspace = self.ws,
                    name = fn,
                    description = f'Data set for {self.task}',
                    create_new_version = True)

    def _upload_model(self, fn, fp):
        """Upload model assets to AzureML Models
        
        NOTE: expects model folder.
        """
        Model.register( workspace   = self.ws,
                        model_name  = self._trim_model_name(fn),
                        model_path  = fp,
                        description='Model assets',
                        tags={'task' : self.task,
                            'language': cu.params.get('language'), 
                            'environment': cu.params.get('environment')}
                    )

    def upload(self,    
                fn, 
                destination, 
                dir = 'root_dir', 
                container = None
            ):
        """Upload any data or assets to the cloud
        
        NOTE: only works with single files
        """
        fp = self.get_path(fn, dir = dir)
        fn = self.get_path(fn, dir = None)

        if destination == 'dataset':
            self._upload_datastore(fn, fp)
        elif destination == 'model':
            self._upload_model(fn, fp)
        elif destination == 'blob':
            if container is None:
                container = self.project_name
            fn = self._get_blob_fn(fn, dir)
            self._upload_blob(fn, fp, container)
        else:
            raise Exception(f'[ERROR] Destination <{destination}> does not exist. \
                Cannot upload file {fn}.')
        log.info(f'UPLOADED: {fn} TO: <{destination}>')

    ##### I/O #####
    def save(self, 
                data, fn, file_type = 'csv', dir = 'root_dir', 
                sep = '\t', encoding = 'utf-8', header = True, 
                index = False, sheet_name = 'Sheet1'
            ):
        """Data saver
        
        Save/dump supported data types in standardized manner.
        """
        fn = self.get_path(fn, dir=dir)
        if file_type == 'csv':
            data.to_csv(fn, sep = sep, encoding = encoding, index = index, header = header)
        elif file_type == 'excel':
            data.to_excel(fn, sheet_name = sheet_name, header = header, index = index)
        elif file_type == 'list':
            with open(fn, 'w', encoding = encoding) as f:
                f.writelines(data)
        elif file_type == 'json':
            with open(fn, 'w', encoding = encoding) as f:
                json.dump(data, f)
        elif file_type == 'numpy':
            np.save(fn, data)
        elif file_type == 'pickle':
            with open(fn, 'wb') as f:
                pickle.dump(data, f)
        else:
            raise Exception(f'[ERROR] - file type ({file_type}) not supported in data saver. {fn} not saved.')
        log.info(f'SAVED: {fn}')

    def load(self, 
                fn, file_type = 'csv', dir = 'root_dir',
                sep = '\t', encoding = 'utf-8', header = 'infer', 
                low_memory = True, dtype = None, sheet_name=0
            ):
        """Data loader
        
        Load/read supported data types in standardized manner.
        """
        fn = self.get_path(fn, dir=dir)
        if file_type == 'csv':
            data = pd.read_csv(fn, sep=sep, encoding=encoding, header=header, 
                                    low_memory=low_memory, dtype=dtype, error_bad_lines=False)
        elif file_type == 'excel':
            data = pd.read_excel(fn, sheet_name=sheet_name, header=header, dtype=dtype)
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
        log.info(f'LOADED: {fn}')
        return data

############################################
#####   Fetch from CosmosDB
############################################

def get_data(src="cdb", dataset_name=None):
    if src == "cdb":
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
    elif src == "tabular" and dataset_name is not None:
        workspace = he.get_aml_ws()
        results = Dataset.get_by_name(workspace, name=dataset_name).to_pandas_dataframe()
        log.warning(f'[INFO] - Collected {dataset_name} dataset from AML.')
    else:
        log.warning('[WARNING] - Could not load data set, please verify source and data set name.')
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

def get_dataset(cl, source="cdb", dataset_name=None):
    # Transform request result
    if source == "cdb":
        results = get_data("cdb")
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
    elif source == "tabular":
        data = get_data("tabular", dataset_name)
    cl.dt.save(data, 'fn_prep', dir = 'data_dir')
    return data