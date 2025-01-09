import * as jsdom from 'jsdom';
const { JSDOM } = jsdom;

function evaluateCode(code) {
    try {
        const dom = new JSDOM(`<!DOCTYPE html><body></body>`, {
            runScripts: "outside-only"
        });
        dom.window.ctx = {};
        dom.window.ctx.api = {};
        dom.window.ctx.d_headers = new Map();
        dom.window.ctx.api.setHeaders = function(entries) {
            for (const [W, U] of Object.entries(entries)) {
                dom.window.ctx.d_headers.set(W, U);
            }
        };
        var chrStub = dom.window.document.createElement("div");
        chrStub.id = "_chr_";
        dom.window.document.body.appendChild(chrStub);
        dom.window.eval(code);
        const cacheId = dom.window.ctx.d_headers.get('Cache-Id');

        return {
            result: dom.window.eval(code),
            cacheId: cacheId
        };
    } catch (e) {
        console.error("Evaluation error:", e);
        return null;
    }
}

const code = process.argv[2];
const evalResult = evaluateCode(code);
if (evalResult) {
    console.log(evalResult.result);
    if (evalResult.cacheId) {
        console.log("Cache-Id:", evalResult.cacheId);
    }
}
