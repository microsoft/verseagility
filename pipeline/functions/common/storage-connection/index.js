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
const storage_blob_1 = require("@azure/storage-blob");
const http_client_1 = require("../../common/http-client");
const streamToBuffer = require('stream-to-buf');
const httpClient = http_client_1.HttpClient.getInstance();
class StorageResponse {
}
exports.StorageResponse = StorageResponse;
class StorageConnection {
    constructor(account, accountKey, containerName = null) {
        const sharedKeyCredential = new storage_blob_1.StorageSharedKeyCredential(account, accountKey);
        this.blobServiceClient = new storage_blob_1.BlobServiceClient(`https://${account}.blob.core.windows.net`, sharedKeyCredential);
        if (containerName != null) {
            this.containerClient = this.blobServiceClient.getContainerClient(containerName);
        }
    }
    streamToString(readableStream) {
        return __awaiter(this, void 0, void 0, function* () {
            return new Promise((resolve, reject) => {
                const chunks = [];
                readableStream.on("data", (data) => {
                    chunks.push(data.toString());
                });
                readableStream.on("end", () => {
                    resolve(chunks.join(""));
                });
                readableStream.on("error", reject);
            });
        });
    }
    containerExists(containerName) {
        return __awaiter(this, void 0, void 0, function* () {
            return new Promise((resolve, reject) => __awaiter(this, void 0, void 0, function* () {
                this.containerClient = this.blobServiceClient.getContainerClient(containerName);
                var exists = yield this.containerClient.exists();
                if (exists) {
                    resolve(true);
                }
                else {
                    resolve(false);
                }
            }));
        });
    }
    listContainerBlobs(containerName) {
        return __awaiter(this, void 0, void 0, function* () {
            return new Promise((resolve, reject) => __awaiter(this, void 0, void 0, function* () {
                this.containerClient = this.blobServiceClient.getContainerClient(containerName);
                var blobs = [];
                var iter = yield this.containerClient.listBlobsFlat();
                var entity = yield iter.next();
                while (!entity.done) {
                    blobs.push(entity.value);
                    entity = yield iter.next();
                }
                // for await (let blob of this.containerClient.listBlobsFlat()) {
                //     blobs.push(blob);
                // }
                resolve(blobs);
            }));
        });
    }
    getBlob(blobName) {
        return __awaiter(this, void 0, void 0, function* () {
            return new Promise((resolve, reject) => __awaiter(this, void 0, void 0, function* () {
                try {
                    var blobClient = yield this.containerClient.getBlobClient(blobName);
                    var response = yield blobClient.download();
                    var contentType = response.contentType;
                    streamToBuffer(response.readableStreamBody).then((buffer) => {
                        var res = new StorageResponse();
                        res.name = blobName;
                        res.contentType = contentType;
                        res.content = buffer;
                        resolve(res);
                    }, (err) => {
                        reject(err);
                    });
                    var downloaded = yield this.streamToString(response.readableStreamBody);
                }
                catch (err) {
                    reject(err);
                }
            }));
        });
    }
}
exports.StorageConnection = StorageConnection;
//# sourceMappingURL=index.js.map