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
const output_1 = require("../../schema/output");
class JsonParser {
    constructor(file) {
        this.fileBuffer = file;
    }
    parse() {
        return __awaiter(this, void 0, void 0, function* () {
            return new Promise((resolve, reject) => {
                var content = this.fileBuffer.toString();
                var objs = JSON.parse(content);
                var outputs = [];
                try {
                    objs.forEach(obj => {
                        var output = new output_1.OutputSchema();
                        var answer = new output_1.Answer();
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
                }
                catch (err) {
                    reject("Wrong input format: " + err);
                }
                resolve(outputs);
            });
        });
    }
}
exports.JsonParser = JsonParser;
//# sourceMappingURL=index.js.map