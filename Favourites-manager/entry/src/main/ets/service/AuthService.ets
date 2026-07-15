import { authentication } from '@kit.AccountKit';
import { preferences } from '@kit.ArkData';
import { common } from '@kit.AbilityKit';
import { hilog } from '@kit.PerformanceAnalysisKit';
import { BusinessError } from '@kit.BasicServicesKit';
import { emitter } from '@kit.BasicServicesKit';
import { util } from '@kit.ArkTS';

const TAG = 'AuthService';
const DOMAIN = 0xFF00;
const AUTH_PREFERENCES = 'auth_preferences';
const USER_INFO_KEY = 'user_info';

/**
 * 用户信息接口
 */
export interface UserInfo {
  openID: string;
  unionID: string;
  displayName: string;
  avatarUri: string;
  email: string;
  countryCode: string;
  phoneNumber: string;
}

/**
 * 认证事件类型
 */
export class AuthEventType {
  static readonly LOGIN_SUCCESS = 3001;
  static readonly LOGOUT_SUCCESS = 3002;
}

/**
 * 认证服务 - 华为账号静默登录
 */
export class AuthService {
  private static instance: AuthService;
  private preferences: preferences.Preferences | null = null;
  private currentUser: UserInfo | null = null;

  private constructor() {
    // 初始化AppStorage中的登录状态
    if (AppStorage.get<boolean>('isLoggedIn') === undefined) {
      AppStorage.setOrCreate('isLoggedIn', false);
    }
    if (AppStorage.get<UserInfo | null>('currentUser') === undefined) {
      AppStorage.setOrCreate('currentUser', null);
    }
  }

  static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  /**
   * 初始化服务
   */
  async init(context: common.Context): Promise<void> {
    try {
      this.preferences = await preferences.getPreferences(context, AUTH_PREFERENCES);
      await this.loadSavedUser();
    } catch (error) {
      hilog.error(DOMAIN, TAG, `Failed to init AuthService: ${JSON.stringify(error)}`);
    }
  }

  /**
   * 加载已保存的用户信息
   */
  private async loadSavedUser(): Promise<void> {
    if (!this.preferences) return;
    
    try {
      const userJson = await this.preferences.get(USER_INFO_KEY, '') as string;
      if (userJson) {
        this.currentUser = JSON.parse(userJson) as UserInfo;
        AppStorage.setOrCreate('isLoggedIn', true);
        AppStorage.setOrCreate('currentUser', this.currentUser);
      }
    } catch (error) {
      hilog.error(DOMAIN, TAG, `Failed to load saved user: ${JSON.stringify(error)}`);
    }
  }

  /**
   * 获取当前用户信息
   */
  getCurrentUser(): UserInfo | null {
    return this.currentUser;
  }

  /**
   * 判断是否已登录
   */
  isLoggedIn(): boolean {
    return this.currentUser !== null;
  }

  /**
   * 华为账号静默登录 - 应用启动时自动调用
   * 无需用户交互，自动尝试登录华为账号
   */
  async silentLogin(): Promise<UserInfo | null> {
    try {
      const loginRequest = new authentication.HuaweiIDProvider().createLoginWithHuaweiIDRequest();
      loginRequest.forceLogin = false; // 静默登录，不弹出登录界面
      loginRequest.state = util.generateRandomUUID();
      
      const controller = new authentication.AuthenticationController();
      const response = await controller.executeRequest(loginRequest) as authentication.LoginWithHuaweiIDResponse;
      
      const credential = response?.data;
      if (credential) {
        const userInfo: UserInfo = {
          openID: credential.openID || '',
          unionID: credential.unionID || '',
          displayName: '华为用户',
          avatarUri: '',
          email: '',
          countryCode: '',
          phoneNumber: ''
        };
        
        this.currentUser = userInfo;
        AppStorage.setOrCreate('isLoggedIn', true);
        AppStorage.setOrCreate('currentUser', userInfo);
        await this.saveUserInfo(userInfo);
        emitter.emit({ eventId: AuthEventType.LOGIN_SUCCESS });
        
        hilog.info(DOMAIN, TAG, 'Silent login succeeded');
        return userInfo;
      }
      return null;
    } catch (error) {
      const err = error as BusinessError;
      hilog.info(DOMAIN, TAG, `Silent login failed (code=${err.code}): user not logged in Huawei account`);
      return null;
    }
  }

  /**
   * 华为账号登录 - 用户主动点击登录按钮时调用
   * 会弹出华为账号登录界面
   */
  async loginWithHuaweiID(): Promise<UserInfo | null> {
    try {
      const loginRequest = new authentication.HuaweiIDProvider().createLoginWithHuaweiIDRequest();
      loginRequest.forceLogin = true; // 强制登录，弹出登录界面
      loginRequest.state = util.generateRandomUUID();
      
      const controller = new authentication.AuthenticationController();
      const response = await controller.executeRequest(loginRequest) as authentication.LoginWithHuaweiIDResponse;
      
      const credential = response?.data;
      if (credential) {
        const userInfo: UserInfo = {
          openID: credential.openID || '',
          unionID: credential.unionID || '',
          displayName: '华为用户',
          avatarUri: '',
          email: '',
          countryCode: '',
          phoneNumber: ''
        };
        
        this.currentUser = userInfo;
        AppStorage.setOrCreate('isLoggedIn', true);
        AppStorage.setOrCreate('currentUser', userInfo);
        await this.saveUserInfo(userInfo);
        emitter.emit({ eventId: AuthEventType.LOGIN_SUCCESS });
        
        hilog.info(DOMAIN, TAG, 'Login with HuaweiID succeeded');
        return userInfo;
      }
      return null;
    } catch (error) {
      const err = error as BusinessError;
      hilog.error(DOMAIN, TAG, `Login with HuaweiID failed: ${err.code} - ${err.message}`);
      return null;
    }
  }

  /**
   * 退出登录
   */
  async logout(): Promise<void> {
    this.currentUser = null;
    AppStorage.setOrCreate('isLoggedIn', false);
    AppStorage.setOrCreate('currentUser', null);
    
    // 清除保存的用户信息
    if (this.preferences) {
      await this.preferences.delete(USER_INFO_KEY);
      await this.preferences.flush();
    }
    
    // 发送登出成功事件
    emitter.emit({ eventId: AuthEventType.LOGOUT_SUCCESS });
    
    hilog.info(DOMAIN, TAG, 'User logged out');
  }

  /**
   * 保存用户信息到本地
   */
  private async saveUserInfo(userInfo: UserInfo): Promise<void> {
    if (!this.preferences) return;
    
    try {
      await this.preferences.put(USER_INFO_KEY, JSON.stringify(userInfo));
      await this.preferences.flush();
    } catch (error) {
      hilog.error(DOMAIN, TAG, `Failed to save user info: ${JSON.stringify(error)}`);
    }
  }
}

// 导出单例实例
export const authService = AuthService.getInstance();