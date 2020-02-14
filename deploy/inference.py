"""
PREPARE FOR DEPLOYMENT

NOTE: set language in custom.py before running

Example (in the command line):
> cd to root dir
> conda activate nlp
> python deploy/aci.py

TODO:
- fetch flair model if not found
"""
import os
import zipfile
import shutil
import json

from azureml.core.authentication import InteractiveLoginAuthentication, MsiAuthentication
from azureml.core import Workspace, Model
from azureml.core.resource_configuration import ResourceConfiguration
from azureml.core.webservice import Webservice, AciWebservice, AksWebservice
from azureml.core import Environment
from azureml.core.conda_dependencies import CondaDependencies
from azureml.core.model import InferenceConfig
from azureml.exceptions import WebserviceException

# Custom functions
import sys
sys.path.append('./code')
import helper as he
import data as dt
import custom as cu

logger = he.get_logger(location=__name__)

language = 'en'
env = 'test'
version = '0.3'
do_zip = False
upload = False
auth_enabled = False
compute_type = 'ACI'
#TODO: move to params

##############################
## CONNECT TO WORKSPACE
##############################

# try:
#     auth = MsiAuthentication()
# except Exception as e:
#     logger.warning(e)
auth = InteractiveLoginAuthentication(tenant_id="72f988bf-86f1-41af-91ab-2d7cd011db47")

ws = Workspace.get(name='nlp-ml', 
                subscription_id='50324bce-875f-4a7b-9d3c-0e33679f5d72', 
                resource_group='nlp', 
                auth=auth)

# ws = Workspace.from_config()
logger.warning(f'[INFO] Loaded Workspace {ws.name} ({ws.resource_group})')
dt_assets = dt.Data()

##############################
## ZIP DEPENDENCIES
##############################
model_name = f'nlp_{language}_{env}'
if do_zip:
    logger.warning(f'[INFO] Zipping model assets -> {model_name}')
    # Zip Assets
    with zipfile.ZipFile(dt_assets.fn_lookup['fn_asset'], 'w') as z:
        for f in cu.params.get('assets'):
            fp = dt_assets.fn_lookup[f]
            if '.' in fp:
                _new_fn = fp.split('/')[-1]
                z.write(fp, arcname=_new_fn)
                logger.warning(f'Zipped : {fp} -> {_new_fn}')
            else:
                # Iterate over all the files in directory
                for folderName, subfolders, filenames in os.walk(fp):
                    for filename in filenames:
                        filePath = os.path.join(folderName, filename)
                        _new_fn = folderName.split('/')[-1] + '/' + filename
                        z.write(filePath, arcname=_new_fn)
                        logger.warning(f'Zipped : {filePath} -> {_new_fn}')

##############################
## UPLOAD DEPENDENCIES
##############################
if upload:   
    logger.warning(f'[INFO] Uploading model assets -> {model_name}') 
    # Upload Assets
    model = Model.register(workspace=ws,
                        model_name=model_name,                      # Name of the registered model in your workspace.
                        model_path=dt_assets.fn_lookup['fn_asset'], # Local file to upload and register as a model.
                        description='NLP inference assets',
                        tags={'models': 'classification, ner, qa', 
                                'version': version,
                                'language': language, 
                                'environment': env})
else:
    logger.warning(f'[INFO] Using existing model -> {model_name}')
    model = Model(ws, model_name)

logger.warning(f'[INFO] \t Model Name: {model.name}')
logger.warning(f'[INFO] \t Model Version: {model.version}')

##############################
## CONFIGURE COMPUTE
##############################

if compute_type == 'ACI':
    compute_config = AciWebservice.deploy_configuration(cpu_cores=2, memory_gb=6, auth_enabled=auth_enabled)
elif compute_type == 'AKS':
    compute_config = AksWebservice.deploy_configuration() #TODO:
else:
    raise Exception(f'[ERROR] Compute type not valid {compute_type}')

environment = Environment('farmenv')
environment.python.conda_dependencies = CondaDependencies.create(pip_packages=[
                                                                                'azureml-defaults',
                                                                                'mlflow', 
                                                                                'azureml-mlflow',
                                                                                'spacy',
                                                                                'transformers==2.3.0',
                                                                                'scipy',
                                                                                'numpy',
                                                                                'azure-storage-blob',
                                                                                'tqdm',
                                                                                'boto3',
                                                                                'scipy>=1.3.2',
                                                                                'sklearn',
                                                                                'seqeval',
                                                                                'mlflow==1.0.0',
                                                                                'dotmap==1.3.0',
                                                                                'git+https://github.com/deepset-ai/FARM.git',
                                                                                'git+https://github.com/zalandoresearch/flair.git'
                                                                            ],
                                                                 conda_packages=[
                                                                                'pytorch',
                                                                                'torchvision',
                                                                                'gensim',
                                                                                'numpy',
                                                                                'pandas'
                                                                            ])

# Move config file
##NOTE: only for local deployment
fn_config_infer = 'config.json'
shutil.copy(f'./project/msforum_{language}.config.json', f'./code/{fn_config_infer}')

os.chdir('./code')

inference_config = InferenceConfig(entry_script='infer.py',
                                   source_directory='.',
                                   environment=environment)

##############################
## DEPLOY COMPUTE
##############################

# Create or update service
service_name = f'nlp-{language}-{env}'
try:
    ## Retrieve existing service.
    service = Webservice(name=service_name, workspace=ws)
    logger.warning('[INFO] Updating web service')
    ## Update to new model(s).
    service.update(models=[model], inference_config=inference_config)
    service.wait_for_deployment(show_output=True)
except WebserviceException:
    ## Create web service
    service = Model.deploy(ws, service_name, [model], inference_config, deployment_config=compute_config, overwrite=True)
    logger.warning('[INFO] Creating web service')
    service.wait_for_deployment(show_output=True)

#Remove temp config
os.remove(fn_config_infer)

# Get service details
logger.warning(service.get_keys)

# Test service
try:
    service.run(json.dumps([{"body": "Mein Windows Vista rechner will nicht mehr - ich kriege dauernd fehler meldungen. Ich wollte mir eh einen neuen kaufen, aber ich hab kein Geld. Kann Bill Gates mir helfen?"}]))
except Exception as e:
    logger.warning(f'[ERROR] Service was not deployed as expected. {e}')