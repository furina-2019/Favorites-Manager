// Small cover-extraction backend.
//
// Browsers cannot read cross-origin pages/APIs (Bilibili sends no
// Access-Control-Allow-Origin and blocks most public CORS proxies), so this
// tiny local server does the fetch in Node - with browser-like headers and a
// Bilibili Referer, exactly like a local Python requests script - and returns
// the raw body to the frontend with permissive CORS headers.
//
// Run: npm run server   (listens on http://localhost:3100)
//
// Endpoints:
//   GET /api/cover?url=<encoded target>  -> raw body of the target page/API
//   GET /api/bilibili-cover?url=<encoded video url> -> extracted cover URL
//   GET /api/debug?url=<encoded target>  -> diagnostic info (status, first bytes)

import http from 'node:http'
import { URL } from 'node:url'

const PORT = Number(process.env.COVER_PORT || 3100)
const MAX_BODY = 3 * 1024 * 1024 // 3MB
const TIMEOUT_MS = 8000

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
}

function send(res, status, body, headers = {}) {
  res.writeHead(status, { ...CORS_HEADERS, ...headers })
  res.end(body)
}

// Realistic browser fingerprint; Bilibili's risk control rejects bare undici.
const BROWSER_HEADERS = {
  'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
  Accept: 'text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8',
  'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
  'Accept-Encoding': 'gzip, deflate, br',
  Connection: 'keep-alive',
  'Upgrade-Insecure-Requests': '1',
  'Sec-Fetch-Dest': 'document',
  'Sec-Fetch-Mode': 'navigate',
  'Sec-Fetch-Site': 'same-origin',
  'Sec-Fetch-User': '?1',
  'Sec-Ch-Ua': '"Chromium";v="126", "Not.A/Brand";v="8", "Google Chrome";v="126"',
  'Sec-Ch-Ua-Mobile': '?0',
  'Sec-Ch-Ua-Platform': '"Windows"',
}

async function fetchBody(url, { referer } = {}) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  try {
    const headers = { ...BROWSER_HEADERS }
    if (referer) headers.Referer = referer
    else if (new URL(url).hostname.endsWith('bilibili.com')) headers.Referer = 'https://www.bilibili.com/'
    const upstream = await fetch(url, { headers, signal: controller.signal, redirect: 'follow' })
    const length = Number(upstream.headers.get('content-length') || 0)
    if (length > MAX_BODY) throw new Error('body too large')
    const text = await upstream.text()
    if (text.length > MAX_BODY) throw new Error('body too large')
    return { status: upstream.status, contentType: upstream.headers.get('content-type') || '', text }
  } finally {
    clearTimeout(timer)
  }
}

function toHttps(url) {
  return typeof url === 'string' ? url.replace(/^http:/i, 'https:') : ''
}

