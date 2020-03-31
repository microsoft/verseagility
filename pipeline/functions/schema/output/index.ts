import {Guid} from '../../common/guid';

export enum DocumentStatus {
    train = "train",
    score = "score",
    corrected = "corrected"
}

export class Answer {
    public rank: number = null;
    public body: string = null;
    public upvotes: number = null;
    public date: string = null;
    public markedAsAnswer: string = null;
}

export class Version {
    public value: string = null;
    public confidence: number = null;
    public author: string = null;
    public date: string = null;
}

export class Classification {
    public task_type: string = null;
    public version: Array<Version> = [];
}

export class Label {
    public classification: Array<Classification> = [];
    public answer: Array<Answer> = [];
}

export class Attachment {
    public link: string = null;
    public pages: Array<string> = [];
    public filename: string = null;
    public filetype: string = null;
    public text: string = null;
    public content: Array<any> = [];
}

export class OutputSchema {
    public id: string = null;
    public from: string = null;
    public date: string = null;
    public subject: string = null;
    public body: string = null;
    public attachment: Array<Attachment> = [];
    public upvotes: number = null;
    public views: number = null;
    public url: string = null;
    public language: string = null;
    public status: DocumentStatus = null;
    public label: Label = new Label();

    private parse(o) {
        Object.keys(o).forEach((k) => {
            if (o[k] !== null && typeof o[k] === 'object') {
                this.parse(o[k]);
                return;
            }
            if (typeof o[k] === 'string') {
                o[k] = o[k].replace(/'/g, "''");
                var key = k;
                var value = o[k];
                if(key == "id") {
                    this.id = value;
                }
                if(key == "from") {
                    this.from = value;
                }
                if(key == "date") {
                    this.date = value;
                }
                if(key == "subject") {
                    this.subject = value;
                }
                if(key == "body") {
                    this.body = value;
                }
                if(key == "upvotes") {
                    this.upvotes = value;
                }
                if(key == "views") {
                    this.views = value;
                }
                if(key == "url") {
                    this.url = value;
                }
                if(key == "language") {
                    this.language = value;
                }
                if(key == "status") {
                    this.status = value;
                }
            }
        });
    }

    constructor(obj: object = null) {
        if(obj != null) {
            this.parse(obj);
        }
        var today = new Date();
        var dd = String(today.getDate()).padStart(2, '0');
        var mm = String(today.getMonth() + 1).padStart(2, '0');
        var yyyy = today.getFullYear();
        this.id = Guid.create();
        this.date = dd+"."+mm+"."+yyyy;

    }

}