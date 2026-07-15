import { router } from '@kit.ArkUI';
import { dataService } from '../service/DataService';
import { categoryService } from '../service/CategoryService';
import { urlParserService } from '../service/UrlParserService';
import { clipboardService } from '../service/ClipboardService';
import { FavoriteItem, Folder, DEFAULT_CATEGORIES, Category } from '../model/FavoriteItem';
import { AddCategoryDialog } from '../component/AddCategoryDialog';
import { themeService } from '../service/ThemeService';

/**
 * 新建收藏项页面参数
 */
class CreateFavoriteParams {
  initialUrl: string = '';
  initialTitle: string = '';
}

@Entry
@Component
struct CreateFavorite {
  @State url: string = '';
  @State title: string = '';
  @State description: string = '';
  @State folders: Folder[] = [];
  @State selectedFolderId: string = 'all';
  @State categories: Category[] = [];
  @State selectedCategory: string = '';
  @State isParsing: boolean = false;
  @State showClipboardPrompt: boolean = false;
  @State clipboardUrl: string = '';
  @State isSaving: boolean = false;
  @State showSuccess: boolean = false;
  @State showAddCategoryDialog: boolean = false;
  @State primaryColor: string = '#4CAF50';

  async aboutToAppear(): Promise<void> {
    // 获取路由参数
    const params = router.getParams() as CreateFavoriteParams;
    if (params.initialUrl) {
      this.url = params.initialUrl;
      await this.parseUrl();
    }
    if (params.initialTitle) {
      this.title = params.initialTitle;
    }
    
    this.loadFolders();
    this.loadCategories();
    this.checkClipboard();
    this.primaryColor = themeService.getPrimaryColor();
  }

  async loadFolders(): Promise<void> {
    this.folders = await dataService.getFolders();
  }

  loadCategories(): void {
    this.categories = categoryService.getCategories();
    if (this.categories.length > 0) {
      this.selectedCategory = this.categories[0].id;
    }
  }

  // 添加自定义分类
  async addCustomCategory(category: Category): Promise<void> {
    try {
      await categoryService.addCustomCategory(category);
      this.categories = categoryService.getCategories();
      this.selectedCategory = category.id;
      this.showAddCategoryDialog = false;
    } catch (error) {
      console.error('Failed to add custom category:', error);
    }
  }

  async checkClipboard(): Promise<void> {
    try {
      const hasUrl = await clipboardService.hasUrlInClipboard();
      if (hasUrl) {
        const clipboardText = await clipboardService.getClipboardText();
        if (clipboardText) {
          // 简单的URL提取逻辑
          const urlPattern = /https?:\/\/[^\s]+|www\.[^\s]+/gi;
          const matches = clipboardText.match(urlPattern);
          if (matches && matches.length > 0) {
            let url = matches[0];
            if (url.startsWith('www.')) {
              url = 'https://' + url;
            }
            this.clipboardUrl = url;
            this.showClipboardPrompt = true;
          }
        }
      }
    } catch (error) {
      console.error('Failed to check clipboard:', error);
    }
  }

  useClipboardUrl(): void {
    this.url = this.clipboardUrl;
    this.showClipboardPrompt = false;
    this.parseUrl();
  }

  dismissClipboardPrompt(): void {
    this.showClipboardPrompt = false;
  }

  async parseUrl(): Promise<void> {
    if (!this.url || this.url.trim().length === 0) {
      return;
    }

    this.isParsing = true;
    try {
      const parsedInfo = await urlParserService.parseUrl(this.url);
      
      // 自动填充信息
      if (parsedInfo.title && !this.title) {
        this.title = parsedInfo.title;
      }
      
      if (parsedInfo.description && !this.description) {
        this.description = parsedInfo.description;
      }
      
      // 自动选择分类
      if (parsedInfo.type) {
        const category = categoryService.classifyByType(parsedInfo.type);
        if (category) {
          this.selectedCategory = category.name;
        }
      }
    } catch (error) {
      console.error('Failed to parse URL:', error);
    } finally {
      this.isParsing = false;
    }
  }

