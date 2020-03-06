import {HttpRequest, Context} from '@azure/functions';
import {HttpResponse, Status} from '../common/http-response';
import {StorageConnection, StorageResponse} from '../common/storage-connection';
import {CSVParser} from '../parser/csv-parser';
import {OutputSchema} from '../schema/output';
import {JsonParser} from '../parser/json-parser';

// Extract storage key from storage account connection string in environment variable "AzureWebJobsStorage"
const storageKey: string = process.env["AzureWebJobsStorage"].split(";")[2].replace("AccountKey=", "");


async function storeValues(context: Context, blob: StorageResponse): Promise<boolean> {
    return new Promise(async (resolve, reject) => {
        var documents: Array<OutputSchema>;

        if(blob.contentType == "text/csv" || blob.contentType == "application/vnd.ms-excel") {
            // Parsers bring a document into the well defined OutputSchema format.
            var csvParser: CSVParser = new CSVParser(blob.content);
            documents = await csvParser.parse();
        } else if(blob.contentType == "application/json") {
            var jsonParser: JsonParser = new JsonParser(blob.content);
            documents = await jsonParser.parse();
        }

        context.bindings.cosmosOutput = JSON.stringify(documents);
        resolve(true);

    });

}


export async function run(context: Context, req: HttpRequest) {

    // Data can be sent as an url to a blob storage or directly as form-data
    // POST http://localhost:7071/api/storevalues?source=https://verseagilitystorage.blob.core.windows.net/data/raw_in_option1.csv

    const command = req.params['command'];
    const queries = req.query;

    context.log('Endpoint triggered');
    context.log(command);
    context.log(queries);

    // This path is used to store values in the database which are sent as URIs to an Azure storage
    // The 'source' query is used to specify the source, the Azure storage is the same which is
    // als used by the function. Store data files in the /data container
    if(command == "storevalues") {
        if("source" in queries) {
            var source: string = queries['source'];
            var sourceParts = source.replace("https://", "").replace("http://", "").split("/");
            var accountName = sourceParts[0].split(".")[0];
            var containerName = sourceParts[1];
            var blobName = sourceParts.slice(2,sourceParts.length).join("/");

            var storageConnection: StorageConnection = new StorageConnection(accountName, storageKey, containerName);
            var blob: StorageResponse = await storageConnection.getBlob(blobName);

            var res: boolean = await storeValues(context, blob);

            if(res == false) {
                var response: HttpResponse = new HttpResponse(Status.BADREQUEST, "Error while storing documents");
                context.res = response.create();
            }

        } else {
            var response: HttpResponse = new HttpResponse(Status.BADREQUEST, "Request must contain 'source' query parameter");
            context.res = response.create();
        }
    } else if(command == "test") {
        var response: HttpResponse = new HttpResponse(Status.SUCCESS, "Test successful");
        context.res = response.create();
    } else {
        var response: HttpResponse = new HttpResponse(Status.SUCCESS, "Successfully uploaded", { "test": 1 });
        context.res = response.create();
    }

}
