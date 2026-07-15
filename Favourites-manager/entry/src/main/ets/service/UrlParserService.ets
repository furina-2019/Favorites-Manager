/**
 * URL解析服务 - 支持从链接中提取标题、封面和来源应用信息
 */
import { http } from '@kit.NetworkKit';

interface ParsedUrlInfo {
  title: string;
  description?: string;
  coverImage?: string;
  sourceApp: string;
  sourcePackage?: string;
  type: 'article' | 'video' | 'image' | 'website' | 'other';
}

interface SourceInfo {
  appName: string;
  packageName?: string;
  title: string;
  coverImage?: string;
  type: 'article' | 'video' | 'image' | 'website' | 'other';
}

interface BaseInfo {
  title: string;
  description?: string;
}

interface PlatformInfo {
  name: string;
  packageName?: string;
  domains: string[];
  type: 'article' | 'video' | 'image' | 'website' | 'other';
}

export class UrlParserService {
  private static instance: UrlParserService;

  private constructor() {}

  static getInstance(): UrlParserService {
    if (!UrlParserService.instance) {
      UrlParserService.instance = new UrlParserService();
    }
    return UrlParserService.instance;
  }

  /**
   * 解析URL并获取相关信息
   */
  async parseUrl(url: string): Promise<ParsedUrlInfo> {
    if (!url || url.trim().length === 0) {
      return {
        title: '无标题',
        sourceApp: '未知应用',
        type: 'other'
      };
    }

    // 清理URL
    const cleanUrl = url.trim();
    
    // 识别来源应用和类型
    const sourceInfo = this.identifySource(cleanUrl);
    
    // 尝试从URL中提取基本信息
    const baseInfo = this.extractBaseInfo(cleanUrl);
    
    // 组合信息
    // 对于网站链接，如果没有封面，使用网站图标作为默认封面
    let coverImage = sourceInfo.coverImage;
    if (!coverImage && sourceInfo.type === 'article') {
      coverImage = this.extractWebsiteFavicon(cleanUrl);
    }
    // 对于website类型，尝试使用网站图标作为封面
    if (sourceInfo.type === 'website' && !coverImage) {
      coverImage = this.extractWebsiteFavicon(cleanUrl);
    }
    
    // 对于 b23.tv 短链接，异步解析获取真实封面
    if (!coverImage && cleanUrl.toLowerCase().includes('b23.tv')) {
      console.log('parseUrl: resolving b23.tv short link for cover');
      const resolvedCover = await this.resolveBilibiliShortUrl(cleanUrl);
      if (resolvedCover) {
        coverImage = resolvedCover;
        console.log('parseUrl: got cover from short link:', coverImage);
      }
    }
    
    return {
      title: baseInfo.title || sourceInfo.title || '无标题',
      description: baseInfo.description,
      coverImage: coverImage,
      sourceApp: sourceInfo.appName,
      sourcePackage: sourceInfo.packageName,
      type: sourceInfo.type
    };
  }

