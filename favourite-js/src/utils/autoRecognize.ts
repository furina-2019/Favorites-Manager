// Auto-recognition utility for extracting metadata from URLs and files.
//
// Title/category recognition is purely local and offline: it derives a title
// and a category from the pasted text/link without any network request.
//
// The ONLY network path is cover extraction (extractCoverFromUrl below): it
// fetches the remote page HTML and parses <meta> tags (og:image etc.) the same
// way a Python requests + BeautifulSoup script would, via a chain of public
// CORS proxies tried in parallel. Nothing else uses the network.

// Common file type mappings to categories
const FILE_TYPE_CATEGORIES: Record<string, string> = {
  // Documents
  '.pdf': 'Document',
  '.doc': 'Document',
  '.docx': 'Document',
  '.txt': 'Document',
  '.md': 'Document',
  '.rtf': 'Document',

  // Spreadsheets
  '.xls': 'Document',
  '.xlsx': 'Document',
  '.csv': 'Document',

  // Presentations
  '.ppt': 'Document',
  '.pptx': 'Document',

  // Images
  '.jpg': 'Image',
  '.jpeg': 'Image',
  '.png': 'Image',
  '.gif': 'Image',
  '.bmp': 'Image',
  '.svg': 'Image',
  '.webp': 'Image',
  '.ico': 'Image',
  '.tiff': 'Image',
  '.tif': 'Image',
  '.psd': 'Design',
  '.ai': 'Design',
  '.sketch': 'Design',
  '.fig': 'Design',
  '.xd': 'Design',

  // Audio
  '.mp3': 'Music',
  '.wav': 'Music',
  '.flac': 'Music',
  '.aac': 'Music',
  '.ogg': 'Music',
  '.wma': 'Music',
  '.m4a': 'Music',
  '.opus': 'Music',

  // Video
  '.mp4': 'Video',
  '.avi': 'Video',
  '.mkv': 'Video',
  '.mov': 'Video',
  '.wmv': 'Video',
  '.flv': 'Video',
  '.webm': 'Video',
  '.m4v': 'Video',
  '.mpg': 'Video',
  '.mpeg': 'Video',
  '.3gp': 'Video',
  '.mts': 'Video',

  // Archives
  '.zip': 'Software',
  '.rar': 'Software',
  '.7z': 'Software',
  '.tar': 'Software',
  '.gz': 'Software',
  '.bz2': 'Software',
  '.xz': 'Software',
  '.iso': 'Software',

  // Code
  '.js': 'Programming',
  '.ts': 'Programming',
  '.html': 'Programming',
  '.css': 'Programming',
  '.py': 'Programming',
  '.java': 'Programming',
  '.cpp': 'Programming',
  '.c': 'Programming',
  '.php': 'Programming',
  '.rb': 'Programming',
  '.go': 'Programming',
  '.rs': 'Programming',
  '.swift': 'Programming',
  '.kt': 'Programming',
  '.scala': 'Programming',
  '.r': 'Programming',
  '.m': 'Programming',
  '.h': 'Programming',
  '.hpp': 'Programming',
  '.cs': 'Programming',
  '.vb': 'Programming',
  '.lua': 'Programming',
  '.pl': 'Programming',
  '.sh': 'Programming',
  '.bat': 'Programming',
  '.ps1': 'Programming',
  '.sql': 'Programming',
  '.json': 'Programming',
  '.xml': 'Programming',
  '.yaml': 'Programming',
  '.yml': 'Programming',
  '.toml': 'Programming',
  '.ini': 'Programming',
  '.cfg': 'Programming',
  '.conf': 'Programming',
  '.vue': 'Programming',
  '.jsx': 'Programming',
  '.tsx': 'Programming',
  '.scss': 'Programming',
  '.sass': 'Programming',
  '.less': 'Programming',
  '.dart': 'Programming',
  '.zig': 'Programming',
  '.nim': 'Programming',
  '.cr': 'Programming',
  '.ex': 'Programming',
  '.erl': 'Programming',
  '.hs': 'Programming',
  '.ml': 'Programming',
  '.clj': 'Programming',
  '.lisp': 'Programming',
  '.el': 'Programming',
  '.rkt': 'Programming',

  // E-books & reading
  '.epub': 'Reading',
  '.mobi': 'Reading',
  '.azw': 'Reading',
  '.azw3': 'Reading',
  '.fb2': 'Reading',
  '.djvu': 'Reading',

  // Games
  '.unity': 'Game',
  '.godot': 'Game',
  '.rpgproject': 'Game',
  '.sav': 'Game',
  '.gam': 'Game',
  '.rgssad': 'Game',

  // 3D & modeling
  '.obj': 'Design',
  '.fbx': 'Design',
  '.blend': 'Design',
  '.stl': 'Design',
  '.gltf': 'Design',
  '.glb': 'Design',
  '.3ds': 'Design',
  '.dae': 'Design',
  '.dwg': 'Design',
  '.dxf': 'Design',

  // Default
  '': 'Other'
};

