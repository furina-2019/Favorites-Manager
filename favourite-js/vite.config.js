var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
/**
 * Dev-only CORS-free fetch proxy.
 *
 * Browsers cannot read cross-origin pages/APIs (Bilibili sends no
 * Access-Control-Allow-Origin and blocks most public CORS proxies), so the
 * cover extractor routes network fetches through this same-origin endpoint:
 * the dev server (Node) does the actual request with browser-like headers -
 * exactly what a local Python requests + BeautifulSoup script would do - and
 * returns the raw body. The browser only ever talks to localhost.
 */
function coverProxyPlugin() {
    return {
        name: 'cover-proxy',
        configureServer: function (server) {
            var _this = this;
            server.middlewares.use('/__cover', function (req, res, next) { return __awaiter(_this, void 0, void 0, function () {
                var raw, target, headers, controller_1, timer, upstream, length_1, text, err_1;
                return __generator(this, function (_a) {
                    switch (_a.label) {
                        case 0:
                            _a.trys.push([0, 6, , 7]);
                            raw = new URL(req.url || '/', 'http://localhost').searchParams.get('url');
                            if (!raw) {
                                res.statusCode = 400;
                                res.end('missing url');
                                return [2 /*return*/];
                            }
                            target = new URL(raw);
                            if (target.protocol !== 'http:' && target.protocol !== 'https:') {
                                res.statusCode = 400;
                                res.end('unsupported protocol');
                                return [2 /*return*/];
                            }
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                                Accept: 'text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8',
                                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                            };
                            if (target.hostname.endsWith('bilibili.com')) {
                                headers.Referer = 'https://www.bilibili.com/';
                            }
                            controller_1 = new AbortController();
                            timer = setTimeout(function () { return controller_1.abort(); }, 8000);
                            upstream = void 0;
                            _a.label = 1;
                        case 1:
                            _a.trys.push([1, , 3, 4]);
                            return [4 /*yield*/, fetch(target.href, { headers: headers, signal: controller_1.signal, redirect: 'follow' })];
                        case 2:
                            upstream = _a.sent();
                            return [3 /*break*/, 4];
                        case 3:
                            clearTimeout(timer);
                            return [7 /*endfinally*/];
                        case 4:
                            length_1 = Number(upstream.headers.get('content-length') || 0);
                            if (length_1 > 3 * 1024 * 1024) {
                                res.statusCode = 413;
                                res.end('body too large');
                                return [2 /*return*/];
                            }
                            return [4 /*yield*/, upstream.text()];
                        case 5:
                            text = _a.sent();
                            if (text.length > 3 * 1024 * 1024) {
                                res.statusCode = 413;
                                res.end('body too large');
                                return [2 /*return*/];
                            }
                            if (text.length === 0) {
                                res.statusCode = 502;
                                res.end('empty body');
                                return [2 /*return*/];
                            }
                            res.statusCode = 200;
                            res.setHeader('Content-Type', upstream.headers.get('content-type') || 'text/plain');
                            res.end(text);
                            return [3 /*break*/, 7];
                        case 6:
                            err_1 = _a.sent();
                            // Never let a proxy failure take down the dev server.
                            res.statusCode = 502;
                            res.end(err_1 instanceof Error ? err_1.message : 'proxy failed');
                            return [3 /*break*/, 7];
                        case 7: return [2 /*return*/];
                    }
                });
            }); });
        },
    };
}
export default defineConfig({
    plugins: [react(), coverProxyPlugin()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
    optimizeDeps: {
        exclude: ['sql.js'],
    },
    // For sql.js WASM file handling
    worker: {
        format: 'es',
    },
});