  /**
   * 识别URL来源应用
   */
  private identifySource(url: string): SourceInfo {
    const lowerUrl = url.toLowerCase();
    
    // 哔哩哔哩
    if (lowerUrl.includes('bilibili.com') || lowerUrl.includes('b23.tv')) {
      return {
        appName: '哔哩哔哩',
        packageName: 'tv.danmaku.bili',
        title: 'B站视频',
        coverImage: this.extractBilibiliCover(url),
        type: 'video'
      };
    }
    
    // 抖音
    if (lowerUrl.includes('douyin.com') || lowerUrl.includes('tiktok.com') || lowerUrl.includes('iesdouyin.com')) {
      return {
        appName: '抖音',
        packageName: 'com.ss.android.ugc.aweme',
        title: '抖音视频',
        coverImage: this.extractDouyinCover(url),
        type: 'video'
      };
    }
    
    // 小红书
    if (lowerUrl.includes('xiaohongshu.com') || lowerUrl.includes('xhs.com')) {
      return {
        appName: '小红书',
        packageName: 'com.xingin.xhs',
        title: '小红书笔记',
        coverImage: this.extractXiaohongshuCover(url),
        type: 'article'
      };
    }
    
    // 知乎
    if (lowerUrl.includes('zhihu.com')) {
      return {
        appName: '知乎',
        packageName: 'com.zhihu.android',
        title: '知乎文章',
        coverImage: this.extractZhihuCover(url),
        type: 'article'
      };
    }
    
    // 微博
    if (lowerUrl.includes('weibo.com') || lowerUrl.includes('weibo.cn')) {
      return {
        appName: '微博',
        packageName: 'com.sina.weibo',
        title: '微博',
        coverImage: this.extractWeiboCover(url),
        type: 'article'
      };
    }
    
    // YouTube
    if (lowerUrl.includes('youtube.com') || lowerUrl.includes('youtu.be')) {
      return {
        appName: 'YouTube',
        packageName: 'com.google.android.youtube',
        title: 'YouTube视频',
        coverImage: this.extractYouTubeCover(url),
        type: 'video'
      };
    }
    
    // Twitter/X
    if (lowerUrl.includes('twitter.com') || lowerUrl.includes('x.com')) {
      return {
        appName: 'Twitter',
        packageName: 'com.twitter.android',
        title: 'Twitter/X',
        coverImage: this.extractTwitterCover(url),
        type: 'article'
      };
    }
    
    // Facebook
    if (lowerUrl.includes('facebook.com') || lowerUrl.includes('fb.com')) {
      return {
        appName: 'Facebook',
        packageName: 'com.facebook.katana',
        title: 'Facebook',
        coverImage: this.extractFacebookCover(url),
        type: 'article'
      };
    }
    
    // Instagram
    if (lowerUrl.includes('instagram.com')) {
      return {
        appName: 'Instagram',
        packageName: 'com.instagram.android',
        title: 'Instagram',
        coverImage: this.extractInstagramCover(url),
        type: 'image'
      };
    }
    
    // 淘宝
    if (lowerUrl.includes('taobao.com')) {
      return {
        appName: '淘宝',
        packageName: 'com.taobao.taobao',
        title: '淘宝商品',
        coverImage: this.extractTaobaoCover(url),
        type: 'website'
      };
    }
    
    // 京东
    if (lowerUrl.includes('jd.com')) {
      return {
        appName: '京东',
        packageName: 'com.jingdong.app.mall',
        title: '京东商品',
        coverImage: this.extractJDCover(url),
        type: 'website'
      };
    }
    
    // 央视频
    if (lowerUrl.includes('yangshipin.cn') || lowerUrl.includes('cctv.com') || lowerUrl.includes('cntv.cn')) {
      return {
        appName: '央视频',
        packageName: 'com.cctv.yangshipin.app.android',
        title: '央视频',
        coverImage: this.extractCctvCover(url),
        type: 'video'
      };
    }
    
    // 腾讯视频
    if (lowerUrl.includes('v.qq.com') || lowerUrl.includes('qq.com') && lowerUrl.includes('/video/')) {
      return {
        appName: '腾讯视频',
        packageName: 'com.tencent.qqlive',
        title: '腾讯视频',
        coverImage: this.extractTencentVideoCover(url),
        type: 'video'
      };
    }
    
    // 爱奇艺
    if (lowerUrl.includes('iqiyi.com') || lowerUrl.includes('qiyi.com')) {
      return {
        appName: '爱奇艺',
        packageName: 'com.qiyi.video',
        title: '爱奇艺',
        coverImage: this.extractIqiyiCover(url),
        type: 'video'
      };
    }
    
    // 优酷
    if (lowerUrl.includes('youku.com')) {
      return {
        appName: '优酷',
        packageName: 'com.youku.phone',
        title: '优酷视频',
        coverImage: this.extractYoukuCover(url),
        type: 'video'
      };
    }
    
    // 芒果TV
    if (lowerUrl.includes('mgtv.com') || lowerUrl.includes('hunantv.com')) {
      return {
        appName: '芒果TV',
        packageName: 'com.hunantv.mangguo',
        title: '芒果TV',
        coverImage: this.extractMgtvCover(url),
        type: 'video'
      };
    }
    
    // 西瓜视频
    if (lowerUrl.includes('ixigua.com')) {
      return {
        appName: '西瓜视频',
        packageName: 'com.ss.android.article.video',
        title: '西瓜视频',
        coverImage: this.extractXiguaCover(url),
        type: 'video'
      };
    }
    
    // 快手
    if (lowerUrl.includes('kuaishou.com') || lowerUrl.includes('gifshow.com')) {
      return {
        appName: '快手',
        packageName: 'com.kuaishou.nebula',
        title: '快手视频',
        coverImage: this.extractKuaishouCover(url),
        type: 'video'
      };
    }
    
    // 微信公众号文章
    if (lowerUrl.includes('mp.weixin.qq.com')) {
      return {
        appName: '微信',
        packageName: 'com.tencent.mm',
        title: '公众号文章',
        type: 'article'
      };
    }
    
    // 百度
    if (lowerUrl.includes('baidu.com')) {
      return {
        appName: '百度',
        packageName: 'com.baidu.searchbox',
        title: '百度',
        coverImage: this.extractBaiduCover(url),
        type: 'website'
      };
    }
    
    // Google
    if (lowerUrl.includes('google.com')) {
      return {
        appName: 'Google',
        packageName: 'com.google.android.googlequicksearchbox',
        title: 'Google',
        coverImage: this.extractGoogleCover(url),
        type: 'website'
      };
    }
    
    // 通用图片链接
    if (lowerUrl.match(/\.(jpg|jpeg|png|gif|webp|bmp)(\?.*)?$/i)) {
      return {
        appName: '图片',
        title: '图片',
        coverImage: url,
        type: 'image'
      };
    }
    
    // 通用视频链接
    if (lowerUrl.match(/\.(mp4|avi|mov|mkv|webm|flv)(\?.*)?$/i)) {
      return {
        appName: '视频',
        title: '视频',
        type: 'video'
      };
    }
    
    // 通用文章链接
    if (lowerUrl.match(/\.(html|htm|php|asp|aspx|jsp)(\?.*)?$/i) || 
        lowerUrl.includes('/article/') || 
        lowerUrl.includes('/post/') || 
        lowerUrl.includes('/blog/')) {
      return {
        appName: '网页',
        title: '网页文章',
        type: 'article'
      };
    }
    
    // 通用网站链接（http/https开头）
    if (lowerUrl.startsWith('http://') || lowerUrl.startsWith('https://')) {
      return {
        appName: '网站',
        title: '网站链接',
        type: 'website'
      };
    }
    
    // 默认
    return {
      appName: '网页',
      title: '网页链接',
      type: 'other'
    };
  }

