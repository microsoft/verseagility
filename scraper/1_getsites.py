import argparse
import re
# Run arguments
# example: python 1_getsites.py --language de-de --product xbox
parser = argparse.ArgumentParser()
parser.add_argument("--language", 
                default="de-de",
                type=str,
                help="'en-us' or 'de-de")
parser.add_argument('--product',
                default='windows',
                type=str,
                help="'windows', 'msoffice', 'xbox', 'outlook_com', 'skype', 'surface', 'protect', 'edge', 'ie', 'musicandvideo'")  
args = parser.parse_args()

# Import and set driver
from selenium import webdriver
path = 'C:/Users/tiwalz/Documents/Projects/NLP/Scraping/'
driver = webdriver.Chrome(executable_path = path + 'chromedriver.exe')

# Set product
product = args.product
language = args.language

# Products
products = ['windows', 'msoffice', 'xbox', 'outlook_com', 'skype', 'surface', 'protect', 'edge', 'ie', 'musicandvideo']
for product in products:
    print(f'[START] {language}, {product}.')
    # Scrape sites
    for x in range(1, 10000):
        driver.get(f'https://answers.microsoft.com/{language}/' + product + '/forum?sort=LastReplyDate&dir=Desc&tab=All&status=all&mod=&modAge=&advFil=&postedAfter=&postedBefore=&threadType=All&isFilterExpanded=false&page=' + str(x))
        html = driver.page_source
        if ('Es wurden keine Ergebnisse gefunden' in html) or ('No results found' in html) or ('Aucun résultat trouvé' in html) or ('Nessun risultato trovato' in html) or ('No se han encontrado resultados' in html) or ('Pubblica domande, segui le discussioni, condividi le tue conoscenze' in html) or ('Posten Sie Fragen, folgen Sie Diskussionen und teilen Sie Ihr Wissen' in html) or ('Post questions, follow discussions, share your knowledge' in html) or ('Publiez des questions, suivez des discussions et partagez vos connaissances' in html) or ('Publique preguntas, siga conversaciones y comparta sus conocimientos' in html):
            print(f'[EXIT] EMPTY PAGE REACHED -> - {language}, {product}.')
            break
        else:
            url_temp = re.findall(r'(https?://answers.microsoft.com/' + language + '/' + product + '/forum/[^\s]+)', html)
            url_temp2 = [s.strip('"') for s in url_temp]
            url_list = [x for x in url_temp2 if not x.endswith('LastReply')]
            with open('output-' + product + '-' + language + '.txt', 'a', encoding='utf-8') as outfile:
                # Prepare Links
                outfile.write("\n".join(url_list) + "\n")
                if (x%50):
                    print(f'[STATUS] Page no. {str(x)} written.')