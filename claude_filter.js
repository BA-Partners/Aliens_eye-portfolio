const http = require('http');

const PORT = 9001;
const TARGET_PORT = 8999;

const server = http.createServer((req, res) => {
    // 1. 新增：拦截 Claude Code 的模型列表和前置可用性探测，直接在本地返回成功，拒绝透传引发报错
    if (req.url.includes('/models') || req.url.includes('/model')) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            object: "list",
            data: [
                { id: "claude-3-5-sonnet-20241022", object: "model", created: 1729555200, owned_by: "anthropic" },
                { id: "claude-3-5-sonnet", object: "model", created: 1729555200, owned_by: "anthropic" }
            ]
        }));
        return;
    }

    let body = [];
    req.on('data', (chunk) => body.push(chunk));
    req.on('end', () => {
        body = Buffer.concat(body);

        // 2. 拦截并重写主交易 POST 请求中的模型字段
        if (req.method === 'POST' && req.headers['content-type']?.includes('application/json')) {
            try {
                let json = JSON.parse(body.toString());
                if (json.model) {
                    // 强制改写为 Nous Portal 中您实际拥有免费额度的可用通道模型
                    json.model = "stepfun/step-3.7-flash:free";
                }
                body = Buffer.from(JSON.stringify(json));
                req.headers['content-length'] = body.length;
            } catch (e) {}
        }

        // 3. 转发经过处理的安全请求给 8999 端口的 Hermes
        const proxyReq = http.request({
            host: '127.0.0.1',
            port: TARGET_PORT,
            path: req.url,
            method: req.method,
            headers: req.headers
        }, (proxyRes) => {
            res.writeHead(proxyRes.statusCode, proxyRes.headers);
            proxyRes.pipe(res);
        });

        proxyReq.on('error', (err) => {
            res.writeHead(500);
            res.end("Gateway Error");
        });

        proxyReq.write(body);
        proxyReq.end();
    });
});

server.listen(PORT, () => {
    console.log(`🚀 升级版探测拦截转换网关已启动，监听端口: ${PORT}`);
});