  /**
   * 提取哔哩哔哩封面图
   * b23.tv 是短链接，格式为 https://b23.tv/xxxxx
   * 真实视频ID需要解析短链接或使用API获取
   */
  private extractBilibiliCover(url: string): string | undefined {
    try {
      console.log('extractBilibiliCover: parsing URL:', url);
      
      // 直接视频链接格式: bilibili.com/video/BVxxxxxx 或 bilibili.com/video/avxxxxxx
      const bvMatch = url.match(/bilibili\.com\/video\/(BV[A-Za-z0-9]+)/i);
      if (bvMatch && bvMatch[1]) {
        const bvid = bvMatch[1];
        console.log('extractBilibiliCover: found BV ID:', bvid);
        // B站封面图格式 - 使用 BV 号构建封面URL
        // 注意：实际封面URL需要通过API获取，这里使用通用格式
        return `https://i0.hdslb.com/bfs/archive/${bvid}.jpg`;
      }
      
      // AV号格式
      const avMatch = url.match(/av(\d+)/i);
      if (avMatch && avMatch[1]) {
        const avid = avMatch[1];
        console.log('extractBilibiliCover: found AV ID:', avid);
        return `https://i0.hdslb.com/bfs/archive/av${avid}.jpg`;
      }
      
      // b23.tv 短链接格式: b23.tv/xxxxx
      // 短链接无法直接提取视频ID，返回 undefined，由调用方异步解析
      if (url.includes('b23.tv')) {
        console.log('extractBilibiliCover: b23.tv short link detected, will resolve async');
        return undefined;
      }
      
      // 其他B站链接
      if (url.includes('bilibili.com')) {
        console.log('extractBilibiliCover: bilibili.com link detected');
        return 'https://i0.hdslb.com/bfs/archive/default.jpg';
      }
    } catch (error) {
      console.error('Failed to extract Bilibili cover:', error);
    }
    return undefined;
  }

