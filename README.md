<img src="demo/logo.PNG" width="500" align="center"><br>

# NLP Toolkit
Verseagility is a Python-based toolkit for your custom natural language processing task, allowing you to bring your own data. It is a central component of the Microsoft Services Knowledge Mining offering.

See the [wiki](./docs/README.md) for detailed documentation how to get started with the toolkit.

## Supported Use Cases
- Binary, multi-class & multi-label classification
- Named entity recognition
- Question answering
- Text summarization

## Live Demo
The live demo of models resulting from Verseagility is hosted at MTC Germany:
> https://aka.ms/nlp-demo

Repository Structure
------------

    ├── /assets            <- Version controlled assets, such as stopword lists. Max size 
    │                         per file: 10 MB. Training data should
    │                         be stored in local data directory, outside of repository or within gitignore. 
    │
    ├── /demo              <- Demo environment that can be deployed as is, or customized. 
    │
    ├── /deploy            <- Scripts used for deploying training or test service  
    │   ├── training.py    <- Deploy your training to a remote compute instance, via AML
    │   │   
    │   ├── hyperdrive.py  <- Deploy hyperparemeter sweep on a remote compute instance, via AML
    │   │
    │   └── service.py     <- Deploy a service (endpoint) to ACI or AKS, via AML
    │
    ├── /docs              <- Detailed documentation.
    │
    ├── /notebook          <- Jupyter notebooks. Naming convention is <[Task]-[Short Description]>,
    │                         for example: 'Data - Exploration.ipynb'
    │
    ├── /pipeline          <- Document processing pipeline components, including document cracker. 
    │
    ├── /project           <- Project configuration files, detailing the tasks to be completed.
    │
    ├── /scraper           <- Website scraper used to fetch sample data. 
    │                         Can be reused for similarly structured forum websites.
    │
    ├── /src               <- Source code for use in this project.
    │   ├── infer.py       <- Inference file, for scoring the model
    │   │   
    │   ├── data.py        <- Use case agnostic utils file, for data management incl upload/download
    │   │
    │   └── helper.py      <- Use case agnostic utils file, with common functions incl secret handling
    │
    ├── /tests              <- Unit tests (using pytest)
    │
    ├── README.md          <- The top-level README for developers using this project.
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment.
    │                         Can be generated using `pip freeze > requirements.txt`
    │
    └── config.ini         <- Configuration and secrets used while developing locally
                              Secrets in production should be stored in the Azure KeyVault
--------

## Naming
### Assets
> \<project name\>(-\<task\>)-\<step\>(-\<environment\>)
- where step in [source, train, deploy], for data assets.
- where task is an int, referring to the parameters, for models.

## Acknowledgements
Verseagility is built in part using the following:
- [Transformers](https://github.com/huggingface/pytorch-transformers) by HuggingFace
- [FARM](https://github.com/deepset-ai/FARM/) by deepset ai
- [spaCy](https://github.com/explosion/spaCy/) by Explosion ai
- [flair](https://github.com/flairNLP/flair/) by Zalando Research
- [gensim](https://radimrehurek.com/gensim/)

Maintainers:
- [Timm Walz](mailto:timm.walz@microsoft.com)
- [Christian Vorhemus](mailto:christian.vorhemus@microsoft.com)
- [Martin Kayser](mailto:martin.kayser@microsoft.com)

## To-Dos
The following section contains a list of possible new features or enhancements. Feel free to contribute. 
### Classification
- [x] multi label support
- [ ] integrate handling for larger documents vs short documents
- [ ] integrate explicit handling for unbalanced datasets
- [ ] ONNX support
### NER
- [ ] improve duplicate handling
### Question Answering
- [ ] apply advanced IR methods
### Summarization
- [ ] **(IP)** full test of integration
### Deployment
- [ ] deploy service to Azure Function (without AzureML)
- [ ] setup GitHub actions
### Notebooks Templates
- [ ] **(IP)** review model results (auto generate after each training step)
- [ ] review model bias (auto generate after each training step)
- [ ] **(IP)** available models benchmark (incl AutoML)
### Tests
- [ ] unit tests (pytest)

## Please note:
- For training data corpora larger than 10.000 documents, we recommend to upload them chunk-wise to the BLOB-storage, otherwise it might come to bottlenecks in the document processor function

## Contributing
This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.