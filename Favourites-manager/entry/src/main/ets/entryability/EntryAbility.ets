import { AbilityConstant, ConfigurationConstant, UIAbility, Want } from '@kit.AbilityKit';
import { hilog } from '@kit.PerformanceAnalysisKit';
import { window } from '@kit.ArkUI';
import { dataService } from '../service/DataService';
import { authService } from '../service/AuthService';
import { formInfo, formProvider, formBindingData } from '@kit.FormKit';

const DOMAIN = 0x0000;
const TAG = 'EntryAbility';

export default class EntryAbility extends UIAbility {
  async onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): Promise<void> {
    hilog.info(DOMAIN, TAG, '%{public}s', 'Ability onCreate');
    
    try {
      // 初始化数据服务
      await dataService.init(this.context);
      hilog.info(DOMAIN, TAG, '%{public}s', 'DataService initialized successfully');
    } catch (error) {
      hilog.error(DOMAIN, TAG, 'DataService init failed: %{public}s', JSON.stringify(error));
    }
    
    try {
      // 初始化认证服务
      await authService.init(this.context);
      hilog.info(DOMAIN, TAG, '%{public}s', 'AuthService initialized successfully');
      
      // 自动执行华为账号静默登录
      const userInfo = await authService.silentLogin();
      if (userInfo) {
        hilog.info(DOMAIN, TAG, 'Silent login succeeded, user: %{public}s', userInfo.openID);
      } else {
        hilog.info(DOMAIN, TAG, '%{public}s', 'Silent login skipped - user not logged in Huawei account');
      }
    } catch (error) {
      hilog.error(DOMAIN, TAG, 'AuthService init or silent login failed: %{public}s', JSON.stringify(error));
    }
    
    try {
      this.context.getApplicationContext().setColorMode(ConfigurationConstant.ColorMode.COLOR_MODE_NOT_SET);
    } catch (err) {
      hilog.error(DOMAIN, TAG, 'Failed to set colorMode. Cause: %{public}s', JSON.stringify(err));
    }
    
    // 处理从服务卡片跳转
    if (want.parameters) {
      const params = want.parameters['params'];
      if (params) {
        hilog.info(DOMAIN, TAG, 'From widget: %{public}s', JSON.stringify(params));
      }
    }
  }

  onDestroy(): void {
    hilog.info(DOMAIN, TAG, '%{public}s', 'Ability onDestroy');
  }

  onWindowStageCreate(windowStage: window.WindowStage): void {
    hilog.info(DOMAIN, TAG, '%{public}s', 'Ability onWindowStageCreate');

    windowStage.loadContent('pages/MainPage', (err) => {
      if (err.code) {
        hilog.error(DOMAIN, TAG, 'Failed to load the content. Cause: %{public}s', JSON.stringify(err));
        return;
      }
      hilog.info(DOMAIN, TAG, 'Succeeded in loading the content.');
    });
  }

  onWindowStageDestroy(): void {
    hilog.info(DOMAIN, TAG, '%{public}s', 'Ability onWindowStageDestroy');
  }

  onForeground(): void {
    hilog.info(DOMAIN, TAG, '%{public}s', 'Ability onForeground');
  }

  onBackground(): void {
    hilog.info(DOMAIN, TAG, '%{public}s', 'Ability onBackground');
  }
}