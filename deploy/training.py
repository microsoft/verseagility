"""
Functions to deploy training

To run locally, use:
> cd ./code
> conda activate nlp
> python deploy/training.py

"""

import os
import shutil
import math
from azureml.core import Workspace, Experiment
from azureml.train.dnn import PyTorch
from azureml.train.hyperdrive import  (BayesianParameterSampling,
                                        HyperDriveConfig, PrimaryMetricGoal,
                                        choice, uniform, loguniform)

# PARAMETERS
language = 'de'
single_run = True
compute_name = 'gpucluster-nc6'
experiment_name = f"msforum_{language}"

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

#TODO: load from file
pip_packages=[
                        'azureml-sdk',
                        'azureml-dataprep[pandas,fuse]',
                        'mlflow', 
                        'azureml-mlflow',
                        'spacy',
                        'transformers==2.3.0',
                        'scipy',
                        'numpy',
                        'azure-storage-blob',
                        'tqdm',
                        'boto3',
                        'scipy>=1.3.2',
                        'sklearn',
                        'seqeval',
                        'mlflow==1.0.0',
                        'dotmap==1.3.0',
                        'farm==0.4.1',
                        'flair==0.4.5'
                    ]
conda_packages=[
                        # 'pytorch',
                        # 'torchvision',
                        'pip==19.3.1', #NOTE: workaround for #745 issue
                        'gensim',
                        'numpy',
                        'pandas'
                    ]

############################################
#####   Task 1
############################################

fn_config_infer = 'config.json'
shutil.copy(f'./project/msforum_{language}.config.json', f'./code/{fn_config_infer}')

os.chdir('./code')

## Experiment
exp = Experiment(workspace = ws, name = experiment_name)
## Config
script_params = {
    '--task'            : 1,
    '--do_format'       : '',
    '--download_source' : '',
    '--use_cuda'        : '',
    '--n_epochs'        : 3,
    # '--learning_rate'   : 2e-5,
    # '--model_type'      : 'roberta',
    # '--max_seq_len'     : 128, #256,
    # '--embeds_dropout'  : 0.3,
    # '--register_model'  : ''
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
    param_sampling = BayesianParameterSampling({
        '--learning_rate' : choice(1e-5, 2e-5, 3e-5, 4e-5),
        '--model_type' :  model_type,
        '--max_seq_len' : choice(64, 128, 256),
        '--embeds_dropout' : choice(0.1, 0.2, 0.3, 0.4)    
    })
    ## Prepare HyperDrive Config
    hdc = HyperDriveConfig(estimator=est, 
                hyperparameter_sampling = param_sampling,
                policy = None, # NOTE: not possible for bayesian
                primary_metric_name = 'f1macro',
                primary_metric_goal = PrimaryMetricGoal.MAXIMIZE,
                max_total_runs = 80,
                max_concurrent_runs = 1)
    ## Run hyperparameter tuning
    hyperdrive_run = exp.submit(config=hdc)
    #Remove temp config
    os.remove(fn_config_infer)
    hyperdrive_run.wait_for_completion(show_output = True)
    ## Get Results
    # best_run = hyperdrive_run.get_best_run_by_primary_metric()