/** Extract the cover URL from Bilibili video page HTML (og:image / __INITIAL_STATE__). */
function extractBiliPageCover(html) {
  // og:image meta
  const metaPatterns = [
    /<meta[^>]+property=["']og:image["'][^>]+content=["']([^"']+)["']/i,
    /<meta[^>]+content=["']([^"']+)["'][^>]+property=["']og:image["']/i,
    /<meta[^>]+name=["']twitter:image["'][^>]+content=["']([^"']+)["']/i,
    /<meta[^>]+content=["']([^"']+)["'][^>]+name=["']twitter:image["']/i,
  ]
  for (const p of metaPatterns) {
    const m = html.match(p)
    if (m && m[1] && !m[1].startsWith('data:')) return m[1]
  }
  // __INITIAL_STATE__ embeds "pic":"https://..."
  const pic = html.match(/"pic":"([^"]+)"/)
  if (pic && pic[1]) return pic[1]
  // also try escaped quotes variant
  const picEsc = html.match(/\\"pic\\":\\"([^\\"]+)\\/)
  if (picEsc && picEsc[1]) return picEsc[1]
  return ''
}

function getBvid(input) {
  const m = input.match(/BV[0-9A-Za-z]{10}/)
  return m ? m[0] : ''
}

/** Try the official API first, then the video page, then the player API. */
async function extractBilibiliCover(videoUrl) {
  const bvid = getBvid(videoUrl)
  if (!bvid) throw new Error('no bvid in url')

  // 1) official API
  try {
    const api = await fetchBody(`https://api.bilibili.com/x/web-interface/view?bvid=${bvid}`, {
      referer: 'https://www.bilibili.com/',
    })
    if (api.status === 200 && api.text) {
      let j = null
      try {
        j = JSON.parse(api.text)
      } catch {
        j = null
      }
      if (j && j.code === 0 && typeof j.data?.pic === 'string' && j.data.pic) {
        return toHttps(j.data.pic)
      }
      // some responses nest differently; try first_frame too
      if (j && j.code === 0 && typeof j.data?.pages?.[0]?.first_frame === 'string' && j.data.pages[0].first_frame) {
        return toHttps(j.data.pages[0].first_frame)
      }
    }
  } catch {
    // fall through
  }

  // 2) video page HTML
  try {
    const page = await fetchBody(videoUrl, { referer: 'https://www.bilibili.com/' })
    if (page.status === 200 && page.text) {
      const cover = extractBiliPageCover(page.text)
      if (cover) return toHttps(cover)
    }
  } catch {
    // fall through
  }

  // 3) player API (less strict)
  try {
    const api2 = await fetchBody(`https://api.bilibili.com/x/player/pic?bvid=${bvid}`, {
      referer: `https://www.bilibili.com/video/${bvid}`,
    })
    if (api2.status === 200 && api2.text) {
      let j = null
      try {
        j = JSON.parse(api2.text)
      } catch {
        j = null
      }
      if (j && j.code === 0 && typeof j.data === 'string' && j.data) {
        return toHttps(j.data)
      }
    }
  } catch {
    // ignore
  }

  throw new Error('no cover found for bilibili link (API and page both blocked)')
}

const server = http.createServer((req, res) => {
  const reqUrl = new URL(req.url || '/', `http://localhost:${PORT}`)

  // CORS preflight
  if (req.method === 'OPTIONS') {
    send(res, 204, '')
    return
  }

  if (req.method !== 'GET') {
    send(res, 405, 'method not allowed')
    return
  }

  // Debug endpoint: show what the target actually returns (status + first bytes)
  if (reqUrl.pathname === '/api/debug') {
    const raw = reqUrl.searchParams.get('url')
    if (!raw) {
      send(res, 400, 'missing url')
      return
    }
    fetchBody(raw)
      .then(({ status, contentType, text }) => {
        send(res, 200, JSON.stringify({ status, contentType, preview: text.slice(0, 500) }))
      })
      .catch((err) => {
        send(res, 502, JSON.stringify({ error: err instanceof Error ? err.message : 'failed' }))
      })
    return
  }

  // Bilibili cover extraction (server-side)
  if (reqUrl.pathname === '/api/bilibili-cover') {
    const raw = reqUrl.searchParams.get('url')
    if (!raw) {
      send(res, 400, 'missing url')
      return
    }
    extractBilibiliCover(raw)
      .then((cover) => send(res, 200, JSON.stringify({ cover })))
      .catch((err) => send(res, 502, JSON.stringify({ error: err instanceof Error ? err.message : 'failed' })))
    return
  }

  // Image proxy: fetch the image server-side (bypasses CDN hotlink protection)
  // and stream it back to the browser.
  if (reqUrl.pathname === '/api/cover-img') {
    const raw = reqUrl.searchParams.get('url')
    if (!raw) {
      send(res, 400, 'missing url')
      return
    }
    let target
    try {
      target = new URL(raw)
    } catch {
      send(res, 400, 'invalid url')
      return
    }
    if (target.protocol !== 'http:' && target.protocol !== 'https:') {
      send(res, 400, 'unsupported protocol')
      return
    }
    const headers = { ...BROWSER_HEADERS }
    if (target.hostname.endsWith('hdslb.com') || target.hostname.endsWith('bilibili.com')) {
      headers.Referer = 'https://www.bilibili.com/'
    }
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
    fetch(target.href, { headers, signal: controller.signal, redirect: 'follow' })
      .then(async (upstream) => {
        if (!upstream.ok) throw new Error(`upstream HTTP ${upstream.status}`)
        const buf = Buffer.from(await upstream.arrayBuffer())
        if (buf.length > MAX_BODY) throw new Error('image too large')
        send(res, 200, buf, {
          'Content-Type': upstream.headers.get('content-type') || 'image/jpeg',
          'Cache-Control': 'public, max-age=86400',
        })
      })
      .catch((err) => {
        const message = err instanceof Error ? err.message : 'image proxy failed'
        send(res, 502, message)
      })
      .finally(() => clearTimeout(timer))
    return
  }

  // Generic fetch proxy
  if (reqUrl.pathname === '/api/cover') {
    const raw = reqUrl.searchParams.get('url')
    if (!raw) {
      send(res, 400, 'missing url')
      return
    }
    fetchBody(raw)
      .then(({ status, contentType, text }) => {
        console.log(`[cover-server] ${status} ${raw.slice(0, 120)} (${text.length} bytes, ${contentType})`)
        send(res, status, text, { 'Content-Type': contentType || 'text/plain' })
      })
      .catch((err) => {
        const message = err instanceof Error ? err.message : 'proxy failed'
        send(res, 502, message)
      })
    return
  }

  send(res, 404, 'not found')
})

server.listen(PORT, '0.0.0.0', () => {
  console.log(`[cover-server] listening on http://localhost:${PORT}`)
  console.log('[cover-server] try: http://localhost:' + PORT + '/api/bilibili-cover?url=' + encodeURIComponent('https://www.bilibili.com/video/BV1ykKN66EsZ'))
})

// Clean shutdown on Ctrl+C
for (const sig of ['SIGINT', 'SIGTERM']) {
  process.on(sig, () => {
    server.close(() => process.exit(0))
  })
}
