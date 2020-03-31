"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const guid_1 = require("../../common/guid");
var DocumentStatus;
(function (DocumentStatus) {
    DocumentStatus["train"] = "train";
    DocumentStatus["score"] = "score";
    DocumentStatus["corrected"] = "corrected";
})(DocumentStatus = exports.DocumentStatus || (exports.DocumentStatus = {}));
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
    constructor(obj = null) {
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
        if (obj != null) {
            this.parse(obj);
        }
        var today = new Date();
        var dd = String(today.getDate()).padStart(2, '0');
        var mm = String(today.getMonth() + 1).padStart(2, '0');
        var yyyy = today.getFullYear();
        this.id = guid_1.Guid.create();
        this.date = dd + "." + mm + "." + yyyy;
    }
    parse(o) {
        Object.keys(o).forEach((k) => {
            if (o[k] !== null && typeof o[k] === 'object') {
                this.parse(o[k]);
                return;
            }
            if (typeof o[k] === 'string') {
                o[k] = o[k].replace(/'/g, "''");
                var key = k;
                var value = o[k];
                if (key == "id") {
                    this.id = value;
                }
                if (key == "from") {
                    this.from = value;
                }
                if (key == "date") {
                    this.date = value;
                }
                if (key == "subject") {
                    this.subject = value;
                }
                if (key == "body") {
                    this.body = value;
                }
                if (key == "upvotes") {
                    this.upvotes = value;
                }
                if (key == "views") {
                    this.views = value;
                }
                if (key == "url") {
                    this.url = value;
                }
                if (key == "language") {
                    this.language = value;
                }
                if (key == "status") {
                    this.status = value;
                }
            }
        });
    }
}
exports.OutputSchema = OutputSchema;
//# sourceMappingURL=index.js.map