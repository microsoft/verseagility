export enum Status {
    SUCCESS = "success",
    BADREQUEST = "error"
}

export class HttpResponse {
    private status: Status;
    private message: string;
    private values: any;
    private headers: any;

    public constructor(status: Status = Status.SUCCESS, message: string = "", values: any = null, headers: object = { "Content-Type": "application/json", "X-own": "1" }) {
        this.status = status;
        this.message = message;
        this.values = values;
        this.headers = headers;
    }

    public create() {

        var httpstatus;
        if(this.status == Status.SUCCESS) {
            httpstatus = 200;
        } else if(this.status == Status.BADREQUEST) {
            httpstatus = 400;
        }

        return {
            status: httpstatus,
            body: { status: this.status, message: this.message, values: this.values },
            headers: this.headers
        }
    }

}