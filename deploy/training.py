'''Functions to deploy training

'''

import os
import math
from azureml.core import Workspace, Experiment
from azureml.train.dnn import PyTorch
from azureml.train.hyperdrive import  (BayesianParameterSampling,
                                        HyperDriveConfig, PrimaryMetricGoal,
                                        choice, uniform, loguniform)

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
compute_name = 'gpucluster-nc12'
compute_target= ws.compute_targets[compute_name]
script_folder = "./"

pip_packages=[
                        'azureml-sdk',
                        'azureml-dataprep[pandas,fuse]',
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
                        'git+https://github.com/deepset-ai/FARM.git',
                        'git+https://github.com/zalandoresearch/flair.git'
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

## Experiment
experiment_name = "answers-de"
exp = Experiment(workspace = ws, name = experiment_name)
## Config
script_params = {
    '--task'            : 1,
    '--do_format'       : '',
    '--download_source' : '',
    # '--model_type'      : 'roberta',
    '--use_cuda'        : '',
    '--batch_size'      : 4
    # '--learning_rate'   : 0.5e-5
}
est = PyTorch(source_directory = script_folder,
            compute_target = compute_target,
            script_params = script_params,
            entry_script = 'code/train.py',
            pip_packages = pip_packages,
            conda_packages = conda_packages,
            use_gpu = True)
## Run
# run = exp.submit(est)
# run.wait_for_completion(show_output = True)
### Hyperparameters params
param_sampling = BayesianParameterSampling( {
    '--learning_rate' : choice(0.5e-5, 1e-5, 2e-5, 3e-5),
    # '--model_type' : choice('roberta','bert','albert')
    '--model_type' : choice('distilbert','bert')
})
## Prepare HyperDrive Config
hdc = HyperDriveConfig(estimator=est, 
            hyperparameter_sampling = param_sampling,
            policy = None, # NOTE: not possible for bayesian
            primary_metric_name = 'f1macro',
            primary_metric_goal = PrimaryMetricGoal.MAXIMIZE,
            max_total_runs = 40,
            max_concurrent_runs = 1)
## Run hyperparameter tuning
hyperdrive_run = exp.submit(config=hdc)
hyperdrive_run.wait_for_completion(show_output = True)
## Get Results
best_run = hyperdrive_run.get_best_run_by_primary_metric()
print(best_run)