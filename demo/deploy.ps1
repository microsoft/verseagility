"""
Deploy demo to web app.

To start:
> cd to root (/demo in repo)
> .\deploy.ps1
> ..update app settings in portal
Note that this is not meant for automate deployment (yet).

SOURCE: https://towardsdatascience.com/deploying-a-streamlit-web-app-with-azure-app-service-1f09a2159743
"""

# Params
$location = 'westeurope'
$rg = 'nlpdemo'
$acr = 'nlpdemoacr'
$image =  'nlp-demo-image'
$sp = 'nlpdemoserviceplan'
$app = 'nlp-demo-app'
$url = $acr + '.azurecr.io/' + $image + ':latest'
$create = $FALSE # create or update app

# az login # if needed
if ($create) {
    # Create Demo App
    az group create -l $location -n $rg
    az acr create --name $acr --resource-group $rg --sku basic --admin-enabled true
    az acr build --registry $acr --resource-group $rg --image $image .
    az appservice plan create -g $rg -n $sp -l $location --is-linux --sku B1
    az webapp create -g $rg -p $sp -n $app -i $url
    # NOTE: the last step requires manual configuration in the Portal. Container settings need to point to ACR.
} Else {
    # Update
    ## Create new image
    az acr build --registry $acr --resource-group $rg --image $image .
    ## Update Web
    az webapp restart -g $rg -n $app
}

