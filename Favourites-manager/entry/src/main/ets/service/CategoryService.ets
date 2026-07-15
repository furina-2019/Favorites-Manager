import { Category, DEFAULT_CATEGORIES, FavoriteItem } from '../model/FavoriteItem';
import { preferences } from '@kit.ArkData';
import { common } from '@kit.AbilityKit';
import { eventService } from './EventService';

const CUSTOM_CATEGORIES_KEY = 'custom_categories';

/**
 * 智能分类服务
 */
export class CategoryService {
  private static instance: CategoryService;
  private categories: Category[] = DEFAULT_CATEGORIES;
  private customCategories: Category[] = [];
  private preferences: preferences.Preferences | null = null;
  private context: common.UIAbilityContext | null = null;

  private constructor() {}

  static getInstance(): CategoryService {
    if (!CategoryService.instance) {
      CategoryService.instance = new CategoryService();
    }
    return CategoryService.instance;
  }

  /**
   * 初始化服务
   */
  async init(context: common.UIAbilityContext): Promise<void> {
    this.context = context;
    try {
      this.preferences = await preferences.getPreferences(context, 'favorite_store');
      await this.loadCustomCategories();
    } catch (error) {
      console.error('CategoryService init failed:', JSON.stringify(error));
    }
  }

  /**
   * 加载自定义分类
   */
  private async loadCustomCategories(): Promise<void> {
    if (!this.preferences) return;
    
    try {
      const data = await this.preferences.get(CUSTOM_CATEGORIES_KEY, '[]') as string;
      this.customCategories = JSON.parse(data) as Category[];
    } catch (error) {
      console.error('loadCustomCategories failed:', JSON.stringify(error));
      this.customCategories = [];
    }
  }

  /**
   * 保存自定义分类
   */
  private async saveCustomCategories(): Promise<void> {
    if (!this.preferences) return;
    
    try {
      await this.preferences.put(CUSTOM_CATEGORIES_KEY, JSON.stringify(this.customCategories));
      await this.preferences.flush();
      eventService.emitCategoryChanged();
    } catch (error) {
      console.error('saveCustomCategories failed:', JSON.stringify(error));
    }
  }

  /**
   * 获取所有分类（包括默认和自定义）
   */
  getCategories(): Category[] {
    return [...this.categories, ...this.customCategories];
  }

  /**
   * 获取默认分类
   */
  getDefaultCategories(): Category[] {
    return this.categories;
  }

  /**
   * 获取自定义分类
   */
  getCustomCategories(): Category[] {
    return this.customCategories;
  }

  /**
   * 添加自定义分类
   */
  async addCustomCategory(category: Category): Promise<void> {
    // 确保ID唯一
    const existing = this.customCategories.find(c => c.id === category.id);
    if (existing) {
      throw new Error(`Category with id ${category.id} already exists`);
    }
    
    this.customCategories.push(category);
    await this.saveCustomCategories();
  }

  /**
   * 更新自定义分类
   */
  async updateCustomCategory(category: Category): Promise<void> {
    const index = this.customCategories.findIndex(c => c.id === category.id);
    if (index !== -1) {
      const updatedCategory: Category = {
        id: category.id,
        name: category.name,
        keywords: category.keywords,
        icon: category.icon,
        color: category.color
      };
      this.customCategories[index] = updatedCategory;
      await this.saveCustomCategories();
    }
  }

  /**
   * 删除自定义分类
   */
  async deleteCustomCategory(id: string): Promise<void> {
    this.customCategories = this.customCategories.filter(c => c.id !== id);
    await this.saveCustomCategories();
  }

  /**
   * 根据ID获取分类
   */
  getCategoryById(id: string): Category | undefined {
    const allCategories = this.getCategories();
    return allCategories.find(c => c.id === id);
  }

