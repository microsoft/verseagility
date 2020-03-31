# NLP toolkit pipeline

## Local development

0) Make sure you fulfill all the requirements as stated [here](https://docs.microsoft.com/en-us/azure/azure-functions/functions-create-first-function-vs-code?pivots=programming-language-csharp).

1) Install the node dependencies
```
npm install
```

2) Install the Azure Function extensions
```
func extensions install
```

3) If you debug locally, create a file `local.settings.json` in the same directory as folders `api` and `blob-trigger` and add the following values:
```
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "<AzureStorageConnectionstring>",
    "CosmosDBConnectionString": "<CosmosDBConnectionstring>",
    "FUNCTIONS_WORKER_RUNTIME": "node",
    "CognitiveServiceKey": "<OCRServiceKey>",
    "CognitiveServiceName": "<OCRServiceName>"
  }
}
```

4) Start the function host
```
func host start
```

## Deploy to Azure

1. Click on the button to start the resource deployment:
<a href="https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fchristian-vorhemus%2Ffunction-app%2Fmaster%2Fazuredeploy.json" target="_blank">
<img src="https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/1-CONTRIBUTION-GUIDE/images/deploytoazure.png"/>
</a>

2. After the deployment has finished (~30min) as a workaround for now, add the function "default" host key as an environment variable
named "FunctionHostKey" in the function (if the variable is already there, replace the value) and click "Save"

<img src="https://github.com/microsoft/verseagility/blob/master/demo/functionkey.png" width="400">

## Usage

The purpose of the pipeline is twofold: 1) It automatically processes supported documents that are put into the "data" container of the created Azure Storage. 2) It creates a REST endpoint that can be used to convert documents (like images, PDFs) into text.

1. If you put files in the storage account "data" container, the files are processed and put in CosmosDB following the standardized output format.

<img src="https://github.com/microsoft/verseagility/blob/master/demo/data_container.png" width="400">

What happens in the background is that the "processor-function" gets triggered. This function takes the newly added blob and parses it based on the content/MIME-type of the blob. To tell the function how a certain document has to be handled, you must write your own parser, parsers are stored in the /parsers directory. By default, three parsers are already implemented (CSV, JSON and default). If you take a look at e.g. csv-parser, you see that the job of the parser is to map content of the CSV file to an object called "OutputSchema". OutputSchema is the document schema that will be used to store the document in CosmosDB (of course you can also adopt the schema to fit your needs). For example, if your CSV file contains a list of documents and the ID in the first column (index 0), the number of views for this document in the second column and the URI to the document in the third column, the parser iterates over all rows and maps all columns to the right OutputSchema properties:

<img src="https://github.com/microsoft/verseagility/blob/master/demo/mapping.png" width="500">

Note: If you want to link attachments to the documents in the CSV file, create a container in the storage account named after the document ID. The pre-implemented parser will search in the storage for any container that has the same ID as the document. If it finds one, it links all blobs in the container as attachments to the document.

2. If no matching parser is implemented, the default-parser will be used. It forwards the document to another function called "documentconverter-function". The document converter can also be called manually by performing the following HTTP request:
`POST https://myfunctionapp.azurewebsites.net/documentconverter?code=[function-key]`
The content of the HTTP request is of type application/json and is a single object containg the properties "name" (the name of the document), "content" (the binary file encoded as base64 string) and "conentType" (MIME-Type). It may look like this:
```javascript
{
  "name": "sample.pdf",
  "content: "JVBERi0xLjUKJY8KOCAwIG9iag[...]",
  "contentType": "application/pdf"
}
```

The job of the documentconverter-function is to return an XML document containing the textual representation of the binary file. If the passed file is a PDF, the text of the PDF is returned (embedded in an XML structure). If the file is an image, OCR will be performed and the result is returned.

3. If you want to store documents for scoring, the "api-function" can be used. It accepts "application/json" HTTP requests and stores the documents described in the HTTP body in CosmosDB following the "OutputSchema". It also parses linked attachments that are stored in the storage account that was created during deployment. You can call the API by using
`POST https://myfunctionapp.azurewebsites.net/api/score?code=[function-key]`

The HTTP request body may look like this
```javascript
{
  "subject": "Document subject",
  "body": "Document content and text",
  "attachments": [
    {
      "link": "https://mystorageaccount.blob.core.windows.net/attachments/sample.pdf"
    }	
  ]
}
```

The function will parse sample.pdf and add the content of the PDF as well as the other properties (subject and body in this case) to the CosmosDB collection. 

