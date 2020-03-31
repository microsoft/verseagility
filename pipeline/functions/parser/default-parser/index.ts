import {IParser} from '../../schema/parser';
import {OutputSchema, Answer, DocumentStatus} from '../../schema/output';
import {StorageConnection, StorageResponse} from '../../common/storage-connection';
import {HttpClient} from '../../common/http-client';
import {Guid} from '../../common/guid';

const httpClient = HttpClient.getInstance();
const hostname: string = process.env["WEBSITE_HOSTNAME"];
const functionHostKey: string = process.env["FunctionHostKey"];

export class DefaultParser implements IParser {

    private fileBuffer: Buffer;
    private fileName: string;
    private fileContentType: string;

    constructor(blob: StorageResponse) {
        this.fileBuffer = blob.content;
        this.fileName = blob.name;
        this.fileContentType = blob.contentType;
    }

    public async parse(): Promise<Array<OutputSchema>> {
        return new Promise(async (resolve, reject) => {
            var contentBase64 = this.fileBuffer.toString('base64');

            var data = {
                "name": this.fileName,
                "content": contentBase64,
                "contentType": this.fileContentType
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
                var text = content['values']['data'];
            } catch(e) {
                reject("Error when calling documentconverter function")
            }

            var outputs: Array<OutputSchema> = [];
            output.status = DocumentStatus.train;
            var output: OutputSchema = new OutputSchema();
            output.id = Guid.create();
            output.body = text

            var answer: Answer = new Answer();
            output.label.answer.push(answer);

            outputs.push(output);
            resolve(outputs);

        });
    }

}