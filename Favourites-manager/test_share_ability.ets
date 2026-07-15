// 测试ShareAbility的extractSourceApp方法
import { hilog } from '@kit.PerformanceAnalysisKit';

const DOMAIN = 0xFF00;
const TAG = 'TestShareAbility';

// 模拟不同的分享场景
function testExtractSourceApp() {
  console.log('Testing extractSourceApp method...');
  
  // 测试1: 从Want中提取来源应用
  const testWant1 = {
    bundleName: 'com.tencent.mm',
    parameters: {
      'ohos.extra.param.key.sourceBundleName': 'com.tencent.mm'
    }
  };
  
  // 测试2: 从文本中提取来源应用
  const testWant2 = {
    parameters: {
      'ohos.extra.param.key.clipData': '分享自微信的内容'
    }
  };
  
  // 测试3: 从URI中提取来源应用
  const testWant3 = {
    uri: 'https://www.bilibili.com/video/BV1GJ411x7h7'
  };
  
  // 测试4: 从参数中提取来源应用
  const testWant4 = {
    parameters: {
      'ohos.extra.param.key.sourceApp': '哔哩哔哩'
    }
  };
  
  console.log('Test 1 - WeChat share:', testWant1);
  console.log('Test 2 - Text with source:', testWant2);
  console.log('Test 3 - URI from Bilibili:', testWant3);
  console.log('Test 4 - Direct source app:', testWant4);
  
  // 测试getAppNameFromBundle方法
  console.log('\nTesting getAppNameFromBundle method...');
  
  const testBundles = [
    'com.tencent.mm',
    'com.tencent.mobileqq',
    'com.sina.weibo',
    'tv.danmaku.bili',
    'com.xingin.xhs',
    'com.ss.android.ugc.aweme',
    'com.zhihu.android',
    'com.google.android.youtube',
    'com.twitter.android',
    'com.facebook.katana',
    'com.instagram.android',
    'com.taobao.taobao',
    'com.jingdong.app.mall',
    'com.baidu.searchbox',
    'com.google.android.googlequicksearchbox',
    'com.example.quickstart' // 当前应用
  ];
  
  testBundles.forEach(bundle => {
    // 这里应该调用实际的getAppNameFromBundle方法
    console.log(`Bundle: ${bundle} -> App Name: [需要实际调用方法]`);
  });
  
  console.log('\nTest completed.');
}

// 运行测试
testExtractSourceApp();