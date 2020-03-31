"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : new P(function (resolve) { resolve(result.value); }).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
const output_1 = require("../../schema/output");
const http_client_1 = require("../../common/http-client");
const httpClient = http_client_1.HttpClient.getInstance();
const hostname = process.env["WEBSITE_HOSTNAME"];
const functionHostKey = process.env["FunctionHostKey"];
class JsonParser {
    constructor(blob, storageConnection) {
        this.fileBuffer = blob.content;
        this.storageConnection = storageConnection;
        this.fileContentType = blob.contentType;
    }
    parse() {
        return __awaiter(this, void 0, void 0, function* () {
            return new Promise((resolve, reject) => __awaiter(this, void 0, void 0, function* () {
                var file = this.fileBuffer.toString();
                var objs = JSON.parse(file);
                var outputs = [];
                try {
                    for (var i = 0; i < objs.length; i++) {
                        var obj = objs[i];
                        var output = new output_1.OutputSchema();
                        var answer = new output_1.Answer();
                        answer.date = obj['answer']['createdAt'];
                        answer.body = obj['answer']['text'];
                        answer.upvotes = obj['answer']['upvotes'];
                        output.label.answer.push(answer);
                        output.from = obj['question']['author'];
                        output.date = obj['question']['createdAt'];
                        output.body = obj['question']['text'];
                        output.subject = obj['question']['title'];
                        output.upvotes = obj['question']['upvotes'];
                        output.status = output_1.DocumentStatus.train;
                        output.id = obj['id'];
                        output.language = obj['language'];
                        output.url = obj['url'];
                        output.views = obj['views'];
                        var label = new output_1.Label();
                        var classification = new output_1.Classification();
                        var version = new output_1.Version();
                        version.value = obj['appliesTo'];
                        classification.task_type = "simple";
                        classification.version.push(version);
                        label.classification.push(classification);
                        label.answer.push(answer);
                        output.label = label;
                        // Check if a container exists in the storage account which is named like the ID of the entry in the JSON
                        var exists = yield this.storageConnection.containerExists(output.id);
                        if (exists) {
                            var blobs = yield this.storageConnection.listContainerBlobs(output.id);
                            for (var j = 0; j < blobs.length; j++) {
                                var blobItem = blobs[j];
                                var blob = yield this.storageConnection.getBlob(blobItem.name);
                                var data = {
                                    "name": blob.name,
                                    "content": blob.content.toString('base64'),
                                    "contentType": blob.contentType
                                };
                                var prefix = "";
                                if (hostname.indexOf("localhost") == 0) {
                                    prefix = "http://";
                                }
                                else {
                                    prefix = "https://";
                                }
                                var url = prefix + hostname + "/documentconverter?code=" + functionHostKey;
                                var res = yield httpClient.post(url, data);
                                if (res.status != 200) {
                                    reject("Error when calling documentconverter function");
                                }
                                var content = JSON.parse(res.text);
                                try {
                                    var text = content['values']['data'];
                                }
                                catch (e) {
                                    reject("Error when calling documentconverter function");
                                }
                                var attachment = new output_1.Attachment();
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
                }
                catch (err) {
                    reject("Wrong input format: " + err);
                }
                resolve(outputs);
            }));
        });
    }
}
exports.JsonParser = JsonParser;
//# sourceMappingURL=index.js.map