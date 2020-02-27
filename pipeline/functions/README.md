# Getting started

## Local development

1) Install the node dependencies
npm install

2) Install the Azure Function extensions
func extensions install

3) If you debug locally, create a local.settings.json file in the same directory as api and common and add the following values:
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "<AzureStorageConnectionstring>",
    "CosmosDBConnectionString": "<CosmosDBConnectionstring>",
    "FUNCTIONS_WORKER_RUNTIME": "node"
  }
}

4) Start the function host or press F5 in VSC for debugging
func host start

# Deploy to Azure

<a href="https://github.com/microsoft/verseagility/tree/master/pipeline/infrastructure/azuredeploy.json" target="_blank">
<img src="https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/1-CONTRIBUTION-GUIDE/images/deploytoazure.png"/>
</a>