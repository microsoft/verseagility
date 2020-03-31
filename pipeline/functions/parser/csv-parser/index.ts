import {IParser} from '../../schema/parser';
import {OutputSchema, Answer, Attachment, DocumentStatus, Label, Classification, Version} from '../../schema/output';
import {StorageConnection, StorageResponse} from '../../common/storage-connection';
import {HttpClient} from '../../common/http-client';
import {Guid} from '../../common/guid';
import {BlobItem} from '@azure/storage-blob';

const csv = require('csvtojson');
const httpClient = HttpClient.getInstance();
const hostname: string = process.env["WEBSITE_HOSTNAME"];
const functionHostKey: string = process.env["FunctionHostKey"];

export class CSVParser implements IParser {

    private fileBuffer: Buffer;
    private storageConnection: StorageConnection;
    private fileContentType: string;

    constructor(blob: StorageResponse, storageConnection: StorageConnection) {
        this.fileBuffer = blob.content;
        this.storageConnection = storageConnection;
        this.fileContentType = blob.contentType;
    }

    public async parse(): Promise<Array<OutputSchema>> {
        return new Promise(async (resolve, reject) => {
            var file = this.fileBuffer.toString();
            var rows = await csv({ noheader:false, output: "csv"}).fromString(file);
            var outputs: Array<OutputSchema> = [];

            for(var i=0;i<rows.length;i++) {
                var row = rows[i];
                var output: OutputSchema = new OutputSchema();
                output.id = row[0];
                output.views = row[1];
                output.url = row[3];
                output.language = row[4];
                output.subject = row[5];
                output.from = row[6];
                output.date = row[7];
                output.body = row[8];
                output.upvotes = row[9];
                output.status = DocumentStatus.train;

                var answer: Answer = new Answer();
                answer.body = row[12];
                answer.date = row[11];
                answer.upvotes = row[13];

                var label: Label = new Label();
                var classification: Classification = new Classification();
                var version: Version = new Version();
                version.value = row[2];
                classification.task_type = "simple"
                classification.version.push(version);

                label.classification.push(classification);
                label.answer.push(answer);

                output.label = label;

                // Check if a container exists in the storage account which is named like the ID of the entry in the CSV
                var exists = await this.storageConnection.containerExists(output.id);

                if(exists) {
                    var blobs: Array<BlobItem> = await this.storageConnection.listContainerBlobs(output.id);
                    for(var j=0;j<blobs.length;j++) {
                        var blobItem: BlobItem = blobs[j];
                        var blob: StorageResponse = await this.storageConnection.getBlob(blobItem.name);

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
                            reject("Error when calling documentconverter function");
                        }
            
                        var content = JSON.parse(res.text);
            
                        try {
                            var text: string = content['values']['data'];
                        } catch(e) {
                            reject("Error when calling documentconverter function")
                        }

                        var attachment: Attachment = new Attachment();
                        attachment.text = text.split('<body>').pop().split('</body>')[0];
                        attachment.filetype = blob.contentType;
                        attachment.filename = blob.name;
                        attachment.content.push({
                            "raw": text
                        });
                        output.attachment.push(attachment);
                    }
                }

                // If object doesn't have an Id, create one
                if(output.id == null) {
                    output.id = Guid.create();
                }

                outputs.push(output);

            }

            resolve(outputs);
        });
    }

}