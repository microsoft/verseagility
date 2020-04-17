from summarizer import Summarizer
import nltk
nltk.download('punkt')
import re
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from sklearn.metrics.pairwise import cosine_similarity
from gensim.summarization.summarizer import summarize
import networkx as nx
import numpy as np

''' BERTABS '''
def summarizeText(text, minLength=60):
    result = model(text, min_length = minLength)
    full = ''.join(result)
    return full

''' SAMPLING '''
def sentencenize(text):
    sentences = []
    for sent in text:
        sentences.append(sent_tokenize(sent))
    sentences = [y for x in sentences for y in x]
    return sentences

def extractWordVectors(file):
    word_embeddings = {}
    for line in file:
        values = line.split()
        word = values[0]
        coefs = np.asarray(values[1:], dtype='float32')
        word_embeddings[word] = coefs
    file.close()

def removeStopwords(sen, sw):
    sentence = " ".join([i for i in sen if i not in sw])
    return sentence

''' BERTABS '''
model = Summarizer()

''' SAMPLING '''
clean_sentences = [removeStopwords(r.split(), sw) for r in clean_sentences]

''' GENSIM '''
summarize()