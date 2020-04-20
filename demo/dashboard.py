# -*- coding: utf-8 -*-
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

LANGUAGES = ["en","de","fr","es","it"]
MODEL_ENDPOINTS = {
    'en': 'http://632632c6-d926-4cd3-961a-fe1ba5dbf003.southcentralus.azurecontainer.io/score', #msforum-en-prod
    'de': 'http://ca073ab1-ec54-4fc3-92be-234c16201112.southcentralus.azurecontainer.io/score', #msforum-de-prod
    'fr': 'http://26e0d4f6-07d4-4736-a2e7-9ec8e0823bf4.southcentralus.azurecontainer.io/score', #msforum-fr-prod
    'es': "http://9918c9b2-7447-49e7-a2e1-84c3710e62ce.southcentralus.azurecontainer.io/score", #msforum-es-prod
    'it': "http://242e81ec-731a-4101-80cd-4ed2885a1dd3.southcentralus.azurecontainer.io/score" #msforum-it-prod
}
ENDPOINT_KEY = {
    'en': '97nZStGWNHfOLqkuHHlS9zm3a6Ivv0ex',
    'de': 'fdcHcveUDSqBUAfvwe9jklQKB0F30sBo',
    'fr': 'lhDUPH3qpLiiwfeVl1ZBS3fbjyICvbc0',
    'es': 'BF0FYTbXMjSuUtsCI31vbNgAc47xGfiE',
    'it': 'AbYdmTYoKUkiwf0AdbVnpP5KhMjLwZUS'
    }
DEFAULT_SUBJECT = {
    'en': "Windows defender shutting everything down",
    'de': "Win 7 ohne Updates",
    'fr': "Erreur lié à l abonnement",
    'es': "Error de actualizacion",
    'it': "Fotocamera schermata nera"
    }
DEFAULT_TEXT = {
    'en': "I am running Windows 7 - I thought it couldn't get a virus. Can I have Bill Gates number, need help?! Microsoft should know better...",
    'de': "Hallo freunde. Mein Windows 7 Rechner will keine Updates mehr laden - mit folgendem fehlercode 0xa00f4289. Normalerweise funktionieren die Microsoft produkte doch so gut! Kann Bill Gates mir nicht helfen?",
    'fr': "J'ai renouvelé mon abonnement office et j'obtiens toujous le message d'erreur 'Nous avons rencontré un problème lié à votre abonnement...' J'ai fait tout ce qui est proposé y compris désinstaller et ré-installer et j'obtiens toujours le message d'erreur. Merci de me dire comment régler le tout.",
    'es': "Cuándo actualizo mi laptop Windows 7 no se actualiza y se queda en 27% y 30% Se reinicia y no la actualiza necesito ayuda.",
    'it': "Buonasera, se apro la fotocamera, la schermata resta nera e ogni tanto compare il messaggio Non è possibile trovare la fotocamera... codice errore fotocamera 0xa00f4289 Acitve Camera Unplugged. Ho fatto varie verifiche nelle impostazioni del pc (win 10), provato ad aggiornare il driver, disinstallare e riavviare, ho aggiunto la fotocamera nelle eccezioni dell'antivirus... Cosa potrei fare ancora? Grazie!"
    }

########################
# FRONTEND 
########################

HTML_WRAPPER = """<div style="overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; margin-bottom: 2.5rem">{}</div>"""
# Logo loading
try:
    logo = Image.open('~/app/logo.png')
    ms = Image.open('~/app/microsoft.png')
except FileNotFoundError:
    logo = Image.open('logo.png')
    ms = Image.open('microsoft.png') 

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

# Credits
st.sidebar.subheader("Data Source")
st.sidebar.markdown(
"""
https://answers.microsoft.com/

"""
)
# st.sidebar.image(ms, width=200)

# Submit text
subject = st.text_input("SUBJECT", DEFAULT_SUBJECT[lang])
text = st.text_area("BODY", DEFAULT_TEXT[lang])
model_load_state = st.info(f"Loading results ({lang})...")
nlp, doc, res = process_text(lang, subject, text)
model_load_state.empty()
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
    st.header(f"CATEGORY")
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
if res_qa is not None and len(res_qa.get('result')) > 0:
    st.header("ANSWER SUGGESTIONS")
    def_qa = pd.read_json(json.dumps(res_qa.get('result')))[['answer_text_clean','score','label_classification_multi']]
    for i, (a, s, t) in enumerate(zip(def_qa.answer_text_clean, def_qa.score, def_qa.label_classification_multi)):
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
    