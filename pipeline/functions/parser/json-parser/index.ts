import {IParser} from '../../schema/parser';
import {OutputSchema, Answer} from '../../schema/output';
import {Guid} from '../../common/guid'

export class JsonParser implements IParser {

    private fileBuffer: Buffer;

    constructor(file: Buffer) {
        this.fileBuffer = file;
    }

    public async parse(): Promise<Array<OutputSchema>> {
        return new Promise((resolve, reject) => {
            var content = this.fileBuffer.toString();
            var objs = JSON.parse(content);
            var outputs: Array<OutputSchema> = [];

            try {
                objs.forEach(obj => {

                    var output: OutputSchema = new OutputSchema();
                    var answer: Answer = new Answer();
    
                    answer.date = obj['answer']['createdAt'];
                    answer.body = obj['answer']['text'];
                    answer.upvotes = obj['answer']['upvotes'];
    
                    output.label.answer.push(answer);
    
                    output.from = obj['question']['author'];
                    output.date = obj['question']['createdAt'];
                    output.body = obj['question']['text'];
                    output.subject = obj['question']['title'];
                    output.upvotes = obj['question']['upvotes'];
    
                    output.id = obj['id'];
                    output.language = obj['language'];
                    output.url = obj['url'];
                    output.views = obj['views'];
    
                    outputs.push(output);
    
                });
            } catch(err) {
                reject("Wrong input format: " + err);
            }

            resolve(outputs);
        });
    }

}