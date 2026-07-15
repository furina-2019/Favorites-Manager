import { router } from '@kit.ArkUI';
import { common, Want } from '@kit.AbilityKit';
import { dataService } from '../service/DataService';
import { Folder, FavoriteItem, DEFAULT_CATEGORIES } from '../model/FavoriteItem';
import { AddFolderDialog } from '../component/AddFolderDialog';
import { eventService } from '../service/EventService';
import { themeService } from '../service/ThemeService';
import { AddMenu } from '../component/AddMenu';

/**
 * 首页组件 - 作为TabContent的内容
 */
@Component
export struct HomePage {
  @State folders: Folder[] = [];
  @State folderStats: Map<string, number> = new Map();
  @State recentFavorites: FavoriteItem[] = [];
  @State showAddDialog: boolean = false;
  @State isLoading: boolean = true;
  @State primaryColor: string = '#4CAF50';
  private eventSubscriptionIds: number[] = [];
  private loadDataTimeout: number = 0; // 用于防抖的定时器ID

  async aboutToAppear(): Promise<void> {
    await this.loadData();
    this.subscribeEvents();
    this.primaryColor = themeService.getPrimaryColor();
  }

  aboutToDisappear(): void {
    this.unsubscribeEvents();
    // 清理定时器
    if (this.loadDataTimeout) {
      clearTimeout(this.loadDataTimeout);
      this.loadDataTimeout = 0;
    }
  }

  private subscribeEvents(): void {
    // 防抖加载数据函数
    const debouncedLoadData = () => {
      // 清除之前的定时器
      if (this.loadDataTimeout) {
        clearTimeout(this.loadDataTimeout);
      }
      // 设置新的定时器，延迟300ms执行
      this.loadDataTimeout = setTimeout(() => {
        this.loadData();
      }, 300);
    };

    // 订阅数据变更事件（使用防抖）
    const dataChangedId = eventService.onDataChanged(debouncedLoadData);
    this.eventSubscriptionIds.push(dataChangedId);

    // 订阅收藏添加事件（使用防抖）
    const favoriteAddedId = eventService.onFavoriteAdded(debouncedLoadData);
    this.eventSubscriptionIds.push(favoriteAddedId);

    // 订阅收藏删除事件（使用防抖）
    const favoriteDeletedId = eventService.onFavoriteDeleted(debouncedLoadData);
    this.eventSubscriptionIds.push(favoriteDeletedId);

    // 订阅文件夹变更事件（使用防抖）
    const folderChangedId = eventService.onFolderChanged(debouncedLoadData);
    this.eventSubscriptionIds.push(folderChangedId);

    // 订阅主题变更事件
    const themeChangedId = eventService.onThemeChanged(() => {
      this.primaryColor = themeService.getPrimaryColor();
    });
    this.eventSubscriptionIds.push(themeChangedId);
  }

  private unsubscribeEvents(): void {
    for (const id of this.eventSubscriptionIds) {
      eventService.off(id);
    }
    this.eventSubscriptionIds = [];
  }

  async loadData(): Promise<void> {
    try {
      this.isLoading = true;
      // 并行加载数据以提高性能
      const foldersPromise = dataService.getFolders();
      const favoritesPromise = dataService.getFavorites();
      
      const folders = await foldersPromise;
      const allFavorites = await favoritesPromise;
      
      this.folders = folders;
      this.recentFavorites = allFavorites.slice(0, 6);
      
      // 批量计算文件夹统计，避免重复调用getFavorites
      this.folderStats.clear();
      for (const folder of this.folders) {
        const count = allFavorites.filter(f => f.folderId === folder.id).length;
        this.folderStats.set(folder.id, count);
      }
      
      this.isLoading = false;
    } catch (error) {
      console.error('Failed to load data:', error);
      this.isLoading = false;
      // 设置默认数据，避免UI完全无响应
      this.folders = [];
      this.recentFavorites = [];
      this.folderStats.clear();
    }
  }

  navigateToFolder(folderId: string, folderName: string): void {
    try {
      router.pushUrl({
        url: 'pages/FolderDetail',
        params: { folderId, folderName }
      });
    } catch (error) {
      console.error('Failed to navigate to folder:', error);
    }
  }

  navigateToCreateFavorite(): void {
    try {
      router.pushUrl({
        url: 'pages/CreateFavorite',
        params: {}
      });
    } catch (error) {
      console.error('Failed to navigate to create favorite:', error);
    }
  }

  navigateToSettings(): void {
    try {
      router.pushUrl({
        url: 'pages/Settings',
        params: {}
      });
    } catch (error) {
      console.error('Failed to navigate to settings:', error);
    }
  }

