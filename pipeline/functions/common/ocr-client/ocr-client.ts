import fetch from 'node-fetch';
import * as fs from 'fs';

export class OCRClient {

    private key: string;
    private name: string;

    constructor(cognitiveServiceName: string, cognitiveServiceKey: string) {
        this.key = cognitiveServiceKey;
        this.name = cognitiveServiceName;
    }

    convertImageToText(filePath: string, counter: number = 0): Promise<any> {

        let requestHeaders: any = { 
            'Content-Type': 'application/octet-stream',
            'Ocp-Apim-Subscription-Key': this.key
        };

        var data = fs.readFileSync(filePath);
        var name = this.name;

        try {
            return new Promise(function (resolve, reject) {

                var url = "https://" + name + ".cognitiveservices.azure.com/vision/v2.0/ocr";

                fetch(url, {
                method: 'post',
                body:    data,
                headers: requestHeaders,
            })
            .then(res => res.json())
            .then(json => {
                if(json == null || json == undefined) {
                    throw Error("Returned OCR JSON is undefined");
                }
                resolve(json);
            });
            });
        } catch(e) {
            if(counter > 5) {
                throw Error(e);
            } else {
                this.convertImageToText(filePath, counter++);
            }

        }

    }

}