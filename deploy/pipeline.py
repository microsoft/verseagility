"""
Functions to deploy pipeline

To run locally, use:
> cd ./root
> conda activate nlp
> python deploy/pipeline.py --language en --do_prepare --do_train
> python deploy/pipeline.py --language en --do_deploy

#NOTE: not using AML Pipelines yet, 
due to technical restrictions
"""
import os
import json
import shutil
import math
import logging
import argparse

from azureml.core import Workspace, Experiment, Model
from azureml.pipeline.steps import PythonScriptStep, EstimatorStep
from azureml.train.dnn import PyTorch
from azureml.train.estimator import Estimator
from azureml.train.hyperdrive import  (BayesianParameterSampling, RandomParameterSampling,
                                        HyperDriveConfig, PrimaryMetricGoal,
                                        choice, uniform, loguniform)

from azureml.core.authentication import InteractiveLoginAuthentication, MsiAuthentication
from azureml.core.resource_configuration import ResourceConfiguration
from azureml.core.webservice import AciWebservice, AksWebservice
from azureml.core import Environment
from azureml.core.conda_dependencies import CondaDependencies
from azureml.core.model import InferenceConfig
from azureml.exceptions import WebserviceException

############################################
#####   Helper Functions
############################################

def get_project_config(fn):
    if os.path.isfile(f'./project/{fn}'):
        with open(f'./project/{fn}', encoding='utf-8') as fp:
            params = json.load(fp)
    elif os.path.isfile(f'../project/{fn}'):
        with open(f'../project/{fn}', encoding='utf-8') as fp:
            params = json.load(fp)
    elif os.path.isfile(f'config.json'):
        ## Training Config
        with open('config.json', encoding='utf-8') as fp:
            params = json.load(fp)
    elif os.path.isfile(f'./code/config.json'):
        ## Inference Config
        with open('./code/config.json', encoding='utf-8') as fp:
            params = json.load(fp)
    else: 
        raise Exception(f'Project parameters not found -> {fn}')
    return params

def load_env():
    # TODO:
    pass

def get_best_argument(details, argument):
    args_list = details['runDefinition']['arguments']
    for i, a in enumerate(args_list):
        if argument in a :
            return args_list[i + 1]

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
parser.add_argument('--do_prepare',
                        action='store_true',
                        help="")
parser.add_argument('--do_train',
                        action='store_true',
                        help="")
parser.add_argument('--do_deploy',
                        action='store_true',
                        help="")
args = parser.parse_args()

# PARAMETERS
project_name = f"msforum_{args.language}"
compute_name = 'gpucluster-nc6'
experiment_name = project_name

## Load 
params = get_project_config(f'{project_name}.config.json')
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

## Compute target
compute_target = ws.compute_targets[compute_name]

#TODO: load from file (load_env)
pip_packages=[
                        'azureml-sdk',
                        'azureml-dataprep[pandas,fuse]',
                        'mlflow==1.6.0', 
                        'azureml-mlflow==1.0.85',
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
                        'flair==0.4.5'
                    ]
conda_packages=[
                        'pip==19.3.1', #NOTE: workaround for #745 issue
                        # 'pytorch', #Included in the PytorchEstimator
                        # 'torchvision',
                        'gensim',
                        'numpy',
                        'pandas'
                    ]

## Experiment
exp = Experiment(workspace = ws, name = experiment_name)

## Local Config
fn_config_infer = 'config.json'
shutil.copy(f'./project/{project_name}.config.json', f'./code/{fn_config_infer}')
os.chdir('./code')

script_folder = "."
tasks = params.get("tasks")

############################################
#####  PREPARE
############################################

if args.do_prepare:
    logging.warning(f'[INFO] Running  prepare for {project_name}')
    for task in tasks:
        config = tasks.get(task)
        if config.get('prepare'):
            print(f'[INFO] Running prepare for {task}')
            script_params = {
                '--task'            : int(task),
                '--do_format'       : '',
                '--register_data'   : ''
            }
            est = Estimator(source_directory = script_folder,
                        compute_target = compute_target,
                        script_params = script_params,
                        entry_script = 'prepare.py',
                        pip_packages = pip_packages,
                        conda_packages = conda_packages,
                        use_gpu = False
                        )
            run = exp.submit(est)
    if args.do_train:
        run.wait_for_completion(show_output = True)

############################################
#####  TRAIN
############################################

if args.do_train:
    logging.warning(f'[INFO] Running train for {project_name}')
    for task in tasks:
        config = tasks.get(task)
        if config.get('type') == 'classification':
            script_params = {
                '--task'            : int(task),
                '--use_cuda'        : '',
                # '--n_epochs'        : 3,
                '--learning_rate'   : config.get('learning_rate'), #2e-5,
                '--model_type'      : config.get('model_type'),
                '--max_seq_len'     : config.get('max_seq_len'), #256,
                '--embeds_dropout'  : config.get('embeds_dropout'), #0.3,
                '--register_model'  : ''
            }
            est = PyTorch(source_directory = script_folder,
                        compute_target = compute_target,
                        script_params = script_params,
                        entry_script = 'classification.py',
                        pip_packages = pip_packages,
                        conda_packages = conda_packages,
                        use_gpu = True)
            run = exp.submit(est)
            print(f'[INFO] Task {task} deployed for training.')
        elif config.get('type') == 'qa':
            script_params = {
                '--task'            : int(task),
                '--download_train'  : '',
                '--register_model'  : ''
            }
            est = Estimator(source_directory = script_folder,
                        compute_target = compute_target,
                        script_params = script_params,
                        entry_script = 'rank.py',
                        pip_packages = pip_packages,
                        conda_packages = conda_packages,
                        use_gpu = False
                        )
            run = exp.submit(est)
            print(f'[INFO] Task {task} deployed for training.')
        else:
            print(f'[INFO] Task {task} does not have a train step.')
        # run.wait_for_completion(show_output = True)

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
        model_name = f'{project_name}-{task}-{env}'
        if int(task) == 3:
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

    inference_config = InferenceConfig(entry_script='infer.py',
                                   source_directory='.',
                                   environment=environment)
    
    # Create or update service
    service_name = f'{project_name}-{env}'.replace('_','-')
    try:
        ## Retrieve existing service.
        if compute_type == 'ACI':
            service = AciWebservice(workspace=ws, name=service_name)
        elif compute_type == 'AKS':
            service = AksWebservice(workspace=ws, name=service_name)
        ## Update to new model(s).
        service.update(models=models, inference_config=inference_config)
        logging.warning('[INFO] Updating web service')
        service.wait_for_deployment(show_output=True)
    except WebserviceException:
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
os.remove(fn_config_infer)