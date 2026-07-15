import { emitter } from '@kit.BasicServicesKit';

/**
 * 事件类型定义接口
 */
export interface EventTypeType {
  DATA_CHANGED: number;
  FAVORITE_ADDED: number;
  FAVORITE_DELETED: number;
  FOLDER_CHANGED: number;
  CATEGORY_CHANGED: number;
  THEME_CHANGED: number;
}

/**
 * 事件类型常量
 */
export const EventType: EventTypeType = {
  DATA_CHANGED: 1001,
  FAVORITE_ADDED: 1002,
  FAVORITE_DELETED: 1003,
  FOLDER_CHANGED: 1004,
  CATEGORY_CHANGED: 1005,
  THEME_CHANGED: 2001
};

/**
 * 事件数据接口
 */
export interface EventData {
  type?: string;
  data?: object;
}

/**
 * 订阅信息接口
 */
interface SubscriptionInfo {
  eventId: number;
  listenerId: number;
}

/**
 * AppStorage同步键名接口
 */
export interface AppStorageKeysType {
  DATA_VERSION: string;
  LAST_UPDATE_TIME: string;
}

/**
 * AppStorage同步键名常量
 */
export const AppStorageKeys: AppStorageKeysType = {
  DATA_VERSION: 'favorite_data_version',
  LAST_UPDATE_TIME: 'favorite_last_update_time'
};

/**
 * 事件服务 - 使用emitter实现组件内通信，AppStorage实现跨UIAbility同步
 */
export class EventService {
  private static instance: EventService;
  private subscriptions: Map<number, SubscriptionInfo> = new Map();
  private nextSubscriptionKey: number = 1;
  private lastDataVersion: number = 0;

  private constructor() {
    // 初始化AppStorage中的数据版本
    if (AppStorage.get<number>(AppStorageKeys.DATA_VERSION) === undefined) {
      AppStorage.setOrCreate(AppStorageKeys.DATA_VERSION, 0);
    }
    if (AppStorage.get<number>(AppStorageKeys.LAST_UPDATE_TIME) === undefined) {
      AppStorage.setOrCreate(AppStorageKeys.LAST_UPDATE_TIME, 0);
    }
  }

  static getInstance(): EventService {
    if (!EventService.instance) {
      EventService.instance = new EventService();
    }
    return EventService.instance;
  }

  /**
   * 发送数据变更事件（支持跨UIAbility）
   */
  emitDataChanged(data?: EventData): void {
    // 更新AppStorage中的数据版本（跨UIAbility同步）
    const currentVersion = AppStorage.get<number>(AppStorageKeys.DATA_VERSION) ?? 0;
    AppStorage.setOrCreate(AppStorageKeys.DATA_VERSION, currentVersion + 1);
    AppStorage.setOrCreate(AppStorageKeys.LAST_UPDATE_TIME, Date.now());
    
    // 同时发送emitter事件（UIAbility内部通信）
    const eventData: emitter.EventData = {
      data: data ?? {}
    };
    emitter.emit({ eventId: EventType.DATA_CHANGED }, eventData);
  }

  /**
   * 发送收藏添加事件
   */
  emitFavoriteAdded(): void {
    this.emitDataChanged();
    emitter.emit({ eventId: EventType.FAVORITE_ADDED });
  }

  /**
   * 发送收藏删除事件
   */
  emitFavoriteDeleted(): void {
    this.emitDataChanged();
    emitter.emit({ eventId: EventType.FAVORITE_DELETED });
  }

  /**
   * 发送文件夹变更事件
   */
  emitFolderChanged(): void {
    this.emitDataChanged();
    emitter.emit({ eventId: EventType.FOLDER_CHANGED });
  }

  /**
   * 发送分类变更事件
   */
  emitCategoryChanged(): void {
    this.emitDataChanged();
    emitter.emit({ eventId: EventType.CATEGORY_CHANGED });
  }

  /**
   * 订阅数据变更事件
   * @returns 订阅key，用于取消订阅
   */
  onDataChanged(callback: () => void): number {
    return this.subscribe(EventType.DATA_CHANGED, callback);
  }

  /**
   * 订阅收藏添加事件
   */
  onFavoriteAdded(callback: () => void): number {
    return this.subscribe(EventType.FAVORITE_ADDED, callback);
  }

  /**
   * 订阅收藏删除事件
   */
  onFavoriteDeleted(callback: () => void): number {
    return this.subscribe(EventType.FAVORITE_DELETED, callback);
  }

  /**
   * 订阅文件夹变更事件
   */
  onFolderChanged(callback: () => void): number {
    return this.subscribe(EventType.FOLDER_CHANGED, callback);
  }

  /**
   * 订阅分类变更事件
   */
  onCategoryChanged(callback: () => void): number {
    return this.subscribe(EventType.CATEGORY_CHANGED, callback);
  }

  /**
   * 发送主题变更事件
   */
  emitThemeChanged(data?: EventData): void {
    const eventData: emitter.EventData = {
      data: data ?? {}
    };
    emitter.emit({ eventId: EventType.THEME_CHANGED }, eventData);
  }

  /**
   * 订阅主题变更事件
   */
  onThemeChanged(callback: () => void): number {
    return this.subscribe(EventType.THEME_CHANGED, callback);
  }

  /**
   * 内部订阅方法
   */
  private subscribe(eventId: number, callback: () => void): number {
    emitter.on({ eventId: eventId }, () => {
      callback();
    });
    const key = this.nextSubscriptionKey++;
    this.subscriptions.set(key, { eventId: eventId, listenerId: key });
    return key;
  }

  /**
   * 取消订阅
   * @param key 订阅时返回的key
   */
  off(key: number): void {
    const info = this.subscriptions.get(key);
    if (info) {
      emitter.off(info.listenerId);
      this.subscriptions.delete(key);
    }
  }

  /**
   * 取消所有订阅
   */
  offAll(): void {
    this.subscriptions.forEach((info) => {
      emitter.off(info.listenerId);
    });
    this.subscriptions.clear();
  }

  /**
   * 获取当前数据版本（用于检测数据变化）
   */
  getDataVersion(): number {
    return AppStorage.get<number>(AppStorageKeys.DATA_VERSION) ?? 0;
  }

  /**
   * 获取最后更新时间
   */
  getLastUpdateTime(): number {
    return AppStorage.get<number>(AppStorageKeys.LAST_UPDATE_TIME) ?? 0;
  }
}

export const eventService = EventService.getInstance();