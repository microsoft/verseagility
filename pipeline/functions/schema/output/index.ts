export enum Status {
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
    public status: Status = null;
    public label: Label = new Label();
}