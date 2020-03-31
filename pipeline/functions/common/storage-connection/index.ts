import {BlobServiceClient,
        StorageSharedKeyCredential,
        ContainerClient,
        BlobClient,
        BlobDownloadResponseModel,
        BlobItem} from '@azure/storage-blob';
import {HttpClient} from '../../common/http-client';

const streamToBuffer = require('stream-to-buf');
const httpClient = HttpClient.getInstance();

export class StorageResponse {
    public name: string;
    public contentType: string;
    public content: Buffer;
}

export class StorageConnection {

    private blobServiceClient: BlobServiceClient;
    private containerClient: ContainerClient;

    constructor(account: string, accountKey: string, containerName: string = null) {

        const sharedKeyCredential = new StorageSharedKeyCredential(account, accountKey);
        this.blobServiceClient = new BlobServiceClient(
          `https://${account}.blob.core.windows.net`,
          sharedKeyCredential
        );

        if(containerName != null) {
            this.containerClient = this.blobServiceClient.getContainerClient(containerName);
        }

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


    public async containerExists(containerName: string): Promise<boolean> {
        return (new Promise(async (resolve, reject) => {

            this.containerClient = this.blobServiceClient.getContainerClient(containerName);
            var exists = await this.containerClient.exists();

            if(exists) {
                resolve(true);
            } else {
                resolve(false);
            }

        }) as Promise<boolean>) ;
    }


    public async listContainerBlobs(containerName: string): Promise<Array<BlobItem>> {
        return (new Promise(async (resolve, reject) => {

            this.containerClient = this.blobServiceClient.getContainerClient(containerName);
            var blobs: Array<BlobItem> = [];

            var iter = await this.containerClient.listBlobsFlat();
            var entity = await iter.next();

            while (!entity.done) {
                blobs.push(entity.value);
                entity = await iter.next();
            }

            // for await (let blob of this.containerClient.listBlobsFlat()) {
            //     blobs.push(blob);
            // }

            resolve(blobs);

        }) as Promise<Array<BlobItem>>) ;
    }


    public async getBlob(blobName: string): Promise<StorageResponse> {
        return (new Promise(async (resolve, reject) => {
            try {
                var blobClient: BlobClient = await this.containerClient.getBlobClient(blobName);
                var response: BlobDownloadResponseModel = await blobClient.download();
                var contentType: string = response.contentType;

                streamToBuffer(response.readableStreamBody).then((buffer) => {
                    var res: StorageResponse = new StorageResponse();
                    res.name = blobName;
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
