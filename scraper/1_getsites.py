''' MICROSOFT FORUM PAGE SCRAPER '''
import argparse
import re
import sys
import os
# Run arguments
# example: python 1_getsites.py --language de-de --product xbox
parser = argparse.ArgumentParser()
parser.add_argument("--language", 
                default="de-de",
                type=str,
                help="'en-us' or 'de-de")
parser.add_argument('--product',
                default='list',
                type=str,
                help="'windows', 'msoffice', 'xbox', 'outlook_com', 'skype', 'surface', 'protect', 'edge', 'ie', 'musicandvideo'")  
args = parser.parse_args()

# Import and set driver
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
driver = webdriver.Chrome(ChromeDriverManager().install())

# Set product 
productsel = args.product
language = args.language

# Select products to be scraped
if productsel == "list": # default option, entire product list
    products = ['windows', 'msoffice', 'xbox', 'outlook_com', 'skype', 'surface', 'protect', 'edge', 'musicandvideo', 'msteams', 'microsoftedge'] # 
    # Check at which position we are
    if os.path.exists('scrape.log'):
        with open('scrape.log', 'r') as log:
            products = products[products.index(log.read().split('/')[0]):]
else: # in case a specific product should be scraped
    products = [productsel]

# Loop through product list and pages
for product in products:
    print(f'[START] {language}, {product}.')
    # Logfile handling
    if os.path.exists('scrape.log'):
        with open('scrape.log', 'r') as log:
            line = log.read()
            i = int(line.split('/')[1])
            j = line.split('/')[0]
            log.close()
        if j != product:
            i = 1
    else:
        i = 1
    # Go to next product, in case value has been set to 0
    if i == 0:
        continue
    # Scrape sites
    for x in range(i, 10000):
        if i == 0: break
        driver.get(f'https://answers.microsoft.com/{language}/{product}/forum?sort=LastReplyDate&dir=Desc&tab=All&status=all&mod=&modAge=&advFil=&postedAfter=&postedBefore=&threadType=All&isFilterExpanded=false&page=' + str(x))
        # Try it three times until breaking the scrape
        for tries in range(0, 3):
            try:
                html = driver.page_source
                if ('Es wurden keine Ergebnisse gefunden' in html) or ('No results found' in html) or ('Aucun résultat trouvé' in html) or ('Nessun risultato trovato' in html) or ('No se han encontrado resultados' in html) or ('Pubblica domande, segui le discussioni, condividi le tue conoscenze' in html) or ('Posten Sie Fragen, folgen Sie Diskussionen und teilen Sie Ihr Wissen' in html) or ('Post questions, follow discussions, share your knowledge' in html) or ('Publiez des questions, suivez des discussions et partagez vos connaissances' in html) or ('Publique preguntas, siga conversaciones y comparta sus conocimientos' in html):
                    print(f'[EXIT] EMPTY PAGE REACHED -> - {language}, {product}.')
                    with open(f'scrape.log', 'w') as logfile:
                        logfile.write(f'{product}/0')
                        logfile.close()
                    i = 0
                    break
                element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'thread-title')))
                html = driver.page_source
                url_temp = re.findall(r'(https?://answers.microsoft.com/' + language + '/' + product + '/forum/[^\s]+)', html)
                url_temp2 = [s.strip('"') for s in url_temp]
                url_list = [x for x in url_temp2 if not x.endswith('LastReply')]
                with open(f'output-{product}-{language}.txt', 'a', encoding='utf-8') as outfile:
                    # Prepare Links
                    outfile.write("\n".join(url_list) + "\n")
                    outfile.close()
                if len(url_list) > 0:
                    print(f'[STATUS] - {product.capitalize()} page {str(x)} -> {len(url_list)} urls extracted.')
                    with open(f'scrape.log', 'w') as logfile:
                        logfile.write(f'{product}/{x+1}')
                        logfile.close()
                    break
                elif len(url_list) == 0:
                    print(f'[WARNING] - page {str(x)} has an empty url list.')
                    break
            except Exception as e:
                print(f'[EXCEPT] - try {tries}/3 -> page {str(x)} took too long -> retrying...')
                continue