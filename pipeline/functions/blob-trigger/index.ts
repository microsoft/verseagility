import {Context} from '@azure/functions';
import {HttpClient} from '../common/http-client';

// The purpose of this function is to automatically trigger the official endpoint ("api"-function)
// once a new document is uploaded to the data container in the storage. If you want to disable
// this automatic call, just disable the function

const hostname: string = process.env["WEBSITE_HOSTNAME"];
const storageAccount: string = process.env["AzureWebJobsStorage"].split(";")[1].replace("AccountName=", "");
const httpClient = HttpClient.getInstance();

export async function run(context: Context, docblob: Buffer) {

    context.log('document-processor triggered by storage blob');

    var prefix = "";
    if(hostname.indexOf("localhost") == 0) {
        prefix = "http://"
    } else {
        prefix =  "https://"
    }

    const docPath = context.bindingData.blobTrigger;
    var url = prefix + hostname + "/api/storevalues?source=https://" + storageAccount + ".blob.core.windows.net/" + docPath;

    context.log("Calling url " + url);
    httpClient.post(url, {});

}