// Known site categories based on domain patterns
const SITE_CATEGORIES: Record<string, string> = {
  // Social Media
  'facebook.com': 'Social',
  'twitter.com': 'Social',
  'x.com': 'Social',
  'instagram.com': 'Social',
  'linkedin.com': 'Social',
  'tiktok.com': 'Social',
  'pinterest.com': 'Social',
  'reddit.com': 'Social',
  'snapchat.com': 'Social',
  'telegram.org': 'Social',
  't.me': 'Social',
  'whatsapp.com': 'Social',
  'line.me': 'Social',
  'discord.com': 'Social',
  'threads.net': 'Social',
  'mastodon.social': 'Social',
  'bsky.app': 'Social',

  // Video
  'youtube.com': 'Video',
  'youtu.be': 'Video',
  'vimeo.com': 'Video',
  'twitch.tv': 'Video',
  'dailymotion.com': 'Video',
  'douyin.com': 'Video',
  'v.qq.com': 'Video',
  'mgtv.com': 'Video',
  'acfun.cn': 'Video',
  'nicovideo.jp': 'Video',
  'crunchyroll.com': 'Video',
  'hulu.com': 'Video',
  'hbomax.com': 'Video',
  'netflix.com': 'Video',
  'disneyplus.com': 'Video',
  'primevideo.com': 'Video',
  'apple.com': 'Video',
  'peacocktv.com': 'Video',
  'paramountplus.com': 'Video',

  // Music
  'spotify.com': 'Music',
  'soundcloud.com': 'Music',
  'bandcamp.com': 'Music',
  'music.163.com': 'Music',
  'music.apple.com': 'Music',
  'music.amazon.com': 'Music',
  'deezer.com': 'Music',
  'tidal.com': 'Music',
  'pandora.com': 'Music',
  'last.fm': 'Music',
  'genius.com': 'Music',

  // News
  'cnn.com': 'News',
  'bbc.com': 'News',
  'nytimes.com': 'News',
  'theguardian.com': 'News',
  'reuters.com': 'News',
  'apnews.com': 'News',
  'washingtonpost.com': 'News',
  'bloomberg.com': 'News',
  'wsj.com': 'News',
  'economist.com': 'News',
  'nature.com': 'News',
  'sciencemag.org': 'News',
  'arstechnica.com': 'News',
  'theverge.com': 'News',
  'wired.com': 'News',
  'engadget.com': 'News',
  'techcrunch.com': 'News',
  'mashable.com': 'News',

  // Shopping
  'amazon.com': 'Shopping',
  'ebay.com': 'Shopping',
  'shopify.com': 'Shopping',
  'etsy.com': 'Shopping',
  'walmart.com': 'Shopping',
  'target.com': 'Shopping',
  'bestbuy.com': 'Shopping',
  'aliexpress.com': 'Shopping',
  'wish.com': 'Shopping',
  'newegg.com': 'Shopping',
  'ikea.com': 'Shopping',
  'homedepot.com': 'Shopping',
  'lowes.com': 'Shopping',
  'macys.com': 'Shopping',

  // Development
  'github.com': 'Programming',
  'gitlab.com': 'Programming',
  'stackoverflow.com': 'Programming',
  'npmjs.com': 'Programming',
  'dev.to': 'Programming',
  'medium.com': 'Programming',
  'hashnode.dev': 'Programming',
  'codepen.io': 'Programming',
  'codesandbox.io': 'Programming',
  'replit.com': 'Programming',
  'leetcode.com': 'Programming',
  'hackerrank.com': 'Programming',
  'codewars.com': 'Programming',
  'freecodecamp.org': 'Programming',
  'w3schools.com': 'Programming',
  'mozilla.org': 'Programming',
  'developer.mozilla.org': 'Programming',
  'docs.python.org': 'Programming',
  'docs.oracle.com': 'Programming',
  'docs.microsoft.com': 'Programming',
  'developer.apple.com': 'Programming',
  'developer.android.com': 'Programming',
  'hub.docker.com': 'Programming',
  'crates.io': 'Programming',
  'pypi.org': 'Programming',
  'rubygems.org': 'Programming',
  'packagist.org': 'Programming',
  'nuget.org': 'Programming',
  'pub.dev': 'Programming',
  'hex.pm': 'Programming',

  // Design
  'dribbble.com': 'Design',
  'behance.net': 'Design',
  'figma.com': 'Design',
  'adobe.com': 'Design',
  'canva.com': 'Design',
  'sketch.com': 'Design',
  'invisionapp.com': 'Design',
  'zeplin.io': 'Design',
  'unsplash.com': 'Design',
  'pexels.com': 'Design',
  'pixabay.com': 'Design',
  'flaticon.com': 'Design',
  'iconfont.cn': 'Design',
  'iconpark.oceanengine.com': 'Design',
  'colorhunt.co': 'Design',
  'coolors.co': 'Design',
  'zh.dribbble.com': 'Design',
  'uisdc.com': 'Design',
  'zcool.com.cn': 'Design',

  // Education
  'coursera.org': 'Education',
  'udemy.com': 'Education',
  'edx.org': 'Education',
  'khanacademy.org': 'Education',
  'ted.com': 'Education',
  'duolingo.com': 'Education',
  'brilliant.org': 'Education',
  'skillshare.com': 'Education',
  'pluralsight.com': 'Education',
  'linkedin.com/learning': 'Education',
  'mooc.cn': 'Education',
  'icourse163.org': 'Education',
  'xuetangx.com': 'Education',
  'bilibili.com': 'Education',
  'study.163.com': 'Education',
  'imooc.com': 'Education',

  // AI
  'openai.com': 'AI',
  'chat.openai.com': 'AI',
  'claude.ai': 'AI',
  'anthropic.com': 'AI',
  'bard.google.com': 'AI',
  'gemini.google.com': 'AI',
  'huggingface.co': 'AI',
  'kaggle.com': 'AI',
  'tensorflow.org': 'AI',
  'pytorch.org': 'AI',
  'midjourney.com': 'AI',
  'stability.ai': 'AI',
  'replicate.com': 'AI',
  'perplexity.ai': 'AI',
  'you.com': 'AI',
  'poe.com': 'AI',
  'character.ai': 'AI',
  'coze.com': 'AI',
  'doubao.com': 'AI',
  'tongyi.aliyun.com': 'AI',
  'yiyan.baidu.com': 'AI',
  'chatglm.cn': 'AI',

  // Gaming
  'store.steampowered.com': 'Game',
  'steampowered.com': 'Game',
  'epicgames.com': 'Game',
  'gog.com': 'Game',
  'itch.io': 'Game',
  'roblox.com': 'Game',
  'leagueoflegends.com': 'Game',
  'playvalorant.com': 'Game',
  'genshin.hoyoverse.com': 'Game',
  'genshin.mihoyo.com': 'Game',
  'minecraft.net': 'Game',
  'nintendo.com': 'Game',
  'playstation.com': 'Game',
  'xbox.com': 'Game',
  'gamefaqs.gamespot.com': 'Game',
  'ign.com': 'Game',
  'gamespot.com': 'Game',
  'kotaku.com': 'Game',
  '3dmgame.com': 'Game',
  'gamersky.com': 'Game',
  'nga.cn': 'Game',
  'taptap.cn': 'Game',
  'taptap.io': 'Game',
  'xiaoheihe.cn': 'Game',

  // Tools
  'notion.so': 'Tool',
  'obsidian.md': 'Tool',
  'todoist.com': 'Tool',
  'trello.com': 'Tool',
  'asana.com': 'Tool',
  'slack.com': 'Tool',
  'zoom.us': 'Tool',
  'teams.microsoft.com': 'Tool',
  'docs.google.com': 'Tool',
  'sheets.google.com': 'Tool',
  'drive.google.com': 'Tool',
  'dropbox.com': 'Tool',
  'onedrive.live.com': 'Tool',
  'airtable.com': 'Tool',
  'miro.com': 'Tool',
  'excalidraw.com': 'Tool',
  'regex101.com': 'Tool',
  'crontab.guru': 'Tool',
  'jsonformatter.org': 'Tool',
  'tinypng.com': 'Tool',
  'convertio.co': 'Tool',
  'remove.bg': 'Tool',
  'deepl.com': 'Tool',
  'fanyi.baidu.com': 'Tool',
  'translate.google.com': 'Tool',
  'grammarly.com': 'Tool',
  'quillbot.com': 'Tool',

  // Reading & blogs
  'substack.com': 'Reading',
  'ghost.org': 'Reading',
  'wordpress.com': 'Reading',
  'blogger.com': 'Reading',
  'notion.site': 'Reading',
  'gutenberg.org': 'Reading',
  'archive.org': 'Reading',
  'wikipedia.org': 'Reading',
  'wikiwand.com': 'Reading',
  'wolframalpha.com': 'Reading',
  'scholar.google.com': 'Reading',
  'zhihu.com': 'Reading',
  'juejin.cn': 'Reading',
  'segmentfault.com': 'Reading',
  'oschina.net': 'Reading',
  'v2ex.com': 'Reading',
  'hackernews.com': 'Reading',
  'news.ycombinator.com': 'Reading',
  'producthunt.com': 'Reading',
  'lobste.rs': 'Reading',
  'digg.com': 'Reading',
  'slashdot.org': 'Reading',

  // Search
  'google.com': 'Search',
  'bing.com': 'Search',
  'duckduckgo.com': 'Search',
  'yahoo.com': 'Search',
  'ecosia.org': 'Search',
  'startpage.com': 'Search',
  'sogou.com': 'Search',
  'so.com': 'Search',
  'yandex.com': 'Search',

  // Chinese sites (additional, not already listed above)
  'weibo.com': 'Social',
  'qq.com': 'Social',
  'taobao.com': 'Shopping',
  'jd.com': 'Shopping',
  'tmall.com': 'Shopping',
  'iqiyi.com': 'Video',
  'youku.com': 'Video',
  'sohu.com': 'News',
  'sina.com.cn': 'News',
  '163.com': 'News',
  'gitee.com': 'Programming',
  'coding.net': 'Programming',
  'jianshu.com': 'Reading',
  'toutiao.com': 'News',
  '36kr.com': 'News',
  'huxiu.com': 'News',
  'ifanr.com': 'News',
  'sspai.com': 'Tool',
  'coolapk.com': 'Tool',
  'smzdm.com': 'Shopping',
  'meituan.com': 'Shopping',
  'eleme.cn': 'Shopping',
  'dianping.com': 'Shopping',
  'ctrip.com': 'Tool',
  '12306.cn': 'Tool',
  'amap.com': 'Tool',
  'map.baidu.com': 'Tool',

  // Default
  '': 'Other'
};

