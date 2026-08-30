// Cloudflare Pages Function — /api/cover-img?url=<encoded image url>
// Proxies images with caching to bypass CORS/hotlink restrictions.

import { BROWSER_HEADERS, TIMEOUT_MS, MAX_BODY } from '../coverExtract.js'
import { imageCache } from '../rateLimit.js'

export const onRequest: PagesFunction = async (context) => {
  // Handle CORS preflight
  if (context.request.method === 'OPTIONS') {
    return new Response(null, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '86400',
      },
    })
  }

  const url = new URL(context.request.url)
  const raw = url.searchParams.get('url')
  if (!raw) return new Response('missing url', { status: 400 })

  let target: URL
  try { target = new URL(raw) } catch { return new Response('invalid url', { status: 400 }) }
  if (target.protocol !== 'http:' && target.protocol !== 'https:') {
    return new Response('unsupported protocol', { status: 400 })
  }

  // Check cache
  const cached = imageCache.get(raw)
  if (cached) {
    return new Response(cached, {
      headers: {
        'Content-Type': 'image/jpeg',
        'Cache-Control': 'public, max-age=86400',
        'Access-Control-Allow-Origin': '*',
      },
    })
  }

  const headers: Record<string, string> = { ...BROWSER_HEADERS }
  if (target.hostname.endsWith('hdslb.com') || target.hostname.endsWith('bilibili.com')) {
    headers.Referer = 'https://www.bilibili.com/'
  }

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  try {
    const upstream = await fetch(target.href, {
      headers,
      signal: controller.signal,
      redirect: 'follow',
    })
    if (!upstream.ok) {
      return new Response('upstream ' + upstream.status, { status: upstream.status })
    }

    const buf = new Uint8Array(await upstream.arrayBuffer())
    if (buf.length > MAX_BODY) {
      return new Response('image too large', { status: 413 })
    }

    // Cache the image
    imageCache.set(raw, buf)

    return new Response(buf, {
      headers: {
        'Content-Type': upstream.headers.get('content-type') || 'image/jpeg',
        'Cache-Control': 'public, max-age=86400',
        'Access-Control-Allow-Origin': '*',
      },
    })
  } catch (err) {
    return new Response(err instanceof Error ? err.message : 'image proxy failed', { status: 502 })
  } finally {
    clearTimeout(timer)
  }
}
