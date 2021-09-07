# Question Answering
This page is devoted to the question-answering component of the NLP toolkit and describes how the answer suggestions are being ranked during runtime. Please keep in mind that this component of the toolkit requires a large amount of potential answers for each text that has been trained along with the input texts in order to



## Ranking Algorithm
The current version of Verseagility supports the Okapi BM25 information retrieval algorithm to sort historical question answer pairs by relevance. BM25 is a ranking approach used by search engines to estimate the relevance of a document to a given search query, such as a text or document. This is implemented using the [gensim library](https://radimrehurek.com/gensim/summarization/bm25.html). The ranking framework is accessed by the file `code/rank.py`.

## Potential Extensions
Due to the modular setup, this section can be extended to support the QNAMaker from Microsoft, or custom question answering algorithms using Transformers and FARM. Support for these may be added in coming versions of Verseagility.