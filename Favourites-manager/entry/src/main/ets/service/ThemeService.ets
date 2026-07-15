import { preferences } from '@kit.ArkData';
import { common } from '@kit.AbilityKit';
import { emitter } from '@kit.BasicServicesKit';

/**
 * 主题配置接口
 */
export interface ThemeConfig {
  primaryColor: string;       // 主题色
  secondaryColor: string;     // 次要色
  backgroundColor: string;    // 背景色
  cardBackgroundColor: string; // 卡片背景色
  textColor: string;          // 主文字色
  secondaryTextColor: string; // 次要文字色
}

/**
 * 预设主题
 */
export class PresetThemes {
  static green: ThemeConfig = {
    primaryColor: '#4CAF50',
    secondaryColor: '#81C784',
    backgroundColor: '#F5F5F5',
    cardBackgroundColor: '#FFFFFF',
    textColor: '#333333',
    secondaryTextColor: '#999999'
  };

  static blue: ThemeConfig = {
    primaryColor: '#2196F3',
    secondaryColor: '#64B5F6',
    backgroundColor: '#F5F5F5',
    cardBackgroundColor: '#FFFFFF',
    textColor: '#333333',
    secondaryTextColor: '#999999'
  };

  static purple: ThemeConfig = {
    primaryColor: '#9C27B0',
    secondaryColor: '#BA68C8',
    backgroundColor: '#F5F5F5',
    cardBackgroundColor: '#FFFFFF',
    textColor: '#333333',
    secondaryTextColor: '#999999'
  };

  static orange: ThemeConfig = {
    primaryColor: '#FF9800',
    secondaryColor: '#FFB74D',
    backgroundColor: '#F5F5F5',
    cardBackgroundColor: '#FFFFFF',
    textColor: '#333333',
    secondaryTextColor: '#999999'
  };

  static pink: ThemeConfig = {
    primaryColor: '#E91E63',
    secondaryColor: '#F06292',
    backgroundColor: '#F5F5F5',
    cardBackgroundColor: '#FFFFFF',
    textColor: '#333333',
    secondaryTextColor: '#999999'
  };

  static cyan: ThemeConfig = {
    primaryColor: '#00BCD4',
    secondaryColor: '#4DD0E1',
    backgroundColor: '#F5F5F5',
    cardBackgroundColor: '#FFFFFF',
    textColor: '#333333',
    secondaryTextColor: '#999999'
  };
}

/**
 * 主题事件类型
 */
export class ThemeEventType {
  static readonly THEME_CHANGED = 2001;
}

const THEME_KEY = 'theme_config';

/**
 * 主题服务 - 管理应用主题配置
 */
export class ThemeService {
  private static instance: ThemeService;
  private preferences: preferences.Preferences | null = null;
  private currentTheme: ThemeConfig = PresetThemes.green;

  private constructor() {
    // 初始化AppStorage中的主题配置
    if (AppStorage.get<string>('primaryColor') === undefined) {
      AppStorage.setOrCreate('primaryColor', this.currentTheme.primaryColor);
    }
  }

  static getInstance(): ThemeService {
    if (!ThemeService.instance) {
      ThemeService.instance = new ThemeService();
    }
    return ThemeService.instance;
  }

  /**
   * 初始化preferences
   */
  async init(): Promise<void> {
    try {
      const context = getContext(this) as common.UIAbilityContext;
      this.preferences = await preferences.getPreferences(context, THEME_KEY);
      await this.loadTheme();
    } catch (error) {
      console.error('ThemeService init error:', error);
    }
  }

  /**
   * 从preferences加载主题
   */
  private async loadTheme(): Promise<void> {
    if (!this.preferences) return;

    try {
      const savedTheme = await this.preferences.get(THEME_KEY, '') as string;
      if (savedTheme) {
        const themeConfig = JSON.parse(savedTheme) as ThemeConfig;
        this.currentTheme = themeConfig;
        this.applyTheme();
      }
    } catch (error) {
      console.error('ThemeService loadTheme error:', error);
    }
  }

  /**
   * 保存主题到preferences
   */
  private async saveTheme(): Promise<void> {
    if (!this.preferences) return;

    try {
      const themeJson = JSON.stringify(this.currentTheme);
      await this.preferences.put(THEME_KEY, themeJson);
      await this.preferences.flush();
    } catch (error) {
      console.error('ThemeService saveTheme error:', error);
    }
  }

