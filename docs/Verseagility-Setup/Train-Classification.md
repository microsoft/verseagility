# Classification / Training
This part of the documentation serves as guideline for the model training process. The data is automatically going to be pulled from the Cosmos DB. Your project language is the respective search criteria, so all English documents are going to be incorporated into the training process if you choose English as your project language and so on.

[[_TOC_]]

## Initiate the Training
After setting up your projects in the previous pages, you are now ready to train your models. This training step incorporates the classification, named entity recognition and question/answering models all in one.
  1. Open your command line in VSCode, PowerShell or bash.
  2. Change your directory to root directory of the repository.
  3. Activate your environment in case you have not yet by typing `conda activate nlp`.
  4. Make sure that the `pytorch` line of the `environment.yml` is commented out as below:
  `#- pytorch=1.3.1 # NOTE: UNCOMMENT THIS FOR LOCAL ENV INSTALL, BUT COMMENT IT AGAIN FOR TRAINING/DEPLOYMENT`
  5. Following command needs to be adapted to your project language:
  ```python
  python deploy/training.py --project_name [INSERT PROJECT NAME FROM CONFIG.JSON] --do_prepare --do_train
  ```
  In case your project name is `msforum_en`, it would look as follows:
  ```python
  python deploy/training.py --project_name msforum_en --do_prepare --do_train
  ```
  6. This step might take a while, especially when executing it for the first time. Training is now running and the datasets as well as experiments are going to be registered in Azure Machine Learning.
  7. Once you see `[INFO] Task 1 deployed for training.` in the logs, the job has successfully been started. Open your experiment in Azure Machine Learning. You can also find a direct URL in the logs which is going to lead you to your experiment.

## Access your experiment in Azure Machine Learning
After running the classification training step, you will find your experiments in Azure Machine Learning.

1. Clicking on "_Experiments_" on the left side, you will find your experiment being registered with the respective name and language shortcut. In case you initiate further training rounds for the same language, they will all be registered under the same experiment. Click on the respective experiments to get insights on running an, failed and finished experiment rounds. <br><br>![Azure ML Experiments](../../.attachments/classification-aml-experiments.PNG) <br><br>

2. There, you will get a detailed view on earlier training rounds. <br><br>![Azure ML Experiments](../../.attachments/classification-aml-experiments-en.PNG)

3. After the training round has successfully been finished, enter the `Models` menu on the left hand side. There you will find models which successfully have been trained.

  ![AML Models](../../.attachments/aml-models.PNG)

4. For every task like classification, NER etc., a separate model is going to be registered. For example, `msforum_de-model-1` stands for a successfully trained classification model, `msforum_de-model-4` for question/answering. Depending on your pre-defined tasks, you should wait until all your models appear here before you proceed with the model deployment.

TODO:
- limitations: max characters, etc.. focus is on paragraph, not document classification

[<< Previous Page](Prepare-Data.md) --- [Next Page >>](Train-NER.md)
