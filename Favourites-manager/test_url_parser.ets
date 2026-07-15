import { urlParserService } from './entry/src/main/ets/service/UrlParserService.ets';

// 测试URL解析功能
console.log('Testing URL parser service...');

// 测试哔哩哔哩URL
const bilibiliUrl = 'https://www.bilibili.com/video/BV1GJ411x7h7';
const bilibiliInfo = urlParserService.parseUrl(bilibiliUrl);
console.log('Bilibili URL:', bilibiliUrl);
console.log('Parsed info:', JSON.stringify(bilibiliInfo, null, 2));

// 测试抖音URL
const douyinUrl = 'https://www.douyin.com/video/123456789';
const douyinInfo = urlParserService.parseUrl(douyinUrl);
console.log('Douyin URL:', douyinUrl);
console.log('Parsed info:', JSON.stringify(douyinInfo, null, 2));

// 测试小红书URL
const xhsUrl = 'https://www.xiaohongshu.com/discovery/item/123456789';
const xhsInfo = urlParserService.parseUrl(xhsUrl);
console.log('Xiaohongshu URL:', xhsUrl);
console.log('Parsed info:', JSON.stringify(xhsInfo, null, 2));

// 测试知乎URL
const zhihuUrl = 'https://www.zhihu.com/question/123456789';
const zhihuInfo = urlParserService.parseUrl(zhihuUrl);
console.log('Zhihu URL:', zhihuUrl);
console.log('Parsed info:', JSON.stringify(zhihuInfo, null, 2));

// 测试微博URL
const weiboUrl = 'https://weibo.com/123456789/123456789';
const weiboInfo = urlParserService.parseUrl(weiboUrl);
console.log('Weibo URL:', weiboUrl);
console.log('Parsed info:', JSON.stringify(weiboInfo, null, 2));

// 测试YouTube URL
const youtubeUrl = 'https://www.youtube.com/watch?v=123456789';
const youtubeInfo = urlParserService.parseUrl(youtubeUrl);
console.log('YouTube URL:', youtubeUrl);
console.log('Parsed info:', JSON.stringify(youtubeInfo, null, 2));

// 测试网站URL
const websiteUrl = 'https://www.example.com/article/123';
const websiteInfo = urlParserService.parseUrl(websiteUrl);
console.log('Website URL:', websiteUrl);
console.log('Parsed info:', JSON.stringify(websiteInfo, null, 2));

console.log('Test completed.');