/**
 * Extracts file extension from a filename or path
 */
export function getFileExtension(filename: string): string {
  const match = filename.match(/\.([^.]+)$/);
  return match ? `.${match[1].toLowerCase()}` : '';
}

/**
 * Gets category based on file extension
 */
export function getCategoryFromFileExtension(extension: string): string {
  return FILE_TYPE_CATEGORIES[extension] || FILE_TYPE_CATEGORIES[''];
}

/**
 * Extracts title from a filename (removes extension and cleans up)
 */
export function getTitleFromFilename(filename: string): string {
  // Remove extension
  let title = filename.replace(/\.[^/.]+$/, '');

  // Replace common separators with spaces and clean up
  title = title.replace(/[_-]/g, ' ');

  // Remove extra whitespace
  title = title.trim();

  // If empty, return original filename
  return title || filename;
}

/**
 * Cleans share links by removing common prefixes/suffixes and extracting the real URL
 */
function cleanShareLink(input: string): string {
  // Example: "【标题】https://example.com" or "标题：https://example.com" or "https://example.com 【标题】"
  const urlMatch = input.match(/(https?:\/\/[^\s]+)/);
  if (urlMatch) {
    return urlMatch[0];
  }
  // If no URL pattern found, return original input
  return input;
}

/**
 * Gets category based on site hostname
 */
