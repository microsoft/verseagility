import requests
import os
subscription_key = "7a49fa7e44b54605856765ac4497798d"
endpoint = "https://verstextanalyticseotlasv25p4ae.cognitiveservices.azure.com/text/analytics/v3.0/entities/recognition/general"
documents = {
  "documents": [
    {
        "id": "1",
        "language": "en",
        "text": "Our tour guide took us up the Space Needle during our trip to Seattle last week."
    }
  ]
}
headers = {"Ocp-Apim-Subscription-Key": subscription_key}
response = requests.post(endpoint, headers=headers, json=documents)
key_phrases = response.json()
print(key_phrases)