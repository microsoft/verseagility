#MAIN for deployment
##PARAMS
# update assets (boolean)
# target (aci, aks,...)


############################################
#####   Task 1
############################################

# ## Experiment
# experiment_name = run_type_str + "-hyper"
# exp = Experiment(workspace = ws, name = experiment_name)
# ## Parameters
# ### Fixed parameters
# script_params = {
#     '--task' : 1,
#     '--run_version': run_version,
#     '--run_type': run_type,
#     '--per_gpu_train_batch_size' : 64,
#     '--max_seq_length' : 128,
#     '--num_train_epochs' : 4,
#     '--do_train' : ''
# }
# ### Task parameters
# script_params_task1 = {
#     '--evaluate_during_training': '',
#     '--eval_all_checkpoints':'',
#     '--cleanup':''
# }
# script_params_task = {**script_params, **script_params_task1}
# ### Hyperparameters params
# param_sampling = BayesianParameterSampling( {
#     '--learning_rate' : choice(2e-5, 4e-5, 5e-5, 6e-5, 8e-5)
# })
# ## Prepare task image
# est_task1 = PyTorch(source_directory = script_folder,
#             compute_target = compute_target,
#             script_params = script_params_task,
#             entry_script = 'code/train.py',
#             pip_packages = pip_packages,
#             use_gpu = True)
# ## Prepare HyperDrive Config
# hdc = HyperDriveConfig(estimator=est_task1, 
#             hyperparameter_sampling = param_sampling,
#             policy = None, # NOTE: not possible for bayesian
#             primary_metric_name = 'eval_f1',
#             primary_metric_goal = PrimaryMetricGoal.MAXIMIZE,
#             max_total_runs = 20,
#             max_concurrent_runs = 1)
# ## Run hyperparameter tuning
# hyperdrive_run = exp.submit(config=hdc)
# hyperdrive_run.wait_for_completion(show_output = False)
# ## Get Results
# best_run = hyperdrive_run.get_best_run_by_primary_metric()
# ## Experiment
# experiment_name = run_type_str + "-train"
# exp = Experiment(workspace = ws, name = experiment_name)
# #Parameters determined by hyperparams
# script_params_hyper = {
#     '--do_upload' : '',
#     '--do_eval':'',
#     '--learning_rate' : get_best_argument(best_run.get_details(), 'learning_rate')
# }
# script_params_best = {**script_params, **script_params_hyper}
# script_params_best
# est_best = PyTorch(source_directory = script_folder,
#             compute_target = compute_target,
#             script_params = script_params_best,
#             entry_script = 'code/train.py',
#             pip_packages = pip_packages,
#             use_gpu = True)
# # # Run single
# run = exp.submit(est_best)
# run.wait_for_completion(show_output = False)