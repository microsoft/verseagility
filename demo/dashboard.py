# -*- coding: utf-8 -*-
"""
Simple Demo Dashboard for the NLP Toolkit.
To run dashboard, use:
- streamlit run dashboard.py
#NOTE: This parameter might have to be changed depending on the system
allow_output_mutation -> ignore_hash
"""
from requests.models import MissingSchema
import streamlit as st
import spacy
from spacy import displacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Span
import pandas as pd
import json
import requests
from PIL import Image
import load_examples as loader
from io import StringIO

# Streamlit config
st.set_page_config(
    page_title="Verseagility Demo",
    page_icon=":shark:",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Set parameters
LANGUAGES = loader.get_languages()
MODEL_ENDPOINTS, ENDPOINT_KEY = loader.get_endpoints(LANGUAGES)
EXAMPLES = loader.get_examples()

# FRONTEND DEFINITION
HTML_WRAPPER = """<div style="overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; margin-bottom: 2.5rem">{}</div>"""
# Logo loading
try:
    logo = Image.open('~/app/logo.png')
except FileNotFoundError:
    logo = Image.open('logo.png')

# @st.cache(allow_output_mutation=True)
def load_model(name):
    return spacy.blank(name)

def validate_concat(col1, col2, max_len=1000):
    """
    Determine if concatination is needed, by checking for dublicate in subject and body.
    Max length of sequence (text) is set. Characters surpassing max_len are cut-off. 
    """
    text_concat = []
    if isinstance(col1, str):
        col1, col2 = [col1], [col2]

    for n, (sub, des) in enumerate(zip(col1, col2)):
        try:
            if sub in des[:len(sub)]:
                text_concat.append(des[:max_len])
            else:
                new_line = sub + '. ' + des
                text_concat.append(new_line[:max_len])
        except Exception as e:
            text_concat.append(des[:max_len])
    return text_concat

# @st.cache(allow_output_mutation=True)
def process_text(model_name, subject, text):
    r = requests.post(MODEL_ENDPOINTS[lang], 
        json=[{
            "subject": subject,
            "body":text
        }],
        headers={"Authorization": f"Bearer {ENDPOINT_KEY[lang]}"}
    )
    nlp = load_model(model_name)
    return nlp, nlp(validate_concat(subject, text)[0]), r.json()

st.sidebar.image(logo, use_column_width=True, output_format='PNG')
st.sidebar.subheader("NLP Toolkit Demo")
st.sidebar.markdown(
"""
Text classification, named entity recognition 
and answer suggestions for 
support emails and attachments.

**Example based on forum posts**
https://answers.microsoft.com/
\n\n
"""
)

# Language selection
st.sidebar.subheader("Language")
lang_select = st.sidebar.selectbox("Select language", [*LANGUAGES])
lang = LANGUAGES[lang_select]

# Credits
st.sidebar.subheader("Build your own NLP solution and demo")
st.sidebar.markdown(
"""
https://github.com/microsoft/verseagility
"""
)

# Submit text
selection = st.selectbox("EXAMPLES", [*EXAMPLES[lang]])
subject = st.text_input("SUBJECT", EXAMPLES[lang][selection]['Subject'])
text = st.text_area("BODY", EXAMPLES[lang][selection]['Body'])
model_load_state = st.info(f"Loading results ({lang})...")
try:
    nlp, doc, res = process_text(lang, subject, text)
    model_load_state.empty()
except MissingSchema:
    model_load_state.empty()
    st.error('Could not score model. Did you set your keys in the app settings?')
    st.stop()
st.button("Submit")
st.header("--------------------------------------------------------------")

# Get results
res_cat = None
res_ner = None
res_qa = None
for r in res:
    if r.get('task') == 1:
        res_cat = r
    elif r.get('task') == 3:
        res_ner = r
    elif r.get('task') == 4:
        res_qa = r

# Classification Output 
if res_cat is not None:
    st.header(f"CLASSIFICATION")
    res_cat = res_cat.get('result')[0]
    st.subheader(f"> {res_cat.get('category').capitalize()} ({res[0].get('result')[0].get('score')})")

# Extracted Entities
if res_ner is not None and len(res_ner.get('result')) > 0:
    st.header("NAMED ENTITIES")
    df_ner = pd.read_json(json.dumps(res_ner.get('result')))
    # Get value pairs as dict
    entity_names = {x:[] for x in df_ner.label}
    for x, y in zip(df_ner.label,df_ner.value):
        entity_names[x].append(y)
    entities = [*entity_names]
    # Create matcher
    matcher = PhraseMatcher(nlp.vocab)
    for key, value in entity_names.items():
        patterns = [nlp(entity) for entity in value] 
        matcher.add(key, None, *patterns)
    doc.ents = [ent for ent in list(doc.ents) if ent.label_ in entity_names]
    matches = matcher(doc)

    # Get matches in text
    for match_id, start, end in matches:
        rule_id = nlp.vocab.strings[match_id]  
        span = doc[start : end]
    
    # Transform to spans and check for duplicates
    starts = []
    for match_id, start, end in matches:
        rule_id = nlp.vocab.strings[match_id]
        for entityname in entities:
            span = Span(doc, start, end, label=entityname)
            if rule_id == entityname:
                try:
                    doc.ents = list(doc.ents) + [span]
                except:
                    pass
    options = {"ents": entities}

    # Render marked sentences
    html = displacy.render(doc, style='ent')

    # Newlines seem to mess with the rendering
    html = html.replace("\n", " ")
    st.write(HTML_WRAPPER.format(html), unsafe_allow_html=True)
    attrs = ["text", "label_", "start", "end", "start_char", "end_char"]
    data = [
        [str(getattr(ent, attr)) for attr in attrs]
        for ent in doc.ents
        if ent.label_ in entity_names
    ]

# Similar Questions Output
if res_qa is not None and len(res_qa.get('result')) > 0:
    st.header("ANSWER SUGGESTIONS")
    def_qa = pd.read_json(StringIO(json.dumps(res_qa.get('result'))))[['answer_text_clean','score','label_classification_multi']]
    for i, (a, s, t) in enumerate(zip(def_qa.answer_text_clean, def_qa.score, def_qa.label_classification_multi)):
        st.subheader(f'> Suggestion {i + 1}')
        st.write(a)
        st.table(pd.DataFrame({'score':[s],'applies to':[t]}, index=[i + 1]))
        st.write('')

# Display raw JSON
st.subheader("JSON Result")
with st.expander("Show raw result"):
    st.json(res)
    