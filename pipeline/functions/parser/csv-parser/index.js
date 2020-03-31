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
const guid_1 = require("../../common/guid");
const csv = require('csvtojson');
const httpClient = http_client_1.HttpClient.getInstance();
const hostname = process.env["WEBSITE_HOSTNAME"];
const functionHostKey = process.env["FunctionHostKey"];
class CSVParser {
    constructor(blob, storageConnection) {
        this.fileBuffer = blob.content;
        this.storageConnection = storageConnection;
        this.fileContentType = blob.contentType;
    }
    parse() {
        return __awaiter(this, void 0, void 0, function* () {
            return new Promise((resolve, reject) => __awaiter(this, void 0, void 0, function* () {
                var file = this.fileBuffer.toString();
                var rows = yield csv({ noheader: false, output: "csv" }).fromString(file);
                var outputs = [];
                for (var i = 0; i < rows.length; i++) {
                    var row = rows[i];
                    var output = new output_1.OutputSchema();
                    output.id = row[0];
                    output.views = row[1];
                    output.url = row[3];
                    output.language = row[4];
                    output.subject = row[5];
                    output.from = row[6];
                    output.date = row[7];
                    output.body = row[8];
                    output.upvotes = row[9];
                    output.status = output_1.DocumentStatus.train;
                    var answer = new output_1.Answer();
                    answer.body = row[12];
                    answer.date = row[11];
                    answer.upvotes = row[13];
                    var label = new output_1.Label();
                    var classification = new output_1.Classification();
                    var version = new output_1.Version();
                    version.value = row[2];
                    classification.task_type = "simple";
                    classification.version.push(version);
                    label.classification.push(classification);
                    label.answer.push(answer);
                    output.label = label;
                    // Check if a container exists in the storage account which is named like the ID of the entry in the CSV
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
                    if (output.id == null) {
                        output.id = guid_1.Guid.create();
                    }
                    outputs.push(output);
                }
                resolve(outputs);
            }));
        });
    }
}
exports.CSVParser = CSVParser;
//# sourceMappingURL=index.js.map