import {IParser} from '../../schema/parser';
import {OutputSchema, Answer, DocumentStatus, Attachment, Label, Classification, Version} from '../../schema/output';
import {StorageConnection, StorageResponse} from '../../common/storage-connection';
import {HttpClient} from '../../common/http-client';
import {BlobItem} from '@azure/storage-blob';

const httpClient = HttpClient.getInstance();
const hostname: string = process.env["WEBSITE_HOSTNAME"];
const functionHostKey: string = process.env["FunctionHostKey"];

export class JsonParser implements IParser {

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
            var objs = JSON.parse(file);
            var outputs: Array<OutputSchema> = [];

            try {
                for(var i=0;i<objs.length;i++) {

                    var obj = objs[i];
                    var output: OutputSchema = new OutputSchema();
                    var answer: Answer = new Answer();
    
                    answer.date = obj['answer']['createdAt'];
                    answer.body = obj['answer']['text'];
                    answer.upvotes = obj['answer']['upvotes'];
    
                    output.label.answer.push(answer);
    
                    output.from = obj['question']['author'];
                    output.date = obj['question']['createdAt'];
                    output.body = obj['question']['text'];
                    output.subject = obj['question']['title'];
                    output.upvotes = obj['question']['upvotes'];
                    output.status = DocumentStatus.train;
    
                    output.id = obj['id'];
                    output.language = obj['language'];
                    output.url = obj['url'];
                    output.views = obj['views'];

                    var label: Label = new Label();
                    var classification: Classification = new Classification();
                    var version: Version = new Version();
                    version.value = obj['appliesTo'];
                    classification.task_type = "simple"
                    classification.version.push(version);
    
                    label.classification.push(classification);
                    label.answer.push(answer);
    
                    output.label = label;
    
                    // Check if a container exists in the storage account which is named like the ID of the entry in the JSON
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
                            attachment.text = text.split('<body>').pop().split('</body>')[0].replace(/\r\n/g, '');
                            attachment.filetype = blob.contentType;
                            attachment.filename = blob.name;
                            attachment.content.push({
                                "raw": text
                            });
                            output.attachment.push(attachment);
                        }
                    }

                    outputs.push(output);
    
                }
            } catch(err) {
                reject("Wrong input format: " + err);
            }

            resolve(outputs);
        });
    }

}