  @Builder
  FolderCard(folder: Folder, index: number) {
    Column() {
      // 文件夹图标和数量
      Row() {
        Text(folder.name.charAt(0))
          .fontSize(32)
          .fontWeight(FontWeight.Bold)
          .fontColor('#FFFFFF')
      }
      .width(64)
      .height(64)
      .borderRadius(16)
      .backgroundColor(this.getFolderColor(index))
      .justifyContent(FlexAlign.Center)
      
      Text(folder.name)
        .fontSize(16)
        .fontWeight(FontWeight.Medium)
        .fontColor('#333333')
        .margin({ top: 12 })
        .maxLines(1)
        .textOverflow({ overflow: TextOverflow.Ellipsis })
      
      Text(`${this.folderStats.get(folder.id) || 0} 个收藏`)
        .fontSize(14)
        .fontColor('#999999')
        .margin({ top: 4 })
    }
    .width('100%')
    .padding(16)
    .backgroundColor('#FFFFFF')
    .borderRadius(16)
    .shadow({
      radius: 8,
      color: '#1A000000',
      offsetX: 0,
      offsetY: 2
    })
    .onClick(() => {
      this.navigateToFolder(folder.id, folder.name);
    })
  }

  getFolderColor(index: number): string {
    // 基于主题色生成不同的颜色变体
    const baseColor = this.primaryColor;
    const colors = this.generateColorVariants(baseColor, 6);
    return colors[index % colors.length];
  }

  // 生成颜色变体
  private generateColorVariants(baseColor: string, count: number): string[] {
    const variants: string[] = [];
    const hex = baseColor.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    
    for (let i = 0; i < count; i++) {
      // 生成不同亮度的变体
      const factor = 0.8 + (i * 0.1);
      const newR = Math.min(255, Math.round(r * factor));
      const newG = Math.min(255, Math.round(g * factor));
      const newB = Math.min(255, Math.round(b * factor));
      
      const variant = `#${newR.toString(16).padStart(2, '0')}${newG.toString(16).padStart(2, '0')}${newB.toString(16).padStart(2, '0')}`;
      variants.push(variant);
    }
    
    return variants;
  }

  @Builder
  RecentItem(item: FavoriteItem) {
    Column() {
      if (item.coverImage) {
        Image(item.coverImage)
          .width('100%')
          .height(100)
          .objectFit(ImageFit.Cover)
          .borderRadius({ topLeft: 12, topRight: 12 })
          .onError(() => {
            console.log('Failed to load cover image in RecentItem:', item.coverImage);
          })
      } else {
        Row() {
          Text(item.type === 'video' ? '🎬' : item.type === 'article' ? '📄' : '🔗')
            .fontSize(32)
        }
        .width('100%')
        .height(100)
        .backgroundColor('#F0F0F0')
        .justifyContent(FlexAlign.Center)
        .borderRadius({ topLeft: 12, topRight: 12 })
      }
      
      Column() {
        Text(item.title)
          .fontSize(14)
          .fontColor('#333333')
          .maxLines(2)
          .textOverflow({ overflow: TextOverflow.Ellipsis })
        
        Text(item.sourceApp)
          .fontSize(12)
          .fontColor('#999999')
          .margin({ top: 4 })
      }
      .width('100%')
      .padding(8)
    }
    .width('100%')
    .backgroundColor('#FFFFFF')
    .borderRadius(12)
    .shadow({
      radius: 4,
      color: '#1A000000',
      offsetX: 0,
      offsetY: 1
    })
    .onClick(() => {
      this.openFavorite(item);
    })
  }

  openFavorite(item: FavoriteItem): void {
    if (item.url) {
      // 传递收藏项ID而不是完整的对象，因为router.pushUrl只能传递可序列化的基本类型数据
      try {
        router.pushUrl({
          url: 'pages/FolderDetail',
          params: { 
            folderId: item.folderId || 'all',
            folderName: '全部收藏',
            openItemId: item.id // 只传递ID
          }
        });
      } catch (error) {
        console.error('Failed to open favorite:', error);
      }
    }
  }

