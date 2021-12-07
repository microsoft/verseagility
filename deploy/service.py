"""
Functions to deploy service
(RELEASE pipeline)

To run locally, use:
> cd ./root
> conda activate nlp
> python deploy/service.py --project_name msforum_en --do_deploy
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
sys.path.append('./src')
import helper as he

############################################
#####   Parameters
############################################

## Arguments
parser = argparse.ArgumentParser()
parser.add_argument("--project_name", 
                    default='mbio_en',
                    type=str)
parser.add_argument('--do_deploy',
                        action='store_true')
parser.add_argument('--show_output',
                        action='store_true')
args = parser.parse_args()

def deploy_service(do_deploy, project_name, show_output=True, ws=None):
    ## Load 
    params = he.get_project_config(f'{project_name}.config.json')
    language = params.get('language')
    env = params.get('environment')

    ############################################
    #####   AML Setup
    ############################################

    ## Workspace
    if ws is None:
        ws = he.get_aml_ws()

    # Python dependencies
    pip_packages=he.get_requirements(req_type='deploy')

    ## Local Config
    fn_config_infer = 'config.json'
    shutil.copy(f'./project/{project_name}.config.json', f'./src/{fn_config_infer}')

    script_folder = "."
    tasks = params.get("tasks")
    deploy = params.get("deploy")

    ############################################
    #####  DEPLOY
    ############################################

    version = '0.2'
    auth_enabled = True

    if do_deploy:
        logging.warning(f'[INFO] Running deploy for {project_name}')
        # Fetch Models
        models = []
        for task in tasks:
            model_name = f'{project_name}-model-{task}' ####
            if tasks.get(task)['type'] == 'ner': # int(task) == 3: 
                # NOTE: task 3 does not have a model
                continue
            model = Model(ws, model_name)
            models.append(
            model
            )
            logging.warning(f'[INFO] Added Model : {model.name} (v{model.version})')
        
        # Deployment Target
        if deploy.get('type') == 'ACI':
            compute_config = AciWebservice.deploy_configuration(cpu_cores=deploy.get('cpu'), memory_gb=deploy.get('memory'), auth_enabled=auth_enabled) #2
        elif deploy.get('type') == 'AKS':
            compute_config = AksWebservice.deploy_configuration()
        
        # Prepare Environment
        environment = Environment('env')
        conda_packages = ['pytorch', 'torchvision']
        pip_packages = ['azureml-defaults'] + pip_packages
        environment.python.conda_dependencies = CondaDependencies.create(pip_packages=pip_packages,
                                                                        conda_packages=conda_packages)

        inference_config = InferenceConfig(entry_script='src/infer.py',
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
        service.wait_for_deployment(show_output=show_output)

        # Get service details
        logging.warning(service.get_keys)

        # Test service
        try:
            service.run(json.dumps([{"body": "Mein Windows Vista rechner will nicht mehr - ich kriege dauernd fehler meldungen. Ich wollte mir eh einen neuen kaufen, aber ich hab kein Geld. Kann Bill Gates mir helfen?"}]))
            logging.warning(f'[SUCCESS] Service was deployed.')
        except Exception as e:
            logging.warning(f'[ERROR] Service was not deployed as expected. {e}')

    #Remove temp config
    os.remove( f'./src/{fn_config_infer}')

if __name__ == '__main__':
    deploy_service(args.do_deploy, args.project_name)
