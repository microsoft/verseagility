import {BlobServiceClient, StorageSharedKeyCredential, ContainerClient, BlobClient, BlobDownloadResponseModel} from '@azure/storage-blob';
import {Context} from '@azure/functions';

const streamToBuffer = require('stream-to-buf');

export class StorageResponse {
    public contentType: string;
    public content: Buffer;
}



export class StorageConnection {

    private blobServiceClient: BlobServiceClient;
    private containerClient: ContainerClient;

    constructor(account: string, accountKey: string, containerName: string = "data") {

        const sharedKeyCredential = new StorageSharedKeyCredential(account, accountKey);
        this.blobServiceClient = new BlobServiceClient(
          `https://${account}.blob.core.windows.net`,
          sharedKeyCredential
        );

        this.containerClient = this.blobServiceClient.getContainerClient(containerName);

    }
    
    private async streamToString(readableStream): Promise<string> {
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
    }

    public async getBlob(blobName: string): Promise<StorageResponse> {
        return (new Promise(async (resolve, reject) => {
            try {
                var blobClient: BlobClient = await this.containerClient.getBlobClient(blobName);

                var response: BlobDownloadResponseModel = await blobClient.download();

                var contentType: string = response.contentType;

                streamToBuffer(response.readableStreamBody).then((buffer) => {
                    var res: StorageResponse = new StorageResponse();
                    res.contentType = contentType;
                    res.content = buffer;
                    resolve(res);
                }, (err) => {
                    reject(err);
                });

                var downloaded: string = await this.streamToString(response.readableStreamBody);

            } catch(err) {
                reject(err)
            }
        }) as Promise<StorageResponse>) ;
    }
}
