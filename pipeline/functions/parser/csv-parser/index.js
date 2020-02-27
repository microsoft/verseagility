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
const guid_1 = require("../../common/guid");
const csv = require('csvtojson');
class CSVParser {
    constructor(file) {
        this.fileBuffer = file;
    }
    parse() {
        return __awaiter(this, void 0, void 0, function* () {
            return new Promise((resolve, reject) => __awaiter(this, void 0, void 0, function* () {
                var content = this.fileBuffer.toString();
                var rows = yield csv({ noheader: false, output: "csv" }).fromString(content);
                var outputs = [];
                rows.forEach(row => {
                    var output = new output_1.OutputSchema();
                    output.id = row[0];
                    output.views = row[1];
                    output.url = row[3];
                    output.language = row[4];
                    output.subject = row[5];
                    output.from = row[6];
                    output.date = row[7];
                    output.body = row[8];
                    output.upvotes = row[9];
                    var answer = new output_1.Answer();
                    answer.body = row[12];
                    answer.date = row[11];
                    answer.upvotes = row[13];
                    output.label.answer.push(answer);
                    // If object doesn't have an Id, create one
                    if (output.id == null) {
                        output.id = guid_1.Guid.create();
                    }
                    outputs.push(output);
                });
                resolve(outputs);
            }));
        });
    }
}
exports.CSVParser = CSVParser;
//# sourceMappingURL=index.js.map