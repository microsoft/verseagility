# Demo Guide
This documentation serves as guideline how to present the Verseagility demo the best way.



The demo/toolkit VERSEAGILITY serves to demonstrate end-to end capabilities for Natural Language Processing use cases. Following features are currently covered in the standard version:
- Text Classification
- Named Entity Recognition
- Question/Answering

Further, the tool supports multiple languages. In the current setup German (_de-de_), English (_en-us_), Spanish (_es-es_), French (_fr-fr_) and Italian (_it-it_) are supported.

The demo is based on the answers.microsoft.com public forum, hence the content covers the Windows, Xbox, Office, IE/Edge, Outlook and Surface categories. For a full overview of available categories and example queries, visit the homepage for your respective language of interest. For English the link is as follows: https://answers.microsoft.com/en-us/.

Supported include:
|| Language | Classification | NER | QA |
|--|--|--|--|--|
|en| English (US) |Windows, Office, Xbox, Outlook, Surface, Edge, Protect | Products, Organizations, People, Locations| Yes|
|de|German | Windows, Office, Xbox, Outlook, Surface, Protect| Products, Organizations, People, Locations|Yes|
|fr|French |Windows, Office, Xbox, Outlook, Surface, Protect|Products, Organizations, People, Locations|Yes|
|es|Spanish |Windows, Office, Xbox, Outlook, Surface, Protect|Products, Organizations, People, Locations|Yes|
|it|Italian |Windows, Office, Xbox, Outlook, Surface, Protect|Products, Organizations, People, Locations|Yes|

### Step-by-Step Guide
1. Open your browser and go to [the web demo](https://verseagility.azurewebsites.net/) (or your custom link which you have created in the [demo setup guide](01%20-%20Demo%20Environment%20Setup.md)).

2. By default, the English model is loaded upon startup and can be changed by the dropdown menu _Select language_ (1) on the left. Afterwards, the other selected model is being loaded and might take a few seconds.

3. The text within the fields is pre-loaded, yet _Subject_ and _Body_ (2) can be changed individually. After clicking on _Submit_ below, the new subject and body are being concatenated and sent to the endpoint for scoring.

4. The classification results will appear afterwards: you can see the predicted main class in (3) with the highest scoring value between 0 and 1, where 0 is the lowest and 1 the highest confidence.

5. The named entities will be displayed below in (4), highlighted with a color. Some entities are pre-trained, and we further added some list-based word collections like _Boss_ for _Bill Gates_, or _Product_ for _Win 7, Windows 7, Windows 10, Internet Explorer_.

6. In (5), the three best matching answer suggestions are going to displayed, sorted by score. The score can vary and has no predefined value range.

## How to Demo
To enable a good demo experience, we recommend you to type some text on the fly during the presentation. The pre-defined examples perform well, yet they are not representative for typical support tickets. We recommend choosing one of the following texts, which are real support tickets as taken from https://answers.microsoft.com.

|         | DE           | EN |
| ------------- |-------------|-----|
| __Subject__  | Aktivieren des bestehenden Systems Windows 8.1 | How to re-order Chromium Edge Quick Links |
| __Body__     | Text: Hallo! Vor einigen jahren habe ich in einem PC- Geschäft meinen PC gekauft. Nach einiger Zeit ist auf dem Monitor unten rechts einen Text erschienen: Windows aktivieren. Im Geschäft wurde das System wieder aktiviert. Das Geschäft ist aber schon zu. Pleite oder so. Keine Ahnung. Wie kann ich nun das System Aktivieren? Ich habe ja meinen PC legal gekauft. Microsoft und Bill Gates ich bitte euch um Hilfe!      | In the pre-Chromium Edge, I had a customize (and, IIRC, pinned) list of quick links in the New Tab page. This the row of 7 icon-decorated boxes. I kept them in a specific order for the purpose of muscle memory. I just got updated to chromium, and while the conversion did maintain my links, it rearranged them in an order that seems to make no sense (not alphabetical, although it may have reverted to most-used). Who moved my cheese? Can I get them back in the order that my muscles remember?  |

### Visual Documentation
![Demo Preview](../.attachments/demo-preview.PNG)
