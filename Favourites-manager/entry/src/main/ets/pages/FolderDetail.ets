import { router } from '@kit.ArkUI';
import { common, Want } from '@kit.AbilityKit';
import { dataService } from '../service/DataService';
import { FavoriteItem, DEFAULT_CATEGORIES, Category } from '../model/FavoriteItem';
import { FavoriteCard } from '../component/FavoriteCard';
import { eventService } from '../service/EventService';
import { categoryService } from '../service/CategoryService';
import { AddCategoryDialog } from '../component/AddCategoryDialog';
import { themeService } from '../service/ThemeService';

/**
 * 路由参数类
 */
class RouterParams {
  folderId: string = 'all';
  folderName: string = '全部收藏';
  openItem: FavoriteItem | null = null;
  openItemId: string = ''; // 收藏项ID
}

/**
 * 分类筛选项类
 */
class FilterCategory {
  id: string = '';
  name: string = '';
}

@Entry
@Component
struct FolderDetail {
  @State folderId: string = 'all';
  @State folderName: string = '全部收藏';
  @State favorites: FavoriteItem[] = [];
  @State isLoading: boolean = true;
  @State showDeleteConfirm: boolean = false;
  @State deleteItemId: string = '';
  @State currentFilter: string = 'all';
  @State searchKeyword: string = '';
  @State showSearch: boolean = false;
  @State categories: Category[] = [];
  // 多选模式状态
  @State isSelectMode: boolean = false;
  @State selectedItems: Set<string> = new Set<string>();
  // 编辑分类相关状态
  @State showCategoryPicker: boolean = false;
  @State showAddCategoryDialog: boolean = false;
  @State primaryColor: string = '#4CAF50';
  private eventSubscriptionIds: number[] = [];

  async aboutToAppear(): Promise<void> {
    const params = router.getParams() as RouterParams;
    if (params.folderId !== undefined) {
      this.folderId = params.folderId;
    }
    if (params.folderName !== undefined) {
      this.folderName = params.folderName;
    }
    this.categories = categoryService.getCategories();
    this.primaryColor = themeService.getPrimaryColor();
    await this.loadData();
    this.subscribeEvents();
    
    // 优先处理openItemId（从Index页面传递过来的收藏项ID）
    if (params.openItemId && params.openItemId.length > 0) {
      const item = await this.getFavoriteById(params.openItemId);
      if (item) {
        this.openUrl(item);
      }
    } else if (params.openItem !== null) {
      // 兼容旧版本的openItem参数
      this.openUrl(params.openItem);
    }
  }

  aboutToDisappear(): void {
    this.unsubscribeEvents();
  }

  private subscribeEvents(): void {
    const dataChangedId = eventService.onDataChanged(() => {
      this.loadData();
    });
    this.eventSubscriptionIds.push(dataChangedId);

    const favoriteAddedId = eventService.onFavoriteAdded(() => {
      this.loadData();
    });
    this.eventSubscriptionIds.push(favoriteAddedId);

    const favoriteDeletedId = eventService.onFavoriteDeleted(() => {
      this.loadData();
    });
    this.eventSubscriptionIds.push(favoriteDeletedId);

    const categoryChangedId = eventService.onCategoryChanged(() => {
      this.categories = categoryService.getCategories();
    });
    this.eventSubscriptionIds.push(categoryChangedId);
  }

  private unsubscribeEvents(): void {
    for (const id of this.eventSubscriptionIds) {
      eventService.off(id);
    }
    this.eventSubscriptionIds = [];
  }

  async loadData(): Promise<void> {
    this.isLoading = true;
    if (this.searchKeyword.length > 0) {
      this.favorites = await dataService.searchFavorites(this.searchKeyword);
    } else {
      this.favorites = await dataService.getFavoritesByFolder(this.folderId);
    }
    this.isLoading = false;
  }