  /**
   * 异步解析哔哩哔哩短链接获取真实封面
   * 通过 HTTP 请求跟随重定向获取真实 URL
   */
  async resolveBilibiliShortUrl(shortUrl: string): Promise<string | undefined> {
    try {
      console.log('resolveBilibiliShortUrl: resolving', shortUrl);
      
      // 提取短链接中的ID
      const shortIdMatch = shortUrl.match(/b23\.tv\/([A-Za-z0-9]+)/);
      if (!shortIdMatch || !shortIdMatch[1]) {
        console.log('resolveBilibiliShortUrl: invalid short URL format');
        return undefined;
      }
      
      const shortId = shortIdMatch[1];
      
      // 尝试使用 B 站 API 解析短链接
      // 方法1: 直接请求短链接，获取重定向后的真实URL
      const httpRequest = http.createHttp();
      
      try {
        const response = await httpRequest.request(shortUrl, {
          method: http.RequestMethod.GET,
          header: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
          }
        });
        
        console.log('resolveBilibiliShortUrl: response code:', response.responseCode);
        
        // 从响应的 URL 或 header 中获取真实地址
        const finalUrl = response.result ? String(response.result) : '';
        
        // 尝试从响应中提取 BV 号
        const bvMatch = finalUrl.match(/(BV[A-Za-z0-9]+)/);
        if (bvMatch && bvMatch[1]) {
          const bvid = bvMatch[1];
          console.log('resolveBilibiliShortUrl: found BV ID from response:', bvid);
          return `https://i0.hdslb.com/bfs/archive/${bvid}.jpg`;
        }
        
        // 尝试从响应头获取重定向地址
        const header = response.header as Record<string, string>;
        const location = header['location'] || header['Location'];
        if (location) {
          console.log('resolveBilibiliShortUrl: redirect location:', location);
          const bvMatch2 = location.match(/(BV[A-Za-z0-9]+)/);
          if (bvMatch2 && bvMatch2[1]) {
            return `https://i0.hdslb.com/bfs/archive/${bvMatch2[1]}.jpg`;
          }
        }
      } catch (httpError) {
        console.error('resolveBilibiliShortUrl: HTTP request failed:', httpError);
      } finally {
        httpRequest.destroy();
      }
      
      // 方法2: 使用 B 站公开 API 解析
      // b23.tv 的短链接可以通过 API 解析
      const apiUrl = `https://api.bilibili.com/x/web-interface/archive/shorturl?short_id=${shortId}`;
      const apiRequest = http.createHttp();
      
      try {
        const apiResponse = await apiRequest.request(apiUrl, {
          method: http.RequestMethod.GET,
          header: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.bilibili.com/'
          },
          connectTimeout: 10000,
          readTimeout: 10000
        });
        
        console.log('resolveBilibiliShortUrl: API response code:', apiResponse.responseCode);
        
        if (apiResponse.responseCode === 200 && apiResponse.result) {
          const resultStr = String(apiResponse.result);
          console.log('resolveBilibiliShortUrl: API result:', resultStr);
          
          try {
            const result = JSON.parse(resultStr) as Record<string, Object>;
            const code = result['code'] as number;
            const data = result['data'] as Record<string, Object>;
            
            if (code === 0 && data) {
              // 优先使用 bvid，如果没有则使用 aid
              const bvid = data['bvid'] as string;
              const avid = data['aid'] as number;
              
              if (bvid) {
                console.log('resolveBilibiliShortUrl: found BV ID:', bvid);
                // B站封面图格式：https://i0.hdslb.com/bfs/archive/{bvid}.jpg
                return `https://i0.hdslb.com/bfs/archive/${bvid}.jpg`;
              } else if (avid) {
                console.log('resolveBilibiliShortUrl: found AV ID:', avid);
                // 使用 AV 号格式：https://i0.hdslb.com/bfs/archive/av{aid}.jpg
                return `https://i0.hdslb.com/bfs/archive/av${avid}.jpg`;
              }
            }
          } catch (parseError) {
            console.error('resolveBilibiliShortUrl: Failed to parse API response:', parseError);
          }
        }
      } catch (apiError) {
        console.error('resolveBilibiliShortUrl: API request failed:', apiError);
      } finally {
        apiRequest.destroy();
      }
      
