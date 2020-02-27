"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var Status;
(function (Status) {
    Status["train"] = "train";
    Status["score"] = "score";
    Status["corrected"] = "corrected";
})(Status = exports.Status || (exports.Status = {}));
class Answer {
    constructor() {
        this.rank = null;
        this.body = null;
        this.upvotes = null;
        this.date = null;
        this.markedAsAnswer = null;
    }
}
exports.Answer = Answer;
class Version {
    constructor() {
        this.value = null;
        this.confidence = null;
        this.author = null;
        this.date = null;
    }
}
exports.Version = Version;
class Classification {
    constructor() {
        this.task_type = null;
        this.version = [];
    }
}
exports.Classification = Classification;
class Label {
    constructor() {
        this.classification = [];
        this.answer = [];
    }
}
exports.Label = Label;
class Attachment {
    constructor() {
        this.link = null;
        this.pages = [];
        this.filename = null;
        this.filetype = null;
        this.text = null;
        this.content = [];
    }
}
exports.Attachment = Attachment;
class OutputSchema {
    constructor() {
        this.id = null;
        this.from = null;
        this.date = null;
        this.subject = null;
        this.body = null;
        this.attachment = [];
        this.upvotes = null;
        this.views = null;
        this.url = null;
        this.language = null;
        this.status = null;
        this.label = new Label();
    }
}
exports.OutputSchema = OutputSchema;
//# sourceMappingURL=index.js.map