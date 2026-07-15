import { preferences } from '@kit.ArkData';
import { common } from '@kit.AbilityKit';
import { formProvider, formBindingData } from '@kit.FormKit';
import { FavoriteItem, Folder, DEFAULT_FOLDERS } from '../model/FavoriteItem';
import { eventService } from './EventService';

const FAVORITES_KEY = 'favorites';
const FOLDERS_KEY = 'folders';
const CATEGORIES_KEY = 'categories';
const WIDGET_IDS_KEY = 'widget_ids';

/**
 * 卡片表单数据接口
 */
interface WidgetFormData {
  latestTitle: string;
  latestSource: string;
  recommendTitle: string;
  recommendSource: string;
  totalCount: number;
}

/**
 * 本地数据存储服务
 */
export class DataService {
  private static instance: DataService;
  private preferences: preferences.Preferences | null = null;
  private context: common.UIAbilityContext | null = null;
  private formIds: string[] = [];

  private constructor() {}

  static getInstance(): DataService {
    if (!DataService.instance) {
      DataService.instance = new DataService();
    }
    return DataService.instance;
  }

  /**
   * 初始化服务
   */
  async init(context: common.UIAbilityContext): Promise<void> {
    this.context = context;
    try {
      this.preferences = await preferences.getPreferences(context, 'favorite_store');
      await this.initDefaultFolders();
      await this.loadFormIds(); // 加载已保存的formIds
    } catch (error) {
      console.error('DataService init failed:', JSON.stringify(error));
    }
  }

  /**
   * 注册卡片ID用于更新
   */
  async registerFormId(formId: string): Promise<void> {
    if (!this.formIds.includes(formId)) {
      this.formIds.push(formId);
      await this.saveFormIds(); // 保存到持久化存储
    }
  }

  /**
   * 取消注册卡片ID
   */
  async unregisterFormId(formId: string): Promise<void> {
    this.formIds = this.formIds.filter(id => id !== formId);
    await this.saveFormIds(); // 保存到持久化存储
  }

  /**
   * 保存卡片ID列表到持久化存储
   */
  private async saveFormIds(): Promise<void> {
    if (!this.preferences) return;
    try {
      await this.preferences.put(WIDGET_IDS_KEY, JSON.stringify(this.formIds));
      await this.preferences.flush();
    } catch (error) {
      console.error('saveFormIds failed:', JSON.stringify(error));
    }
  }

  /**
   * 从持久化存储加载卡片ID列表
   */
  private async loadFormIds(): Promise<void> {
    if (!this.preferences) return;
    try {
      const data = await this.preferences.get(WIDGET_IDS_KEY, '[]') as string;
      this.formIds = JSON.parse(data) as string[];
      console.log('DataService: Loaded formIds:', this.formIds);
    } catch (error) {
      console.error('loadFormIds failed:', JSON.stringify(error));
      this.formIds = [];
    }
  }

  /**
   * 更新所有已注册的卡片
   */
  private async updateAllWidgets(): Promise<void> {
    for (const formId of this.formIds) {
      try {
        const latest = await this.getLatestFavorite();
        const recommend = await this.getRecommendFavorite();
        const allFavorites = await this.getFavorites();
        
        const formData: WidgetFormData = {
          latestTitle: latest?.title ?? '暂无收藏',
          latestSource: latest?.sourceApp ?? '',
          recommendTitle: recommend?.title ?? '暂无收藏',
          recommendSource: recommend?.sourceApp ?? '',
          totalCount: allFavorites.length
        };
        
        const bindingData = formBindingData.createFormBindingData(formData);
        await formProvider.updateForm(formId, bindingData);
      } catch (error) {
        console.error('updateAllWidgets failed:', JSON.stringify(error));
      }
    }
  }

  /**
   * 初始化默认文件夹
   */
  private async initDefaultFolders(): Promise<void> {
    const folders = await this.getFolders();
    if (folders.length === 0) {
      await this.saveFolders(DEFAULT_FOLDERS);
    }
  }

  /**
   * 获取所有收藏
   */
  async getFavorites(): Promise<FavoriteItem[]> {
    if (!this.preferences) return [];
    try {
      const data = await this.preferences.get(FAVORITES_KEY, '[]') as string;
      return JSON.parse(data) as FavoriteItem[];
    } catch (error) {
      console.error('getFavorites failed:', JSON.stringify(error));
      return [];
    }
  }

  /**
   * 保存所有收藏
   */
  async saveFavorites(favorites: FavoriteItem[]): Promise<void> {
    if (!this.preferences) return;
    try {
      await this.preferences.put(FAVORITES_KEY, JSON.stringify(favorites));
      await this.preferences.flush();
    } catch (error) {
      console.error('saveFavorites failed:', JSON.stringify(error));
    }
  }

  /**
   * 添加收藏
   */
  async addFavorite(item: FavoriteItem): Promise<void> {
    const favorites = await this.getFavorites();
    favorites.unshift(item);
    await this.saveFavorites(favorites);
    // 触发事件和更新卡片
    eventService.emitFavoriteAdded();
    eventService.emitDataChanged();
    await this.updateAllWidgets();
  }

