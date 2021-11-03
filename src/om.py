
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

# Custom functions
import sys
sys.path.append('./src')
import custom as cu
import data as dt
import helper as he

class OpinionMiningMatcher(object): 
    def __init__(self):
        key = he.get_secret('text-analytics-key')
        self.endpoint = f"https://{he.get_secret('text-analytics-name')}.cognitiveservices.azure.com/"
        self.key = AzureKeyCredential(key)
        self.client = TextAnalyticsClient(endpoint = self.endpoint, credential = self.key, default_language=cu.params.get('language'))
        
    def __call__(self, doc):
        result = self.client.analyze_sentiment(doc, show_opinion_mining=True)
        doc_result = [doc for doc in result if not doc.is_error]
        
        # Loop through every result
        for document in doc_result:
            results = list()
            # Loop through every document in the results
            for document in doc_result:
                sentences = list()

                # Loop through every document
                for sentence in document.sentences:
                    opinion = list()

                    # Loop through every mined opinion                    
                    for mined_opinion in sentence.mined_opinions:
                        assesment = list()

                        # Loop through every assessment    
                        for assessment in mined_opinion.assessments:
                            # Append assessment
                            assesment.append((dict(text_assessment = assessment.text, 
                                sentiment_assessment = assessment.sentiment,
                                confidence_scores_assessment = dict(positive_assessment = assessment.confidence_scores.positive,
                                neutral_assessment = assessment.confidence_scores.neutral,
                                negative_assessment = assessment.confidence_scores.negative), length_assessment = assessment.length, 
                                offset_assessment = assessment.offset)))
                        
                        # Append opinion
                        opinion.append(dict(text_mined_opinion = mined_opinion.target.text, 
                            sentiment_mined_opinion = mined_opinion.target.sentiment,
                            confidence_scores_mined_opinion = dict(positive_mined_opinion = mined_opinion.target.confidence_scores.positive,
                            neutral_mined_opinion = mined_opinion.target.confidence_scores.neutral,
                            negative_mined_opinion = mined_opinion.target.confidence_scores.negative), length_mined_opinion = mined_opinion.target.length, 
                            offset_mined_opinion = mined_opinion.target.offset, assessment_mined_opinion = assesment))    
                    
                    # Append sentencews
                    sentences.append(dict(text_sentence=sentence.text, sentiment_sentence=sentence.sentiment,
                        confidence_scores_sentence=dict(positive_sentence=sentence.confidence_scores.positive,
                        neutral_sentence=sentence.confidence_scores.neutral,negative_sentence=sentence.confidence_scores.negative), 
                        length_sentence=sentence.length, offset_sentence=sentence.offset, opinions_sentence=opinion))
                
                # Pack the results
                results.append(dict(id_doc = document.id, sentiment_doc = document.sentiment, statistics_doc = document.statistics,
                    doc_confidence_scores = dict(postive = document.confidence_scores.positive, neutral = document.confidence_scores.neutral, 
                    negative = document.confidence_scores.negative), sentences_doc = sentences))
        
        return results

class OM():
    def __init__(self, task, inference=False):
        # Opinion Mining
        self.om_matcher = OpinionMiningMatcher()

    def run(self, text):
        # Text to document object
        om_results = self.om_matcher([text])
        return om_results
    
    def inference_from_dicts(self, dicts):
        """Used for inference
        NOTE: expects one input, one output given
        """
        return self.run(dicts[0]['text'])

if __name__ == '__main__':
    res = OM(task=5, inference=True).run('Microsoft Surface Laptop with Windows 7 by Bill Gates. I loved win 7. My surface laptop is great, however I lost my typecover.')
    logging.info(res)