  /**
   * 根据内容智能分类
   */
  classifyContent(title: string, description?: string): Category {
    const content = `${title} ${description ?? ''}`.toLowerCase();
    
    let bestMatch: Category | null = null;
    let maxScore = 0;

    // 首先检查自定义分类
    for (const category of this.customCategories) {
      const score = this.calculateScore(content, category.keywords);
      if (score > maxScore) {
        maxScore = score;
        bestMatch = category;
      }
    }

    // 然后检查默认分类
    for (const category of this.categories) {
      if (category.id === 'other') continue;
      
      const score = this.calculateScore(content, category.keywords);
      if (score > maxScore) {
        maxScore = score;
        bestMatch = category;
      }
    }

    return bestMatch ?? this.categories.find(c => c.id === 'other')!;
  }

  /**
   * 计算关键词匹配分数
   */
  private calculateScore(content: string, keywords: string[]): number {
    let score = 0;
    for (const keyword of keywords) {
      const regex = new RegExp(keyword, 'gi');
      const matches = content.match(regex);
      if (matches !== null) {
        score += matches.length;
      }
    }
    return score;
  }

  /**
   * 为收藏项自动分类
   */
  autoClassify(title: string, description?: string): string {
    const category = this.classifyContent(title, description);
    return category.id;
  }

  /**
   * 分析内容类型
   */
  analyzeContentType(title: string, url?: string, description?: string): 'article' | 'video' | 'image' | 'website' | 'other' {
    const content = `${title} ${url ?? ''} ${description ?? ''}`.toLowerCase();
    
    if (content.includes('video') || content.includes('视频') || 
        content.includes('bilibili') || content.includes('youtube') ||
        content.includes('.mp4') || content.includes('watch') ||
        content.includes('抖音') || content.includes('douyin')) {
      return 'video';
    }
    
    if (content.includes('image') || content.includes('图片') || 
        content.includes('photo') || content.includes('.jpg') ||
        content.includes('.png') || content.includes('.gif') ||
        content.includes('.webp') || content.includes('.bmp')) {
      return 'image';
    }
    
    if (content.includes('article') || content.includes('文章') || 
        content.includes('post') || content.includes('帖子') ||
        content.includes('blog') || content.includes('博客') ||
        content.includes('小红书') || content.includes('笔记')) {
      return 'article';
    }
    
    // 如果是URL，检查是否是网站链接
    if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
      // 检查是否是特定类型的链接
      if (url.includes('.html') || url.includes('.htm') || 
          url.includes('/article/') || url.includes('/post/') || 
          url.includes('/blog/')) {
        return 'article';
      }
      // 通用网站链接
      return 'website';
    }
    
    return 'other';
  }

  /**
   * 生成唯一的分类ID
   */
  generateCategoryId(name: string): string {
    const baseId = name.toLowerCase().replace(/[^a-z0-9]/g, '_');
    const timestamp = Date.now().toString(36);
    return `custom_${baseId}_${timestamp}`;
  }

  /**
   * 验证分类名称是否唯一
   */
  isCategoryNameUnique(name: string): boolean {
    const allCategories = this.getCategories();
    return !allCategories.some(c => c.name === name);
  }

  /**
   * 根据类型获取分类
   */
  classifyByType(type: 'article' | 'video' | 'image' | 'website' | 'other'): Category | undefined {
    const allCategories = this.getCategories();
    
    // 根据类型映射到对应的分类
    const typeToCategoryMap: Record<string, string> = {
      'article': '文章',
      'video': '视频', 
      'image': '图片',
      'website': '网站',
      'other': '其他'
    };
    
    const targetName = typeToCategoryMap[type];
    if (targetName) {
      return allCategories.find(c => c.name === targetName);
    }
    
    return undefined;
  }

  /**
   * 根据名称获取分类
   */
  getCategoryByName(name: string): Category | undefined {
    const allCategories = this.getCategories();
    return allCategories.find(c => c.name === name);
  }
}

export const categoryService = CategoryService.getInstance();