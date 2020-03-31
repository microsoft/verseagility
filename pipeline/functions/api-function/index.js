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
const http_response_1 = require("../common/http-response");
const output_1 = require("../schema/output");
const storage_connection_1 = require("../common/storage-connection");
const http_client_1 = require("../common/http-client");
// Extract storage key from storage account connection string in environment variable "AzureWebJobsStorage"
const storageKey = process.env["AzureWebJobsStorage"].split(";")[2].replace("AccountKey=", "");
const storageAccount = process.env["AzureWebJobsStorage"].split(";")[1].replace("AccountName=", "");
const httpClient = http_client_1.HttpClient.getInstance();
const hostname = process.env["WEBSITE_HOSTNAME"];
const functionHostKey = process.env["FunctionHostKey"];
function run(context, req) {
    return __awaiter(this, void 0, void 0, function* () {
        const command = req.params['command'];
        const queries = req.query;
        var body = req.body;
        context.log('api endpoint triggered');
        context.log(command);
        context.log(queries);
        // The purpose of this endpoint is to store documents that should be stored in CosmosDB with "status": "score"
        if (command == "score") {
            // Assumption is that only one element exists in the HTTP request. If structure is an array, take the first element
            if (Array.isArray(body)) {
                body = body[0];
            }
            var allAttachments = [];
            if ("attachments" in body) {
                const attachments = body["attachments"];
                for (var i = 0; i < attachments.length; i++) {
                    var attachment = attachments[i];
                    if ("link" in attachment) {
                        var docPath = attachment["link"];
                        var accountName = storageAccount;
                        // Assumption is that user stores attachments in Azure Storage
                        // Assumption is that user doesn't use virtual directories to store attachments, otherwise this will fail
                        var parts = docPath.split("/");
                        var containerName = parts[parts.length - 2];
                        var blobName = parts[parts.length - 1];
                        var storageConnection = new storage_connection_1.StorageConnection(accountName, storageKey, containerName);
                        var blob = yield storageConnection.getBlob(blobName);
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
                            throw Error("Error when calling documentconverter function");
                        }
                        var content = JSON.parse(res.text);
                        var att = new output_1.Attachment();
                        att.link = docPath;
                        att.text = content["values"]["data"];
                        allAttachments.push(att);
                    }
                }
            }
            var output = new output_1.OutputSchema(body);
            output.status = output_1.DocumentStatus.score;
            output.attachment = allAttachments;
            context.bindings.cosmosOutput = JSON.stringify(output);
            var response = new http_response_1.HttpResponse(http_response_1.Status.SUCCESS, "Document stored");
            context.res = response.create();
        }
        else if (command == "test") {
            var response = new http_response_1.HttpResponse(http_response_1.Status.SUCCESS, "Test successful");
            context.res = response.create();
        }
        else {
            var response = new http_response_1.HttpResponse(http_response_1.Status.BADREQUEST, "No valid command was provided");
            context.res = response.create();
        }
    });
}
exports.run = run;
//# sourceMappingURL=index.js.map