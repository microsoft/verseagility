"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var Status;
(function (Status) {
    Status["SUCCESS"] = "success";
    Status["BADREQUEST"] = "error";
})(Status = exports.Status || (exports.Status = {}));
class HttpResponse {
    constructor(status = Status.SUCCESS, message = "", values = null, headers = { "Content-Type": "application/json" }) {
        this.status = status;
        this.message = message;
        this.values = values;
        this.headers = headers;
    }
    create() {
        var httpstatus;
        if (this.status == Status.SUCCESS) {
            httpstatus = 200;
        }
        else if (this.status == Status.BADREQUEST) {
            httpstatus = 400;
        }
        return {
            status: httpstatus,
            body: { status: this.status, message: this.message, values: this.values },
            headers: this.headers
        };
    }
}
exports.HttpResponse = HttpResponse;
//# sourceMappingURL=index.js.map