declare class TTLCache<T> {
    private store;
    private readonly defaultTTL;
    private cleanupTimer;
    constructor(defaultTTL_ms: number);
    get(key: string): T | undefined;
    set(key: string, data: T, ttlOverride?: number): void;
    delete(key: string): void;
    /** Evict expired entries every 5 minutes */
    private scheduleCleanup;
    get size(): number;
}
export declare const coverCache: TTLCache<string>;
export declare const BILIBILI_CACHE_TTL: number;
export declare const imageCache: TTLCache<Uint8Array<ArrayBufferLike>>;
declare class DomainRateLimiter {
    private buckets;
    private cleanupTimer;
    /** Check if a request is allowed. Throws if rate-limited. */
    check(domain: string, windowMs: number, maxRequests: number): void;
    /** Record that a domain is temporarily backed off */
    markBackoff(domain: string, backoffMs: number): void;
    private scheduleCleanup;
}
export declare const rateLimiter: DomainRateLimiter;
export declare const RATE_LIMITS: {
    readonly bilibili: {
        readonly windowMs: 60000;
        readonly maxRequests: 30;
    };
    readonly generic: {
        readonly windowMs: 60000;
        readonly maxRequests: 50;
    };
    readonly image: {
        readonly windowMs: 60000;
        readonly maxRequests: 100;
    };
};
export declare function getRateLimitConfig(domain: string): {
    readonly windowMs: 60000;
    readonly maxRequests: 30;
} | {
    readonly windowMs: 60000;
    readonly maxRequests: 50;
};
/**
 * Deduplicate concurrent requests for the same key.
 * If a request for `key` is already in flight, returns the same promise.
 * Otherwise, runs `fn` and stores the promise until it settles.
 */
export declare function dedupRequest<T>(key: string, fn: () => Promise<T>): Promise<T>;
export declare class RateLimitError extends Error {
    readonly domain: string;
    readonly retryAfterSec: number;
    constructor(domain: string, retryAfterSec: number);
}
export declare class UpstreamBlockedError extends Error {
    readonly domain: string;
    readonly upstreamCode: number;
    constructor(domain: string, upstreamCode: number, message?: string);
}
export declare function extractDomain(url: string): string;
export declare function isBilibiliDomain(domain: string): boolean;
export {};
