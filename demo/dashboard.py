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
import os

########################
# PARAMS 
########################

LANGUAGES = ["en","de","fr","es","it"]
MODEL_ENDPOINTS = {
    'en': os.environ.get('ACI_EN'), #msforum-en-prod
    'de': os.environ.get('ACI_DE'), #msforum-de-prod
    'fr': os.environ.get('ACI_FR'), #msforum-fr-prod
    'es': os.environ.get('ACI_ES'), #msforum-es-prod
    'it': os.environ.get('ACI_IT') #msforum-it-prod
}
ENDPOINT_KEY = {
    'en': os.environ.get('ACI_EN_KEY'),
    'de': os.environ.get('ACI_DE_KEY'),
    'fr': os.environ.get('ACI_FR_KEY'),
    'es': os.environ.get('ACI_ES_KEY'),
    'it': os.environ.get('ACI_IT_KEY')
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
EXAMPLES = {
    'en': {'Default': 
            {'Subject': DEFAULT_SUBJECT['en'], 
             'Body': DEFAULT_TEXT['en']},
            'Support Ticket 1': 
            {'Subject': 'Windows screen goes dark except for small box of squiggly lines -- virus?', 
             'Body': 'This is new HP system running Windows 10. The screen suddenly goes dark except for a few squiggly lines in the middle of the screen:Suspecting virus. Any ideas about what this is and how to fix it? Thanks!'},
             'Support Ticket 2': 
            {'Subject': 'Switching from rear to front camera on Surface Pro 4', 
             'Body': "I can't figure out how to switch from the rear (default) to front camera. The guidance I've found so far on the Web indicates that there should be a reverse icon on the small control bar at the top of the camera screen. I don't have that. The other instruction I found says to swipe down from the top of the screen to expose the reverse button. This doesn't work for me. I'd appreciate some help with this.Thanks,Don E."},
             'Support Ticket 3': 
            {'Subject': 'Favorites Tab - Who can help to restore old links in Favorites Tab?', 
             'Body': "Lost all my links on Fave tab - 3 new tabs replaced all my links in the Yellow Star - they are Microsoft Wesites, MSN Websites and Windows Live. Also Bing toolbar has suddenly appeared even though I didn't want it! Any ideas please?"},
            'Free Text': 
            {'Subject': 'Subject', 
             'Body': 'Body'}},
    'de': {'Default': 
            {'Subject': DEFAULT_SUBJECT['de'], 
             'Body': DEFAULT_TEXT['de']},
             'Support Ticket 1': 
            {'Subject': 'PDF Vorschau im Datei Explorer mit PDF Viewer von Edge Browser', 
             'Body': 'Hallo zusammen,der Edge Browser bringt ja einen PDF viewer mit der zuerstein mal vollkommen ausreichend für mich ist. Ist es irgendwie möglich im Datei Explorer in der Ansicht den PDF Viewer des Edge Browsers zur Vorschau zu nutzen?'},
             'Support Ticket 2': 
            {'Subject': 'Defender ist deaktiviert (0x80070424)', 
             'Body': 'Hallo Leute,ich hab alles versucht, jetzt bin ich am Ende.Ich habe keine Firewall und kein Defender mehr. Jedesmal wenn ich Defender aktivieren will erscheint ( Dieser Dienst ist kein installierter Dienst Fehlercode 0x80070424) In den Programmen ist er nicht drin. Will ich den installieren erscheint die Meldung, schon installiert. Merkwürdig.Bei meiner Firewall ist es nicht anders. Ist angeblich nicht installiert. Jetzt habe ich mir dieses von One Care Firewall repair Tool runter geladen und es läuft seit 2 Stunden. Mir fehlen noch so viel wie der Strich ist --- .Lustig ist. ich habe nichts deaktiviert.Noch was, auf meinem Laptop habe ich nur dieses Defender laufen. Die Kaspersky von 10 ist abgelaufen. Seit dem bin ich ohne schnick schnack im Netzt. Der läuft jetzt noch einwandfrei.'},
            'Support Ticket 3': 
            {'Subject': 'Fehler nach Win Updates', 
             'Body': 'Nach dem Installieren der Win 10 - Updates startet mein PC nicht mehr, der Bildschirm bleibt schwarz, nur der Mauszeiger ist zu sehen! Es hilft nur Wiederherstellung per Systemwiederherstellungspunkt! Was läuft da schief, was kann ich tun?'},
            'Free Text': 
            {'Subject': 'Subject', 
             'Body': 'Body'}},
    'fr': {'Default': 
            {'Subject': DEFAULT_SUBJECT['fr'], 
             'Body': DEFAULT_TEXT['fr']},
             'Support Ticket 1': 
            {'Subject': 'Fonction Bluetooth', 
             'Body': "Bonjour! Depuis la dernière mise à jour du 22/11/2019 de Windows 10, version 1909 (2) mon pc Samsung ne reconnais plus aucun appareil en Bluetooth, téléphone ou haut-parleur ou tablette, alors que mes paramètres Blueetooh sont activé sur le pc & visible ainsi que sur mon tel ect…. Hélas après plusieurs tentatives il m'est totalement impossible de pouvoir solutionner se problème.Qui a une solution? Merci!"},
             'Support Ticket 2': 
            {'Subject': 'Surface Book ne marche plus + craquement venant du chargeur', 
             'Body': "Bonjour,j'ai acheté une Surface Book il y a 20 jours. Aujourd'hui elle a arrêté de fonctionner inopinément alors qu'elle était en train de charger. La tablette ne s'allume plus et ne répond plus, seul le voyant blanc de charge reste allumé.Désormais il y a un bruit étrange qui s'active dès que je branche le cable de chargement à l'endroit du branchement de la tablette. Lorsque j'essaye les procédures d'urgence pour rallumer la tablette (30 seconde sur le bouton power + 15 seconde sur le bouton power et le bouton volume + ), seul le voyant qui indique le détachement de l'écran s'éclaire en rouge pendant 1 seconde puis s'éteint. Lorsque j'appuie sur le voyant de détachement tout en laissant mes doigts appuyés sur les boutons power et +, le bouton clignote 3 fois en vert puis s'éteint. J'ai donc essayé de rester appuyé plus longtemps sur le bouton power et le bouton + et j'ai remarqué que le bouton de détachement d'écran éclairait une lumière rouge toute les 15 secondes pendant 1 seconde. Je me demandais donc si ce craquement venant du chargeur ne venait pas du système de détachement de l'écran ? Ou est ce normal qu'il craque comme cela ? Ou est ce normal que le voyant de détachement clignote toutes les 15 secondes ? Dans tous les cas la tablette ne s'allume pas. Avec tous ces détails j'espère que vous situez d'où vient le problème et m'informer sur ce que je peux faire? Merci,Ines"},
             'Support Ticket 3': 
            {'Subject': 'Antivirus Defender', 
             'Body': 'Bonjour ca va antivirus defender est un tres bon antivirus qui protege bien mon ordinateur et c est gratuit et j aime bien'},
           'Free Text': 
            {'Subject': 'Subject', 
             'Body': 'Body'}},
    'es': {'Default': 
            {'Subject': DEFAULT_SUBJECT['es'], 
             'Body': DEFAULT_TEXT['es']},
            'Support Ticket 1': 
            {'Subject': 'quiero descargar la imagen iso de windows 10 pero la version windows 10 home 10204 pero no se de donde descargarla', 
             'Body': 'Hola. he tenido problemas los últimos días con varias cuentas de mi dominio, no reciben correos desde cuentas del mismo dominio y externas, situación que se presentó desde el 28 de julio. la configuración de filtros, usuarios y dominios seguros esta correcta. las cuentas afectadas pertenecen al dominio davidpenchyna.com y son: *** La dirección de correo electrónico se ha quitado por razones de privacidad ****** La dirección de correo electrónico se ha quitado por razones de privacidad también parece que no reciben correo desde otros dominios. Saludos y gracias'},
             'Support Ticket 2': 
            {'Subject': 'Problema con cuenta Hotmail URGENTE', 
             'Body': 'Despues de actualizar mi información de seguridad, ya no tengo acceso a mi cuenta. Cambie las direcciones de seguridad ya que ya no tenia acceso a ellas, puse una nueva, me enviaron el código el cual ingrese pero ahora me habla de un período de espera hasta el 9/12 (espero que sea mm/dd porque de no ser asi no puedo estar hasta diciembre sin mail) ! yo, como mucha gente usa el mail para trabajar, estudiar etc no puedo estar 30 dias sin usarlo por una actualizacion inutil, innecesaria y contra mi voluntad. realmente no me interesa y no tengo por que recibirla, ya que me perjudica MUCHO más de lo que me sirve.espero una respuesta en COMO Y CUANDO voy a poder usar de nuevo mi cuenta.un saludo y gracias'},
             'Support Ticket 3': 
            {'Subject': 'Ayuda con virus que controla MS-DOS', 
             'Body': 'Hola.Tengo un virus en mi computador y no he podido eliminarlo ni a través de Microsoft Security Essentials, ni a través de Spybot, ni a través de las aplicaciones online de Microsoft que se ejecutan en el Modo Seguro de Windows. No sé cómo se llama el virus, ni en dónde está alojado, pero sé más o menos cómo actúa:De vez en cuando, mientras estoy en el PC, aparece repentinamente una ventana de MS-DOS que se retira sola rápidamente. Al rato vuelve a aparecer y en ella veo cómo comienzan a copiarse mis archivos. Lo único que he atinado a hacer mientras veo cómo se copian mis archivos es a apagar el computador de manera forzada. No sé qué hacer, he intentado repetidamente todo lo que mencioné arriba pero las búsquedas de los antivirus y antimalware no revelan nada. También he ejecutado el CCleaner repetidamente... ¿Alguien sabe de qué virus se trata?¿Qué otra cosa podría intentar? Muchas gracias.'},
            'Free Text': 
            {'Subject': 'Subject', 
             'Body': 'Body'}},
    'it': {'Default': 
            {'Subject': DEFAULT_SUBJECT['it'], 
             'Body': DEFAULT_TEXT['it']},
             'Support Ticket 1': 
            {'Subject': 'Errore Aggiornamento a Windows 10', 
             'Body': 'Buongiorno, ho un HP Compaq 6000 pro microtower, ho provato a fare aggiornamento a windows 10 con il tool, ma esce sempre errore mi sembra associato al processore.come posso fare x aggiornare a win10?grazie in anticipo'},
             'Support Ticket 2': 
            {'Subject': 'Family shared games and live membership', 
             'Body': 'I remember xbox 360 had a family membership. I have my xbox and my two teenagers have an xbox as well. I would gladly pay for a family membership where I can share games, share live, and manage content from one location without having to login to my kids xbox anytime they would like to play a game. Is this a feature that will become available in the future?'},
             'Support Ticket 3': 
            {'Subject': 'Problemi Firma Elettronica in risposta alle Mail', 
             'Body': "Salve a tutti, ho riscontrato un problema nella firma digitale della mia email Outlook.Ho creato la firma con il logo della mia azienda e al momento dell'invio la firma compare perfettamente.Il problema si presenta quando rispondo ad una mail, poiché, al momento dell'invio della risposta, il logo dell'azienda non viene più visualizzato ma appare un riquadro con un punto interrogativo all'interno. Come posso fare a far visualizzare il logo anche in risposta? Grazie mille a tutti."},
            'Free Text': 
            {'Subject': 'Subject', 
             'Body': 'Body'}},
}

########################
# FRONTEND 
########################

HTML_WRAPPER = """<div style="overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; margin-bottom: 2.5rem">{}</div>"""
# Logo loading
try:
    logo = Image.open('~/app/logo.PNG')
    ms = Image.open('~/app/microsoft.PNG')
except FileNotFoundError:
    logo = Image.open('logo.PNG')
    ms = Image.open('microsoft.PNG') 

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
selection = st.selectbox("EXAMPLES", [*EXAMPLES[lang]])
subject = st.text_input("SUBJECT", EXAMPLES[lang][selection]['Subject'])
text = st.text_area("BODY", EXAMPLES[lang][selection]['Body'])
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
    