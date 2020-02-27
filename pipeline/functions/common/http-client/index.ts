import * as request from "superagent";
import * as url from 'url';

export class HttpClient {

    public static getInstance() {
        return HttpClient.instance;
    }

    private static instance: HttpClient = new HttpClient();

    constructor() {
        if (HttpClient.instance) {
            throw new Error('Error: Instantiation failed: Use HttpClient.getInstance() instead of new.');
        }
        HttpClient.instance = this;
    }

    /**
     * @param {string} endpoint
     * @returns {Promise<any>}
     */
    public async get(endpoint: string): Promise<any> {

        var urlObj = {
            host: endpoint,
        };
          
        const response = await request.get(url.format(urlObj));
        return response;

    }

    /**
     * @param {string} endpoint
     * @param {any} payload
     * @returns {Promise<any>}
     */
    public async post(endpoint: string, payload: any): Promise<any> {

        var urlObj = {
            host: endpoint,
        };
          
        const response = request
            .post(url.format(urlObj))
            .send(payload)
            .set('Accept', 'application/json')

        return response;

    }

}