  /**
   * 应用主题到AppStorage
   */
  private applyTheme(): void {
    AppStorage.setOrCreate('primaryColor', this.currentTheme.primaryColor);
    AppStorage.setOrCreate('secondaryColor', this.currentTheme.secondaryColor);
    AppStorage.setOrCreate('backgroundColor', this.currentTheme.backgroundColor);
    AppStorage.setOrCreate('cardBackgroundColor', this.currentTheme.cardBackgroundColor);
    AppStorage.setOrCreate('textColor', this.currentTheme.textColor);
    AppStorage.setOrCreate('secondaryTextColor', this.currentTheme.secondaryTextColor);
    
    // 发送主题变更事件
    emitter.emit({ eventId: ThemeEventType.THEME_CHANGED }, { data: { theme: this.currentTheme } });
  }

  /**
   * 设置主题色
   */
  async setPrimaryColor(color: string): Promise<void> {
    this.currentTheme.primaryColor = color;
    await this.saveTheme();
    this.applyTheme();
  }

  /**
   * 使用预设主题
   */
  async usePresetTheme(presetName: string): Promise<void> {
    let presetTheme: ThemeConfig | undefined;
    
    switch (presetName) {
      case 'green':
        presetTheme = PresetThemes.green;
        break;
      case 'blue':
        presetTheme = PresetThemes.blue;
        break;
      case 'purple':
        presetTheme = PresetThemes.purple;
        break;
      case 'orange':
        presetTheme = PresetThemes.orange;
        break;
      case 'pink':
        presetTheme = PresetThemes.pink;
        break;
      case 'cyan':
        presetTheme = PresetThemes.cyan;
        break;
    }
    
    if (presetTheme) {
      this.currentTheme = {
        primaryColor: presetTheme.primaryColor,
        secondaryColor: presetTheme.secondaryColor,
        backgroundColor: presetTheme.backgroundColor,
        cardBackgroundColor: presetTheme.cardBackgroundColor,
        textColor: presetTheme.textColor,
        secondaryTextColor: presetTheme.secondaryTextColor
      };
      await this.saveTheme();
      this.applyTheme();
    }
  }

  /**
   * 获取当前主题
   */
  getCurrentTheme(): ThemeConfig {
    return {
      primaryColor: this.currentTheme.primaryColor,
      secondaryColor: this.currentTheme.secondaryColor,
      backgroundColor: this.currentTheme.backgroundColor,
      cardBackgroundColor: this.currentTheme.cardBackgroundColor,
      textColor: this.currentTheme.textColor,
      secondaryTextColor: this.currentTheme.secondaryTextColor
    };
  }

  /**
   * 获取当前主题色
   */
  getPrimaryColor(): string {
    return this.currentTheme.primaryColor;
  }

  /**
   * 颜色变亮处理
   */
  private lightenColor(color: string, amount: number): string {
    const hex = color.replace('#', '');
    const r = Math.min(255, parseInt(hex.substring(0, 2), 16) + Math.round(255 * amount));
    const g = Math.min(255, parseInt(hex.substring(2, 4), 16) + Math.round(255 * amount));
    const b = Math.min(255, parseInt(hex.substring(4, 6), 16) + Math.round(255 * amount));
    
    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
  }

  /**
   * 颜色变暗处理
   */
  private darkenColor(color: string, amount: number): string {
    const hex = color.replace('#', '');
    const r = Math.max(0, parseInt(hex.substring(0, 2), 16) - Math.round(255 * amount));
    const g = Math.max(0, parseInt(hex.substring(2, 4), 16) - Math.round(255 * amount));
    const b = Math.max(0, parseInt(hex.substring(4, 6), 16) - Math.round(255 * amount));
    
    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
  }

  /**
   * 获取主题变亮颜色
   */
  getLightenColor(color: string, amount: number = 0.2): string {
    return this.lightenColor(color, amount);
  }

  /**
   * 获取主题变暗颜色
   */
  getDarkenColor(color: string, amount: number = 0.2): string {
    return this.darkenColor(color, amount);
  }
}

export const themeService = ThemeService.getInstance();