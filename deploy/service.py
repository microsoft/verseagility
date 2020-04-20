"""
Functions to deploy service
(RELEASE pipeline)

To run locally, use:
> cd ./root
> conda activate nlp
> python deploy/pipeline.py  --project_name msforum_en --do_deploy
"""
import os
import json
import shutil
import math
import logging
import argparse

from azureml.core import Workspace, Experiment, Model, Webservice
from azureml.core.authentication import InteractiveLoginAuthentication
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

## Arguments
parser = argparse.ArgumentParser()
parser.add_argument("--project_name", 
                    default='msforum_en',
                    type=str)
parser.add_argument('--do_deploy',
                        action='store_true',
                        help="")
args = parser.parse_args()

## Load 
params = he.get_project_config(f'{args.project_name}.config.json')
language = params.get('language')
env = params.get('environment')

############################################
#####   AML Setup
############################################

## Workspace
ws = he.get_aml_ws()

# Python dependencies
pip_packages=he.get_requirements(req_type='pip')
conda_packages=he.get_requirements(req_type='conda')

## Local Config
fn_config_infer = 'config.json'
shutil.copy(f'./project/{args.project_name}.config.json', f'./code/{fn_config_infer}')

script_folder = "."
tasks = params.get("tasks")

############################################
#####  DEPLOY
############################################

version = '0.2'
auth_enabled = True
compute_type = 'ACI'

if args.do_deploy:
    logging.warning(f'[INFO] Running deploy for {args.project_name}')
    # Fetch Models
    models = []
    for task in tasks:
        model_name = f'{args.project_name}-model-{task}' ####
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
    if compute_type == 'ACI':
        compute_config = AciWebservice.deploy_configuration(cpu_cores=1, memory_gb=memory_gb, auth_enabled=auth_enabled)
    elif compute_type == 'AKS':
        compute_config = AksWebservice.deploy_configuration()
    
    # Prepare Environment
    environment = Environment('env')
    conda_packages = ['pytorch', 'torchvision'] +  conda_packages
    pip_packages = ['azureml-defaults'] + pip_packages
    environment.python.conda_dependencies = CondaDependencies.create(pip_packages=pip_packages,
                                                                    conda_packages=conda_packages)

    inference_config = InferenceConfig(entry_script='code/infer.py',
                                   source_directory='.',
                                   environment=environment)
    
    # Create or update service
    service_name = f'{args.project_name}-{env}'.replace('_','-')
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