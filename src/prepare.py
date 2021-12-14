"""
PREPARE

Before running train, you need to run prepare.py with the respective task.

Example (in the command line):
> cd to root dir
> conda activate nlp
> python src/prepare.py --do_format --task 1
"""
#NOTE: the following is a workaround for AML to load modules
import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import pandas as pd
import numpy as np
import string
import re
import argparse
from sklearn.model_selection import StratifiedShuffleSplit

# Custom functions
import sys
sys.path.append('./src')
import helper as he
import data as dt
import custom as cu

logger = he.get_logger(location = __name__)
class Clean():
    """Text preprocessing and cleaning steps

    SUPPORTED LANGUAGES
    - EN
    - DE
    - IT
    - ES
    - FR
    - XX (multi - NER only)

    SUPPORTED MODULES
    - Remove Noise
    Remove formatting and other noise that may be contained in emails or
    other document types.
    - Get Placeholders
    Placeholders for common items such as dates, times, urls but also
    custom customer IDs.
    - Remove Stopwords
    Stopwords can be added by adding a language specific stopword file
    to /assets. Format: "assets/stopwords_<language>.txt".
    - Lemmatize
    """

    def __init__(self, task,
                        download_source = False,
                        download_train  = False,
                        inference       = False):
        self.task = task
        self.language = cu.params.get('language')
        
        # Load data class
        self.dt = dt.Data(task=self.task, inference=inference)

        # Download data, if needed
        if download_train:
            self.dt.download('data_dir', dir = 'data_dir', source = 'datastore')

        # Load spacy model
        self.nlp = he.load_spacy_model(language=self.language, disable = ['ner','parser','tagger'])
        
        # Create stopword list
        stopwords_active = []
        ## Load names
        try:
            names = self.dt.load('fn_names', dir = 'asset_dir', file_type = 'list')
            stopwords_active = stopwords_active + names
        except FileNotFoundError as e:
            logger.warning(f'[WARNING] No names list loaded: {e}')
        
        ## Load stopwords
        try:
            stopwords = self.dt.load('fn_stopwords', dir = 'asset_dir', file_type = 'list')
            stopwords_active = stopwords_active + stopwords
        except FileNotFoundError as e:
            logger.warning(f'[WARNING] No stopwords list loaded: {e}')

        ## Add to Spacy stopword list
        logger.warning(f'[INFO] Active stopwords list lenght: {len(stopwords_active)}')
        for w in stopwords_active:
            self.nlp.vocab[w.replace('\n','')].is_stop = True
   
    def remove(self, line, 
                rm_email_formatting = False, 
                rm_email_header     = False, 
                rm_email_footer     = False,
                rm_punctuation      = False):
        """Remove content from text"""
    
        if not isinstance(line, str):
            line = str(line)
        
        # Customer Remove
        line = cu.remove(line)

        if rm_email_formatting:
            line = re.sub(r'<[^>]+>', ' ', line) # Remove HTML tags
            line = re.sub(r'^(.*\.eml)', ' ', line) # remove header for system generated emails

        if rm_email_header:
            # DE/EN
            if self.language == 'en' or self.language == 'de':
                line = re.sub(r'\b(AW|RE|VON|WG|FWD|FW)(\:| )', '', line, flags=re.I)
            # DE
            if self.language == 'de':
                line = re.sub(r'(Sehr geehrte( Damen und Herren.)?.)|hallo.|guten( tag)?.', '', line, flags=re.I)

        if rm_email_footer:
            # EN
            if self.language == 'en':
                line = re.sub(r'\bkind regards.*', '', line, flags=re.I)
                line = re.sub(r'\bbest regards.*', '', line, flags=re.I)
                line = re.sub(r'\bsincerely yours.*', '', line, flags=re.I)
                line = re.sub(r'\byours sincerely.*', '', line, flags=re.I)
                line = re.sub(r'\bsent from my mobile.*', '', line, flags=re.I)
                line = re.sub(r'\bsent via iphone.*', '', line, flags=re.I)
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

        # Remove remaining characters
        ## NOTE: may break other regex
        if rm_punctuation:
            line = re.sub('['+string.punctuation+']',' ',line)
        
        return line

    def get_placeholder(self, line,
                        rp_generic  = False,
                        rp_custom   = False,
                        rp_num      = False):
        """Replace text with type specfic placeholders"""


        # Customer placeholders
        line = cu.get_placeholder(line)

        # Generic placeholder
        if rp_generic:
            line = re.sub(r' \+[0-9]+', ' ', line) # remove phone numbers
            line = re.sub(r'0x([a-z]|[0-9])+ ',' PER ',line, re.IGNORECASE) # replace 
            line = re.sub(r'[0-9]{2}[\/.,:][0-9]{2}[\/.,:][0-9]{2,4}', ' PDT ', line) # remove dates and time, replace with placeholder
            line = re.sub(r'([0-9]{2,3}[\.]){3}[0-9]{1,3}',' PIP ',line) # replace ip with placeholder
            line = re.sub(r'[0-9]{1,2}[\/.,:][0-9]{1,2}', ' PTI ', line) # remove only time, replace with placeholder
            line = re.sub(r'[\w\.-]+@[\w\.-]+', ' PEM ', line) # remove emails
            line = re.sub(r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&amp;+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+', ' PUR ', line) # Remove links
            line = re.sub(r'€|\$|(USD)|(EURO)', ' PMO ', line)
        
        # Placeholders for numerics
        if rp_num:
            line = re.sub(r' ([0-9]{4,30}) ',' PNL ', line) # placeholder for long stand alone numbers
            line = re.sub(r' [0-9]{2,3} ',' PNS ', line) # placeholder for short stand alone numbers

        return line

    def tokenize(self, line, lemmatize = False, rm_stopwords = False):
        """Tokenizer for non DL tasks"""
        if not isinstance(line, str):
            line = str(line)
        
        
        if lemmatize and rm_stopwords:
            line = ' '.join([t.lemma_ for t in self.nlp(line) if not t.is_stop])
        elif lemmatize:
            line = ' '.join([t.lemma_ for t in self.nlp(line)])
        elif rm_stopwords:
            line = ' '.join([t.text for t in self.nlp(line) if not t.is_stop])

        return line
    
    def transform(self, texts, 
                    to_lower            = False,
                    # Remove
                    rm_email_formatting = False, 
                    rm_email_header     = False,
                    rm_email_footer     = False, 
                    rm_punctuation      = False,
                    # Placeholders
                    rp_generic          = False, 
                    rp_num              = False,
                    # Tokenize
                    lemmatize           = False,
                    rm_stopwords        = False,
                    return_token        = False,
                    # Whitespace
                    remove_whitespace   = True
                ):
        """Main run function for cleaning process"""

        if isinstance(texts, str):
            texts = [texts]

        # Convert to series for improved performance processing the data
        df_texts = pd.Series(texts)

        # Avoid loading errors
        df_texts = df_texts.replace('\t', ' ', regex = True)
        
        # Remove noise
        if any((rm_email_formatting, rm_email_header, 
                    rm_email_footer, rm_punctuation)):
            df_texts = df_texts.apply(lambda x: self.remove(x,
                                            rm_email_formatting =   rm_email_formatting, 
                                            rm_email_header     =   rm_email_header, 
                                            rm_email_footer     =   rm_email_footer,
                                            rm_punctuation      =   rm_punctuation))

        # Replace placeholders
        if any((rp_generic, rp_num)):
            df_texts = df_texts.apply(lambda x: self.get_placeholder(x,
                                                        rp_generic  =   rp_generic,
                                                        rp_num      =   rp_num))

        # Tokenize text
        if any((lemmatize, rm_stopwords, return_token)):
            df_texts = df_texts.apply(self.tokenize,
                                    lemmatize    = lemmatize,
                                    rm_stopwords = rm_stopwords)
        # To lower
        if to_lower:
            df_texts = df_texts.apply(str.lower)

        # Remove spacing
        if remove_whitespace:
            df_texts = df_texts.apply(lambda x: " ".join(x.split()))
        
        # Return Tokens
        if return_token:
            return [t.split(' ') for t in df_texts.to_list()]
        else:
            return df_texts.to_list()

    def transform_by_task(self, text):
        '''Custom cleaning/transforming based on task, as every task requires different formats'''
        # Classification
        if cu.tasks.get(str(self.task)).get('type') == 'classification':
            return self.transform(text,
                    rm_email_formatting = True, 
                    rm_email_header     = True,
                    rm_email_footer     = True,
                    rp_generic          = True)[0]
        # Multi-Label Classification
        elif cu.tasks.get(str(self.task)).get('type') == 'multi_classification':
            return self.transform(text,
                    rm_email_formatting = True, 
                    rm_email_header     = True,
                    rm_email_footer     = True,
                    rp_generic          = True)[0]
        # NER
        elif cu.tasks.get(str(self.task)).get('type') == 'ner':
            return text[0]
        # QA
        elif cu.tasks.get(str(self.task)).get('type') == 'qa':
            return self.transform(text,
                    to_lower            = True,
                    # Remove
                    rm_email_formatting = True, 
                    rm_email_header     = True,
                    rm_email_footer     = True, 
                    rm_punctuation      = True,
                    # Placeholders
                    rp_generic          = True, 
                    rp_num              = True,
                    # Tokenize
                    lemmatize           = True,
                    rm_stopwords        = True,
                    return_token        = True
                )[0]
        # OM
        elif cu.tasks.get(str(self.task)).get('type') == 'om':
            return text[0]
        # Anything else
        else:
            logger.warning('[WARNING] No transform by task found.')
            return text[0]

def prepare_classification(task, do_format, train_split, min_cat_occurance, 
                            min_char_length, register_data, data_source, dataset_name=None):
    '''Prepare data specifically for classification task'''
    # Get clean object
    cl = Clean(task = task, download_source = True)
    # Load data
    if not os.path.isfile(cl.dt.get_path('fn_prep', dir = 'data_dir')) or do_format:
        data = dt.get_dataset(cl, data_source, dataset_name=dataset_name)
    else:
        data = cl.dt.load('fn_prep', dir = 'data_dir')
    logger.warning(f'Data Length : {len(data)}')

    # TODO : Temporary workaround, need to make it possible to handle missing column "subject"
    # Lowercase all cols and change name
    data.columns    = [x.lower() for x in data.columns]
    data['subject'] = "x "
    data.columns    = ['body', 'label', 'subject']

    # Load text & label field
    text_raw      = cu.load_text(data)
    data['label'] = cu.load_label(data, task)
    # If we do multi label classification, there are quite some steps to be done to bring it into the right format
    if cu.tasks.get(str(task)).get('type') == 'multi_classification':
        # Replacing ", " in case we have comma-separations within the labels
        data['label']  = data['label'].str.replace(', ', '_').str.replace(' ', '_')
        # Flatten to list of lists with labels
        flat_labels    = [row['label'].split(',') for index, row in data.iterrows()] 
        # Create duplicate-free list of labels
        label_list_raw = list(set([label for labels in flat_labels for label in labels]))
    # If it is only single label classification, it is much easier
    elif cu.tasks.get(str(task)).get('type') == 'classification': 
        label_list_raw = data.label.drop_duplicates()
    
    # Clean text
    data['text'] = cl.transform(text_raw,
                    rm_email_formatting = True, 
                    rm_email_header     = True,
                    rm_email_footer     = True,
                    rp_generic          = True)
    
    # Filter by length
    data = he.remove_short(data, 'text', min_char_length = min_char_length)
    logger.warning(f'Data Length : {len(data)}')

    # Remove duplicates
    data_red = data.drop_duplicates(subset = ['text'])
    logger.warning(f'Data Length : {len(data_red)}')
    
    # Remove classes not having enough examples (minimum class occurence)
    if cu.tasks.get(str(task)).get('type') == 'classification':
        data_red = data_red[data_red.groupby('label').label.transform('size') > min_cat_occurance]
    elif cu.tasks.get(str(task)).get('type') == 'multi_classification':
        # This one is quite complicated, as we cannot simply filter by occurences
        # First, we create a copy of the df
        data_transform = data_red[['id', 'label']].copy()
        # Secondly, we need to split every combination of labels and transform it to a list
        data_transform['label'] = [row['label'].split(",") for index, row in data_transform.iterrows()]
        # Next, we need to explode the whole df to temporarily have every document assigned to each sub-label separately
        data_transform = pd.DataFrame({'index': data_transform.index.repeat(data_transform.label.str.len()), 'label': np.concatenate(data_transform.label.values)})
        # Now, we filter by minimum occurence for each label
        data_transform = data_transform[data_transform.groupby('label').label.transform('size') > min_cat_occurance] # count for min occurance and only keep relevant ones
        # As the worst part is done, we re-merge the labels again and only the ones occuring often enough stay here
        data_transform = data_transform.groupby(['index'])['label'].apply(lambda x: ','.join(x.astype(str))).reset_index() # re-merge
        # Wrapping up, we set a new index
        data_transform = data_transform.set_index('index')
        del data_red['label']
        # Last but not least, we concatenate the reduced and transformed data by doing an inner join
        data_red = pd.concat([data_red, data_transform], join = 'inner', axis=1)
    logger.warning(f'Data Length : {len(data_red)}')

    # Same procedure as above, now with reduced set of data
    # If we do multi label classification, there are quite some steps to be done to bring it into the right format
    if cu.tasks.get(str(task)).get('type') == 'multi_classification':
        # Flatten to list of lists with labels
        flat_labels = [row['label'].split(',') for index, row in data_red.iterrows()]
        # Create duplicate-free list of labels
        label_list  = list(set([label for labels in flat_labels for label in labels]))
    # If it is only single label classification, it is much easier
    elif cu.tasks.get(str(task)).get('type') == 'classification': 
        label_list  = data_red.label.drop_duplicates()
    logger.warning(f'Excluded labels: {list(set(label_list_raw) - set(label_list))}')

    # Split data
    strf_split = StratifiedShuffleSplit(n_splits = 1, test_size=(1-train_split), random_state=200)
    if cu.tasks.get(str(task)).get('type') == 'classification':
        for train_index, test_index in strf_split.split(data_red, data_red['label']):
            df_cat_train    = data_red.iloc[train_index]
            df_cat_test     = data_red.iloc[test_index]
    elif cu.tasks.get(str(task)).get('type') == 'multi_classification':
        for train_index, test_index in strf_split.split(data_red, pd.DataFrame({'label':[l.split(',')[0] for l in data_red['label']]})['label']):
            df_cat_train    = data_red.iloc[train_index]
            df_cat_test     = data_red.iloc[test_index]
    
    # Save data
    cl.dt.save(data_red, fn = 'fn_clean', dir = 'data_dir')
    cl.dt.save(df_cat_train[['text','label']], fn = 'fn_train', dir = 'data_dir')
    cl.dt.save(df_cat_test[['text','label']], fn = 'fn_test', dir = 'data_dir')
    cl.dt.save(label_list, fn = 'fn_label', header = False, dir = 'data_dir')

    # Upload data
    if register_data:
        cl.dt.upload('data_dir', destination = 'dataset')

def prepare_ner(task, do_format, register_data, data_source, dataset_name=None):
    '''Placeholder for NER-specific preparation, if needed'''
    pass

def prepare_qa(task, do_format, min_char_length, register_data, data_source, dataset_name=None):
    '''Data preparation function for question-answering'''
    # Get clean object
    cl = Clean(task=task, download_source=True)
    
    # Load data
    if not os.path.isfile(cl.dt.get_path('fn_prep', dir = 'data_dir')) or do_format:
        data = dt.get_dataset(cl, source='cdb')
    else:
        data = cl.dt.load('fn_prep', dir = 'data_dir')
    logger.warning(f'Data Length : {len(data)}')

    # Filter relevant question answer pairs
    data = cu.filter_qa(data)
    logger.warning(f'Data Length : {len(data)}')

    # Load question & answer fields
    question, answer = cu.load_qa(data)
    
    # Clean text
    data['question_clean'] = cl.transform(question,
                    to_lower            = True,
                    rm_email_formatting = True, 
                    rm_email_header     = True,
                    rm_email_footer     = True, 
                    rm_punctuation      = True,
                    rp_generic          = True, 
                    rp_num              = True,
                    lemmatize           = True,
                    rm_stopwords        = True
                    )
    data['answer_clean'] = cl.transform(answer,
                    to_lower            = True,
                    rm_email_formatting = True, 
                    rm_email_header     = True,
                    rm_email_footer     = True, 
                    rm_punctuation      = True,
                    rp_generic          = True, 
                    rp_num              = True,
                    lemmatize           = True,
                    rm_stopwords        = True
                    )
    # For display
    data['answer_text_clean'] = cl.transform(answer,
                rm_email_formatting = True, 
                rm_email_header     = True,
                rm_email_footer     = True
            )

    # Filter by length
    data = he.remove_short(data, 'question_clean', min_char_length = min_char_length)
    logger.warning(f'Data Length : {len(data)}')

    # Remove duplicates
    data = data.drop_duplicates(subset = ['question_clean'])
    logger.warning(f'Data Length : {len(data)}')
    data = data.reset_index(drop=True).copy()

    # Save data
    cl.dt.save(data, fn = 'fn_clean', dir = 'data_dir')
    # Upload data
    if register_data:
        cl.dt.upload('data_dir', destination = 'dataset')

def prepare_om(task, do_format, register_data, data_source, dataset_name = None):
    '''Placeholder for OM-specific preparation, if needed'''
    pass

def main(task             = 1, 
        do_format         = False, 
        split             = 0.9, 
        min_cat_occurance = 300, 
        min_char_length   = 20,
        register_data     = False,
        dataset_name      = None,
        data_source       = "cosmosdb"):
    logger.warning(f'Running <PREPARE> for task {task}')
    task_type = cu.tasks.get(str(task)).get('type')
    # Go a specific preparation way, depending on the task performed
    if 'classification' == task_type:
        prepare_classification(task, do_format, split, min_cat_occurance, min_char_length, register_data, data_source, dataset_name)
    elif 'multi_classification' == task_type:
        prepare_classification(task, do_format, split, min_cat_occurance, min_char_length, register_data, data_source, dataset_name)
    elif 'ner' == task_type:
        prepare_ner(task, do_format, register_data, data_source, dataset_name)
    elif 'qa' == task_type:
        prepare_qa(task, do_format, min_char_length, register_data, data_source, dataset_name)
    elif 'om' == task_type:
        prepare_om(task, do_format, register_data, data_source, dataset_name)
    else:
        logger.warning('[ERROR] TASK TYPE UNKNOWN. Nothing was processed.')

def run():
    """Run from the command line"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", 
                    default = 1,
                    type    = int,
                    help    = "Task where: \
                            -task 1 : classification cat \
                            -task 2 : classification subcat \
                            -task 3 : ner \
                            -task 4 : qa \
                            -task 5 : om") 
    parser.add_argument("--do_format",
                    action  = "store_true",
                    help    = "Avoid reloading and normalizing data")
    parser.add_argument("--split", 
                    default = 0.9,
                    type    = float,
                    help="Train test split. Dev split is taken from train set.")    
    parser.add_argument("--min_cat_occurance", 
                    default = 300,
                    type    = int,
                    help    = "Min occurance required by category.")      
    parser.add_argument("--min_char_length", 
                    default = 20,
                    type    = int,
                    help    = "") 
    parser.add_argument("--register_data",
                    action  = "store_true",
                    help    = "")
    parser.add_argument("--dataset_name", # TODO pipe through scripts
                    type    = str,
                    default = "sample")
    parser.add_argument("--data_source", # TODO pipe through scripts
                    type    = str,
                    default = "cosmosdb")
    args = parser.parse_args()
    main(args.task, args.do_format, args.split, min_cat_occurance = args.min_cat_occurance, 
            min_char_length = args.min_char_length, register_data = args.register_data, dataset_name = args.dataset_name)
        
if __name__ == '__main__':
    run()