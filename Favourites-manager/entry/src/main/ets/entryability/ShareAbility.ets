import { AbilityConstant, UIAbility, Want } from '@kit.AbilityKit';
import { window } from '@kit.ArkUI';
import { systemShare } from '@kit.ShareKit';
import { BusinessError } from '@kit.BasicServicesKit';
import { hilog } from '@kit.PerformanceAnalysisKit';
import { UrlParserService } from '../service/UrlParserService';

const DOMAIN = 0x0000;
const TAG = 'ShareAbility';

/**
 * 分享数据结构
 */
class SharedDataInfo {
  title: string = '';
  text: string = '';
  url: string = '';
  imageUri: string = '';
  sourceApp: string = '';
  sourcePackage: string = '';
}

/**
 * 分享接收Ability
 */
export default class ShareAbility extends UIAbility {
  private sharedData: SharedDataInfo = new SharedDataInfo();

  onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void {
    hilog.info(DOMAIN, TAG, 'ShareAbility onCreate');
    
    // 打印完整的 want 信息用于调试
    hilog.info(DOMAIN, TAG, `Want bundleName: ${want.bundleName ?? 'null'}`);
    hilog.info(DOMAIN, TAG, `Want action: ${want.action ?? 'null'}`);
    hilog.info(DOMAIN, TAG, `Want uri: ${want.uri ?? 'null'}`);
    if (want.parameters) {
      hilog.info(DOMAIN, TAG, `Want parameters keys: ${Object.keys(want.parameters).join(', ')}`);
      // 打印所有参数
      for (const key of Object.keys(want.parameters)) {
        hilog.info(DOMAIN, TAG, `  ${key}: ${want.parameters[key]}`);
      }
    }
    
    systemShare.getSharedData(want)
      .then((data: systemShare.SharedData) => {
        hilog.info(DOMAIN, TAG, 'Got shared data');
        const records = data.getRecords();
        hilog.info(DOMAIN, TAG, `Records count: ${records.length}`);
        
        if (records.length > 0) {
          const record = records[0];
          hilog.info(DOMAIN, TAG, `Record title: ${record.title ?? 'null'}`);
          hilog.info(DOMAIN, TAG, `Record content: ${record.content ?? 'null'}`);
          hilog.info(DOMAIN, TAG, `Record uri: ${record.uri ?? 'null'}`);
          
          this.sharedData = new SharedDataInfo();
          this.sharedData.title = record.title ?? '';
          this.sharedData.text = record.content ?? '';
          
          // URL 可能在 uri 或 content 中
          let url = record.uri ?? '';
          if (!url || url.length === 0) {
            // 检查 content 是否是 URL
            const content = record.content ?? '';
            if (content.startsWith('http://') || content.startsWith('https://') || 
                content.includes('.com') || content.includes('.tv') || content.includes('.cn')) {
              url = content;
              hilog.info(DOMAIN, TAG, `URL extracted from content: ${url}`);
            }
          }
          this.sharedData.url = url;
          
          this.sharedData.imageUri = this.extractImageUri(record);
          this.sharedData.sourceApp = this.extractSourceApp(want, record);
          this.sharedData.sourcePackage = this.extractSourcePackage(want);
          
          hilog.info(DOMAIN, TAG, `=== Final shared data ===`);
          hilog.info(DOMAIN, TAG, `  title: ${this.sharedData.title}`);
          hilog.info(DOMAIN, TAG, `  text: ${this.sharedData.text}`);
          hilog.info(DOMAIN, TAG, `  url: ${this.sharedData.url}`);
          hilog.info(DOMAIN, TAG, `  imageUri: ${this.sharedData.imageUri}`);
          hilog.info(DOMAIN, TAG, `  sourceApp: ${this.sharedData.sourceApp}`);
          hilog.info(DOMAIN, TAG, `  sourcePackage: ${this.sharedData.sourcePackage}`);
          
          AppStorage.setOrCreate('pendingShareData', this.sharedData);
          
          // 如果没有封面图片但有 URL，异步解析 URL 获取封面（不阻塞主流程）
          if (!this.sharedData.imageUri && this.sharedData.url) {
            hilog.info(DOMAIN, TAG, 'No imageUri, trying to parse URL for cover async');
            this.parseUrlForCover(this.sharedData.url);
          }
        }
      })
      .catch((error: BusinessError) => {
        hilog.error(DOMAIN, TAG, `Failed to getSharedData: ${error.message}, code: ${error.code}`);
        this.parseWantDirectly(want);
      });
  }