  async saveFavorite(): Promise<void> {
    if (!this.url || this.url.trim().length === 0) {
      // 提示用户输入URL
      return;
    }

    this.isSaving = true;
    
    try {
      // 解析URL获取更多信息
      const parsedInfo = await urlParserService.parseUrl(this.url);
      
      // 获取分类ID
      const categoryId = this.selectedCategory || DEFAULT_CATEGORIES[0].id;
      
      // 确定内容类型
      let contentType: 'article' | 'video' | 'image' | 'website' | 'other' = parsedInfo.type;
      
      // 如果是网站链接，设置为'article'类型
      if (this.url.startsWith('http') && !contentType) {
        contentType = 'article';
      }
      
      const item: FavoriteItem = {
        id: `fav_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        title: this.title.trim() || parsedInfo.title || '无标题',
        sourceApp: parsedInfo.sourceApp || '手动添加',
        sourcePackage: parsedInfo.sourcePackage || '',
        url: this.url.trim(),
        coverImage: parsedInfo.coverImage,
        description: this.description.trim() || parsedInfo.description || undefined,
        folderId: this.selectedFolderId,
        category: categoryId,
        createTime: Date.now(),
        updateTime: Date.now(),
        type: contentType
      };
      
      console.log('CreateFavorite: Saving favorite item:', item);
      await dataService.addFavorite(item);
      
      this.showSuccess = true;
      
      // 延迟返回上一页
      setTimeout(() => {
        router.back();
      }, 1500);
      
    } catch (error) {
      console.error('Failed to save favorite:', error);
    } finally {
      this.isSaving = false;
    }
  }

  cancel(): void {
    router.back();
  }

  build() {
    Column() {
      // 标题栏
      Row({ space: 12 }) {
        Text('新建收藏')
          .fontSize(20)
          .fontWeight(FontWeight.Bold)
          .fontColor('#000000')
          .layoutWeight(1)
        
        Button('取消')
          .fontSize(14)
          .fontColor('#666666')
          .backgroundColor(Color.Transparent)
          .borderWidth(0)
          .onClick(() => {
            this.cancel();
          })
        
        Button('保存')
          .fontSize(14)
          .fontColor(this.url.trim().length > 0 ? this.primaryColor : '#CCCCCC')
          .backgroundColor(Color.Transparent)
          .borderWidth(0)
          .onClick(() => {
            if (this.url.trim().length > 0) {
              this.saveFavorite();
            }
          })
      }
      .width('100%')
      .padding({ left: 16, right: 16, top: 12, bottom: 12 })
      .backgroundColor('#FFFFFF')
      .borderRadius(8)
      .margin({ top: 12, bottom: 12 })

      Scroll() {
        Column({ space: 16 }) {
          // 剪贴板提示
          if (this.showClipboardPrompt) {
            Column() {
              Row({ space: 8 }) {
                Text('✂️')
                  .fontSize(16)
                Text('检测到剪贴板中的链接')
                  .fontSize(14)
                  .fontColor('#666666')
                  .layoutWeight(1)
                Button('使用')
                  .fontSize(12)
                  .fontColor(this.primaryColor)
                  .backgroundColor('#E8F5E9')
                  .borderRadius(4)
                  .padding({ left: 8, right: 8, top: 4, bottom: 4 })
                  .onClick(() => {
                    this.useClipboardUrl();
                  })
                Button('忽略')
                  .fontSize(12)
                  .fontColor('#666666')
                  .backgroundColor('#F5F5F5')
                  .borderRadius(4)
                  .padding({ left: 8, right: 8, top: 4, bottom: 4 })
                  .onClick(() => {
                    this.dismissClipboardPrompt();
                  })
              }
              .width('100%')
              .padding({ left: 12, right: 12, top: 8, bottom: 8 })
              .backgroundColor('#F0F9FF')
              .borderRadius(8)
              
              Text(this.clipboardUrl)
                .fontSize(12)
                .fontColor('#666666')
                .maxLines(2)
                .textOverflow({ overflow: TextOverflow.Ellipsis })
                .width('100%')
                .margin({ top: 4 })
            }
            .width('100%')
            .padding({ left: 12, right: 12, top: 8, bottom: 8 })
            .backgroundColor('#F0F9FF')
            .borderRadius(8)
            .margin({ bottom: 8 })
          }

          // URL输入
          Column({ space: 8 }) {
            Text('链接地址')
              .fontSize(14)
              .fontColor('#333333')
              .fontWeight(FontWeight.Medium)
              .width('100%')
            
            TextInput({ placeholder: '请输入或粘贴链接地址', text: this.url })
              .width('100%')
              .height(40)
              .fontSize(14)
              .backgroundColor('#FFFFFF')
              .borderRadius(4)
              .border({ width: 1, color: '#E0E0E0' })
              .padding({ left: 8, right: 8 })
              .onChange((value: string) => {
                this.url = value;
              })
            
            if (this.url.length > 0) {
              Row({ space: 8 }) {
                if (this.isParsing) {
                  LoadingProgress()
                    .width(16)
                    .height(16)
                  Text('正在解析链接...')
                    .fontSize(12)
                    .fontColor('#666666')
                } else {
                  Button('解析链接')
                    .fontSize(12)
                    .fontColor(this.primaryColor)
                    .backgroundColor('#E8F5E9')
                    .borderRadius(4)
                    .padding({ left: 8, right: 8, top: 4, bottom: 4 })
                    .onClick(() => {
                      this.parseUrl();
                    })
                }
              }
              .margin({ top: 4 })
            }
          }
          .width('100%')
          .padding({ left: 16, right: 16 })

          // 标题输入
          Column({ space: 8 }) {
            Text('标题')
              .fontSize(14)
              .fontColor('#333333')
              .fontWeight(FontWeight.Medium)
              .width('100%')
            
            TextInput({ placeholder: '请输入标题（可选）', text: this.title })
              .width('100%')
              .height(40)
              .fontSize(14)
              .backgroundColor('#FFFFFF')
              .borderRadius(4)
              .border({ width: 1, color: '#E0E0E0' })
              .padding({ left: 8, right: 8 })
              .onChange((value: string) => {
                this.title = value;
              })
          }
          .width('100%')
          .padding({ left: 16, right: 16 })

          // 描述输入
          Column({ space: 8 }) {
            Text('描述')
              .fontSize(14)
              .fontColor('#333333')
              .fontWeight(FontWeight.Medium)
              .width('100%')
            
            TextArea({ placeholder: '请输入描述（可选）', text: this.description })
              .width('100%')
              .height(80)
              .fontSize(14)
              .backgroundColor('#FFFFFF')
              .borderRadius(4)
              .border({ width: 1, color: '#E0E0E0' })
              .padding({ left: 8, right: 8, top: 8, bottom: 8 })
              .onChange((value: string) => {
                this.description = value;
              })
          }
          .width('100%')
          .padding({ left: 16, right: 16 })

          // 文件夹选择
          Column({ space: 8 }) {
            Text('文件夹')
              .fontSize(14)
              .fontColor('#333333')
              .fontWeight(FontWeight.Medium)
              .width('100%')
            
            Flex({ wrap: FlexWrap.Wrap }) {
              ForEach(this.folders, (folder: Folder) => {
                Button(folder.name)
                  .fontSize(12)
                  .fontColor(this.selectedFolderId === folder.id ? '#FFFFFF' : '#666666')
                  .backgroundColor(this.selectedFolderId === folder.id ? this.primaryColor : '#F0F0F0')
                  .borderRadius(16)
                  .padding({ left: 12, right: 12, top: 6, bottom: 6 })
                  .margin({ right: 8, bottom: 8 })
                  .onClick(() => {
                    this.selectedFolderId = folder.id;
                  })
              })
            }
            .width('100%')
          }
          .width('100%')
          .padding({ left: 16, right: 16 })

          // 分类选择
          Column({ space: 8 }) {
            Text('分类')
              .fontSize(14)
              .fontColor('#333333')
              .fontWeight(FontWeight.Medium)
              .width('100%')
            
            Flex({ wrap: FlexWrap.Wrap }) {
              ForEach(this.categories, (category: Category) => {
                Button(category.name)
                  .fontSize(12)
                  .fontColor(this.selectedCategory === category.id ? '#FFFFFF' : '#666666')
                  .backgroundColor(this.selectedCategory === category.id ? this.primaryColor : '#F0F0F0')
                  .borderRadius(16)
                  .padding({ left: 12, right: 12, top: 6, bottom: 6 })
                  .margin({ right: 8, bottom: 8 })
                  .onClick(() => {
                    this.selectedCategory = category.id;
                  })
              })
              
              // 自定义分类按钮
              Button('⊕自定义')
                .fontSize(12)
                .fontColor('#FFFFFF')
                .backgroundColor('#2196F3')
                .borderRadius(16)
                .padding({ left: 12, right: 12, top: 6, bottom: 6 })
                .margin({ right: 8, bottom: 8 })
                .onClick(() => {
                  this.showAddCategoryDialog = true;
                })
            }
            .width('100%')
          }
          .width('100%')
          .padding({ left: 16, right: 16 })

          // 保存按钮
          Button('保存收藏')
            .width('90%')
            .height(48)
            .fontSize(16)
            .fontColor('#FFFFFF')
            .backgroundColor(this.url.trim().length > 0 ? this.primaryColor : '#CCCCCC')
            .borderRadius(8)
            .margin({ top: 24, bottom: 24 })
            .onClick(() => {
              if (this.url.trim().length > 0) {
                this.saveFavorite();
              }
            })
            .enabled(this.url.trim().length > 0 && !this.isSaving)

          // 成功提示
          if (this.showSuccess) {
            Column() {
              Text('✅')
                .fontSize(24)
                .margin({ bottom: 8 })
              Text('收藏已保存')
                .fontSize(16)
                .fontColor(this.primaryColor)
                .fontWeight(FontWeight.Medium)
            }
            .width('100%')
            .justifyContent(FlexAlign.Center)
            .alignItems(HorizontalAlign.Center)
            .margin({ top: 16, bottom: 16 })
          }
        }
        .width('100%')
        .padding({ top: 8, bottom: 24 })
      }
      .width('100%')
      .height('100%')
      
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
    .backgroundColor('#F5F5F5')
  }
}