  // 根据ID获取收藏项
  async getFavoriteById(id: string): Promise<FavoriteItem | null> {
    try {
      const favorites = await dataService.getFavorites();
      const item = favorites.find(favorite => favorite.id === id);
      return item || null;
    } catch (error) {
      console.error('Failed to get favorite by id:', error);
      return null;
    }
  }

  getFilteredFavorites(): FavoriteItem[] {
    if (this.currentFilter === 'all') {
      return this.favorites;
    }
    return this.favorites.filter(f => f.category === this.currentFilter);
  }

  async deleteItem(): Promise<void> {
    await dataService.deleteFavorite(this.deleteItemId);
    this.showDeleteConfirm = false;
    await this.loadData();
  }

  // 切换多选模式
  toggleSelectMode(): void {
    this.isSelectMode = !this.isSelectMode;
    if (!this.isSelectMode) {
      this.selectedItems.clear();
    }
  }

  // 切换选中状态
  toggleItemSelection(item: FavoriteItem, selected: boolean): void {
    if (selected) {
      this.selectedItems.add(item.id);
    } else {
      this.selectedItems.delete(item.id);
    }
    // 触发UI更新
    this.selectedItems = new Set(this.selectedItems);
  }

  // 全选/取消全选
  toggleSelectAll(): void {
    const filteredItems = this.getFilteredFavorites();
    if (this.selectedItems.size === filteredItems.length) {
      // 已全选，取消全选
      this.selectedItems.clear();
    } else {
      // 全选
      this.selectedItems.clear();
      for (const item of filteredItems) {
        this.selectedItems.add(item.id);
      }
    }
    this.selectedItems = new Set(this.selectedItems);
  }

  // 批量删除
  async deleteSelectedItems(): Promise<void> {
    const ids = Array.from(this.selectedItems);
    await dataService.deleteFavorites(ids);
    this.isSelectMode = false;
    this.selectedItems.clear();
    await this.loadData();
  }

  // 批量更新分类
  async updateSelectedItemsCategory(categoryId: string): Promise<void> {
    const ids = Array.from(this.selectedItems);
    const allFavorites = await dataService.getFavorites();
    
    for (const id of ids) {
      const item = allFavorites.find(f => f.id === id);
      if (item) {
        item.category = categoryId;
        item.updateTime = Date.now();
        await dataService.updateFavorite(item);
      }
    }
    
    this.showCategoryPicker = false;
    this.isSelectMode = false;
    this.selectedItems.clear();
    await this.loadData();
  }

  // 添加自定义分类
  async addCustomCategory(category: Category): Promise<void> {
    try {
      await categoryService.addCustomCategory(category);
      this.categories = categoryService.getCategories();
      this.showAddCategoryDialog = false;
      // 自动选择新创建的分类
      await this.updateSelectedItemsCategory(category.id);
    } catch (error) {
      console.error('Failed to add custom category:', error);
    }
  }