  /**
   * 直接从Want中解析分享数据
   */
  private parseWantDirectly(want: Want): void {
    try {
      hilog.info(DOMAIN, TAG, 'parseWantDirectly: parsing want directly');
      
      if (want.parameters !== undefined) {
        const params = want.parameters;
        
        // 打印所有参数
        hilog.info(DOMAIN, TAG, 'parseWantDirectly: all parameters:');
        for (const key of Object.keys(params)) {
          hilog.info(DOMAIN, TAG, `  ${key}: ${params[key]}`);
        }
        
        this.sharedData = new SharedDataInfo();
        this.sharedData.title = (params['title'] ?? params['subject'] ?? '') as string;
        this.sharedData.text = (params['text'] ?? params['content'] ?? '') as string;
        this.sharedData.url = (params['url'] ?? params['link'] ?? params['uri'] ?? '') as string;
        this.sharedData.imageUri = (params['imageUri'] ?? params['stream'] ?? params['image'] ?? '') as string;
        this.sharedData.sourceApp = this.extractSourceApp(want);
        this.sharedData.sourcePackage = this.extractSourcePackage(want);
        
        hilog.info(DOMAIN, TAG, `=== parseWantDirectly result ===`);
        hilog.info(DOMAIN, TAG, `  title: ${this.sharedData.title}`);
        hilog.info(DOMAIN, TAG, `  text: ${this.sharedData.text}`);
        hilog.info(DOMAIN, TAG, `  url: ${this.sharedData.url}`);
        hilog.info(DOMAIN, TAG, `  imageUri: ${this.sharedData.imageUri}`);
        hilog.info(DOMAIN, TAG, `  sourceApp: ${this.sharedData.sourceApp}`);
        
        AppStorage.setOrCreate('pendingShareData', this.sharedData);
      } else {
        // 如果没有 parameters，尝试从 want 的其他字段获取
        hilog.info(DOMAIN, TAG, 'parseWantDirectly: no parameters, trying other fields');
        this.sharedData = new SharedDataInfo();
        this.sharedData.title = want.uri ?? '';
        this.sharedData.url = want.uri ?? '';
        this.sharedData.sourceApp = this.extractSourceApp(want);
        this.sharedData.sourcePackage = this.extractSourcePackage(want);
        
        AppStorage.setOrCreate('pendingShareData', this.sharedData);
      }
    } catch (error) {
      hilog.error(DOMAIN, TAG, `parseWantDirectly failed: ${JSON.stringify(error)}`);
    }
  }

  /**
   * 异步解析 URL 获取封面图片
   */
  private async parseUrlForCover(url: string): Promise<void> {
    hilog.info(DOMAIN, TAG, `parseUrlForCover: parsing URL: ${url}`);
    try {
      const urlParser = UrlParserService.getInstance();
      const parsedInfo = await urlParser.parseUrl(url);
      hilog.info(DOMAIN, TAG, `parseUrlForCover: parsed info: ${JSON.stringify(parsedInfo)}`);
      
      if (parsedInfo.coverImage && parsedInfo.coverImage.length > 0) {
        this.sharedData.imageUri = parsedInfo.coverImage;
        hilog.info(DOMAIN, TAG, `parseUrlForCover: got cover: ${this.sharedData.imageUri}`);
        // 更新 AppStorage 中的数据
        AppStorage.setOrCreate('pendingShareData', this.sharedData);
      }
    } catch (error) {
      hilog.error(DOMAIN, TAG, `parseUrlForCover failed: ${JSON.stringify(error)}`);
    }
  }

