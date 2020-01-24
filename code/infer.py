"""
INFERENCE: Orchestration service for serving the model.

"""
import os
import json
import shutil
import threading

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
        return Inferencer.load(_dt.fn_lookup.get('fn_cat'))
    elif task_type == 'ner':
        return ner.NER(inference=True)
    elif task_type == 'qa':
        return rank.Rank(task=task, inference=True)
    else:
        logger.info('TASK TYPE NOT SUPPORTED')
        return None
    
def init():
    global task_models, prepare_classes

    # Unpack model dependencies
    dt_init = dt.Data(inference=True)
    shutil.unpack_archive(dt_init.fn_lookup['fn_asset'], dt_init.data_dir, 'zip')
    logger.info(f'[INFO] Unpacked model assets from {dt_init.fn_lookup["fn_asset"]}')

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
        logger.info(f'[INFO] Loaded model and prepare steps for task {task}.')

def run_model():
    pass

def run(req):
    # Load request
    req_data = json.loads(req)
    # Prepare text
    if 'subject' in req_data[0]:
        s = req_data[0]['subject']
    else:
        s = ''
    if 'body' in req_data[0]:
        b = req_data[0]['body']
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
            _temp = []
            for r in result[0]['predictions']:
                _temp.append(dict(
                    category = r.get('label'),
                    score = f"{r.get('probability'):.3}"
                ))
            _cat = _temp[0].get('category')
            result = _temp
        except:
            pass
        # Prepare output
        res.append({
            "task" : int(tm['task']),
            "params" : tm['params'],
            "result" : result
        })
        logger.info(f'[INFO] Completed {tm["task"]}.')
    return res

if __name__ == '__main__':
    #NOTE: FOR TESTING ONLY
    init()
    print(run(json.dumps([{"subject":"My pc won't start", 
                        "body":"When I try booting, a red light goes on and then nothing happens",
                        "attachment":""
        }])))