  openUrl(item: FavoriteItem): void {
    // 参数验证
    if (!item) {
      console.error('openUrl: item is null or undefined');
      return;
    }
    
    if (!item.url || item.url.length === 0) {
      console.error('openUrl: item.url is empty', JSON.stringify(item));
      return;
    }
    
    // 验证URL格式
    let urlToOpen = item.url;
    // 确保URL有正确的协议前缀
    if (!urlToOpen.startsWith('http://') && !urlToOpen.startsWith('https://')) {
      urlToOpen = 'https://' + urlToOpen;
    }
    
    console.log('openUrl: opening URL:', urlToOpen);
    console.log('openUrl: item details:', JSON.stringify(item));
    
    try {
      const context = getContext(this) as common.UIAbilityContext;
      if (!context) {
        console.error('openUrl: context is null');
        return;
      }
      
      // 直接使用隐式 Intent 打开 URL，让系统选择合适的应用
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

  @Builder
  FilterTabs() {
    Scroll() {
      Row() {
        // 全部分类
        Text('全部')
          .fontSize(14)
          .fontColor(this.currentFilter === 'all' ? '#FFFFFF' : '#666666')
          .backgroundColor(this.currentFilter === 'all' ? this.primaryColor : '#F0F0F0')
          .padding({ left: 12, right: 12, top: 6, bottom: 6 })
          .borderRadius(16)
          .margin({ right: 8 })
          .onClick(() => {
            this.currentFilter = 'all';
          })
        
        // 其他分类
        ForEach(this.categories, (category: Category) => {
          Text(category.name)
            .fontSize(14)
            .fontColor(this.currentFilter === category.id ? '#FFFFFF' : '#666666')
            .backgroundColor(this.currentFilter === category.id ? this.primaryColor : '#F0F0F0')
            .padding({ left: 12, right: 12, top: 6, bottom: 6 })
            .borderRadius(16)
            .margin({ right: 8 })
            .onClick(() => {
              this.currentFilter = category.id;
            })
        })
      }
      .padding({ left: 16, right: 16, top: 12, bottom: 12 })
    }
    .scrollable(ScrollDirection.Horizontal)
    .scrollBar(BarState.Off)
    .width('100%')
    .backgroundColor('#FFFFFF')
  }

  build() {
    Stack() {
      Column() {
        // 标题栏
        Row() {
          Text('←')
            .fontSize(24)
            .fontColor('#333333')
            .onClick(() => {
              if (this.isSelectMode) {
                this.toggleSelectMode();
              } else {
                router.back();
              }
            })
          
          if (this.showSearch) {
            TextInput({ placeholder: '搜索收藏', text: this.searchKeyword })
              .layoutWeight(1)
              .height(36)
              .fontSize(16)
              .backgroundColor('#F5F5F5')
              .borderRadius(18)
              .margin({ left: 12, right: 12 })
              .onChange((value: string) => {
                this.searchKeyword = value;
                this.loadData();
              })
          } else {
            Text(this.isSelectMode ? `已选择 ${this.selectedItems.size} 项` : this.folderName)
              .fontSize(20)
              .fontWeight(FontWeight.Bold)
              .fontColor('#333333')
              .margin({ left: 12 })
              .layoutWeight(1)
          }
          
          // 搜索按钮
          if (!this.isSelectMode) {
            Text('🔍')
              .fontSize(24)
              .fontColor('#666666')
              .onClick(() => {
                this.showSearch = !this.showSearch;
                if (!this.showSearch) {
                  this.searchKeyword = '';
                  this.loadData();
                }
              })
          }
          
          // 编辑/取消按钮 - 显眼的样式
          if (this.isSelectMode) {
            Button('取消')
              .fontSize(14)
              .fontColor('#FF6B6B')
              .backgroundColor(Color.Transparent)
              .height(32)
              .onClick(() => {
                this.toggleSelectMode();
              })
          } else if (this.favorites.length > 0) {
            // 有收藏项时显示显眼的编辑按钮
            Button('编辑')
              .fontSize(14)
              .fontColor('#FFFFFF')
              .backgroundColor(this.primaryColor)
              .height(32)
              .borderRadius(16)
              .padding({ left: 16, right: 16 })
              .margin({ left: 12 })
              .onClick(() => {
                this.toggleSelectMode();
              })
          }
          
          // 多选模式下的全选按钮
          if (this.isSelectMode) {
            Button(this.selectedItems.size === this.getFilteredFavorites().length ? '取消全选' : '全选')
              .fontSize(14)
              .fontColor(this.primaryColor)
              .backgroundColor(Color.Transparent)
              .height(32)
              .margin({ left: 8 })
              .onClick(() => {
                this.toggleSelectAll();
              })
          }
        }
        .width('100%')
        .padding({ left: 16, right: 16, top: 12, bottom: 12 })
        .backgroundColor('#FFFFFF')
        
        // 分类筛选
        this.FilterTabs()
        
        // 收藏列表
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
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
        } else if (this.getFilteredFavorites().length === 0) {
          Column() {
            Text('📭')
              .fontSize(64)
            Text('暂无收藏')
              .fontSize(18)
              .fontColor('#999999')
              .margin({ top: 16 })
            Text('快去其他应用分享收藏吧')
              .fontSize(14)
              .fontColor('#CCCCCC')
              .margin({ top: 8 })
          }
          .width('100%')
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
        } else {
          List() {
            ForEach(this.getFilteredFavorites(), (item: FavoriteItem) => {
              ListItem() {
                FavoriteCard({
                  item: item,
                  isSelectMode: this.isSelectMode,
                  isSelected: this.selectedItems.has(item.id),
                  onItemClick: (clickedItem: FavoriteItem) => {
                    this.openUrl(clickedItem);
                  },
                  onItemLongPress: (longPressedItem: FavoriteItem) => {
                    if (!this.isSelectMode) {
                      this.toggleSelectMode();
                      this.selectedItems.add(longPressedItem.id);
                      this.selectedItems = new Set(this.selectedItems);
                    }
                  },
                  onItemSelect: (selectedItem: FavoriteItem, selected: boolean) => {
                    this.toggleItemSelection(selectedItem, selected);
                  }
                })
              }
            })
          }
          .width('100%')
          .layoutWeight(1)
          .padding({ left: 12, right: 12, top: 12, bottom: this.isSelectMode ? 80 : 12 })
          .lanes(2, 12)
          .scrollBar(BarState.Off)
        }
      }
      .width('100%')
      .height('100%')
      .backgroundColor('#F5F5F5')
      
      // 多选模式底部操作栏
      if (this.isSelectMode) {
        Row({ space: 12 }) {
          Text(`已选择 ${this.selectedItems.size} 项`)
            .fontSize(14)
            .fontColor('#666666')
            .layoutWeight(1)
          
          Button('分类')
            .height(40)
            .fontSize(16)
            .fontColor('#FFFFFF')
            .backgroundColor(this.selectedItems.size > 0 ? this.primaryColor : '#CCCCCC')
            .borderRadius(20)
            .padding({ left: 20, right: 20 })
            .enabled(this.selectedItems.size > 0)
            .onClick(() => {
              if (this.selectedItems.size > 0) {
                this.showCategoryPicker = true;
              }
            })
          
          Button('删除')
            .height(40)
            .fontSize(16)
            .fontColor('#FFFFFF')
            .backgroundColor(this.selectedItems.size > 0 ? '#FF5252' : '#CCCCCC')
            .borderRadius(20)
            .padding({ left: 20, right: 20 })
            .enabled(this.selectedItems.size > 0)
            .onClick(() => {
              if (this.selectedItems.size > 0) {
                this.showDeleteConfirm = true;
              }
            })
        }
        .width('100%')
        .height(60)
        .padding({ left: 16, right: 16 })
        .backgroundColor('#FFFFFF')
        .shadow({
          radius: 8,
          color: '#1A000000',
          offsetX: 0,
          offsetY: -2
        })
        .position({ x: 0, y: '100%' })
        .translate({ y: -60 })
      }
      
      // 删除确认弹窗
      if (this.showDeleteConfirm) {
        Column() {
          Column() {
            Text('确认删除')
              .fontSize(20)
              .fontWeight(FontWeight.Bold)
              .fontColor('#333333')
              .margin({ bottom: 16 })
            
            Text(this.isSelectMode && this.selectedItems.size > 1 
              ? `确定要删除选中的 ${this.selectedItems.size} 条收藏吗？` 
              : '确定要删除这条收藏吗？')
              .fontSize(16)
              .fontColor('#666666')
              .margin({ bottom: 24 })
            
            Row() {
              Button('取消')
                .width('45%')
                .height(44)
                .fontSize(16)
                .fontColor('#666666')
                .backgroundColor('#F0F0F0')
                .borderRadius(22)
                .onClick(() => {
                  this.showDeleteConfirm = false;
                })
              
              Button('删除')
                .width('45%')
                .height(44)
                .fontSize(16)
                .fontColor('#FFFFFF')
                .backgroundColor('#FF5252')
                .borderRadius(22)
                .onClick(() => {
                  if (this.isSelectMode && this.selectedItems.size > 0) {
                    this.deleteSelectedItems();
                  } else {
                    this.deleteItem();
                  }
                  this.showDeleteConfirm = false;
                })
            }
            .width('100%')
            .justifyContent(FlexAlign.SpaceBetween)
          }
          .width('85%')
          .padding(24)
          .backgroundColor('#FFFFFF')
          .borderRadius(16)
        }
        .width('100%')
        .height('100%')
        .justifyContent(FlexAlign.Center)
        .backgroundColor('rgba(0,0,0,0.5)')
        .onClick(() => {
          this.showDeleteConfirm = false;
        })
      }
      
      // 分类选择弹窗
      if (this.showCategoryPicker) {
        Column() {
          // 遮罩层
          Column()
            .width('100%')
            .height('100%')
            .backgroundColor('rgba(0, 0, 0, 0.5)')
            .onClick(() => {
              this.showCategoryPicker = false;
            })
          
          // 弹窗内容
          Column() {
            Text('选择分类')
              .fontSize(20)
              .fontWeight(FontWeight.Bold)
              .fontColor('#333333')
              .margin({ bottom: 20 })
            
            // 分类列表
            Flex({ wrap: FlexWrap.Wrap }) {
              ForEach(this.categories, (category: Category) => {
                Button(category.name)
                  .fontSize(14)
                  .fontColor('#666666')
                  .backgroundColor('#F0F0F0')
                  .borderRadius(16)
                  .padding({ left: 16, right: 16, top: 8, bottom: 8 })
                  .margin({ right: 8, bottom: 8 })
                  .onClick(() => {
                    this.updateSelectedItemsCategory(category.id);
                  })
              })
              
              // 自定义分类按钮
              Button('⊕自定义')
                .fontSize(14)
                .fontColor('#FFFFFF')
                .backgroundColor('#2196F3')
                .borderRadius(16)
                .padding({ left: 16, right: 16, top: 8, bottom: 8 })
                .margin({ right: 8, bottom: 8 })
                .onClick(() => {
                  this.showCategoryPicker = false;
                  this.showAddCategoryDialog = true;
                })
            }
            .width('100%')
            
            Button('取消')
              .width('100%')
              .height(44)
              .fontSize(16)
              .fontColor('#666666')
              .backgroundColor('#F0F0F0')
              .borderRadius(22)
              .margin({ top: 20 })
              .onClick(() => {
                this.showCategoryPicker = false;
              })
          }
          .width('85%')
          .padding(24)
          .backgroundColor('#FFFFFF')
          .borderRadius(16)
          .position({ x: '7.5%', y: '50%' })
          .translate({ y: '-50%' })
        }
        .width('100%')
        .height('100%')
        .position({ x: 0, y: 0 })
      }
      
      // 添加分类对话框
      if (this.showAddCategoryDialog) {
        Column() {
          // 遮罩层
          Column()
            .width('100%')
            .height('100%')
            .backgroundColor('rgba(0, 0, 0, 0.5)')
            .onClick(() => {
              this.showAddCategoryDialog = false;
            })
          
          // 对话框内容
          Column() {
            AddCategoryDialog({
              onConfirm: (category: Category) => {
                this.addCustomCategory(category);
              },
              onCancel: () => {
                this.showAddCategoryDialog = false;
              }
            })
          }
          .width('90%')
          .position({ x: '5%', y: '50%' })
          .translate({ y: '-50%' })
        }
        .width('100%')
        .height('100%')
        .position({ x: 0, y: 0 })
      }
    }
    .width('100%')
    .height('100%')
  }
}