  // 打开URL到对应应用
  private openUrl(item: FavoriteItem): void {
    if (!item.url || item.url.length === 0) {
      console.error('openUrl: item.url is empty');
      return;
    }
    
    let urlToOpen = item.url;
    // 确保URL有正确的协议前缀
    if (!urlToOpen.startsWith('http://') && !urlToOpen.startsWith('https://')) {
      urlToOpen = 'https://' + urlToOpen;
    }
    
    console.log('openUrl: opening URL:', urlToOpen);
    
    try {
      const context = getContext(this) as common.UIAbilityContext;
      if (!context) {
        console.error('openUrl: context is null');
        return;
      }
      
      // 直接使用隐式 Intent 打开 URL
      const want: Want = {
        action: 'ohos.want.action.viewData',
        uri: urlToOpen
      };
      
      console.log('openUrl: starting ability with want:', JSON.stringify(want));
      context.startAbility(want)
        .then(() => {
          console.log('openUrl: successfully started ability');
        })
        .catch((err: Error) => {
          console.error('openUrl: failed to start ability:', err.message);
        });
    } catch (error) {
      console.error('openUrl: exception occurred:', JSON.stringify(error));
    }
  }

  build() {
    Stack() {
      Column() {
        // 标题栏（移除设置按钮，因为设置已移动到"我的"页面）
        Row() {
          Text('我的收藏')
            .fontSize(28)
            .fontWeight(FontWeight.Bold)
            .fontColor('#333333')
          
          Blank()
        }
        .width('100%')
        .padding({ left: 20, right: 20, top: 16, bottom: 16 })
        
        if (this.isLoading) {
          Column() {
            LoadingProgress()
              .width(48)
              .height(48)
              .color(this.primaryColor)
            Text('加载中...')
              .fontSize(14)
              .fontColor('#999999')
              .margin({ top: 16 })
          }
          .width('100%')
          .height('100%')
          .justifyContent(FlexAlign.Center)
        } else {
          Scroll() {
            Column() {
              // 最近收藏
              if (this.recentFavorites.length > 0) {
                Column() {
                  Row() {
                    Text('最近收藏')
                      .fontSize(18)
                      .fontWeight(FontWeight.Medium)
                      .fontColor('#333333')
                    
                    Blank()
                    
                    Text('查看全部')
                      .fontSize(14)
                      .fontColor(this.primaryColor)
                      .onClick(() => {
                        this.navigateToFolder('all', '全部收藏');
                      })
                  }
                  .width('100%')
                  .padding({ left: 20, right: 20, bottom: 12 })
                  
                  Grid() {
                    ForEach(this.recentFavorites, (item: FavoriteItem) => {
                      GridItem() {
                        this.RecentItem(item);
                      }
                    })
                  }
                  .columnsTemplate('1fr 1fr')
                  .rowsGap(12)
                  .columnsGap(12)
                  .width('100%')
                  .height(240)
                  .padding({ left: 20, right: 20 })
                }
                .width('100%')
                .margin({ bottom: 24 })
              }
              
              // 文件夹列表
              Column() {
                Text('收藏夹')
                  .fontSize(18)
                  .fontWeight(FontWeight.Medium)
                  .fontColor('#333333')
                  .width('100%')
                  .padding({ left: 20, right: 20, bottom: 12 })
                
                Grid() {
                  ForEach(this.folders, (folder: Folder, index: number) => {
                    GridItem() {
                      this.FolderCard(folder, index);
                    }
                  })
                }
                .columnsTemplate('1fr 1fr')
                .rowsGap(16)
                .columnsGap(16)
                .width('100%')
                .padding({ left: 20, right: 20, bottom: 100 })
              }
              .width('100%')
            }
          }
          .width('100%')
          .layoutWeight(1)
          .scrollBar(BarState.Off)
        }
      }
      .width('100%')
      .height('100%')
      .backgroundColor('#F5F5F5')
      
      // 添加文件夹弹窗
      if (this.showAddDialog) {
        AddFolderDialog({
          onConfirm: async (name: string) => {
            const newFolder: Folder = {
              id: `folder_${Date.now()}`,
              name: name,
              isDefault: false,
              createTime: Date.now(),
              updateTime: Date.now()
            };
            await dataService.addFolder(newFolder);
            this.showAddDialog = false;
            await this.loadData();
          },
          onCancel: () => {
            this.showAddDialog = false;
          }
        })
      }

      // 合并的添加菜单（移除主题设置按钮）
      AddMenu({
        onAddFolder: async (name: string) => {
          try {
            const newFolder: Folder = {
              id: `folder_${Date.now()}`,
              name: name,
              isDefault: false,
              createTime: Date.now(),
              updateTime: Date.now()
            };
            await dataService.addFolder(newFolder);
            await this.loadData();
          } catch (error) {
            console.error('Failed to add folder:', error);
            // 可以在这里添加用户提示
          }
        },
        onNavigateToCreateFavorite: () => {
          this.navigateToCreateFavorite();
        }
      })
    }
    .width('100%')
    .height('100%')
  }
}