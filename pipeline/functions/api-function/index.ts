import {HttpRequest, Context} from '@azure/functions';
import {HttpResponse, Status} from '../common/http-response';
import {OutputSchema, DocumentStatus, Attachment} from '../schema/output';
import {StorageConnection, StorageResponse} from '../common/storage-connection';
import {HttpClient} from '../common/http-client';

// Extract storage key from storage account connection string in environment variable "AzureWebJobsStorage"
const storageKey: string = process.env["AzureWebJobsStorage"].split(";")[2].replace("AccountKey=", "");
const storageAccount: string = process.env["AzureWebJobsStorage"].split(";")[1].replace("AccountName=", "");

const httpClient = HttpClient.getInstance();
const hostname: string = process.env["WEBSITE_HOSTNAME"];
const functionHostKey: string = process.env["FunctionHostKey"];

export async function run(context: Context, req: HttpRequest) {

    const command = req.params['command'];
    const queries = req.query;
    var body = req.body;

    context.log('api endpoint triggered');
    context.log(command);
    context.log(queries);

    // The purpose of this endpoint is to store documents that should be stored in CosmosDB with "status": "score"
    if(command == "score") {

        // Assumption is that only one element exists in the HTTP request. If structure is an array, take the first element
        if(Array.isArray(body)) {
            body = body[0];
        }

        var allAttachments: Array<Attachment> = [];
        if("attachments" in body) {
            const attachments = body["attachments"];
            for(var i=0;i<attachments.length;i++) {
                var attachment = attachments[i];
                if("link" in attachment) {
                    var docPath = attachment["link"];
                    var accountName = storageAccount;
                    // Assumption is that user stores attachments in Azure Storage
                    // Assumption is that user doesn't use virtual directories to store attachments, otherwise this will fail
                    var parts = docPath.split("/")
                    var containerName = parts[parts.length-2];
                    var blobName = parts[parts.length-1];
                
                    var storageConnection: StorageConnection = new StorageConnection(accountName, storageKey, containerName);
                    var blob: StorageResponse = await storageConnection.getBlob(blobName);

                    var data = {
                        "name": blob.name,
                        "content": blob.content.toString('base64'),
                        "contentType": blob.contentType
                    }
        
                    var prefix = "";
                    if(hostname.indexOf("localhost") == 0) {
                        prefix = "http://"
                    } else {
                        prefix =  "https://"
                    }
                
                    var url = prefix + hostname + "/documentconverter?code=" + functionHostKey;
                
                    var res = await httpClient.post(url, data);
                    if(res.status != 200) {
                        throw Error("Error when calling documentconverter function");
                    }
        
                    var content = JSON.parse(res.text);

                    var att: Attachment = new Attachment();
                    att.link = docPath;
                    att.text = content["values"]["data"];
                    allAttachments.push(att);
                }
            }
        }

        var output: OutputSchema = new OutputSchema(body);
        output.status = DocumentStatus.score;
        output.attachment = allAttachments;
        context.bindings.cosmosOutput = JSON.stringify(output);

        var response: HttpResponse = new HttpResponse(Status.SUCCESS, "Document stored");
        context.res = response.create();

    } else if(command == "test") {
        var response: HttpResponse = new HttpResponse(Status.SUCCESS, "Test successful");
        context.res = response.create();
    } else {
        var response: HttpResponse = new HttpResponse(Status.BADREQUEST, "No valid command was provided");
        context.res = response.create();
    }

}
