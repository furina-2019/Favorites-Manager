import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

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
function coverProxyPlugin(): Plugin {
  return {
    name: 'cover-proxy',
    configureServer(server) {
      server.middlewares.use('/__cover', async (req, res, next) => {
        try {
          const raw = new URL(req.url || '/', 'http://localhost').searchParams.get('url')
          if (!raw) {
            res.statusCode = 400
            res.end('missing url')
            return
          }
          const target = new URL(raw)
          if (target.protocol !== 'http:' && target.protocol !== 'https:') {
            res.statusCode = 400
            res.end('unsupported protocol')
            return
          }

          // Browser-like headers; Bilibili serves its API/page to these.
          const headers: Record<string, string> = {
            'User-Agent':
              'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            Accept: 'text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
          }
          if (target.hostname.endsWith('bilibili.com')) {
            headers.Referer = 'https://www.bilibili.com/'
          }

          const controller = new AbortController()
          const timer = setTimeout(() => controller.abort(), 8000)
          let upstream: Response
          try {
            upstream = await fetch(target.href, { headers, signal: controller.signal, redirect: 'follow' })
          } finally {
            clearTimeout(timer)
          }

          const length = Number(upstream.headers.get('content-length') || 0)
          if (length > 3 * 1024 * 1024) {
            res.statusCode = 413
            res.end('body too large')
            return
          }
          const text = await upstream.text()
          if (text.length > 3 * 1024 * 1024) {
            res.statusCode = 413
            res.end('body too large')
            return
          }
          if (text.length === 0) {
            res.statusCode = 502
            res.end('empty body')
            return
          }

          res.statusCode = 200
          res.setHeader('Content-Type', upstream.headers.get('content-type') || 'text/plain')
          res.end(text)
        } catch (err) {
          // Never let a proxy failure take down the dev server.
          res.statusCode = 502
          res.end(err instanceof Error ? err.message : 'proxy failed')
        }
      })
    },
  }
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
})
