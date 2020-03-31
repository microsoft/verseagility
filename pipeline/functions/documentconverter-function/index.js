"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : new P(function (resolve) { resolve(result.value); }).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
const http_response_1 = require("../common/http-response");
const ocr_client_1 = require("../common/ocr-client/ocr-client");
const fs_1 = require("fs");
const child = __importStar(require("child_process"));
const ocrName = process.env["CognitiveServiceName"];
const ocrKey = process.env["CognitiveServiceKey"];
const ocrClient = new ocr_client_1.OCRClient(ocrName, ocrKey);
function run(context, req) {
    return __awaiter(this, void 0, void 0, function* () {
        context.log('documentconverter endpoint triggered');
        var body = req.body;
        if ("name" in body == false || "content" in body == false || "contentType" in body == false) {
            var response = new http_response_1.HttpResponse(http_response_1.Status.BADREQUEST, "documentconverter function must be called with JSON HTTP POST body containing 'name' (string), 'content' and 'contentType' (MIME type string). 'content' must be base64 encoded binary file.");
            context.res = response.create();
            return;
        }
        var blobName = body['name'].split(" ").join("_");
        var blobContentBase64 = body['content'];
        var blobContentType = body['contentType'];
        try {
            var buff = new Buffer(blobContentBase64, 'base64');
        }
        catch (e) {
            var response = new http_response_1.HttpResponse(http_response_1.Status.BADREQUEST, "'content' must be a base64 encoded Buffer containing a binary document", e);
            context.res = response.create();
            return;
        }
        // Save file to disk
        fs_1.writeFileSync(blobName, buff);
        // If blobContentType starts with "image", call OCR tool, otherwise use Apache Tika
        if (blobContentType.indexOf("image") == 0) {
            var imageConversion = yield ocrClient.convertImageToText(blobName);
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
                    fs_1.unlinkSync(blobName);
                }
                catch (e) { }
            }, 2000);
            var response = new http_response_1.HttpResponse(http_response_1.Status.SUCCESS, "Image parsed", { data: doc });
            context.res = response.create();
        }
        else {
            var promise = new Promise((resolve) => __awaiter(this, void 0, void 0, function* () {
                var res = child.exec('java -jar tika-app-1.23.jar ' + blobName);
                res.stdout.on('data', function (data) {
                    setTimeout(() => {
                        // Delete file from disk
                        try {
                            fs_1.unlinkSync(blobName);
                        }
                        catch (e) { }
                    }, 2000);
                    resolve(data);
                });
            }));
            yield Promise.all([promise]).then(result => {
                var response = new http_response_1.HttpResponse(http_response_1.Status.SUCCESS, "Document parsed", { data: result[0] });
                context.res = response.create();
            });
        }
    });
}
exports.run = run;
//# sourceMappingURL=index.js.map