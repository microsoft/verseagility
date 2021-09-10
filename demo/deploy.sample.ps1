"""
Deploy Streamlit Demo to Azure App Service

To start:
> cd to root (/demo in repo)
> az login # if needed
> az account set -s [subscription name] # if needed
> .\deploy.ps1
> ..update app settings in portal
Note that this is not meant for automate deployment (yet).

SOURCE: https://towardsdatascience.com/deploying-a-streamlit-web-app-with-azure-app-service-1f09a2159743
"""

# Params
$location = 'insert your region'
$rg = 'insert your resource group'
$acr = 'insert your acr name'
$image =  'nlp-demo'
$sp = 'insert your service plan name'
$app = 'insert your app name'
$url = $acr + '.azurecr.io/' + $image + ':latest'
$create = $TRUE # create or update app

if ($create) {
    # Create Demo App
    az group create -l $location -n $rg
    az acr create --name $acr --resource-group $rg --sku basic --admin-enabled true
    az acr build --registry $acr --resource-group $rg --image $image .
    az appservice plan create -g $rg -n $sp -l $location --is-linux --sku B1
    az webapp create -g $rg -p $sp -n $app -i $url
} Else {
    # Update
    ## Create new image
    az acr build --registry $acr --resource-group $rg --image $image .
    ## Update Web
    az webapp restart -g $rg -n $app
}

