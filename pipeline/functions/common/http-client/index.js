"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : new P(function (resolve) { resolve(result.value); }).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
const request = __importStar(require("superagent"));
const url = __importStar(require("url"));
class HttpClient {
    constructor() {
        if (HttpClient.instance) {
            throw new Error('Error: Instantiation failed: Use HttpClient.getInstance() instead of new.');
        }
        HttpClient.instance = this;
    }
    static getInstance() {
        return HttpClient.instance;
    }
    /**
     * @param {string} endpoint
     * @returns {Promise<any>}
     */
    get(endpoint) {
        return __awaiter(this, void 0, void 0, function* () {
            var urlObj = {
                host: endpoint,
            };
            const response = yield request.get(url.format(urlObj));
            return response;
        });
    }
    /**
     * @param {string} endpoint
     * @param {any} payload
     * @returns {Promise<any>}
     */
    post(endpoint, payload) {
        return __awaiter(this, void 0, void 0, function* () {
            var urlObj = {
                host: endpoint,
            };
            const response = request
                .post(url.format(urlObj))
                .send(payload)
                .set('Accept', 'application/json');
            return response;
        });
    }
}
HttpClient.instance = new HttpClient();
exports.HttpClient = HttpClient;
//# sourceMappingURL=index.js.map