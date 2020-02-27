import {Context} from '@azure/functions';

var hostname = process.env["WEBSITE_HOSTNAME"];

export async function run(context: Context, docblob: Buffer) {

    const docPath = context.bindingData.blobTrigger;
    const docName = docPath.split("/")[1];
    const docBlob = context.bindings.docblob;

    context.log('document-processor triggered by storage blob');

}
