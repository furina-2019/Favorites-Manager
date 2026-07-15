import { preferences } from '@kit.ArkData';
import { common } from '@kit.AbilityKit';
import { hilog } from '@kit.PerformanceAnalysisKit';
import { emitter } from '@kit.BasicServicesKit';

const TAG = 'LocalAuthService';
const DOMAIN = 0xFF00;
const AUTH_PREFERENCES = 'local_auth_preferences';
const USER_INFO_KEY = 'user_info';

/**
 * 本地用户信息接口
 */
export interface LocalUserInfo {
  username: string;
  avatar: string;
  createdAt: number;
}

/**
 * 本地登录服务 - 简单的本地账号管理
 */
class LocalAuthService {
  private context: common.UIAbilityContext | null = null;
  private prefs: preferences.Preferences | null = null;
  private currentUser: LocalUserInfo | null = null;

  /**
   * 初始化服务
   */
  async init(context: common.UIAbilityContext): Promise<void> {
    this.context = context;
    try {
      this.prefs = await preferences.getPreferences(context, AUTH_PREFERENCES);
      await this.loadUserInfo();
      hilog.info(DOMAIN, TAG, 'LocalAuthService initialized');
    } catch (error) {
      hilog.error(DOMAIN, TAG, `Failed to init: ${error}`);
    }
  }

  /**
   * 加载用户信息
   */
  private async loadUserInfo(): Promise<void> {
    if (!this.prefs) return;
    try {
      const userJson = await this.prefs.get(USER_INFO_KEY, '') as string;
      if (userJson) {
        this.currentUser = JSON.parse(userJson) as LocalUserInfo;
      }
    } catch (error) {
      hilog.error(DOMAIN, TAG, `Failed to load user info: ${error}`);
    }
  }

  /**
   * 保存用户信息
   */
  private async saveUserInfo(): Promise<void> {
    if (!this.prefs || !this.currentUser) return;
    try {
      await this.prefs.put(USER_INFO_KEY, JSON.stringify(this.currentUser));
      await this.prefs.flush();
    } catch (error) {
      hilog.error(DOMAIN, TAG, `Failed to save user info: ${error}`);
    }
  }

  /**
   * 登录（注册或登录）
   */
  async login(username: string, avatar?: string): Promise<LocalUserInfo | null> {
    if (!username || username.trim().length === 0) {
      hilog.error(DOMAIN, TAG, 'Username is empty');
      return null;
    }

    const trimmedName = username.trim();
    
    // 创建或获取用户
    this.currentUser = {
      username: trimmedName,
      avatar: avatar || this.generateAvatar(trimmedName),
      createdAt: this.currentUser?.createdAt || Date.now()
    };

    await this.saveUserInfo();

    // 发送登录成功事件
    emitter.emit({ eventId: 1001 });

    hilog.info(DOMAIN, TAG, `User logged in: ${trimmedName}`);
    return this.currentUser;
  }

  /**
   * 游客登录
   */
  async guestLogin(): Promise<LocalUserInfo | null> {
    const guestName = `游客${Math.floor(Math.random() * 10000)}`;
    return await this.login(guestName);
  }

  /**
   * 登出
   */
  async logout(): Promise<void> {
    this.currentUser = null;
    if (this.prefs) {
      try {
        await this.prefs.delete(USER_INFO_KEY);
        await this.prefs.flush();
      } catch (error) {
        hilog.error(DOMAIN, TAG, `Failed to logout: ${error}`);
      }
    }

    // 发送登出成功事件
    emitter.emit({ eventId: 1002 });

    hilog.info(DOMAIN, TAG, 'User logged out');
  }

  /**
   * 更新用户信息
   */
  async updateProfile(username?: string, avatar?: string): Promise<LocalUserInfo | null> {
    if (!this.currentUser) return null;

    if (username) {
      this.currentUser.username = username.trim();
    }
    if (avatar) {
      this.currentUser.avatar = avatar;
    }

    await this.saveUserInfo();
    return this.currentUser;
  }

  /**
   * 检查是否已登录
   */
  isLoggedIn(): boolean {
    return this.currentUser !== null;
  }

  /**
   * 获取当前用户
   */
  getCurrentUser(): LocalUserInfo | null {
    return this.currentUser;
  }

  /**
   * 生成默认头像颜色
   */
  private generateAvatar(username: string): string {
    const colors = [
      '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', 
      '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F'
    ];
    const index = username.charCodeAt(0) % colors.length;
    return colors[index];
  }
}

export const localAuthService = new LocalAuthService();