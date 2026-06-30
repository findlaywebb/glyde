// HTTPS-over-LAN front door: wrap adapter-node's request handler in a `node:https` server.
//
// An installable / offline PWA needs a *secure context*, which a plain-HTTP LAN origin is not
// (only `https://…` and `localhost` qualify). `serve_lan` (backend) spawns this script instead
// of `build/index.js` when `lan_https` is configured, passing the mkcert cert/key paths and the
// `https://…` ORIGIN. The adapter-node `handler` derives `event.url.origin` from that ORIGIN, so
// the same-origin proxy + CSRF guard in `hooks.server.ts` keep working unchanged over TLS.
//
// HTTPS is the first thing to degrade within LAN (HTTPS → plain-HTTP LAN → localhost): if the
// cert/key are missing this exits non-zero and `serve_lan` surfaces the failure.

import { readFileSync } from 'node:fs';
import { createServer } from 'node:https';
import process from 'node:process';
import { handler } from './build/handler.js';

const host = process.env.HOST ?? '0.0.0.0';
const port = Number(process.env.PORT ?? 3000);
const certPath = process.env.GLYDE_LAN_CERT_PATH;
const keyPath = process.env.GLYDE_LAN_KEY_PATH;

if (!certPath || !keyPath) {
	console.error('serve-lan-https: GLYDE_LAN_CERT_PATH and GLYDE_LAN_KEY_PATH are required');
	process.exit(1);
}

// adapter-node's `handler` is connect-style middleware; supply a terminal `next` that 404s for
// the rare request it does not handle itself, so the server never hangs on an unhandled route.
const server = createServer(
	{ cert: readFileSync(certPath), key: readFileSync(keyPath) },
	(req, res) =>
		handler(req, res, () => {
			res.statusCode = 404;
			res.end('Not Found');
		})
);

server.listen(port, host, () => {
	console.log(`Glyde HTTPS LAN door listening on https://${host}:${port}`);
});

for (const signal of ['SIGINT', 'SIGTERM']) {
	process.on(signal, () => server.close(() => process.exit(0)));
}