export function getCategoryFromSite(hostname: string): string {
  // Remove www. prefix
  const cleanHostname = hostname.replace(/^www\./, '');

  // Check for exact match
  if (SITE_CATEGORIES[cleanHostname]) {
    return SITE_CATEGORIES[cleanHostname];
  }

  // Check for partial matches (domain contains keyword)
  for (const [domain, category] of Object.entries(SITE_CATEGORIES)) {
    if (cleanHostname.includes(domain)) {
      return category;
    }
  }

  return SITE_CATEGORIES[''];
}

/**
 * Extracts a best-effort title from the pasted text without any network
 * access (used so the fields are never left empty).
 */
function localMetadataFromInput(input: string): { title: string; description?: string } {
  let extractedTitle = '';

  // Title text surrounding the URL in share-text like "【标题】https://..."
  const urlMatch = input.match(/(https?:\/\/[^\s]+)/);
  if (urlMatch) {
    const matchedUrl = urlMatch[0];
    const start = input.indexOf(matchedUrl);
    const before = input.substring(0, start).trim();
    const after = input.substring(start + matchedUrl.length).trim();
    const parts: string[] = [];
    if (before && !/^[\s\-–——【\[「『》」』\]]+$/.test(before)) parts.push(before);
    if (after && !/^[\s\-–——【\[「『》」』\]]+$/.test(after)) parts.push(after);
    if (parts.length) extractedTitle = parts.join(' ');
  }

  // Bracketed content, e.g. 【标题】 《标题》 [标题]
  if (!extractedTitle) {
    const bracketPatterns = [
      /[【\[「『]([^】\]」』]+)[】\]」』]/,
      /《([^》]+)》/,
    ];
    for (const pattern of bracketPatterns) {
      const match = input.match(pattern);
      if (match && match[1] && match[1].trim()) {
        extractedTitle = match[1].trim();
        break;
      }
    }
  }

  if (extractedTitle) {
    extractedTitle = extractedTitle
      .replace(/^[【\[「『]+/, '')
      .replace(/[】\]」』]+$/, '')
      .replace(/^[\s\u3000]+|[\s\u3000]+$/g, '');
    if (extractedTitle.length > 100) {
      extractedTitle = extractedTitle.substring(0, 100) + '...';
    }
    return { title: extractedTitle };
  }

  // Hostname fallback
  try {
    const url = input.match(/(https?:\/\/[^\s]+)/)?.[0] || input;
    const hostname = new URL(url).hostname.replace(/^www\./, '');
    return { title: hostname.replace(/[._-]/g, ' ') || input };
  } catch (e) {
    return { title: input };
  }
}

