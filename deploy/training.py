"""
Functions to deploy training pipeline
(BUILD pipeline)

To run locally, use:
> cd ./root
> activate environment
> python deploy/training.py --project_name msforum_en --do_prepare --do_train

"""
import os
import shutil
import logging
import argparse

from azureml.core import Experiment
from azureml.train.dnn import PyTorch
from azureml.train.estimator import Estimator
from azureml.core.compute import ComputeTarget, AmlCompute
from azureml.core.compute_target import ComputeTargetException

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
                    default='msforum_en',
                    type=str)
parser.add_argument("--compute_name", 
                    default='gpucluster-nc12',
                    type=str)
parser.add_argument('--do_prepare',
                        action='store_true')
parser.add_argument('--do_train',
                        action='store_true')
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

## Compute target   
try:
    compute_target = ComputeTarget(workspace=ws, name=args.compute_name)
    logging.warning(f'[INFO] Using compute {args.compute_name}')
except ComputeTargetException:
    logging.warning(f'[INFO] Creating compute {args.compute_name}')
    compute_config = AmlCompute.provisioning_configuration(vm_size='Standard_NC12',
                                                            max_nodes=5)
    compute_target = ComputeTarget.create(ws, args.compute_name, compute_config)
    compute_target.wait_for_completion(show_output=True)

# Python dependencies
pip_packages = he.get_requirements(req_type='train')

## Local Config
fn_config_infer = 'config.json'
shutil.copy(f'./project/{args.project_name}.config.json', f'./src/{fn_config_infer}')

script_folder = "./"
tasks = params.get("tasks")

############################################
#####  PREPARE
############################################

if args.do_prepare:
    logging.warning(f'[INFO] Running  prepare for {args.project_name}')
    for task in tasks:
        config = tasks.get(task)
        if config.get('prepare'):
            exp = Experiment(workspace = ws, name = f'{args.project_name}_prepare_{task}')
            print(f'[INFO] Running prepare for {task}')
            script_params = {
                '--task'            : int(task),
                '--do_format'       : '',
                '--register_data'   : ''
            }
            est = Estimator(source_directory = script_folder,
                        compute_target = compute_target,
                        script_params = script_params,
                        entry_script = 'src/prepare.py',
                        pip_packages = pip_packages,
                        use_gpu = False
                        )
            run = exp.submit(est)
    if args.do_train:
        run.wait_for_completion(show_output = True)

############################################
#####  TRAIN
############################################

if args.do_train:
    logging.warning(f'[INFO] Running train for {args.project_name}')
    for task in tasks:
        exp = Experiment(workspace = ws, name = f'{args.project_name}_train_{task}')
        config = tasks.get(task)
        if config.get('type') == 'classification':
            script_params = {
                '--task'            : int(task),
                '--use_cuda'        : '',
                '--n_epochs'        : 3,
                '--learning_rate'   : config.get('learning_rate'),
                '--model_type'      : config.get('model_type'),
                '--max_seq_len'     : config.get('max_seq_len'),
                '--embeds_dropout'  : config.get('embeds_dropout'),
                '--register_model'  : ''
            }
            est = PyTorch(source_directory = script_folder,
                        compute_target = compute_target,
                        script_params = script_params,
                        entry_script = 'src/classification.py',
                        pip_packages = pip_packages,
                        use_gpu = True)
            run = exp.submit(est)
            print(f'[INFO] Task {task} deployed for training.')
        elif config.get('type') == 'multi_classification':
            script_params = {
                '--task'            : int(task),
                '--use_cuda'        : '',
                '--learning_rate'   : config.get('learning_rate'),
                '--model_type'      : config.get('model_type'),
                '--max_seq_len'     : config.get('max_seq_len'),
                '--embeds_dropout'  : config.get('embeds_dropout'),
                '--register_model'  : ''
            }
            est = PyTorch(source_directory = script_folder,
                        compute_target = compute_target,
                        script_params = script_params,
                        entry_script = 'src/multi_classification.py',
                        pip_packages = pip_packages,
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
                        entry_script = 'src/rank.py',
                        pip_packages = pip_packages,
                        use_gpu = False
                        )
            run = exp.submit(est)
            logging.info(f'[INFO] Task {task} deployed for training.')
        else:
            logging.info(f'[INFO] Task {task} does not have a train step.')

############################################
#####  CLEANUP
############################################

# Remove temp config
os.remove(f'./src/{fn_config_infer}')