"""
Functions to deploy training pipeline

To run locally, use:
> cd ./root
> conda activate nlp
> python deploy/training.py --language en --do_prepare --do_train

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

# Custom Functions
import sys 
sys.path.append('./code')
import helper as he

############################################
#####   Parameters
############################################
#TODO: these arguments should be passed from central pipeline.py
parser = argparse.ArgumentParser() 
parser.add_argument("--language", 
                    default='en',
                    type=str,
                    help="")
parser.add_argument("--compute_name", 
                    default='gpucluster-nc12',
                    type=str,
                    help="")
parser.add_argument('--do_prepare',
                        action='store_true',
                        help="")
parser.add_argument('--do_train',
                        action='store_true',
                        help="")
args = parser.parse_args()

# PARAMETERS
project_name = f"msforum_{args.language}"
compute_name = args.compute_name
experiment_name = project_name

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
# os.chdir('./code') #TODO: go to root

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
                        entry_script = 'code/prepare.py',
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
                        entry_script = 'code/classification.py',
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
                        entry_script = 'code/rank.py',
                        pip_packages = pip_packages,
                        conda_packages = conda_packages,
                        use_gpu = False
                        )
            run = exp.submit(est)
            print(f'[INFO] Task {task} deployed for training.')
        else:
            print(f'[INFO] Task {task} does not have a train step.')
        # run.wait_for_completion(show_output = True)


# ## Run
# if single_run:
#     run = exp.submit(est)
#     #Remove temp config
#     os.remove(fn_config_infer)
#     run.wait_for_completion(show_output = True)
# else:
#     ### Hyperparameters params
#     if language == 'en':
#         model_type = choice('roberta','bert','albert') #,'xlm-roberta'
#     elif language == 'de':
#         model_type = choice('distilbert','bert', 'roberta')
#     elif language == 'it' or language == 'es':
#         model_type = choice('bert')
#     elif language == 'fr':
#         model_type = choice('camembert', 'bert') #,'xlm-roberta'
#     param_sampling = RandomParameterSampling({
#         '--learning_rate' : choice(1e-5, 2e-5, 3e-5, 4e-5),
#         '--model_type' :  model_type,
#         '--max_seq_len' : choice(128, 256),
#         '--embeds_dropout' : choice(0.1, 0.2, 0.3)    
#     })
#     ## Prepare HyperDrive Config
#     hdc = HyperDriveConfig(estimator=est, 
#                 hyperparameter_sampling = param_sampling,
#                 policy = None, # NOTE: not possible for bayesian
#                 primary_metric_name = 'f1macro',
#                 primary_metric_goal = PrimaryMetricGoal.MAXIMIZE,
#                 max_total_runs = 40,
#                 max_concurrent_runs = 4)
#     ## Run hyperparameter tuning
#     hyperdrive_run = exp.submit(config=hdc)
#     hyperdrive_run.wait_for_completion(show_output = True)
#     if update_model:
#         ## Get Results
#         best_run = hyperdrive_run.get_best_run_by_primary_metric()
#         ## Experiment
#         experiment_name = experiment_name + "-train"
#         exp = Experiment(workspace = ws, name = experiment_name)
#         #Parameters determined by hyperparams
#         script_params_hyper = {
#             '--learning_rate'   : get_best_argument(best_run.get_details(), 'learning_rate'),
#             '--model_type'      : get_best_argument(best_run.get_details(), 'model_type'),
#             '--max_seq_len'     : get_best_argument(best_run.get_details(), 'max_seq_len'),
#             '--embeds_dropout'  : get_best_argument(best_run.get_details(), 'embeds_dropout'),
#             '--register_model'  : ''
#         }
#         script_params_best = {**script_params, **script_params_hyper}
#         est_best = PyTorch(source_directory = script_folder,
#                     compute_target = compute_target,
#                     script_params = script_params_best,
#                     entry_script = 'train.py',
#                     pip_packages = pip_packages,
#                     conda_packages = conda_packages,
#                     use_gpu = True)
#         # # Run single
#         run = exp.submit(est_best)
#         run.wait_for_completion(show_output = False)

############################################
#####  CLEANUP
############################################

#Remove temp config
os.remove(f'./code/{fn_config_infer}')