/**
 * Main function to auto-recognize and extract metadata from a URL or file path.
 * Local-only: no network requests are made.
 */
// ===== Cover extraction (metadata-based; the only network path) =====
//
// Browsers block direct cross-origin fetches, so every request goes through a
// chain of public CORS proxies tried in parallel (first success wins), each
// with a timeout and a 3MB size cap. Public proxies come and go, so failures
// degrade gracefully - the UI shows a warning and the cover is set manually.

// The dedicated local backend (server/index.js, `npm run server`) does the
// cross-origin fetch in Node - no CORS, browser-like headers, Bilibili Referer
// - and returns the raw body with permissive CORS headers. The Vite dev-server
// proxy (vite.config.ts) and the public CORS proxies below are only fallbacks.
const COVER_BACKEND = 'http://localhost:3100'
const DEV_PROXY = '/__cover?url='

const CORS_PROXIES = [
  'https://corsproxy.io/?url=',
  'https://api.allorigins.win/raw?url=',
  'https://api.codetabs.com/v1/proxy?quest=',
  'https://cors.eu.org/',
  'https://whateverorigin.org/get?url=',
  'https://api.cors.lol/?url=',
  'https://thingproxy.freeboard.io/fetch/',
]

const MAX_BODY = 3 * 1024 * 1024
const FETCH_TIMEOUT = 8000

