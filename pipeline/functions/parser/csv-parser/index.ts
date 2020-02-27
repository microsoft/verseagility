import {IParser} from '../../schema/parser';
import {OutputSchema, Answer} from '../../schema/output';
import {Guid} from '../../common/guid';

const csv = require('csvtojson');

export class CSVParser implements IParser {

    private fileBuffer: Buffer;

    constructor(file: Buffer) {
        this.fileBuffer = file;
    }

    public async parse(): Promise<Array<OutputSchema>> {
        return new Promise(async (resolve, reject) => {
            var content = this.fileBuffer.toString();
            var rows = await csv({ noheader:false, output: "csv"}).fromString(content);
            var outputs: Array<OutputSchema> = [];

            rows.forEach(row => {
                
                var output: OutputSchema = new OutputSchema();
                output.id = row[0];
                output.views = row[1];
                output.url = row[3];
                output.language = row[4];
                output.subject = row[5];
                output.from = row[6];
                output.date = row[7];
                output.body = row[8];
                output.upvotes = row[9];

                var answer: Answer = new Answer();
                answer.body = row[12];
                answer.date = row[11];
                answer.upvotes = row[13];
                output.label.answer.push(answer);

                // If object doesn't have an Id, create one
                if(output.id == null) {
                    output.id = Guid.create();
                }

                outputs.push(output);

            });

            resolve(outputs);
        });
    }

}