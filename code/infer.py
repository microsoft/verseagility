"""
INFERENCE: Orchestration service for serving the model.

"""
#NOTE: the following is a workaround for AML to load modules
import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import os
import json
import shutil
# import threading
from farm.infer import Inferencer

# Custom functions
import sys
sys.path.append('./code')
import helper as he
import data as dt
import prepare as pr
import custom as cu
import rank
import ner

# Load configs & logger 
logger = he.get_logger(location=__name__)

def score(task):
    task_type = cu.tasks.get(str(task)).get('type')
    if task_type == 'classification':
        _dt = dt.Data(task=task, inference=True)
        return Inferencer.load(_dt.get_path('model_dir'))
    elif task_type == 'ner':
        return ner.NER(task=task, inference=True)
    elif task_type == 'qa':
        return rank.Rank(task=task, inference=True)
    else:
        logger.warning('TASK TYPE NOT SUPPORTED')
        return None
    
def init():
    global task_models, prepare_classes

    # Load models & prepare steps
    task_models = []
    prepare_classes = {}
    for task in cu.tasks.keys():
        task = int(task)
        task_models.append({
            'task' : task,
            'infer': score(task),
            'params' : cu.tasks.get(str(task))
        })
        prepare_classes[task] = pr.Clean(task=task, inference=True)
        logger.warning(f'[INFO] Loaded model and prepare steps for task {task}.')

def run(req):
    # Load request
    req_data = json.loads(req)[0]
    # Prepare text
    if 'subject' in req_data:
        s = req_data['subject']
    else:
        s = ''
    if 'body' in req_data:
        b = req_data['body']
    else:
        b = ''
    text = he.validate_concat(s, b)
    # Score request for multiple models
    res = []
    _cat = ''
    for tm in task_models:
        # Clean text
        clean = prepare_classes[tm['task']].transform_by_task(text)
        # Infer text
        result = tm['infer'].inference_from_dicts(dicts=[{"text": clean, "cat": _cat}])
        try:
            # Special treatment for classification (FARM)
            ##TODO: standardize for all
            _temp = []
            for r in result[0]['predictions']:
                _temp.append(dict(
                    category = r.get('label'),
                    score = f"{r.get('probability'):.3}"
                ))
            _cat = _temp[0].get('category')
            result = _temp
        except Exception as e:
            logger.info(f"Not a FARM model -> {e}")

        # Prepare output
        res.append({
            "task" : int(tm['task']),
            "params" : tm['params'],
            "result" : result
        })
        logger.warning(f'[INFO] Completed task {tm["task"]}.')
    return res

if __name__ == '__main__':
    #NOTE: FOR TESTING ONLY
    init()
    print(run(json.dumps([{"subject":"My pc won't start", 
                        "body":"When I try booting, a red light goes on and then nothing happens",
                        "attachment":""
        }])))