async function tryFetchText(fullUrl: string): Promise<string> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT)
  try {
    const res = await fetch(fullUrl, { signal: controller.signal, redirect: 'follow' })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const contentLength = Number(res.headers.get('content-length') || 0)
    if (contentLength > MAX_BODY) throw new Error('body too large')
    const text = await res.text()
    if (text.length > MAX_BODY) throw new Error('body too large')
    return text
  } finally {
    clearTimeout(timer)
  }
}

/** Some proxies wrap the response as JSON ({ contents: "..." }) - unwrap it */
function decodeProxyResponse(text: string): string {
  const trimmed = text.trim()
  if (trimmed.startsWith('{"contents"')) {
    try {
      const j = JSON.parse(trimmed)
      if (typeof j.contents === 'string' && j.contents) return j.contents
    } catch {
      // not JSON after all - use the raw text
    }
  }
  return trimmed
}

async function fetchPageText(url: string): Promise<string> {
  const attempts: Array<Promise<string>> = []
  // Local backend first (npm run server) - the reliable route.
  attempts.push(tryFetchText(`${COVER_BACKEND}/api/cover?url=` + encodeURIComponent(url)).catch(() => ''))
  // Same-origin dev-server proxy as a second fallback.
  attempts.push(tryFetchText(DEV_PROXY + encodeURIComponent(url)).catch(() => ''))
  // Direct (only works if the target allows CORS - cheap to try)
  attempts.push(tryFetchText(url).catch(() => ''))
  for (const proxy of CORS_PROXIES) {
    attempts.push(tryFetchText(proxy + encodeURIComponent(url)).catch(() => ''))
  }
  const results = await Promise.all(attempts)
  for (const result of results) {
    if (result) {
      const decoded = decodeProxyResponse(result)
      if (decoded) return decoded
    }
  }
  throw new Error('all fetch routes failed')
}

function resolveUrl(href: string, base: string): string {
  try {
    return new URL(href, base).href
  } catch {
    return href
  }
}