  /**
   * 提取图片URI
   */
  private extractImageUri(record: systemShare.SharedRecord): string {
    hilog.info(DOMAIN, TAG, 'extractImageUri: starting extraction');
    
    // 方法1: 检查 thumbnailUri（HarmonyOS ShareKit 提供的缩略图 URI，API 12+）
    if (record.thumbnailUri && record.thumbnailUri.length > 0) {
      hilog.info(DOMAIN, TAG, `extractImageUri: found thumbnailUri: ${record.thumbnailUri}`);
      return record.thumbnailUri;
    }
    
    // 方法2: 检查 URI 是否是图片类型
    if (record.uri) {
      const uri = record.uri.toLowerCase();
      if (uri.includes('.jpg') || uri.includes('.jpeg') || 
          uri.includes('.png') || uri.includes('.gif') ||
          uri.includes('.webp') || uri.includes('.bmp')) {
        hilog.info(DOMAIN, TAG, `extractImageUri: found image uri: ${record.uri}`);
        return record.uri;
      }
    }
    
    // 方法3: 检查 content 是否包含图片 URL
    const content = record.content ?? '';
    if (content.startsWith('http://') || content.startsWith('https://')) {
      const contentLower = content.toLowerCase();
      if (contentLower.includes('.jpg') || contentLower.includes('.jpeg') || 
          contentLower.includes('.png') || contentLower.includes('.gif') ||
          contentLower.includes('.webp') || contentLower.includes('.bmp')) {
        hilog.info(DOMAIN, TAG, `extractImageUri: found image in content: ${content}`);
        return content;
      }
    }
    
    hilog.info(DOMAIN, TAG, 'extractImageUri: no image URI found');
    return '';
  }