      console.log('resolveBilibiliShortUrl: could not resolve, returning undefined');
      return undefined;
    } catch (error) {
      console.error('resolveBilibiliShortUrl: unexpected error:', error);
      return undefined;
    }
  }

  /**
   * 提取抖音封面图
   */
  private extractDouyinCover(url: string): string | undefined {
    try {
      // 尝试从抖音URL中提取视频ID
      const videoIdMatch = url.match(/douyin\.com\/video\/([A-Za-z0-9]+)/) ||
                          url.match(/iesdouyin\.com\/share\/video\/([A-Za-z0-9]+)/) ||
                          url.match(/v\.douyin\.com\/([A-Za-z0-9]+)/);
      
      if (videoIdMatch && videoIdMatch[1]) {
        const videoId = videoIdMatch[1];
        // 抖音封面图格式（可能需要通过API获取，这里提供可能的格式）
        return `https://p3-pc.douyinpic.com/obj/tos-cn-p-0015/${videoId}`;
      }
      
      // 如果没有找到视频ID，使用默认封面
      return 'https://p3-pc.douyinpic.com/obj/ies-music/aweme-web-static/image/default_cover.png';
    } catch (error) {
      console.error('Failed to extract Douyin cover:', error);
      // 返回默认封面
      return 'https://p3-pc.douyinpic.com/obj/ies-music/aweme-web-static/image/default_cover.png';
    }
  }

  /**
   * 提取小红书封面图
   */
  private extractXiaohongshuCover(url: string): string | undefined {
    try {
      // 尝试从小红书URL中提取笔记ID
      const noteIdMatch = url.match(/xiaohongshu\.com\/discovery\/item\/([A-Za-z0-9]+)/) ||
                         url.match(/xhs\.com\/share\/([A-Za-z0-9]+)/);
      
      if (noteIdMatch && noteIdMatch[1]) {
        const noteId = noteIdMatch[1];
        // 小红书封面图格式（可能需要通过API获取）
        return `https://ci.xiaohongshu.com/${noteId}`;
      }
      
      // 如果没有找到笔记ID，使用默认封面
      return 'https://ci.xiaohongshu.com/static/img/default_cover.png';
    } catch (error) {
      console.error('Failed to extract Xiaohongshu cover:', error);
      // 返回默认封面
      return 'https://ci.xiaohongshu.com/static/img/default_cover.png';
    }
  }

  /**
   * 提取知乎封面图
   */
  private extractZhihuCover(url: string): string | undefined {
    try {
      // 尝试从知乎URL中提取文章ID
      const articleIdMatch = url.match(/zhihu\.com\/question\/(\d+)/) ||
                            url.match(/zhihu\.com\/answer\/(\d+)/) ||
                            url.match(/zhihu\.com\/p\/(\d+)/);
      
      if (articleIdMatch && articleIdMatch[1]) {
        const articleId = articleIdMatch[1];
        // 知乎封面图格式（可能需要通过API获取）
        // 知乎文章封面通常有特定的格式
        return `https://pic1.zhimg.com/v2-${articleId}_b.jpg`;
      }
      
      // 如果没有找到文章ID，使用默认封面
      return 'https://pic1.zhimg.com/80/v2-6c3b7e7b8c7d8c8f8e8d8c8b8a8f8e8d_720w.jpg';
    } catch (error) {
      console.error('Failed to extract Zhihu cover:', error);
      // 返回默认封面
      return 'https://pic1.zhimg.com/80/v2-6c3b7e7b8c7d8c8f8e8d8c8b8a8f8e8d_720w.jpg';
    }
  }

  /**
   * 提取微博封面图
   */
  private extractWeiboCover(url: string): string | undefined {
    try {
      // 尝试从微博URL中提取微博ID
      const weiboIdMatch = url.match(/weibo\.com\/(\d+)\/([A-Za-z0-9]+)/) ||
                          url.match(/weibo\.cn\/comment\/([A-Za-z0-9]+)/);
      
      if (weiboIdMatch) {
        // 微博封面图格式（可能需要通过API获取）
        // 微博的封面通常与用户头像相关
        return 'https://wx1.sinaimg.cn/large/default_avatar_male_50.gif';
      }
      
      // 如果没有找到微博ID，使用默认封面
      return 'https://h5.sinaimg.cn/upload/2016/11/01/1000/default_avatar_male_50.gif';
    } catch (error) {
      console.error('Failed to extract Weibo cover:', error);
      // 返回默认封面
      return 'https://h5.sinaimg.cn/upload/2016/11/01/1000/default_avatar_male_50.gif';
    }
  }

  /**
   * 提取YouTube封面图
   */
  private extractYouTubeCover(url: string): string | undefined {
    try {
      // 尝试从YouTube URL中提取视频ID
      const videoIdMatch = url.match(/youtube\.com\/watch\?v=([A-Za-z0-9_-]+)/) || 
                          url.match(/youtu\.be\/([A-Za-z0-9_-]+)/);
      if (videoIdMatch && videoIdMatch[1]) {
        const videoId = videoIdMatch[1];
        // YouTube封面图格式
        return `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`;
      }
    } catch (error) {
      console.error('Failed to extract YouTube cover:', error);
    }
    return undefined;
  }

  /**
   * 提取网站图标作为封面
   */
  private extractWebsiteFavicon(url: string): string | undefined {
    try {
      // 使用正则表达式解析URL
      const urlPattern = /^(https?:\/\/)?([^\/:]+)(:\d+)?(\/.*)?$/i;
      const match = url.match(urlPattern);
      if (match && match[2]) {
        const hostname = match[2];
        // 使用网站图标作为封面
        return `https://${hostname}/favicon.ico`;
      }
    } catch (error) {
      console.error('Failed to extract website favicon:', error);
    }
    return undefined;
  }

  /**
   * 提取Twitter/X封面图
   */
  private extractTwitterCover(url: string): string | undefined {
    try {
      // Twitter/X封面通常使用用户头像或推文中的图片
      // 这里使用Twitter的默认图标
      return 'https://abs.twimg.com/favicons/twitter.2.ico';
    } catch (error) {
      console.error('Failed to extract Twitter cover:', error);
    }
    return undefined;
  }

  /**
   * 提取Facebook封面图
   */
  private extractFacebookCover(url: string): string | undefined {
    try {
      // Facebook封面通常使用用户头像或帖子中的图片
      // 这里使用Facebook的默认图标
      return 'https://static.xx.fbcdn.net/rsrc.php/yb/r/hLRJ1GG_y0J.ico';
    } catch (error) {
      console.error('Failed to extract Facebook cover:', error);
    }
    return undefined;
  }

  /**
   * 提取Instagram封面图
   */
  private extractInstagramCover(url: string): string | undefined {
    try {
      // Instagram封面通常使用帖子中的图片
      // 这里使用Instagram的默认图标
      return 'https://static.cdninstagram.com/rsrc.php/v3/yI/r/VsNE-OHk_8a.png';
    } catch (error) {
      console.error('Failed to extract Instagram cover:', error);
    }
    return undefined;
  }

  /**
   * 提取淘宝封面图
   */
  private extractTaobaoCover(url: string): string | undefined {
    try {
      // 淘宝商品封面通常可以从URL中提取商品ID
      const productIdMatch = url.match(/id=(\d+)/);
      if (productIdMatch && productIdMatch[1]) {
        const productId = productIdMatch[1];
        // 淘宝商品图片格式
        return `https://img.alicdn.com/imgextra/i1/${productId}/O1CN01.jpg`;
      }
      // 使用淘宝默认图标
      return 'https://gw.alicdn.com/tfs/TB1qEwUvWL7gK0jSZFBXXXZZpXa-72-72.png';
    } catch (error) {
      console.error('Failed to extract Taobao cover:', error);
    }
    return undefined;
  }

  /**
   * 提取京东封面图
   */
  private extractJDCover(url: string): string | undefined {
    try {
      // 京东商品封面通常可以从URL中提取商品ID
      const productIdMatch = url.match(/product\/(\d+)\.html/) || url.match(/item\.jd\.com\/(\d+)\.html/);
      if (productIdMatch && productIdMatch[1]) {
        const productId = productIdMatch[1];
        // 京东商品图片格式
        return `https://img14.360buyimg.com/n0/jfs/t1/${productId.substring(0, 4)}/${productId}.jpg`;
      }
      // 使用京东默认图标
      return 'https://m.360buyimg.com/babel/jfs/t1/1876/12/12911/1342/5bd6d30aE7c2c9a5c/0c3b9c5e0d5c5b5c.png';
    } catch (error) {
      console.error('Failed to extract JD cover:', error);
    }
    return undefined;
  }

  /**
   * 提取百度封面图
   */
  private extractBaiduCover(url: string): string | undefined {
    try {
      // 百度使用其favicon作为封面
      return 'https://www.baidu.com/favicon.ico';
    } catch (error) {
      console.error('Failed to extract Baidu cover:', error);
    }
    return undefined;
  }

  /**
   * 提取Google封面图
   */
  private extractGoogleCover(url: string): string | undefined {
    try {
      // Google使用其favicon作为封面
      return 'https://www.google.com/favicon.ico';
    } catch (error) {
      console.error('Failed to extract Google cover:', error);
    }
    return undefined;
  }

  /**
   * 提取央视频封面图
   */
  private extractCctvCover(url: string): string | undefined {
    return 'https://www.cctv.com/favicon.ico';
  }

  /**
   * 提取腾讯视频封面图
   */
  private extractTencentVideoCover(url: string): string | undefined {
    try {
      const vidMatch = url.match(/vid[=\/]([a-zA-Z0-9]+)/);
      if (vidMatch && vidMatch[1]) {
        return `https://vpic.video.qq.com/${vidMatch[1]}.png`;
      }
    } catch (error) {
      console.error('Failed to extract Tencent Video cover:', error);
    }
    return undefined;
  }

  /**
   * 提取爱奇艺封面图
   */
  private extractIqiyiCover(url: string): string | undefined {
    return 'https://www.iqiyi.com/favicon.ico';
  }

  /**
   * 提取优酷封面图
   */
  private extractYoukuCover(url: string): string | undefined {
    return 'https://www.youku.com/favicon.ico';
  }

  /**
   * 提取芒果TV封面图
   */
  private extractMgtvCover(url: string): string | undefined {
    return 'https://www.mgtv.com/favicon.ico';
  }

  /**
   * 提取西瓜视频封面图
   */
  private extractXiguaCover(url: string): string | undefined {
    return 'https://www.ixigua.com/favicon.ico';
  }

  /**
   * 提取快手封面图
   */
  private extractKuaishouCover(url: string): string | undefined {
    return 'https://www.kuaishou.com/favicon.ico';
  }

  /**
   * 从URL中提取基本信息
   */
  private extractBaseInfo(url: string): BaseInfo {
    try {
      // 使用正则表达式解析URL
      const urlPattern = /^(https?:\/\/)?([^\/:]+)(:\d+)?(\/[^?#]*)?/i;
      const match = url.match(urlPattern);
      if (!match) {
        return {
          title: '链接',
          description: url.length > 50 ? url.substring(0, 47) + '...' : url
        };
      }
      
      const hostname = match[2] || '';
      const pathname = match[4] || '';
      
      // 从路径中提取可能的标题
      let title = '';
      const pathParts = pathname.split('/').filter(part => part.length > 0);
      
      if (pathParts.length > 0) {
        // 尝试从最后一个路径段提取标题
        const lastPart = pathParts[pathParts.length - 1];
        if (lastPart) {
          // 移除文件扩展名和特殊字符
          title = lastPart
            .replace(/\.(html|htm|php|asp|aspx|jsp|md|txt)$/i, '')
            .replace(/[-_]/g, ' ')
            .replace(/\d+/g, '')
            .trim();
            
          // 如果标题太短，使用域名
          if (title.length < 3) {
            title = hostname.replace(/^www\./, '').split('.')[0] || '网页';
          }
        }
      }
      
      // 如果没有提取到标题，使用域名
      if (!title) {
        title = hostname.replace(/^www\./, '').split('.')[0] || '网页';
      }
      
      // 首字母大写
      title = title.charAt(0).toUpperCase() + title.slice(1);
      
      return {
        title: title,
        description: `来自 ${hostname} 的链接`
      };
    } catch (error) {
      // 如果不是有效的URL，使用原始文本
      const truncated = url.length > 50 ? url.substring(0, 47) + '...' : url;
      return {
        title: '链接',
        description: truncated
      };
    }
  }

  /**
   * 验证URL是否有效
   */
  isValidUrl(url: string): boolean {
    if (!url || url.trim().length === 0) {
      return false;
    }
    
    const urlPattern = /^(https?:\/\/)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(:\d+)?(\/[^?#]*)?(\?[^#]*)?(#[^\s]*)?$/i;
    const lowerUrl = url.toLowerCase().trim();
    
    // 检查是否以常见协议开头或包含有效域名
    return urlPattern.test(lowerUrl) || 
           lowerUrl.startsWith('http://') || 
           lowerUrl.startsWith('https://') ||
           lowerUrl.startsWith('www.');
  }

  /**
   * 从文本中提取URL
   */
  extractUrlFromText(text: string): string | null {
    if (!text || text.trim().length === 0) {
      return null;
    }
    
    const urlPattern = /https?:\/\/[^\s]+|www\.[^\s]+/gi;
    const matches = text.match(urlPattern);
    
    if (matches && matches.length > 0) {
      let url = matches[0];
      
      // 确保URL有协议
      if (url.startsWith('www.')) {
        url = 'https://' + url;
      }
      
      return url;
    }
    
    return null;
  }

  /**
   * 获取支持的平台列表
   */
  getSupportedPlatforms(): PlatformInfo[] {
    return [
      {
        name: '哔哩哔哩',
        packageName: 'tv.danmaku.bili',
        domains: ['bilibili.com', 'b23.tv'],
        type: 'video'
      },
      {
        name: '抖音',
        packageName: 'com.ss.android.ugc.aweme',
        domains: ['douyin.com', 'tiktok.com', 'iesdouyin.com'],
        type: 'video'
      },
      {
        name: '小红书',
        packageName: 'com.xingin.xhs',
        domains: ['xiaohongshu.com', 'xhs.com'],
        type: 'article'
      },
      {
        name: '知乎',
        packageName: 'com.zhihu.android',
        domains: ['zhihu.com'],
        type: 'article'
      },
      {
        name: '微博',
        packageName: 'com.sina.weibo',
        domains: ['weibo.com', 'weibo.cn'],
        type: 'article'
      },
      {
        name: 'YouTube',
        packageName: 'com.google.android.youtube',
        domains: ['youtube.com', 'youtu.be'],
        type: 'video'
      },
      {
        name: 'Twitter',
        packageName: 'com.twitter.android',
        domains: ['twitter.com', 'x.com'],
        type: 'article'
      },
      {
        name: 'Facebook',
        packageName: 'com.facebook.katana',
        domains: ['facebook.com', 'fb.com'],
        type: 'article'
      },
      {
        name: 'Instagram',
        packageName: 'com.instagram.android',
        domains: ['instagram.com'],
        type: 'image'
      },
      {
        name: '淘宝',
        packageName: 'com.taobao.taobao',
        domains: ['taobao.com'],
        type: 'website'
      },
      {
        name: '京东',
        packageName: 'com.jingdong.app.mall',
        domains: ['jd.com'],
        type: 'website'
      },
      {
        name: '百度',
        packageName: 'com.baidu.searchbox',
        domains: ['baidu.com'],
        type: 'website'
      },
      {
        name: 'Google',
        packageName: 'com.google.android.googlequicksearchbox',
        domains: ['google.com'],
        type: 'website'
      }
    ];
  }
}

export const urlParserService = UrlParserService.getInstance();