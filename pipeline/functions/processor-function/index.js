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
const http_client_1 = require("../common/http-client");
const storage_connection_1 = require("../common/storage-connection");
const csv_parser_1 = require("../parser/csv-parser");
const json_parser_1 = require("../parser/json-parser");
const default_parser_1 = require("../parser/default-parser");
// The purpose of this function is to store documents that are placed into the /data container
// of the created storage account
const hostname = process.env["WEBSITE_HOSTNAME"];
const functionHostKey = process.env["FunctionHostKey"];
const storageAccount = process.env["AzureWebJobsStorage"].split(";")[1].replace("AccountName=", "");
const httpClient = http_client_1.HttpClient.getInstance();
// Extract storage key from storage account connection string in environment variable "AzureWebJobsStorage"
const storageKey = process.env["AzureWebJobsStorage"].split(";")[2].replace("AccountKey=", "");
function storeValues(context, blob, storageConnection) {
    return __awaiter(this, void 0, void 0, function* () {
        return new Promise((resolve, reject) => __awaiter(this, void 0, void 0, function* () {
            var documents;
            // Parsers bring a document into the well defined OutputSchema format.
            // Add an if-else-statement here to decide how documents should be processed (e.g. based on the Content-Type)
            // To parse a new file type, add a folder and class to the /parser directory
            // The DefaultParser will call the documentconverter-function. If you just need a general parser without finetuning
            // the parsing process, you may use the DefaultParser as your standard parser.
            if (blob.contentType == "text/csv" || blob.contentType == "application/vnd.ms-excel") {
                var csvParser = new csv_parser_1.CSVParser(blob, storageConnection);
                documents = yield csvParser.parse();
            }
            else if (blob.contentType == "application/json") {
                var jsonParser = new json_parser_1.JsonParser(blob, storageConnection);
                documents = yield jsonParser.parse();
            }
            else {
                var defaultParser = new default_parser_1.DefaultParser(blob);
                documents = yield defaultParser.parse();
            }
            context.bindings.cosmosOutput = JSON.stringify(documents);
            resolve(true);
        }));
    });
}
function run(context, docblob) {
    return __awaiter(this, void 0, void 0, function* () {
        context.log('document-processor triggered by storage blob');
        const docPath = context.bindingData.blobTrigger;
        var accountName = storageAccount;
        var containerName = docPath.split("/")[0];
        var blobName = docPath.split("/")[1];
        var storageConnection = new storage_connection_1.StorageConnection(accountName, storageKey, containerName);
        var blob = yield storageConnection.getBlob(blobName);
        var finished = yield storeValues(context, blob, storageConnection);
        if (finished) {
            context.log("Document processed");
        }
        else {
            context.log("Error while processing document");
        }
    });
}
exports.run = run;
//# sourceMappingURL=index.js.map