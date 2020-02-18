"""
Functions to deploy training

To run locally, use:
> cd ./code
> conda activate nlp
> python deploy/training.py

TODO: switch to AML pipelines
"""

import os
import json
import shutil
import math
from azureml.core import Workspace, Experiment
from azureml.train.dnn import PyTorch
from azureml.train.hyperdrive import  (BayesianParameterSampling, RandomParameterSampling,
                                        HyperDriveConfig, PrimaryMetricGoal,
                                        choice, uniform, loguniform)

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

# PARAMETERS
project_name = f"msforum_de"
single_run = True
update_model = False
compute_name = 'gpucluster-nc12'
experiment_name = project_name

## Load 
params = get_project_config(f'{project_name}.config.json')
language = params.get('language')
env = params.get('environment')

############################################
#####   AML Setup
############################################

## Workspace
# auth = InteractiveLoginAuthentication(tenant_id="72f988bf-86f1-41af-91ab-2d7cd011db47")
ws = Workspace.get(name='nlp-ml', 
                subscription_id='50324bce-875f-4a7b-9d3c-0e33679f5d72', 
                resource_group='nlp')
                # ,auth=auth)

## Compute target
compute_target= ws.compute_targets[compute_name]
script_folder = "."

#TODO: load from file (load_env)
pip_packages=[
                        'azureml-sdk',
                        'azureml-dataprep[pandas,fuse]',
                        'mlflow==1.0.0', 
                        'azureml-mlflow',
                        'spacy',
                        'transformers==2.4.1',
                        'scipy',
                        'numpy',
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
                        # 'pytorch', #Included in the PytorchEstimator
                        # 'torchvision',
                        'pip==19.3.1', #NOTE: workaround for #745 issue
                        'gensim',
                        'numpy',
                        'pandas'
                    ]

############################################
#####   Training
############################################

fn_config_infer = 'config.json'
shutil.copy(f'./project/{project_name}.config.json', f'./code/{fn_config_infer}')

os.chdir('./code')

## Experiment
exp = Experiment(workspace = ws, name = experiment_name)

## Config
script_params = {
    '--task'            : 1,
    # '--run_prepare'     : '',
    # '--do_format'       : '',
    # '--download_source' : '',
    '--use_cuda'        : '',
    '--n_epochs'        : 3,
    '--learning_rate'   : 4e-5,
    '--model_type'      : 'distilbert',
    '--max_seq_len'     : 256,
    '--embeds_dropout'  : 0.2,
    '--register_model'  : ''
}
est = PyTorch(source_directory = script_folder,
            compute_target = compute_target,
            script_params = script_params,
            entry_script = 'train.py',
            pip_packages = pip_packages,
            conda_packages = conda_packages,
            use_gpu = True)
## Run
if single_run:
    run = exp.submit(est)
    #Remove temp config
    os.remove(fn_config_infer)
    run.wait_for_completion(show_output = True)
else:
    ### Hyperparameters params
    if language == 'en':
        model_type = choice('roberta','bert','albert') #,'xlm-roberta'
    elif language == 'de':
        model_type = choice('distilbert','bert', 'roberta')
    elif language == 'it' or language == 'es':
        model_type = choice('bert')
    elif language == 'fr':
        model_type = choice('camembert', 'bert') #,'xlm-roberta'
    param_sampling = RandomParameterSampling({
        '--learning_rate' : choice(1e-5, 2e-5, 3e-5, 4e-5),
        '--model_type' :  model_type,
        '--max_seq_len' : choice(128, 256),
        '--embeds_dropout' : choice(0.1, 0.2, 0.3)    
    })
    ## Prepare HyperDrive Config
    hdc = HyperDriveConfig(estimator=est, 
                hyperparameter_sampling = param_sampling,
                policy = None, # NOTE: not possible for bayesian
                primary_metric_name = 'f1macro',
                primary_metric_goal = PrimaryMetricGoal.MAXIMIZE,
                max_total_runs = 40,
                max_concurrent_runs = 4)
    ## Run hyperparameter tuning
    hyperdrive_run = exp.submit(config=hdc)
    hyperdrive_run.wait_for_completion(show_output = True)
    if update_model:
        ## Get Results
        best_run = hyperdrive_run.get_best_run_by_primary_metric()
        ## Experiment
        experiment_name = experiment_name + "-train"
        exp = Experiment(workspace = ws, name = experiment_name)
        #Parameters determined by hyperparams
        script_params_hyper = {
            '--learning_rate'   : get_best_argument(best_run.get_details(), 'learning_rate'),
            '--model_type'      : get_best_argument(best_run.get_details(), 'model_type'),
            '--max_seq_len'     : get_best_argument(best_run.get_details(), 'max_seq_len'),
            '--embeds_dropout'  : get_best_argument(best_run.get_details(), 'embeds_dropout'),
            '--register_model'  : ''
        }
        script_params_best = {**script_params, **script_params_hyper}
        est_best = PyTorch(source_directory = script_folder,
                    compute_target = compute_target,
                    script_params = script_params_best,
                    entry_script = 'train.py',
                    pip_packages = pip_packages,
                    conda_packages = conda_packages,
                    use_gpu = True)
        # # Run single
        run = exp.submit(est_best)
        run.wait_for_completion(show_output = False)
    #Remove temp config
    os.remove(fn_config_infer)