# Named Entity Recognition
The toolkit supports and includes different approaches and frameworks for recognizing relevant entities in text paragraphs, called _Named Entity Recognition_, short _NER_:
- [Azure Text Analytics API](https://docs.microsoft.com/en-us/azure/cognitive-services/text-analytics/how-tos/text-analytics-how-to-entity-linking?tabs=version-3)
- Flair Pre-Trained NER
- FARM/Transformer Custom NER
- Basic approaches (like regex and term lists)



The central components can be found in the script `code/ner.py`.

## Azure Text Analytics API
Azure Text Analytics is a Cognitive Service providing an API-based extraction of relevant entities from texts. You can find the documentation for Azure Text Analytics API [here](https://docs.microsoft.com/en-us/azure/cognitive-services/text-analytics/how-tos/text-analytics-how-to-entity-linking?tabs=version-3). In order to use it within the NLP toolkit, you need to [set up a Cognitive Service](https://docs.microsoft.com/en-us/azure/cognitive-services/cognitive-services-apis-create-account?tabs=multiservice%2Cwindows) in your personal Azure subscription and insert the relevant subscription keys. A basic service is free, yet it has request limitations. You will find a description how to set your keys in [Project Setup](Project Setup.md)

## Flair Pre-trained NER

## FARM / Transformer Custom NER

## Basic approaches
The most basic approach of Named Entity Recognition in text files is to take use of lists or regular expressions (regex). You can add your own terms to the toolkit scope by following these steps:

1. Go to the subfolder `assets/` of the repository folder

2. You find two relevant files in there:
  - `names.txt`
    - stop word list
  - `ner.txt`
    - value-key-pairs of terms and their category, tab-delimited file

3. Open them in a text editor of your choice and add further value-key pairs to `ner.txt` or continue to extend the list of stop words in `names.txt`. Stop words are words which are filtered out before or after processing as they are too common and frequent for bringing value to the analysis.

4. Make sure the values are all lower-case, but the keys should be properly formatted

[<< Previous Page](Train-Classification.md) --- [Next Page >>](Train-QA.md)
