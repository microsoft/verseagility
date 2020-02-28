# Getting started

## Local development

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
    "FUNCTIONS_WORKER_RUNTIME": "node"
  }
}
```

4) Start the function host
```
func host start
```

## Deploy to Azure

Click on the button below to start the deployment

<a href="https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fmicrosoft%2Fverseagility%2Fmaster%2Fpipeline%2Finfrastructure%2Fazuredeploy.json%3Ftoken%3DAAYUN4GNHPA7T37JHQMXNG26MEUYO" target="_blank">
<img src="https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/1-CONTRIBUTION-GUIDE/images/deploytoazure.png"/>
</a>

