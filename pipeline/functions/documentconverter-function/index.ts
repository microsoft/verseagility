import {HttpRequest, Context} from '@azure/functions';
import {HttpResponse, Status} from '../common/http-response';
import {OCRClient} from '../common/ocr-client/ocr-client';
import {readFileSync, writeFileSync, unlinkSync} from 'fs';
import * as child from 'child_process';

const ocrName: string = process.env["CognitiveServiceName"];
const ocrKey: string = process.env["CognitiveServiceKey"];
const ocrClient = new OCRClient(ocrName, ocrKey);

export async function run(context: Context, req: HttpRequest) {

    context.log('documentconverter endpoint triggered');
    var body = req.body;

    if("name" in body == false || "content" in body == false || "contentType" in body == false) {
        var response: HttpResponse = new HttpResponse(Status.BADREQUEST, "documentconverter function must be called with JSON HTTP POST body containing 'name' (string), 'content' and 'contentType' (MIME type string). 'content' must be base64 encoded binary file.");
        context.res = response.create();
        return;
    }

    var blobName: string = body['name'].split(" ").join("_")
    var blobContentBase64: string = body['content'];
    var blobContentType: string = body['contentType'];

    try {
        var buff = new Buffer(blobContentBase64, 'base64');
    } catch(e) {
        var response: HttpResponse = new HttpResponse(Status.BADREQUEST, "'content' must be a base64 encoded Buffer containing a binary document", e);
        context.res = response.create();
        return;
    }

    // Save file to disk
    writeFileSync(blobName, buff);

    // If blobContentType starts with "image", call OCR tool, otherwise use Apache Tika
    if(blobContentType.indexOf("image") == 0) {
        var imageConversion = await ocrClient.convertImageToText(blobName);
        var regions = imageConversion['regions'];
        var doc = "";
        regions.forEach(region => {
            region['lines'].forEach(line => {
                line['words'].forEach(word => {
                    doc += word['text'] + " ";
                });
            });
        });
        setTimeout(() => {
            // Delete file from disk
            try {
                unlinkSync(blobName);
            } catch(e) {}
        }, 2000);
        var response: HttpResponse = new HttpResponse(Status.SUCCESS, "Image parsed", { data: doc });
        context.res = response.create();
    } else {
        var promise = new Promise(async resolve => {
            var res: child.ChildProcess = child.exec('java -jar tika-app-1.23.jar ' + blobName);
            res.stdout.on('data', function (data) {
                setTimeout(() => {
                    // Delete file from disk
                    try {
                        unlinkSync(blobName);
                    } catch(e) {}
                }, 2000);
                resolve(data);
            });
        });

        await Promise.all([promise]).then(result => {
            var response: HttpResponse = new HttpResponse(Status.SUCCESS, "Document parsed", { data: result[0] });
            context.res = response.create();
        });
    }

}