  /**
   * 提取来源应用信息
   */
  private extractSourceApp(want: Want, record?: systemShare.SharedRecord): string {
    const currentAppBundleName = 'com.example.quickstart'; // 当前应用的包名
    
    hilog.info(DOMAIN, TAG, 'extractSourceApp: starting extraction');
    
    // 方法1: 从 ohos.aafwk.param.callerBundleName 获取（HarmonyOS 分享时使用）
    if (want.parameters !== undefined) {
      const callerBundleName = want.parameters['ohos.aafwk.param.callerBundleName'] as string;
      if (callerBundleName && callerBundleName.length > 0 && callerBundleName !== currentAppBundleName) {
        const appName = this.getAppNameFromBundle(callerBundleName);
        hilog.info(DOMAIN, TAG, `extractSourceApp: from callerBundleName - ${callerBundleName} -> ${appName}`);
        if (appName !== '未知应用') {
          return appName;
        }
      }
      
      // 方法2: 从 ohos.extra.param.key.sourceBundleName 获取
      const sourceBundleName = want.parameters['ohos.extra.param.key.sourceBundleName'] as string;
      if (sourceBundleName && sourceBundleName.length > 0 && sourceBundleName !== currentAppBundleName) {
        const appName = this.getAppNameFromBundle(sourceBundleName);
        hilog.info(DOMAIN, TAG, `extractSourceApp: from sourceBundleName - ${sourceBundleName} -> ${appName}`);
        if (appName !== '未知应用') {
          return appName;
        }
      }
      
      // 方法3: 尝试其他可能的参数名
      const paramKeys = [
        'sourceApp',
        'sourceApplication',
        'fromApp',
        'sharingApp',
        'originApp',
        'callerBundleName',
        'sourceBundleName'
      ];
      
      for (const key of paramKeys) {
        const value = want.parameters[key] as string;
        if (value && value.length > 0 && value !== currentAppBundleName) {
          const appName = this.getAppNameFromBundle(value);
          if (appName !== '未知应用') {
            hilog.info(DOMAIN, TAG, `extractSourceApp: from parameter ${key} - ${value} -> ${appName}`);
            return appName;
          }
        }
      }
    }
    
    // 方法4: 从Want的bundleName中获取（排除当前应用）
    if (want.bundleName && want.bundleName.length > 0 && want.bundleName !== currentAppBundleName) {
      const appName = this.getAppNameFromBundle(want.bundleName);
      hilog.info(DOMAIN, TAG, `extractSourceApp: from bundleName - ${want.bundleName} -> ${appName}`);
      return appName;
    }
    
    // 方法3: 从分享数据中提取应用信息
    if (record) {
      // 从标题或内容中提取应用信息
      const textToSearch = (record.title + ' ' + record.content).toLowerCase();
      
      // 常见应用关键词识别
      const appKeywords: Record<string, string> = {
        '微信': '微信',
        'wechat': '微信',
        'qq': 'QQ',
        '微博': '微博',
        'weibo': '微博',
        '哔哩哔哩': '哔哩哔哩',
        'bilibili': '哔哩哔哩',
        'b站': '哔哩哔哩',
        '小红书': '小红书',
        'xhs': '小红书',
        '抖音': '抖音',
        'douyin': '抖音',
        'tiktok': '抖音',
        '知乎': '知乎',
        'zhihu': '知乎',
        'youtube': 'YouTube',
        'twitter': 'Twitter',
        'x.com': 'Twitter',
        'facebook': 'Facebook',
        'instagram': 'Instagram',
        '浏览器': '浏览器',
        'chrome': 'Chrome',
        'safari': 'Safari',
        'firefox': 'Firefox'
      };
      
      const appKeywordsEntries = Object.entries(appKeywords);
      for (let i = 0; i < appKeywordsEntries.length; i++) {
        const keyword = appKeywordsEntries[i][0];
        const appName = appKeywordsEntries[i][1];
        if (textToSearch.includes(keyword.toLowerCase())) {
          hilog.info(DOMAIN, TAG, `extractSourceApp: from text keyword - ${keyword} -> ${appName}`);
          return appName;
        }
      }
    }
    
    // 方法4: 从URI中推断
    if (record && record.uri) {
      const uri = record.uri.toLowerCase();
      const uriPatterns: Record<string, string> = {
        'bilibili.com': '哔哩哔哩',
        'b23.tv': '哔哩哔哩',
        'weibo.com': '微博',
        'weibo.cn': '微博',
        'zhihu.com': '知乎',
        'xiaohongshu.com': '小红书',
        'xhs.com': '小红书',
        'douyin.com': '抖音',
        'tiktok.com': '抖音',
        'youtube.com': 'YouTube',
        'youtu.be': 'YouTube',
        'twitter.com': 'Twitter',
        'x.com': 'Twitter',
        'facebook.com': 'Facebook',
        'instagram.com': 'Instagram',
        'taobao.com': '淘宝',
        'tmall.com': '天猫',
        'jd.com': '京东',
        'baidu.com': '百度',
        'google.com': 'Google'
      };
      
      const uriPatternsEntries = Object.entries(uriPatterns);
      for (let i = 0; i < uriPatternsEntries.length; i++) {
        const pattern = uriPatternsEntries[i][0];
        const appName = uriPatternsEntries[i][1];
        if (uri.includes(pattern)) {
          hilog.info(DOMAIN, TAG, `extractSourceApp: from URI pattern - ${pattern} -> ${appName}`);
          return appName;
        }
      }
    }
    
    hilog.info(DOMAIN, TAG, 'extractSourceApp: unknown source');
    return '未知应用';
  }

  /**
   * 提取来源应用包名
   */
  private extractSourcePackage(want: Want): string {
    if (want.parameters !== undefined) {
      // 优先使用 callerBundleName（HarmonyOS 分享时使用）
      const callerBundleName = want.parameters['ohos.aafwk.param.callerBundleName'] as string;
      if (callerBundleName && callerBundleName.length > 0) {
        return callerBundleName;
      }
      
      // 备用：使用 sourceBundleName
      const sourceBundleName = want.parameters['ohos.extra.param.key.sourceBundleName'] as string;
      if (sourceBundleName && sourceBundleName.length > 0) {
        return sourceBundleName;
      }
    }
    
    if (want.bundleName && want.bundleName.length > 0) {
      return want.bundleName;
    }
    
    return '';
  }

