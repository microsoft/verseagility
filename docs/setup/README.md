# Getting Started with Verseagility
This part of the documentation helps you to set up Verseagility in our own subscription and with your data, step by step. Each of the points below will lead you to the respective documentation page. At the bottom of each page you will find a link to the previous and next page.

1. [Setup of Code and Infrastructure](01%20-%20Setup%20of%20Code%20and%20Infrastructure.md)
2. [Data Preparation Pipeline](02%20-%20Bring%20your%20Data.md)
3. [Project Setup](03%20-%20Project%20Setup.md)
4. [Data Cleaning Steps](04%20-%20Data%20Cleaning%20Steps.md)
5. [Model Training](05%20-%20Training%20of%20Models.md)
6. [Deployment (Inferencing)](06%20-%20Deployment.md)

# Overview
![image.PNG](../.attachments/architecture-verseagility-v1-2.PNG)
There are three main components within Verseagility:
1. Data processing pipeline
2. Task modeling
3. Deployment (Inferencing)

## Data Processing Pipeline
The NLP pipeline will standardize the data into a extenible JSON format, from which data preparation and training steps are initiated. These result in custom models for the pre-defined tasks, which can be deployed in a single container instance on ACI or AKS.

**Supported document types**: PDF, Word Document, .txt, PowerPoint, ...

## Task Modeling
![image.PNG](../.attachments/mlflow-verseagility-v1.PNG)
The starting point for each project with Verseagility, is the project configuration (`/project/\*.config.json`). The configuration defines what tasks need to be addressed using the NLP toolkit.

### Supported task types
- Text/Document classification
- Named Entity Recognition
- Question Answering

**Example use cases:**
- Automated support ticket processing (answer suggestion, automatic routing)
- Automated ERP/CRM workflows (extraction of entities from text to auto-complete fields)
- Chatbot extension, with custom classification and entity extraction

**Supported languages**:<br>
Versegility was developed to be as language agnostic as possible. This means that the most common languages are supported (and have been tested) out of the box, while new languages require only minor adjustments to the toolkit.

Validated languages include:
|Shortcut|Language|
|--|--|
|en| English (US)|
|de|German|
|fr|French|
|es|Spanish|
|it|Italian|

Further languages are supported with multi-language pre-trained models or required minor additions to the pre-processing and pre-trained model loading. See the [FAQ](FAQ.md) for details.
