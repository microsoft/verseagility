"""
Functions to deploy service

To run locally, use:
> cd ./root
> conda activate nlp
> python deploy/pipeline.py --language en --do_deploy
"""
import os
import json
import shutil
import math
import logging
import argparse

from azureml.core import Workspace, Experiment, Model, Webservice
from azureml.core.authentication import InteractiveLoginAuthentication, MsiAuthentication
from azureml.core.resource_configuration import ResourceConfiguration
from azureml.core.webservice import AciWebservice, AksWebservice
from azureml.core import Environment
from azureml.core.conda_dependencies import CondaDependencies
from azureml.core.model import InferenceConfig
from azureml.exceptions import WebserviceException

# Custom Functions
import sys 
sys.path.append('./code')
import helper as he

############################################
#####   Parameters
############################################
# Two stages: dev + train.
## dev: test changes, trial runs
## train: training, full runs, deployment
parser = argparse.ArgumentParser()
parser.add_argument("--language", 
                    default='en',
                    type=str,
                    help="")
parser.add_argument('--do_deploy',
                        action='store_true',
                        help="")
args = parser.parse_args()

# PARAMETERS
project_name = f"msforum_{args.language}"

## Load 
params = he.get_project_config(f'{project_name}.config.json')
language = params.get('language')
env = params.get('environment')

############################################
#####   AML Setup
############################################

## Workspace
# try:
#     auth = MsiAuthentication()
# except Exception as e:
#     logger.warning(e)
# auth = None
auth = InteractiveLoginAuthentication(tenant_id="72f988bf-86f1-41af-91ab-2d7cd011db47")

ws = Workspace.get(name='nlp-ml', 
                subscription_id='50324bce-875f-4a7b-9d3c-0e33679f5d72', 
                resource_group='nlp',
                auth=auth)

#TODO: load from file (load_env)
pip_packages=[
                        'azureml-sdk',
                        'azureml-dataprep[pandas,fuse]',
                        'mlflow', 
                        'azureml-mlflow',
                        'spacy',
                        'transformers==2.4.1',
                        'scipy',
                        'azure-storage-blob',
                        'tqdm',
                        'boto3',
                        'scipy>=1.3.2',
                        'sklearn',
                        'seqeval',
                        'dotmap==1.3.0',
                        'farm==0.4.1',
                        'flair==0.4.5',
                        'azure-ai-textanalytics'
                    ]
conda_packages=[
                        'pip==19.3.1', #NOTE: workaround for #745 issue
                        # 'pytorch', #Included in the PytorchEstimator
                        # 'torchvision',
                        'gensim',
                        'numpy',
                        'pandas'
                    ]

## Local Config
fn_config_infer = 'config.json'
shutil.copy(f'./project/{project_name}.config.json', f'./code/{fn_config_infer}')

script_folder = "."
tasks = params.get("tasks")

############################################
#####  DEPLOY
############################################

version = '0.2'
auth_enabled = True
compute_type = 'ACI'

if args.do_deploy:
    logging.warning(f'[INFO] Running deploy for {project_name}')
    # Fetch Models
    models = []
    for task in tasks:
        model_name = f'{project_name}-model-t{task}'
        if int(task) == 3:
            # NOTE: task 3 does not have a model
            continue
        model = Model(ws, model_name)
        models.append(
           model
        )
        logging.warning(f'[INFO] Added Model : {model.name} (v{model.version})')
    
    # Deployment Target
    memory_gb = 2
    # ram_size = params.get('environment')
    # if ram_size is not None:
        # memory_gb = ram_size
    if compute_type == 'ACI':
        compute_config = AciWebservice.deploy_configuration(cpu_cores=2, memory_gb=memory_gb, auth_enabled=auth_enabled)
    elif compute_type == 'AKS':
        compute_config = AksWebservice.deploy_configuration() #TODO:
    
    # Prepare Environment
    environment = Environment('farmenv')
    conda_packages = ['pytorch', 'torchvision'] +  conda_packages
    conda_packages.remove('pip==19.3.1')
    pip_packages = ['azureml-defaults'] + pip_packages
    # pip_packages.remove('azureml-sdk')
    # pip_packages.remove('azureml-dataprep[pandas,fuse]')
    environment.python.conda_dependencies = CondaDependencies.create(pip_packages=pip_packages,
                                                                    conda_packages=conda_packages)

    inference_config = InferenceConfig(entry_script='code/infer.py',
                                   source_directory='.',
                                   environment=environment)
    
    # Create or update service
    service_name = f'{project_name}-{env}'.replace('_','-')
    ## Create web service
    service = Model.deploy(workspace=ws, 
                            name=service_name, 
                            models=models, 
                            inference_config=inference_config, 
                            deployment_config=compute_config, 
                            overwrite=True)
    logging.warning('[INFO] Creating web service')
    service.wait_for_deployment(show_output=True)

    # Get service details
    logging.warning(service.get_keys)

    # Test service
    try:
        service.run(json.dumps([{"body": "Mein Windows Vista rechner will nicht mehr - ich kriege dauernd fehler meldungen. Ich wollte mir eh einen neuen kaufen, aber ich hab kein Geld. Kann Bill Gates mir helfen?"}]))
        logging.warning(f'[SUCCESS] Service was deployed.')
    except Exception as e:
        logging.warning(f'[ERROR] Service was not deployed as expected. {e}')

#Remove temp config
os.remove( f'./code/{fn_config_infer}')