  /**
   * 更新收藏
   */
  async updateFavorite(item: FavoriteItem): Promise<void> {
    const favorites = await this.getFavorites();
    const index = favorites.findIndex(f => f.id === item.id);
    if (index !== -1) {
      const updatedItem: FavoriteItem = {
        id: item.id,
        title: item.title,
        sourceApp: item.sourceApp,
        sourcePackage: item.sourcePackage,
        url: item.url,
        coverImage: item.coverImage,
        description: item.description,
        folderId: item.folderId,
        category: item.category,
        createTime: item.createTime,
        updateTime: Date.now(),
        type: item.type
      };
      favorites[index] = updatedItem;
      await this.saveFavorites(favorites);
      eventService.emitDataChanged();
      await this.updateAllWidgets();
    }
  }

  /**
   * 删除收藏
   */
  async deleteFavorite(id: string): Promise<void> {
    const favorites = await this.getFavorites();
    const newFavorites = favorites.filter(f => f.id !== id);
    await this.saveFavorites(newFavorites);
    // 触发事件和更新卡片
    eventService.emitFavoriteDeleted();
    eventService.emitDataChanged();
    await this.updateAllWidgets();
  }

  /**
   * 批量删除收藏
   */
  async deleteFavorites(ids: string[]): Promise<void> {
    if (ids.length === 0) return;
    const favorites = await this.getFavorites();
    const idSet = new Set(ids);
    const newFavorites = favorites.filter(f => !idSet.has(f.id));
    await this.saveFavorites(newFavorites);
    // 触发事件和更新卡片
    eventService.emitFavoriteDeleted();
    eventService.emitDataChanged();
    await this.updateAllWidgets();
  }

  /**
   * 根据文件夹获取收藏
   */
  async getFavoritesByFolder(folderId: string): Promise<FavoriteItem[]> {
    const favorites = await this.getFavorites();
    if (folderId === 'all') {
      return favorites;
    }
    return favorites.filter(f => f.folderId === folderId);
  }

  /**
   * 获取最新收藏
   */
  async getLatestFavorite(): Promise<FavoriteItem | null> {
    const favorites = await this.getFavorites();
    return favorites.length > 0 ? favorites[0] : null;
  }

  /**
   * 获取猜你想看
   */
  async getRecommendFavorite(): Promise<FavoriteItem | null> {
    const favorites = await this.getFavorites();
    if (favorites.length < 2) return favorites.length > 0 ? favorites[0] : null;
    const randomIndex = Math.floor(Math.random() * Math.min(favorites.length, 10));
    return favorites[randomIndex];
  }

  /**
   * 获取所有文件夹
   */
  async getFolders(): Promise<Folder[]> {
    if (!this.preferences) return [];
    try {
      const data = await this.preferences.get(FOLDERS_KEY, '[]') as string;
      return JSON.parse(data) as Folder[];
    } catch (error) {
      console.error('getFolders failed:', JSON.stringify(error));
      return [];
    }
  }

  /**
   * 保存所有文件夹
   */
  async saveFolders(folders: Folder[]): Promise<void> {
    if (!this.preferences) return;
    try {
      await this.preferences.put(FOLDERS_KEY, JSON.stringify(folders));
      await this.preferences.flush();
    } catch (error) {
      console.error('saveFolders failed:', JSON.stringify(error));
    }
  }

  /**
   * 添加文件夹
   */
  async addFolder(folder: Folder): Promise<void> {
    const folders = await this.getFolders();
    folders.push(folder);
    await this.saveFolders(folders);
    eventService.emitFolderChanged();
    eventService.emitDataChanged();
  }

  /**
   * 更新文件夹
   */
  async updateFolder(folder: Folder): Promise<void> {
    const folders = await this.getFolders();
    const index = folders.findIndex(f => f.id === folder.id);
    if (index !== -1) {
      const updatedFolder: Folder = {
        id: folder.id,
        name: folder.name,
        icon: folder.icon,
        color: folder.color,
        isDefault: folder.isDefault,
        createTime: folder.createTime,
        updateTime: Date.now()
      };
      folders[index] = updatedFolder;
      await this.saveFolders(folders);
      eventService.emitFolderChanged();
      eventService.emitDataChanged();
    }
  }

  /**
   * 删除文件夹
   */
  async deleteFolder(id: string): Promise<void> {
    if (id === 'all') return;
    const folders = await this.getFolders();
    const newFolders = folders.filter(f => f.id !== id);
    await this.saveFolders(newFolders);
    const favorites = await this.getFavorites();
    const updatedFavorites = favorites.filter(f => f.folderId !== id);
    await this.saveFavorites(updatedFavorites);
    eventService.emitFolderChanged();
    eventService.emitDataChanged();
    await this.updateAllWidgets();
  }

  /**
   * 获取文件夹统计信息
   */
  async getFolderStats(folderId: string): Promise<number> {
    const favorites = await this.getFavoritesByFolder(folderId);
    return favorites.length;
  }

  /**
   * 搜索收藏
   */
  async searchFavorites(keyword: string): Promise<FavoriteItem[]> {
    const favorites = await this.getFavorites();
    const lowerKeyword = keyword.toLowerCase();
    return favorites.filter(f =>
      f.title.toLowerCase().includes(lowerKeyword) ||
      (f.description !== undefined && f.description.toLowerCase().includes(lowerKeyword)) ||
      f.sourceApp.toLowerCase().includes(lowerKeyword)
    );
  }
}

export const dataService = DataService.getInstance();