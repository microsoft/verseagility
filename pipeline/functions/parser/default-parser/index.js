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
const httpClient = http_client_1.HttpClient.getInstance();
const hostname = process.env["WEBSITE_HOSTNAME"];
const functionHostKey = process.env["FunctionHostKey"];
class DefaultParser {
    constructor(blob) {
        this.fileBuffer = blob.content;
        this.fileName = blob.name;
        this.fileContentType = blob.contentType;
    }
    parse() {
        return __awaiter(this, void 0, void 0, function* () {
            return new Promise((resolve, reject) => __awaiter(this, void 0, void 0, function* () {
                var contentBase64 = this.fileBuffer.toString('base64');
                var data = {
                    "name": this.fileName,
                    "content": contentBase64,
                    "contentType": this.fileContentType
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
                var outputs = [];
                output.status = output_1.DocumentStatus.train;
                var output = new output_1.OutputSchema();
                output.id = guid_1.Guid.create();
                output.body = text;
                var answer = new output_1.Answer();
                output.label.answer.push(answer);
                outputs.push(output);
                resolve(outputs);
            }));
        });
    }
}
exports.DefaultParser = DefaultParser;
//# sourceMappingURL=index.js.map