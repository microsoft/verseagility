"""
Helper function for data management
Includes source & prepared data, as well as
model assets.

"""
import pandas as pd
import numpy as np
import pickle
import json
import os
from io import StringIO
from pathlib import Path
from azureml.core import Run, Dataset, Model
# from azure.storage.blob import BlockBlobService

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
    logger.warning(f'AML not installed -> {e}')

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
        logger.warning(f'ROOT FOLDER NOT FOUND. {os.getcwd()}')
    return root_dir

def get_assets_dir():
    """Get assets directory"""
    assets_dir = ''
    if os.path.isdir(Path(__file__).parent.parent / 'assets'):
        assets_dir = f"{str((Path(__file__).parent.parent).resolve() / 'assets')}/"
    elif os.path.isdir('../assets'):
        assets_dir = '../assets/'
    elif os.path.isdir('./assets'):
        assets_dir = './assets/'
    else:
        logger.warning(f'ASSETS FOLDER NOT FOUND. {os.getcwd()}')
    return assets_dir

class Data():
    def __init__(self,  task            =   1,
                        version         =   1,
                        inference       =   False,
                        download_source =   False, #TODO:
                        download_train  =   False
                ):
        # Parameters
        self.name = cu.params.get('name')
        self.task = task
        self.language = cu.params.get('language')
        self.version = version
        self.env = cu.params.get('environment')

        # Directories
        self.data_dir = f'{self.name}-data-{self.task}'
        self.model_dir = f"{self.name}-model-t{self.task}"
        ## Assuming deployment via AzureML
        if 'AZUREML_MODEL_DIR' in os.environ:
            _dir = f"{os.environ['AZUREML_MODEL_DIR']}/{self.model_dir}"
            if os.path.isdir(_dir):
                ### Deployed with multiple model objects in AML
                self.root_dir = f'{_dir}/{os.listdir(_dir)[0]}/'
            else:
                ### Deployed with single model objects in AML
                self.root_dir = f"{os.environ['AZUREML_MODEL_DIR']}/"
        else:
            self.root_dir = f"{os.path.abspath(cu.params.get('data_dir'))}/"
            os.makedirs(f"{self.root_dir}{self.data_dir}", exist_ok=True)
            os.makedirs(f"{self.root_dir}{self.model_dir}", exist_ok=True)
        
        logger.warning(f'[INFO] Root directory: {self.root_dir}')
        logger.warning(f'[INFO] Data directory: {self.data_dir}')
        logger.warning(f'[INFO] Model directory: {self.model_dir}')

        # Lookup
        ## Directory
        self.dir_lookup = {
            'repo_dir'   : get_repo_dir(),
            'root_dir'   : self.root_dir,
            'data_dir'   : self.data_dir,
            # 'train_dir'  : self.train_dir,
            'model_dir'  : self.model_dir,
            'asset_dir'  : get_assets_dir()
        }
        ## Filename
        self.fn_lookup = {
            'fn_source'     : f"{self.name}-source.json",
            'fn_prep'       : f'data-l{self.language}.txt',
            'fn_train'      : f'train-l{self.language}-t{self.task}.txt',
            'fn_clean'      : f'clean-l{self.language}-t{self.task}.txt',
            'fn_test'       : f'test-l{self.language}-t{self.task}.txt',
            'fn_label'      : f'label-l{self.language}-t{self.task}.txt',
            'fn_rank'       : f'data-l{self.language}-t4.pkl',
            'fn_ner_list'   : f'ner.txt',
            'fn_ner_flair'  : f'{he.get_flair_model(self.language, "fn")}',
            'fn_names'      : f'names.txt',
            'fn_stopwords'  : f'stopwords-{self.language}.txt',
        }

        # Load AML
        try:
            run = Run.get_context()
            self.ws = run.experiment.workspace
        except Exception as e:
            #TODO: for local runs only
            # auth = InteractiveLoginAuthentication(tenant_id="72f988bf-86f1-41af-91ab-2d7cd011db47")
            # self.ws = Workspace.get(name='nlp-ml', 
            #                 subscription_id='50324bce-875f-4a7b-9d3c-0e33679f5d72', 
            #                 resource_group='nlp',
            #                 auth=auth)
            logger.warning(f'[WARNING] AML Workspace not loaded -> {e}')

        # Load Storage Account
        try:
            from azure.storage.blob import BlockBlobService
            self.blob_connection_string = ''
            self.bbs = BlockBlobService(connection_string=self.blob_connection_string)
        except Exception as e:
            logger.warning(f'[WARNING] Storage account not loaded -> {e}')


    def get_path(self, fn, dir='root_dir'):
        """Resolve standardized file and directory paths"""
        # Resolve fn
        if fn in self.fn_lookup:
            fn = self.fn_lookup.get(fn)
        elif fn in self.dir_lookup:
            if 'root' in fn:
                dir = None
            fn = self.dir_lookup.get(fn)

        # Append directory
        # ## If deployed to AML
        # if fn in self.root_dir:
        #     fn = self.root_dir
        #     dir = None
        # ## Else append directory
        if dir is not None:
            if dir == 'repo_dir':
                fn = f"{self.dir_lookup.get('repo_dir')}{fn}"
            elif dir == 'root_dir':
                fn = f"{self.root_dir}{fn}"
            elif dir == 'data_dir':
                fn = f"{self.root_dir}{self.data_dir}/{fn}"
            elif dir == 'model_dir':
                fn = f"{self.root_dir}{self.model_dir}/{fn}"
            elif dir == 'asset_dir':
                fn = f"{self.dir_lookup.get('asset_dir')}{fn}"
        return fn

    ##### DOWNLOAD #####
    def _download_blob(self, fn, fp):
        """Download from blob storage account"""
        self.bbs.get_blob_to_path(self.name, fn, fp)

    def _download_datastore(self, fn, dir='data_dir'):
        """Download from AML Data Store"""
        Dataset.get_by_name(workspace=self.ws, name=fn).download(target_path=self.get_path(dir), overwrite=True)
    
    def _download_model(self, fn, dir='model_dir'):
        """Download from AML Model Management"""
        Model(self.ws, name=fn).download(self.get_path(dir))
        #NOTE: models are loaded in inference, and do not need to be downloaded

    def download(self, fn ='', 
                        dir = 'root_dir',
                        container=None, 
                        source='datastore'):
        """Download file from online storage"""
        fn = self.get_path(fn, dir=None)
        fp = self.get_path(fn, dir=dir)

        if source == 'blob':
            self._download_blob(fn, fp)
        elif source == 'datastore':
            self._download_datastore(fn, dir = dir)
        elif source == 'model':
            self._download_model(fn)  # TODO: include dir
        else:
            logger.warning(f'[ERROR] Source <{source}> does not exist. Cannot download file.')
        logger.warning(f'[INFO] Downloaded data {fn} from {source}')

    ### UPLOAD
    def _upload_blob(self, fn, fp):
        """Upload to blob storage"""
        self.bbs.create_blob_from_path(self.name, fn, fp)
    
    def _upload_datastore(self, fn, fp):
        """Upload dataset to AzureML Datastore
        Note:
        -only works for single file or directory
        -not meant for model assets, see _upload_model
        """
        datastore = self.ws.get_default_datastore()
        if os.path.isdir(fp):
            datastore.upload(src_dir = fp,
                        target_path = fn,
                        overwrite = True,
                        show_progress = True)
        elif os.path.isfile(fp):
            datastore.upload_files([fp],
                                target_path = fn,
                                overwrite = True,
                                show_progress = True)
        else:
            raise Exception(f'File type not determined for {fn}, could not upload to datastore.')
        ds = Dataset.File.from_files([(datastore, fn)])
        ds.register(workspace = self.ws,
                    name = fn,
                    description = f'Data for task {self.task}',
                    create_new_version = True)

    def _upload_model(self, fn, fp):
        """Upload model assets to AzureML Models"""
        Model.register(workspace = self.ws,
                model_name= fn, 
                model_path=fp, # Local file to upload and register as a model.
                description='Model assets',
                tags={'task' : self.task,
                    'language': cu.params.get('language'), 
                    'environment': cu.params.get('environment')})
    
    def upload(self,    fp, 
                        dir='root_dir', 
                        destination='model'):
        """Upload any data or assets to the cloud"""
        fn = self.get_path(fp, dir=None)
        fp = self.get_path(fp, dir=dir)

        if destination == 'blob':
            self._upload_blob(fn, fp)
        elif destination == 'dataset':
            self._upload_datastore(fn, fp)
        elif destination == 'model':
            self._upload_model(fn, fp) 
        else:
            logger.warning(f'[ERROR] Destination <{destination}> does not exist. Cannot upload file.')
        logger.warning(f'[INFO] Upload complete to <{destination}> completed.')

    ##### PROCESS #####
    def process(self, data_type='json', save=True):
        """Convert source data to normalized data structure"""
        # Load source data
        if data_type == 'json':
            with open(self.get_path('fn_source', dir='root_dir'), encoding='utf-8') as fp:
                data = json.load(fp)
        elif data_type == 'dataframe':
            data = self.load('fn_source')
        else:
            logger.warning('SOURCE DATA TYPE NOT SUPPORTED')
       
        # Custom steps
        df = cu.prepare_source(data)

        # Store data
        if save:
            self.save(df, 'fn_prep')
        return df

    ##### I/O #####
    def save(self, data, fn, file_type='dataframe', dir = 'data_dir', 
                sep='\t', encoding='utf-8', header=True, index=False):
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
            data.save(fn)
        elif file_type == 'pickle':
            with open(fn, 'wb') as f:
                pickle.dump(data, f)
        else:
            raise Exception(f'[ERROR] - file type ({file_type}) not supported in data saver. {fn} not saved.')
        logger.warning(f'SAVED: {fn}')

    def load(self, fn, file_type='dataframe', dir = 'data_dir',
                    sep='\t', encoding='utf-8', header=0, low_memory=True, dtype=None):
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
            data = np.load(fn)
        elif file_type == 'pickle':
            with open(fn, 'rb') as f:
                data = pickle.load(f)
        elif file_type == 'parquet':
            data = pd.read_parquet(fn)
        else:
            raise Exception(f'[ERROR] - file type ({file_type}) not supported in data loader. {fn} not loaded.')
        logger.warning(f'LOADED: {fn}')
        return data