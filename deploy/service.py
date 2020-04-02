"""
Functions to deploy service
(RELEASE pipeline)

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
auth = None
# auth = InteractiveLoginAuthentication(tenant_id="72f988bf-86f1-41af-91ab-2d7cd011db47")
ws = Workspace.get(name=he.get_secret('aml-ws-name'), 
                subscription_id=he.get_secret('aml-ws-sid'), 
                resource_group=he.get_secret('aml-ws-rg'),
                auth=auth)

# Python dependencies
pip_packages=he.get_requirements(req_type='pip')
conda_packages=he.get_requirements(req_type='conda')

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
    if compute_type == 'ACI':
        compute_config = AciWebservice.deploy_configuration(cpu_cores=2, memory_gb=memory_gb, auth_enabled=auth_enabled)
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