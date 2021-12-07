import sys
from training import run_training

if __name__ == '__main__':
    run_training(do_prepare=True, do_train=True, project_name='mbio_en', dataset_name='sample', ws=None)