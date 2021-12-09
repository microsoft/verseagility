 # Data Cleaning Steps
 
 The following section covers aspects of data pre-processing used for different tasks. Some pre-processing steps are universal, while others are task specific. They are split accordingly. You may edit/comment some steps out, or even add further ones depending on your needs in the file `src/prepare.py`. This section for example covers data cleaning steps exclusively for German emails and support tickets, with typical phrases occuring in these kinds of documents. You may add further phrases for the language code needed and they will be considered in the data preparation.
 ```python
# DE
if self.language == 'de':
    line = re.sub(r'\b(mit )?(beste|viele|liebe|freundlich\w+)? (gr[u,ü][ß,ss].*)', '', line, flags=re.I)
    line = re.sub(r'\b(besten|herzlichen|lieben) dank.*', '', line, flags=re.I)
    line = re.sub(r'\bvielen dank für ihr verständnis.*', '', line, flags=re.I) 
    line = re.sub(r'\bvielen dank im voraus.*', '', line, flags=re.I) 
    line = re.sub(r'\b(mfg|m\.f\.g) .*','', line, flags=re.I)
    line = re.sub(r'\b(lg) .*','',line, flags=re.I)
    line = re.sub(r'\b(meinem iPhone gesendet) .*','',line, flags=re.I)
    line = re.sub(r'\b(Gesendet mit der (WEB|GMX)) .*','',line, flags=re.I)
    line = re.sub(r'\b(Diese E-Mail wurde von Avast) .*','',line, flags=re.I)
```

## Universal Steps
- Placeholders

## Question Answering
- Stopword removal
- Lemmatization
- Regex removal

In the next step, we will describe the [Training of Models](05%20-%20Training%20of%20Models.md).