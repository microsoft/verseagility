"""
Helper function for data management
Includes source & prepared data, as well as
model assets.

"""
import pandas as pd
import json
import os
import pathlib
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

class Data():
    def __init__(self,  task            =   1,
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
        ## Assuming deployment via AzureML
        if 'AZUREML_MODEL_DIR' in os.environ:
            self.data_dir = os.environ['AZUREML_MODEL_DIR']
        else:
            self.data_dir = cu.params.get('data_dir')
            os.makedirs(self.data_dir, exist_ok=True)
        logger.warning(f'[INFO] Root data directory: {self.data_dir}')
        
        
        ## Model directory
        self.model_dir  = str(Path(self.data_dir + f"/model_type-l{self.language}-t{self.task}-{self.env}").resolve())
        ### NOTE: source file expected to follow naming convention, otherwise edit here
        self.fn_source = f"{cu.params.get('name')}-source.{cu.params.get('prepare').get('data_type')}"
        self.fp_train = f"{cu.params.get('name')}-train-{cu.params.get('environment')}"

        # Lookup
        self.fn_lookup = {
            ## DATASTORE
            'fn_source' : self.fn_source,
            'fp_train' : self.fp_train,
            ## LOCAL
            'fp_data'   : os.path.abspath(self.data_dir),
            'fn_prep'   : f'{self.data_dir}/data-l{self.language}.txt',
            'fn_clean'  : f'{self.data_dir}/clean-l{self.language}-t{self.task}.txt',
            'fn_train'  : f'{self.data_dir}/train-l{self.language}-t{self.task}.txt',
            'fn_test'   : f'{self.data_dir}/test-l{self.language}-t{self.task}.txt',
            'fn_label'  : f'{self.data_dir}/label-l{self.language}-t{self.task}.txt',
            'fn_eval'   : f'TODO:',
            ## ASSETS
            'fn_asset'      : f'{self.data_dir}/assets-{self.language}.zip',     
            'fn_cat'        : self.model_dir.replace('model_type', cu.params.get('tasks').get('1').get('model_type')),
            'fn_rank'       : f'{self.data_dir}/data-l{self.language}-t4.pkl',
            'fn_ner_list'   : f'{self.data_dir}/ner.txt',
            'fn_ner_flair'  : f'{self.data_dir}/{he.get_flair_model(self.language, "fn")}',
            'fn_ner_spacy'  : f'TODO:',
            'fn_names'      : f'{self.data_dir}/names.txt',
            'fn_stopwords'  : f'{self.data_dir}/stopwords-{self.language}.txt',
        } #TODO: when to link data dir, when only filename?
        # for t in cu.params.get('tasks'): #TODO: auto generate fetching param list
        #     task_property = cu.params.get('tasks').get(t)
        #     self.fn_lookup[f'fn_{task_property.get('type')}']

        # Files
        self.fn_data = self.fn_lookup['fn_prep']

        # AML Components
        try:
            run = Run.get_context()
            self.ws = run.experiment.workspace
        except Exception as e:
            logger.warning(f'[WARNING] AML Workspace not loaded -> {e}')

    ### DOWNLOAD
    def _download_blob(self):
        # self.block_blob_service = BlockBlobService(account_name=run_config['blob']['account'], 
        #                                             account_key=run_config['blob']['key'])
        # if no_run_version:
        #     self.block_blob_service.get_blob_to_path(container, fn_blob, fn_local)
        # elif not encrypted:
        #     self.block_blob_service.get_blob_to_path(container, 
        #             str(fn_blob).replace('./',''),
        #             fn_local)
        # elif encrypted:
        #     self.block_blob_service.get_blob_to_path(container, 
        #             str(fn_blob).replace('.txt', '.enc').replace('./',''),
        #             fn_local)
        # if to_dataframe:
        #     with open(str(fn_local), "rb") as text_file:
        #         _data = text_file.read()
        #     if encrypted:
        #         df = decrypt(_data, dataframe=True)
        #     else:
        #         df = pd.read_csv(_data, sep='\t', error_bad_lines=False, warn_bad_lines=False,  encoding='utf-8') 
        #     df.to_csv(fn_local, sep='\t', encoding='utf-8', index=False)
        pass

    def _download_datastore(self):
        pass

    def _download_model(self):
        #NOTE: not needed when running on AML compute
        pass

    def download(self, dataset_name=None, 
                        task='',
                        step='',
                        container=None, 
                        fn_blob=None, 
                        fn_local=None,
                        no_run_version=False,
                        encrypted=False,
                        to_dataframe=False,
                        source='datastore'):
        """Download file from online storage"""
        if source == 'blob':
            self._download_blob() #TODO:
        elif source == 'datastore':
            run = Run.get_context()
            ws = run.experiment.workspace
            if dataset_name is None:
                dataset_name = f'{cu.params.get("name")}-{task}-{step}-{cu.params.get("environment")}'
            try:
                Dataset.get_by_name(workspace=ws, name=dataset_name).download(self.data_dir, overwrite=True)
            except Exception as e:
                logger.warning(f'[WARNING] Dataset {dataset_name} not found. Trying without <env>. -> {e}')
                Dataset.get_by_name(workspace=ws, name=dataset_name.replace(f'_{self.env}', '')).download(self.data_dir, overwrite=True)
            else:
                logger.warning(f'[INFO] Downloaded data from data store {dataset_name}')
        elif source == 'model':
            pass
        else:
            logger.warning(f'[ERROR] Source <{source}> does not exist. Can not download file.')

    ### UPLOAD
    def _upload_dataset(self, fp, task, step, ws):
        """Upload dataset to AzureML Datastore
        Note:
        -only works for single file or directory
        -not meant for model assets
        """
        target_name = f'{cu.params.get("name")}-{task}-{step}-{cu.params.get("environment")}'
        datastore = ws.get_default_datastore()
        datastore.upload(src_dir = str(fp),
                            target_path = target_name,
                            overwrite = True,
                            show_progress = True)
        ds = Dataset.File.from_files([(datastore, target_name)])
        #ds = Dataset.File.from_files(path=[fp])
        ds.register(workspace = ws,
                    name = target_name,
                    description = f'Data set for {step}',
                    create_new_version = True)

    def _upload_model(self, fp, task, ws):
        """Upload model to AzureML Models"""
        Model.register(workspace=ws,
                model_name=f'{cu.params.get("name")}-{task}-{cu.params.get("environment")}',
                model_path=fp, # Local file to upload and register as a model.
                description='Model assets',
                tags={'task' : task,
                        # 'model_type': model_type,
                        'language': cu.params.get('language'), 
                        'environment': cu.params.get('environment')})

    def upload(self, fp, task='', step='', destination='model'):
        if fp in self.fn_lookup:
            fp = self.fn_lookup[fp]
        if destination == 'dataset':
            self._upload_dataset(fp, task, step, self.ws)
        elif destination == 'model':
            self._upload_model(fp, task, self.ws)
        else:
            logger.warning(f'[ERROR] Destination <{destination}> does not exist. Can not upload file.')
        logger.warning(f'[INFO] Upload complete to <{destination}> completed.')

    ## PROCESS
    def process(self, data_type='json', save=True):
        """Convert source data to normalized data structure"""
        # Load source data
        if data_type == 'json':
            with open(self.data_dir + self.fn_source, encoding='utf-8') as fp:
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

    def save(self, data, fn, header=True):
        data.to_csv(self.fn_lookup[fn], sep='\t', encoding='utf-8', index=False, header=header)
        logger.warning(f'SAVED: {self.fn_lookup[fn]}')

    def load(self, fn, header=0, encoding='utf-8', file_type='dataframe'):
        if file_type == 'dataframe':
            return pd.read_csv(self.fn_lookup[fn], sep='\t', encoding=encoding, header=header)
        elif file_type == 'list':
            with open(self.fn_lookup[fn], encoding=encoding) as f:
                data = f.readlines()
            return data
        else:
            raise Exception(f'ERROR - file type ({file_type}) not supported in data loader')