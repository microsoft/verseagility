import argparse
# Run arguments
parser = argparse.ArgumentParser()
parser.add_argument("--lang", 
                default="de-de",
                type=str,
                help="'en-us' or 'de-de")
parser.add_argument('--product',
                default='windows',
                type=str,
                help="'windows', 'msoffice', 'xbox', 'outlook_com', 'skype', 'surface', 'protect','edge','ie','musicandvideo'")  
args = parser.parse_args()

# Import and set driver
from selenium import webdriver
path = 'C:/Users/tiwalz/Documents/Projects/NLP/Scraping/'
driver = webdriver.Chrome(executable_path = path + 'chromedriver.exe')

# Set product
product = args.product
language = args.language

# Scrape sites
for x in range(1, 8000):
    driver.get(f'https://answers.microsoft.com/{language}/' + product + '/forum?sort=LastReplyDate&dir=Desc&tab=All&status=all&mod=&modAge=&advFil=&postedAfter=&postedBefore=&threadType=All&isFilterExpanded=false&page=' + str(x))
    html = driver.page_source
    if ('Es wurden keine Ergebnisse gefunden' in html) or ('No results found' in html):
        print('##### EMPTY PAGE REACHED -> EXIT')
        break
    else:
        with open('output-' + product + '.txt', 'a', encoding='utf-8') as myfile:
            myfile.write(html+'\n\n\n')
            print('Written:' + str(x))