"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
class Time {
    static sleep(milliseconds) {
        return new Promise(resolve => setTimeout(resolve, milliseconds));
    }
}
exports.Time = Time;
//# sourceMappingURL=index.js.map