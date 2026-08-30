export declare const BROWSER_HEADERS: Record<string, string>;
export declare const MAX_BODY: number;
export declare const TIMEOUT_MS = 8000;
export declare function toHttps(u: string): string;
export declare function resolveUrl(href: string, base: string): string;
export declare function fetchBody(url: string, opts?: {
    referer?: string;
}): Promise<{
    status: number;
    contentType: string;
    text: string;
}>;
export interface FetchResult {
    status: number;
    contentType: string;
    text: string;
}
/**
 * Fetch with three layers of protection:
 * 1. Cache — returns cached result if available (Bilibili: 10 min, others: 30 min)
 * 2. Rate limit — blocks if too many requests to the same domain
 * 3. Dedup — concurrent requests for the same URL share one upstream fetch
 *
 * @param cacheKey  Cache key (usually the URL itself)
 * @param url       Actual URL to fetch
 * @param opts      fetchBody options
 * @param cacheTTL  Override TTL in ms (default: 30 min)
 */
export declare function fetchProtected(cacheKey: string, url: string, opts?: {
    referer?: string;
    cacheTTL?: number;
}): Promise<FetchResult>;
export declare function extractMetaImage(html: string, pageUrl: string): string | undefined;
export declare function extractBiliPageCover(html: string): string | undefined;
export declare function getBvid(input: string): string;
