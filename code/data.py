import pandas as pd
import json
import os
import pathlib
from io import StringIO
from pathlib import Path
from azureml.core import Dataset, Run, Workspace
# from azure.storage.blob import BlockBlobService

# Custom functions
import sys
sys.path.append('../code')
import helper as he
import custom as cu

# Get config
run_config = he.get_config()
logger = he.get_logger(location=__name__)

flair_model_lookup = {
    'en' : 'en-ner-ontonotes-fast-v0.4.pt', 
    'de' : 'ner-multi-fast.pt',
    'xx' : 'ner-multi-fast.pt'
}

class Data():
    def __init__(self, fn_source    =   'answers_microsoft_lang.json',
                    task            =   1,
                    version         =   1,
                    env             =   1,
                    inference       =   False
                ):
        # Parameters
        self.task = task
        self.language = cu.params.get('language')
        self.version = version
        self.env = env

        # Directories
        ## Asset directory
        if inference:
            ## Assuming deployment via AzureML
            try:
                self.data_dir = os.environ['AZUREML_MODEL_DIR']
            except KeyError:
                logger.info(f'[WARNING] Not running on AML')
                self.data_dir = he.run_config['path']['infer_dir']
        else:
            self.data_dir = he.run_config['path']['data_dir']
        ## Model directory
        self.model_dir  = str(Path(self.data_dir + f"/model_type-l{self.language}-t{self.task}").resolve())
        ### If present, replace language tag in name
        fn_source = fn_source.replace('lang', self.language)

        # Lookup
        self.fn_lookup = {
            'fn_source' : fn_source,
            'fn_prep'   : f'data_l{self.language}.txt',
            'fn_clean'  : f'clean_l{self.language}_t{self.task}.txt',
            'fn_train'  : f'train_l{self.language}_t{self.task}.txt',
            'fn_test'   : f'test_l{self.language}_t{self.task}.txt',
            'fn_label'  : f'label_l{self.language}_t{self.task}.txt',
            'fn_eval'   : f'TODO:',
            ## ASSETS #TODO: auto generate fetching param list
            'fn_asset'      : f'{self.data_dir}/assets_{self.language}.zip',     
            'fn_cat'        : self.model_dir.replace('model_type', cu.params.get('tasks').get('1').get('model_type')),
            'fn_rank'       : f'{self.data_dir}/data_l{self.language}_t4.pkl',
            'fn_ner_list'   : f'{self.data_dir}/ner.txt',
            'fn_ner_flair'  : f'{self.data_dir}/{flair_model_lookup[self.language]}',
            'fn_ner_spacy'  : f'TODO:',
            'fn_names'      : f'{self.data_dir}/names.txt',
            'fn_stopwords'  : f'{self.data_dir}/stopwords_{self.language}.txt',
        }

        # Files
        self.fn_source = fn_source
        self.fn_data = self.fn_lookup['fn_prep']

    def download(self, container=None, fn_blob=None, fn_local=None,
                        no_run_version=False,
                        encrypted=False,
                        to_dataframe=False,
                        source='blob'):
        """Download file from Azure"""
        if source == 'blob':
            self.block_blob_service = BlockBlobService(account_name=run_config['blob']['account'], 
                                                        account_key=run_config['blob']['key'])
            if no_run_version:
                self.block_blob_service.get_blob_to_path(container, fn_blob, fn_local)
            elif not encrypted:
                self.block_blob_service.get_blob_to_path(container, 
                        str(fn_blob).replace('./',''),
                        fn_local)
            elif encrypted:
                self.block_blob_service.get_blob_to_path(container, 
                        str(fn_blob).replace('.txt', '.enc').replace('./',''),
                        fn_local)
            if to_dataframe:
                with open(str(fn_local), "rb") as text_file:
                    _data = text_file.read()
                if encrypted:
                    df = decrypt(_data, dataframe=True)
                else:
                    df = pd.read_csv(_data, sep='\t', error_bad_lines=False, warn_bad_lines=False,  encoding='utf-8') 
                df.to_csv(fn_local, sep='\t', encoding='utf-8', index=False)
        elif source == 'datastore':
            run = Run.get_context()
            ws = run.experiment.workspace
            dataset_name = self.fn_source.split('.')[0]
            Dataset.get_by_name(workspace=ws, name=dataset_name).download(self.data_dir, overwrite=True)
            logger.info(f'[INFO] Downloaded data from data store {dataset_name}')
        else:
            logger.info('[ERROR] Source <{source}> does not exist. Can not download file.')

    def upload(self):
        #TODO:
        pass

    def process(self, data_type='json', save=True):
        """Convert source data to normalized data structure"""
        
        # Load source data
        if data_type == 'json':
            with open(self.data_dir + self.fn_source, encoding='utf-8') as fp:
                data = json.load(fp)
        elif data_type == 'dataframe':
            data = self.load('fn_source')
        else:
            logger.info('SOURCE DATA TYPE NOT SUPPORTED')
       
        # Custom steps
        df = cu.prepare_source(data)

        # Store data
        if save:
            self.save(df, 'fn_prep')
        return df

    def save(self, data, fn, header=True):
        data.to_csv(self.data_dir + self.fn_lookup[fn], sep='\t', encoding='utf-8', index=False, header=header)
        logger.info(f'SAVED: {self.fn_lookup[fn]}')

    def load(self, fn, header=0):
        return pd.read_csv(self.data_dir + self.fn_lookup[fn], sep='\t', encoding='utf-8', header=header)