// ── In-memory cache, rate limiter, and request deduplication ─────────────────
//
// Three layers of protection:
//
// 1. **Cache** — Same URL within TTL returns the cached result instantly.
//    Bilibili: 10 min, generic sites: 30 min, images: 24 h.
//
// 2. **Per-domain rate limiter** — Sliding-window counter per hostname.
//    Bilibili: 30 req/min, other domains: 50 req/min.
//    Exceeding the limit throws a retryable error.
//
// 3. **In-flight dedup** — Two simultaneous requests for the same URL share
//    a single upstream fetch, halving load on duplicate traffic.
class TTLCache {
    constructor(defaultTTL_ms) {
        this.store = new Map();
        this.cleanupTimer = null;
        this.defaultTTL = defaultTTL_ms;
    }
    get(key) {
        const entry = this.store.get(key);
        if (!entry)
            return undefined;
        if (Date.now() > entry.expiresAt) {
            this.store.delete(key);
            return undefined;
        }
        return entry.data;
    }
    set(key, data, ttlOverride) {
        this.store.set(key, {
            data,
            expiresAt: Date.now() + (ttlOverride ?? this.defaultTTL),
        });
        this.scheduleCleanup();
    }
    delete(key) {
        this.store.delete(key);
    }
    /** Evict expired entries every 5 minutes */
    scheduleCleanup() {
        if (this.cleanupTimer)
            return;
        this.cleanupTimer = setInterval(() => {
            const now = Date.now();
            for (const [k, v] of this.store) {
                if (now > v.expiresAt)
                    this.store.delete(k);
            }
            if (this.store.size === 0 && this.cleanupTimer) {
                clearInterval(this.cleanupTimer);
                this.cleanupTimer = null;
            }
        }, 5 * 60 * 1000);
        // Allow Node to exit even if the timer is running
        if (this.cleanupTimer && typeof this.cleanupTimer === 'object' && 'unref' in this.cleanupTimer) {
            this.cleanupTimer.unref();
        }
    }
    get size() { return this.store.size; }
}
// Cover URL cache: 10 min default (Bilibili), 30 min for generic sites
export const coverCache = new TTLCache(30 * 60 * 1000);
export const BILIBILI_CACHE_TTL = 10 * 60 * 1000; // 10 minutes
// Image proxy cache: 24 hours (images rarely change)
export const imageCache = new TTLCache(24 * 60 * 60 * 1000);
class DomainRateLimiter {
    constructor() {
        this.buckets = new Map();
        this.cleanupTimer = null;
    }
    /** Check if a request is allowed. Throws if rate-limited. */
    check(domain, windowMs, maxRequests) {
        const now = Date.now();
        let bucket = this.buckets.get(domain);
        if (!bucket) {
            bucket = { timestamps: [] };
            this.buckets.set(domain, bucket);
        }
        // Prune timestamps outside the window
        bucket.timestamps = bucket.timestamps.filter(t => now - t < windowMs);
        if (bucket.timestamps.length >= maxRequests) {
            const oldestInWindow = bucket.timestamps[0];
            const retryAfterMs = windowMs - (now - oldestInWindow);
            const retryAfterSec = Math.ceil(retryAfterMs / 1000);
            throw new RateLimitError(domain, retryAfterSec);
        }
        bucket.timestamps.push(now);
        this.scheduleCleanup(windowMs);
    }
    /** Record that a domain is temporarily backed off */
    markBackoff(domain, backoffMs) {
        const now = Date.now();
        let bucket = this.buckets.get(domain);
        if (!bucket) {
            bucket = { timestamps: [] };
            this.buckets.set(domain, bucket);
        }
        // Flood the bucket to block requests for the backoff period
        const floodCount = 100;
        bucket.timestamps = [];
        for (let i = 0; i < floodCount; i++) {
            bucket.timestamps.push(now - backoffMs + (i * backoffMs / floodCount));
        }
    }
    scheduleCleanup(windowMs) {
        if (this.cleanupTimer)
            return;
        this.cleanupTimer = setInterval(() => {
            const now = Date.now();
            for (const [domain, bucket] of this.buckets) {
                bucket.timestamps = bucket.timestamps.filter(t => now - t < windowMs * 2);
                if (bucket.timestamps.length === 0)
                    this.buckets.delete(domain);
            }
            if (this.buckets.size === 0 && this.cleanupTimer) {
                clearInterval(this.cleanupTimer);
                this.cleanupTimer = null;
            }
        }, windowMs);
        if (this.cleanupTimer && typeof this.cleanupTimer === 'object' && 'unref' in this.cleanupTimer) {
            this.cleanupTimer.unref();
        }
    }
}
export const rateLimiter = new DomainRateLimiter();
// Rate limit config per domain type
export const RATE_LIMITS = {
    bilibili: { windowMs: 60000, maxRequests: 30 }, // 30 req/min
    generic: { windowMs: 60000, maxRequests: 50 }, // 50 req/min
    image: { windowMs: 60000, maxRequests: 100 }, // 100 req/min for images
};
export function getRateLimitConfig(domain) {
    if (domain.endsWith('bilibili.com'))
        return RATE_LIMITS.bilibili;
    return RATE_LIMITS.generic;
}
// ── In-flight request deduplication ──────────────────────────────────────────
const inflight = new Map();
/**
 * Deduplicate concurrent requests for the same key.
 * If a request for `key` is already in flight, returns the same promise.
 * Otherwise, runs `fn` and stores the promise until it settles.
 */
export async function dedupRequest(key, fn) {
    const existing = inflight.get(key);
    if (existing)
        return existing;
    const promise = fn().finally(() => inflight.delete(key));
    inflight.set(key, promise);
    return promise;
}
// ── Custom error types ───────────────────────────────────────────────────────
export class RateLimitError extends Error {
    constructor(domain, retryAfterSec) {
        super(`Rate limit exceeded for ${domain}. Please retry after ${retryAfterSec}s.`);
        this.domain = domain;
        this.retryAfterSec = retryAfterSec;
        this.name = 'RateLimitError';
    }
}
export class UpstreamBlockedError extends Error {
    constructor(domain, upstreamCode, message) {
        super(message || `Upstream ${domain} blocked the request (code: ${upstreamCode}). Please try again later.`);
        this.domain = domain;
        this.upstreamCode = upstreamCode;
        this.name = 'UpstreamBlockedError';
    }
}
// ── Helpers ──────────────────────────────────────────────────────────────────
export function extractDomain(url) {
    try {
        return new URL(url).hostname;
    }
    catch {
        return 'unknown';
    }
}
export function isBilibiliDomain(domain) {
    return domain.endsWith('bilibili.com') || domain.endsWith('hdslb.com');
}
