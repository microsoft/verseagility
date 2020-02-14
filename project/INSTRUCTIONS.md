# How to run your first project

## Steps
1. Upload your source dataset (raw) to AzureML Datasets
2. Upload your dependencies to AzureML Datasets (stopwords, custom ner)
3. Customize custom.py with any required pre-processing steps
4. Create a *.config.json where * = project name
5. Run deploy/training.py
6. Run deploy/inference.py

## Requirements
To make the NLP kit work flawlessly, there are some naming requirements and best practices.
 
- Use language short froms (eg. German = de, French = fr)
- Naming
 - stopword list: stopwords-<language>.txt (tab delimited, utf-8)