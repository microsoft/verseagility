"""
Functions to deploy training pipeline
(BUILD pipeline)

To run locally, use:
> cd ./root
> activate environment
> python deploy/training.py --project_name msforum_en --do_prepare --do_train

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
from azureml.train.hyperdrive import  (BayesianParameterSampling, RandomParameterSampling,
                                        HyperDriveConfig, PrimaryMetricGoal,
                                        choice, uniform, loguniform)

from azureml.core.authentication import InteractiveLoginAuthentication
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
parser.add_argument("--compute_name", 
                    default='gpucluster-nc12',
                    type=str)
parser.add_argument('--do_prepare',
                        action='store_true')
parser.add_argument('--do_train',
                        action='store_true')
parser.add_argument('--dataset_name', # TODO pipe through scripts
                        type=str,
                        default=None)
args = parser.parse_args()

def run_training(do_prepare, do_train, project_name, dataset_name, compute_name='gpucluster-nc12', ws=None):
    ## Load 
    params = he.get_project_config(f'{project_name}.config.json')
    language = params.get('language')
    env = params.get('environment')

    ############################################
    #####   AML Setup
    ############################################

    ## Workspace
    if ws is None:
        ws = he.get_aml_ws() # TODO - Initialize via backend

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
    pip_packages=he.get_requirements(req_type='train')

    ## Local Config
    fn_config_infer = 'config.json'
    shutil.copy(f'./project/{project_name}.config.json', f'./src/{fn_config_infer}')

    script_folder = "./"
    tasks = params.get("tasks")

    ############################################
    #####  PREPARE
    ############################################

    if do_prepare:
        logging.warning(f'[INFO] Running  prepare for {project_name}')
        for task in tasks:
            config = tasks.get(task)
            if config.get('prepare'):
                exp = Experiment(workspace = ws, name = f'{project_name}_prepare_{task}')
                logging.warning(f'[INFO] Running prepare for {task}')
                script_params = {
                    '--task'            : int(task),
                    '--do_format'       : '',
                    '--register_data'   : '',
                    '--dataset_name'    : dataset_name
                }
                est = Estimator(source_directory = script_folder,
                            compute_target = compute_target,
                            script_params = script_params,
                            entry_script = 'src/prepare.py',
                            pip_packages = pip_packages,
                            use_gpu = False
                            )
                run = exp.submit(est)
        if do_train:
            run.wait_for_completion(show_output = True)

    ############################################
    #####  TRAIN
    ############################################

    if do_train:
        logging.warning(f'[INFO] Running train for {project_name}')
        for task in tasks:
            exp = Experiment(workspace = ws, name = f'{project_name}_train_{task}')
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
                print(f'[INFO] Task {task} deployed for training.')
            else:
                print(f'[INFO] Task {task} does not have a train step.')

    ############################################
    #####  CLEANUP
    ############################################

    #Remove temp config
    os.remove(f'./src/{fn_config_infer}')

if __name__ == '__main__':
    run_training(args.do_prepare, args.do_train, args.project_name, dataset_name="sample")