/** Parses og:image / twitter:image / link[rel=image_src] out of raw HTML */
function extractMetaImage(html: string, pageUrl: string): string | undefined {
  const patterns = [
    /<meta[^>]+property=["']og:image["'][^>]+content=["']([^"']+)["']/i,
    /<meta[^>]+content=["']([^"']+)["'][^>]+property=["']og:image["']/i,
    /<meta[^>]+name=["']twitter:image["'][^>]+content=["']([^"']+)["']/i,
    /<meta[^>]+content=["']([^"']+)["'][^>]+name=["']twitter:image["']/i,
    /<link[^>]+rel=["']image_src["'][^>]+href=["']([^"']+)["']/i,
    /<link[^>]+href=["']([^"']+)["'][^>]+rel=["']image_src["']/i,
  ]
  for (const pattern of patterns) {
    const match = html.match(pattern)
    if (match && match[1] && !match[1].startsWith('data:')) {
      const resolved = resolveUrl(match[1], pageUrl)
      if (/^https?:/i.test(resolved)) return resolved
    }
  }
  return undefined
}

/** Bilibili embeds the real cover inside __INITIAL_STATE__ as "pic":"https://..." */
function extractPicField(html: string): string | undefined {
  const match = html.match(/"pic":"([^"]+)"/)
  return match ? match[1] : undefined
}

/**
 * The local backend (server/index.js) extracts the cover server-side for
 * Bilibili (API -> page og:image -> player API), which is far more reliable
 * than parsing in the browser. Returns the cover URL or throws.
 */
async function extractBiliCoverViaBackend(url: string): Promise<string> {
  const res = await fetch(`${COVER_BACKEND}/api/bilibili-cover?url=` + encodeURIComponent(url), {
    signal: AbortSignal.timeout(12000),
  })
  if (!res.ok) throw new Error(`backend cover failed: HTTP ${res.status}`)
  const j = (await res.json()) as { cover?: string; error?: string }
  if (typeof j.cover === 'string' && j.cover) return j.cover
  throw new Error(j.error || 'backend returned no cover')
}

function getYouTubeId(url: string): string | undefined {
  const patterns = [
    /(?:youtube\.com\/(?:watch\?(?:.*&)?v=|embed\/|shorts\/))([A-Za-z0-9_-]{11})/,
    /youtu\.be\/([A-Za-z0-9_-]{11})/,
  ]
  for (const pattern of patterns) {
    const match = url.match(pattern)
    if (match) return match[1]
  }
  return undefined
}

function getBilibiliBV(url: string): string | undefined {
  const match = url.match(/BV[0-9A-Za-z]{10}/)
  return match ? match[0] : undefined
}

function toHttps(url: string): string {
  return url.replace(/^http:/i, 'https:')
}

/**
 * Extracts the cover image of a link by reading the page metadata, exactly
 * like a Python requests + BeautifulSoup script would. Only the cover uses
 * this network path - title/category/summary stay local.
 *
 * - YouTube: deterministic thumbnail URL (no fetch needed)
 * - Bilibili: official API + page meta in parallel (API preferred)
 * - Anything else: page HTML -> og:image / twitter:image
 *
 * @throws if the page cannot be reached or no cover is found
 */
export async function extractCoverFromUrl(input: string): Promise<string> {
  const url = cleanShareLink(input)

  // YouTube thumbnails are deterministic - no network request
  const ytId = getYouTubeId(url)
  if (ytId) return `https://img.youtube.com/vi/${ytId}/hqdefault.jpg`

  const bv = getBilibiliBV(url)
  if (bv) {
    // Preferred: the local backend extracts it server-side (API -> page -> player API)
    try {
      return await extractBiliCoverViaBackend(url)
    } catch (err) {
      console.warn('Bilibili backend cover failed, falling back to browser-side:', err)
    }

    // Fallback: browser-side parsing (API JSON, then page meta)
    const apiCover = fetchPageText(`https://api.bilibili.com/x/web-interface/view?bvid=${bv}`)
      .then(text => {
        let j: { data?: { pic?: unknown } } = {}
        try {
          j = JSON.parse(text) as { data?: { pic?: unknown } }
        } catch {
          throw new Error('api response is not json')
        }
        const pic: unknown = j?.data?.pic
        if (typeof pic === 'string' && pic) return toHttps(pic)
        throw new Error('no pic in api response')
      })
      .catch(() => undefined as string | undefined)
    const pageCover = fetchPageText(url)
      .then(text => {
        const image = extractMetaImage(text, url) || extractPicField(text)
        if (image) return toHttps(image)
        throw new Error('no cover in page')
      })
      .catch(() => undefined as string | undefined)
    const [api, page] = await Promise.all([apiCover, pageCover])
    if (api) return api
    if (page) return page
    throw new Error('no cover found for bilibili link')
  }

  // Generic path: fetch the page HTML and parse the meta tags
  const html = await fetchPageText(url)
  const image = extractMetaImage(html, url)
  if (image) return toHttps(image)
  throw new Error('no cover found')
}

export async function autoRecognizeItem(
  input: string,
  itemType: 'link' | 'file'
): Promise<{
  title: string;
  urlOrPath: string;
  category: string;
  summary?: string;
}> {
  if (itemType === 'link') {
    // Clean the input to get the real URL
    const cleanedUrl = cleanShareLink(input);

    let hostname = '';
    try {
      hostname = new URL(cleanedUrl).hostname.toLowerCase();
    } catch (e) {
      // invalid URL - heuristics below will still produce a result
    }

    const local = localMetadataFromInput(input);

    return {
      title: local.title || cleanedUrl,
      urlOrPath: cleanedUrl,
      category: getCategoryFromSite(hostname) || 'Other',
      summary: local.description || '',
    };
  } else {
    // For files, extract info from filename
    // Extract filename from path (handle both Windows and Unix paths)
    const filename = input.split(/[\\/]/).pop() || input;

    const title = getTitleFromFilename(filename);
    const extension = getFileExtension(filename);
    const category = getCategoryFromFileExtension(extension);

    return {
      title,
      urlOrPath: input,
      category,
      summary: `File type: ${extension || 'unknown'}`
    };
  }
}
