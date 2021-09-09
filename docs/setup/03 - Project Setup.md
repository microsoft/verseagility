# Project Setup
This page describes how you get and set the right Azure resource keys to make Verseagility work end-to-end.

## Grab your Keys
1. In the root directory of the Verseagility repository, you will find a file named `config.sample.ini`, which has the following content:

  ```
  [environ]
  aml-ws-name=
  aml-ws-sid=
  aml-ws-rg=
  text-analytics-name=
  text-analytics-key=
  cosmos-db-name=
  cosmos-db-key=
  ```

2. Create a copy of this file and name it `config.ini`. Store it in the same folder as the `config.sample.ini`

3. Go to your newly created resource group in your [Azure portal](https://portal.azure.com) and enter following resources one after another:
  - __Azure Machine Learning__
    - The main page of Azure Machine Learning has all the information you need, starting with the name of your resource, which you have to insert in the `aml-ws-name`.
    - Secondly, you have to insert your subscription ID as stated in the screenshot below in the second row `aml-ws-sid`.
    - Also, you have to insert the name of your resource group in the line `aml-ws-rg`.
    - ![Azure Machine Learning Keys](../.attachments/keys-aml.PNG)

  - __Text Analytics Service__
    - At the main page called _Quick start_, copy the following elements:
    - Copy  _Key1_ and insert it in the `text-analytics-key` row of your `ini`-file.
    - Mark and copy the  _Endpoint_ name of the text analytics service as stated in the frame and insert it in the `text-analytics-name` of your file. You do not need the whole URL, the name is sufficient.
    - Please verify with the icon you see below that you are actually using the Text Analytics resource instead of the Computer Vision.

    - ![Text Analytics Keys](../.attachments/keys-ta.PNG)
  - __Cosmos DB__
    - After entering your _Cosmos DB_ resource, click on _Keys_ in the left menu.
    - From there, copy the resource name from the _URI_-field, which matches to the name of the resource. Similarly to the _Text Analytics Service_, you do not need the entire URL, the name is sufficient. Insert it in the `cosmos-db-name` of your file.
    - Last but not least, copy the _Primary Key_ and set it in the `cosmos-db-key` row.
    - ![Cosmos DB Keys](../.attachments/keys-cdb.PNG)

4. Your file should look similarly to this one (the values below are random):
  ```
  [environ]
  aml-ws-name=vers-aml-workspace-ikkavgc641vq2
  aml-ws-sid=1dca2144-0815-3301-b6a5-8a97ef7632a5
  aml-ws-rg=verseagility
  text-analytics-name=verstaxhksd72s
  text-analytics-key=9b82deffedca46bd9b4938cd8029a355
  cosmos-db-name=verscosmosiqkkxah120vq2
  cosmos-db-key=XH0mse9II5wYaXJMFb5sycyDcaAWwATwJTAdvVhBD18QdQaYsZe23mupgD378VZW751yHP6v4YbOZitgxSXSg==
  ```

## Tasks
As described before, currently the following tasks are supported:
- Text/Document classification
- Named Entity Recognition
- Question Answering
The section below covers briefly what they consist of, which dependencies they have and how you can customize them further.

### **Classification**
This section describes which models are used to train classification models. Both multi-class and multi-label approaches are supported and facilitated by the [FARM](https://github.com/deepset-ai/FARM) framework. We primarily use so-called Transformer models to train classification assets.

#### **Transformers**
- Transformers provides thousands of pretrained models to perform tasks on texts such as classification, information extraction, question answering, summarization, translation, text generation, etc in 100+ languages. Its aim is to make cutting-edge NLP easier to use for everyone.
- Transformers provides APIs to quickly download and use those pretrained models on a given text, fine-tune them on your own datasets then share them with the community on our model hub. At the same time, each Python module defining an architecture can be used as a standalone and modified to enable quick research experiments.
- Transformers is backed by the two most popular deep learning libraries, PyTorch and TensorFlow, with a seamless integration between them, allowing you to train your models with one then load it for inference with the other. In this setup, we use PyTorch.

The models used are defined in `src/helper.py` and the dictionary below can be extended by other model names and languages. The list of pretrained models for many purposes can be found on [HuggingFace](https://huggingface.co/transformers/pretrained_models.html).
```python
farm_model_lookup = {
    'bert': {
        'xx':'bert-base-multilingual-cased',
        'en':'bert-base-cased',
        'de':'bert-base-german-cased',
        'fr':'camembert-base',
        'cn':'bert-base-chinese'
        },
    'roberta' : {
        'en' : 'roberta-base',
        'de' : 'roberta-base',
        'fr' : 'roberta-base',
        'es' : 'roberta-base',
        'it' : 'roberta-base'
        # All languages for roberta because of multi_classificaiton
    },
    'xlm-roberta' : {
        'xx' : 'xlm-roberta-base'
    },
    'albert' : {
        'en' : 'albert-base-v2'
    },
    'distilbert' : {
        'xx' : 'distilbert-base-multilingual-cased',
        'de' : 'distilbert-base-german-cased'
    }
}
```

### **Named Entity Recognition**
The toolkit supports and includes different approaches and frameworks for recognizing relevant entities in text paragraphs, called _Named Entity Recognition_, short _NER_:
- [Azure Text Analytics API](https://docs.microsoft.com/en-us/azure/cognitive-services/text-analytics/how-tos/text-analytics-how-to-entity-linking?tabs=version-3)
- Flair Pre-Trained NER
- FARM/Transformer Custom NER
- Basic approaches (like regex and term lists)

The central components can be found in the script `code/ner.py`.

#### **Azure Text Analytics API**
Azure Text Analytics is a Cognitive Service providing an API-based extraction of relevant entities from texts. You can find the documentation for Azure Text Analytics API [here](https://docs.microsoft.com/en-us/azure/cognitive-services/text-analytics/how-tos/text-analytics-how-to-entity-linking?tabs=version-3). In order to use it within the NLP toolkit, you need to [set up a Cognitive Service](https://docs.microsoft.com/en-us/azure/cognitive-services/cognitive-services-apis-create-account?tabs=multiservice%2Cwindows) in your personal Azure subscription and insert the relevant subscription keys. A basic service is free, yet it has request limitations. You will find a description how to set your keys in [Project Setup](Project Setup.md)

#### **Flair Pre-trained NER**

#### **FARM / Transformer Custom NER**

#### Basic approaches
The most basic approach of Named Entity Recognition in text files is to take use of lists or regular expressions (regex). You can add your own terms to the toolkit scope by following these steps:

1. Go to the subfolder `assets/` of the repository folder

2. You find two relevant files in there:
  - `names.txt`
    - stop word list
  - `ner.txt`
    - value-key-pairs of terms and their category, tab-delimited file

3. Open them in a text editor of your choice and add further value-key pairs to `ner.txt` or continue to extend the list of stop words in `names.txt`. Stop words are words which are filtered out before or after processing as they are too common and frequent for bringing value to the analysis.

4. Make sure the values are all lower-case, but the keys should be properly formatted

### **Question Answering**
This section is devoted to the question-answering component of the NLP toolkit and describes how the answer suggestions are being ranked during runtime. Please keep in mind that this component of the toolkit requires a large amount of potential answers for each text that has been trained along with the input texts in order to

#### **Ranking Algorithm**
The current version of Verseagility supports the Okapi BM25 information retrieval algorithm to sort historical question answer pairs by relevance. BM25 is a ranking approach used by search engines to estimate the relevance of a document to a given search query, such as a text or document. This is implemented using the [gensim library](https://radimrehurek.com/gensim/summarization/bm25.html). The ranking framework is accessed by the file `code/rank.py`.

#### **Potential Extensions**
Due to the modular setup, this section can be extended to support the QNAMaker from Microsoft, or custom question answering algorithms using Transformers and FARM. Support for these may be added in coming versions of Verseagility.

## Project File

1. Create a config file for your end-to-end Verseagility-project in the subfolder _project/_ (located in the root folder of the repository). We recommend you to follow this naming convention:
`[name of your project]\_[language code, two letters].config.json` -> `msforum_en.config.json` <br>
See the following json-snippet as an example:
```json
{
    "name":"msforum_en",
    "language": "en",
    "environment" : "dev",
    "data_dir" : "./run/",
    "prepare" : {
        "data_type" : "json"
    },
    "tasks": {
        "1": {
            "label": "subcat",
            "type": "classification",
            "model_type": "roberta",
            "max_seq_len": 256,
            "embeds_dropout":0.3,
            "learning_rate":3e-5,
            "prepare": true
        },
        "3": {
            "type": "ner",
            "prepare": false
        },
        "4": {
            "type": "qa",
            "model_type": "historical",
            "prepare": true
        }
    },
        "deploy": {
            "type": "ACI",
            "memory": 2,
            "cpu": 1
        }
}
```
You see that there are multiple task levels. If you only want to go for classification, keep task level 1 in mind. In case you do not want to integrate Named Entity Recognition and Question/Answering, simply remove it from your JSON.

2. After creating the json file, you need to do a slight change in the `custom.py` script:
  - Look for this line within the script: <br>
  ```python
  params = he.get_project_config('[INSERT CONFIG NAME HERE]')
  ```
  - Insert the file name of the JSON (e.g. `msforum_en.config.json`) you just created in the first step of this section. You do not need to pass a folder name as long as the file is located in `project/`, which we highly recommend. The line of your code should look like this:
  ```python
  params = he.get_project_config('msforum_en.config.json')
  ```

Your project is now set up!