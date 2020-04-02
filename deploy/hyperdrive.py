"""
Functions to deploy training pipeline
(BUILD pipeline)

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
from azureml.train.dnn import PyTorch
from azureml.train.estimator import Estimator
from azureml.core.compute import ComputeTarget, AmlCompute
from azureml.core.compute_target import ComputeTargetException
from azureml.train.hyperdrive import  (BanditPolicy, RandomParameterSampling,
                                        HyperDriveConfig, PrimaryMetricGoal,
                                        choice, uniform, loguniform)

from azureml.core.authentication import InteractiveLoginAuthentication
from azureml.core.model import InferenceConfig
from azureml.exceptions import WebserviceException

# Custom Functions
import sys 
sys.path.append('./code')
import helper as he

############################################
#####   Parameters
############################################

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
parser.add_argument('--update_model',
                        action='store_true',
                        help="")
args = parser.parse_args()

# PARAMETERS
project_name = f"msforum_{args.language}"
compute_name = args.compute_name

## Load 
params = he.get_project_config(f'{project_name}.config.json')
language = params.get('language')
env = params.get('environment')

############################################
#####   AML Setup
############################################

## Workspace
auth = None
ws = Workspace.get(name=he.get_secret('aml-ws-name'), 
                subscription_id=he.get_secret('aml-ws-sid'), 
                resource_group=he.get_secret('aml-ws-rg'),
                auth=auth)

## Compute target   
try:
    compute_target = ComputeTarget(workspace=ws, name=compute_name)
    logging.warning(f'[INFO] Using compute {compute_name}')
except ComputeTargetException:
    logging.warning(f'[INFO] Creating compute {compute_name}')
    compute_config = AmlCompute.provisioning_configuration(vm_size='Standard_NC12',
                                                            max_nodes=5)
    compute_target = ComputeTarget.create(ws, compute_name, compute_config)
    compute_target.wait_for_completion(show_output=True)

# Python dependencies
pip_packages=he.get_requirements(req_type='pip')
conda_packages=he.get_requirements(req_type='conda')

## Local Config
fn_config_infer = 'config.json'
shutil.copy(f'./project/{project_name}.config.json', f'./code/{fn_config_infer}')

script_folder = "./"
tasks = params.get("tasks")

############################################
#####  PREPARE
############################################

if args.do_prepare:
    logging.warning(f'[INFO] Running  prepare for {project_name}')
    for task in tasks:
        config = tasks.get(task)
        if config.get('prepare'):
            exp = Experiment(workspace = ws, name = f'{project_name}_prepare_{task}')
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
#####  HYPERPARAMETER TUNING
############################################

if args.do_train:
    logging.warning(f'[INFO] Running train for {project_name}')
    for task in tasks:
        exp = Experiment(workspace = ws, name = f'{project_name}_train_{task}')
        config = tasks.get(task)
        if config.get('type') == 'classification':
            script_params = {
                '--task'            : int(task),
                '--use_cuda'        : '',
                
                '--register_model'  : ''
            }
            est = PyTorch(source_directory = script_folder,
                        compute_target = compute_target,
                        script_params = script_params,
                        entry_script = 'code/classification.py',
                        pip_packages = pip_packages,
                        conda_packages = conda_packages,
                        use_gpu = True)
            
            ### Hyperparameters params
            if language == 'en':
                model_type = choice('roberta','bert','albert')
            elif language == 'de':
                model_type = choice('distilbert','bert', 'roberta')
            elif language == 'it' or language == 'es':
                model_type = choice('bert')
            elif language == 'fr':
                model_type = choice('camembert', 'bert')
            param_sampling = RandomParameterSampling({
                '--n_epochs'        : choice(3, 5, 10),
                '--learning_rate'   : choice(1e-5, 2e-5, 3e-5, 4e-5),
                '--model_type'      : model_type,
                '--max_seq_len'     : choice(128, 256),
                '--embeds_dropout'  : choice(0.1, 0.2, 0.3)    
            })
            ## Termination policy
            early_termination_policy = BanditPolicy(slack_factor = 0.1, 
                                                    evaluation_interval=1, 
                                                    delay_evaluation=3)
            ## Prepare HyperDrive Config
            hdc = HyperDriveConfig(estimator=est, 
                        hyperparameter_sampling = param_sampling,
                        policy = early_termination_policy,
                        primary_metric_name = 'f1macro',
                        primary_metric_goal = PrimaryMetricGoal.MAXIMIZE,
                        max_total_runs = 40,
                        max_concurrent_runs = 4)
            ## Run hyperparameter tuning
            hyperdrive_run = exp.submit(config=hdc)
            if args.update_model:
                hyperdrive_run.wait_for_completion(show_output = True)
                ## Get Results
                best_run = hyperdrive_run.get_best_run_by_primary_metric()
                ## Experiment
                experiment_name = project_name + "-train"
                exp = Experiment(workspace = ws, name = experiment_name)
                #Parameters determined by hyperparams
                script_params_hyper = {
                    '--learning_rate'   : he.get_best_argument(best_run.get_details(), 'learning_rate'),
                    '--model_type'      : he.get_best_argument(best_run.get_details(), 'model_type'),
                    '--max_seq_len'     : he.get_best_argument(best_run.get_details(), 'max_seq_len'),
                    '--embeds_dropout'  : he.get_best_argument(best_run.get_details(), 'embeds_dropout'),
                    '--register_model'  : ''
                }
                script_params_best = {**script_params, **script_params_hyper}
                est_best = PyTorch(source_directory = script_folder,
                            compute_target = compute_target,
                            script_params = script_params_best,
                            entry_script = 'code/classification.py',
                            pip_packages = pip_packages,
                            conda_packages = conda_packages,
                            use_gpu = True)
                # # Run single
                run = exp.submit(est_best)
                run.wait_for_completion(show_output = False)
        else:
            print(f'[INFO] Task {task} does not have a train step.')

############################################
#####  CLEANUP
############################################

#Remove temp config
os.remove(f'./code/{fn_config_infer}')