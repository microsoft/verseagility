"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
const node_fetch_1 = __importDefault(require("node-fetch"));
const fs = __importStar(require("fs"));
class OCRClient {
    constructor(cognitiveServiceName, cognitiveServiceKey) {
        this.key = cognitiveServiceKey;
        this.name = cognitiveServiceName;
    }
    convertImageToText(filePath, counter = 0) {
        let requestHeaders = {
            'Content-Type': 'application/octet-stream',
            'Ocp-Apim-Subscription-Key': this.key
        };
        var data = fs.readFileSync(filePath);
        var name = this.name;
        try {
            return new Promise(function (resolve, reject) {
                var url = "https://" + name + ".cognitiveservices.azure.com/vision/v2.0/ocr";
                node_fetch_1.default(url, {
                    method: 'post',
                    body: data,
                    headers: requestHeaders,
                })
                    .then(res => res.json())
                    .then(json => {
                    if (json == null || json == undefined) {
                        throw Error("Returned OCR JSON is undefined");
                    }
                    resolve(json);
                });
            });
        }
        catch (e) {
            if (counter > 5) {
                throw Error(e);
            }
            else {
                this.convertImageToText(filePath, counter++);
            }
        }
    }
}
exports.OCRClient = OCRClient;
//# sourceMappingURL=ocr-client.js.map