  /**
   * 根据包名获取应用名称
   */
  private getAppNameFromBundle(bundleName: string): string {
    const appMap: Record<string, string> = {
      // HarmonyOS 应用包名
      'yylx.danmaku.bili': '哔哩哔哩',  // HarmonyOS 哔哩哔哩
      'com.tencent.mm': '微信',
      'com.tencent.mobileqq': 'QQ',
      'com.sina.weibo': '微博',
      'com.huawei.browser': '华为浏览器',
      // Android 应用包名（兼容）
      'tv.danmaku.bili': '哔哩哔哩',
      'com.xingin.xhs': '小红书',
      'com.ss.android.ugc.aweme': '抖音',
      'com.zhihu.android': '知乎',
      'com.android.browser': '浏览器',
      'com.android.chrome': 'Chrome',
      'com.huawei.himovie': '华为视频',
      'com.huawei.news': '华为阅读',
      'com.huawei.notes': '备忘录',
      'com.huawei.filemanager': '文件管理',
      'com.huawei.health': '运动健康',
      'com.google.android.youtube': 'YouTube',
      'com.twitter.android': 'Twitter',
      'com.facebook.katana': 'Facebook',
      'com.instagram.android': 'Instagram',
      'com.taobao.taobao': '淘宝',
      'com.tmall.wireless': '天猫',
      'com.jingdong.app.mall': '京东',
      'com.baidu.searchbox': '百度',
      'com.google.android.googlequicksearchbox': 'Google',
      'com.android.vending': 'Google Play',
      'com.netease.cloudmusic': '网易云音乐',
      'com.tencent.qqmusic': 'QQ音乐',
      'com.kugou.android': '酷狗音乐',
      'com.youku.phone': '优酷',
      'com.qiyi.video': '爱奇艺',
      'com.tencent.videolite': '腾讯视频',
      'com.ss.android.article.news': '今日头条',
      'com.ss.android.article.video': '西瓜视频',
      'com.tencent.news': '腾讯新闻',
      'com.sohu.newsclient': '搜狐新闻',
      'com.ifeng.news2': '凤凰新闻',
      'com.sina.news': '新浪新闻'
    };
    
    const name = appMap[bundleName];
    if (name !== undefined) {
      return name;
    }
    
    // 尝试从包名中提取应用名
    const parts = bundleName.split('.');
    if (parts.length > 0) {
      const lastPart = parts[parts.length - 1];
      if (lastPart && lastPart.length > 0) {
        // 简单的包名到应用名转换
        const appNameMap: Record<string, string> = {
          'mm': '微信',
          'mobileqq': 'QQ',
          'weibo': '微博',
          'browser': '浏览器',
          'chrome': 'Chrome',
          'bili': '哔哩哔哩',
          'xhs': '小红书',
          'aweme': '抖音',
          'zhihu': '知乎',
          'himovie': '华为视频',
          'news': '新闻',
          'notes': '笔记',
          'filemanager': '文件管理',
          'health': '健康'
        };
        
        const mappedName = appNameMap[lastPart];
        if (mappedName) {
          return mappedName;
        }
        
        // 将下划线/驼峰转换为空格
        const formattedName = lastPart.replace(/([A-Z])/g, ' $1').replace(/_/g, ' ').trim();
        return formattedName.charAt(0).toUpperCase() + formattedName.slice(1);
      }
    }
    
    return '未知应用';
  }

  onWindowStageCreate(windowStage: window.WindowStage): void {
    hilog.info(DOMAIN, TAG, 'ShareAbility onWindowStageCreate');
    
    windowStage.loadContent('pages/SaveShare', (err) => {
      if (err.code) {
        hilog.error(DOMAIN, TAG, `Failed to load content: ${JSON.stringify(err)}`);
        return;
      }
      hilog.info(DOMAIN, TAG, 'Succeeded in loading SaveShare page');
    });
  }

  onDestroy(): void {
    hilog.info(DOMAIN, TAG, 'ShareAbility onDestroy');
    AppStorage.delete('pendingShareData');
  }

  onForeground(): void {
    hilog.info(DOMAIN, TAG, 'ShareAbility onForeground');
  }

  onBackground(): void {
    hilog.info(DOMAIN, TAG, 'ShareAbility onBackground');
  }
}