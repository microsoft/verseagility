"""
Simple Demo Dashboard for the NLP Toolkit.

To run dashboard, use:
- streamlit run dashboard.py

#NOTE: This parameter might have to be changed depending on the system
allow_output_mutation -> ignore_hash
"""
import streamlit as st
import spacy
from spacy import displacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Span
import pandas as pd
import json
import requests
from PIL import Image

########################
# PARAMS 
########################

LANGUAGES = ["en","de"]
MODEL_ENDPOINTS = {
    'en':'http://f85b4e51-b725-4813-b383-e2b0146539c8.westeurope.azurecontainer.io/score',
    'de':'http://97c42256-419c-4478-bab4-70d542152037.westeurope.azurecontainer.io/score'
    }
DEFAULT_SUBJECT = {
    'en': "Windows defender shutting everything down",
    'de': "Win 7 ohne Updates"
    }
DEFAULT_TEXT = {
    'en': "I am running Windows 7. Can I have Bill Gates number, need help?! Microsoft should know better...",
    'de': "Hallo freunde. Mein Windows 7 Rechner will keine Updates mehr laden. Normalerweise funktionieren die Microsoft produkte so gut! Kann Bill Gates mir nicht helfen?"
    }

########################
# FRONTEND 
########################

HTML_WRAPPER = """<div style="overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; margin-bottom: 2.5rem">{}</div>"""
try:
    logo = Image.open('~/app/logo2_nbg.PNG')
    # ms = Image.open('~/app/microsoft.png')
except FileNotFoundError:
    logo = Image.open('logo2_nbg.png')
    # ms = Image.open('microsoft.png')

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
    r = requests.post(MODEL_ENDPOINTS[lang], json=[{
		"subject": subject,
		"body":text
	}
    ])
    nlp = load_model(model_name)
    return nlp, nlp(validate_concat(subject, text)[0]), r.json()

st.sidebar.image(logo, use_column_width=True, format='PNG')
st.sidebar.subheader("NLP Toolkit Demo")
st.sidebar.markdown(
    """
Text classification, named entity recognition 
and answer suggestions for 
support emails and attachments.

\n\n
"""
)

# Language selection
st.sidebar.subheader("Language")
lang = st.sidebar.selectbox("Select language", LANGUAGES)

# # Credits
# st.sidebar.subheader("Credits")
# st.sidebar.markdown(
# """
# Authors: Timm Walz, Martin Kayser

# Powered by
# """
# )
# st.sidebar.image(ms, width=200)

# Submit text
subject = st.text_input("SUBJECT", DEFAULT_SUBJECT[lang])
text = st.text_area("BODY", DEFAULT_TEXT[lang])
model_load_state = st.info(f"Loading results ({lang})...")
nlp, doc, res = process_text(lang, subject, text)
model_load_state.empty()
st.button("Submit")

st.header("--------------------------------------------------------------")

# Classification Output
st.header(f"CATEGORY")
res_cat = res[0].get('result')[0]
st.subheader(f"> {res_cat.get('category').capitalize()} ({res[0].get('result')[0].get('score')})")

# Extracted Entities
if len(res[1]['result']) > 0:
    st.header("NAMED ENTITIES")
    df_ner = pd.read_json(json.dumps(res[1]['result']))
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

    # # Custom colors
    # colors = {"ORG": "linear-gradient(90deg, #aa9cfc, #fc9ce7)"}
    # options = {"ents": ["ORG"], "colors": colors}
    # displacy.serve(doc, style="ent", options=options)

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
if len(res[2]['result']) > 0:
    st.header("ANSWER SUGGESTIONS")
    def_qa = pd.read_json(json.dumps(res[2]['result']))[['answer_text_clean','score','appliesTo']]
    for i, (a, s, t) in enumerate(zip(def_qa.answer_text_clean, def_qa.score, def_qa.appliesTo)):
        st.subheader(f'> Suggestion {i + 1}')
        st.write(a)
        st.table(pd.DataFrame({'score':[s],'applies to':[t]}, index=[i + 1]))
        st.write('')

st.header("----------------------------END-----------------------------")

# Display raw JSON
if st.button("Show raw result"):
    try:
        st.table(df_ner)
        st.table(def_qa)
    except:
        pass
    st.json(res)
    