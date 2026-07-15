import { router } from '@kit.ArkUI';
import { common } from '@kit.AbilityKit';
import { dataService } from '../service/DataService';
import { categoryService } from '../service/CategoryService';
import { urlParserService } from '../service/UrlParserService';
import { FavoriteItem, Folder, DEFAULT_CATEGORIES } from '../model/FavoriteItem';
import { themeService } from '../service/ThemeService';

/**
 * 分享数据类
 */
class ShareDataItem {
  title: string = '';
  text: string = '';
  url: string = '';
  imageUri: string = '';
  sourceApp: string = '';
  sourcePackage: string = '';
}

@Entry
@Component
struct SaveShare {
  @State shareData: ShareDataItem | null = null;
  @State folders: Folder[] = [];
  @State selectedFolderId: string = 'all';
  @State detectedCategory: string = '';
  @State isSaving: boolean = false;
  @State showSuccess: boolean = false;
  @State previewCoverImage: string = ''; // 预览封面图片
  @State previewSourceApp: string = ''; // 预览来源应用
  @State primaryColor: string = '#4CAF50';

  async aboutToAppear(): Promise<void> {
    // 获取分享数据
    const data = AppStorage.get<ShareDataItem>('pendingShareData');
    console.log('=== SaveShare aboutToAppear ===');
    console.log('SaveShare: pendingShareData =', JSON.stringify(data));
    
    if (data !== undefined && data !== null) {
      this.shareData = data;
      console.log('SaveShare: Loaded share data:');
      console.log('  title:', data.title);
      console.log('  sourceApp:', data.sourceApp);
      console.log('  sourcePackage:', data.sourcePackage);
      console.log('  url:', data.url);
      console.log('  imageUri:', data.imageUri);
      console.log('  text:', data.text);
      
      // 设置预览来源应用（优先使用 ShareAbility 提取的）
      if (data.sourceApp && data.sourceApp.length > 0 && data.sourceApp !== '未知应用') {
        this.previewSourceApp = data.sourceApp;
        console.log('SaveShare: Using sourceApp from ShareAbility:', this.previewSourceApp);
      }
      
      // 设置预览封面图片（如果有）
      if (data.imageUri && data.imageUri.length > 0) {
        this.previewCoverImage = data.imageUri;
        console.log('SaveShare: Using imageUri from ShareAbility:', this.previewCoverImage);
      }
      
      // 如果有 URL，尝试解析获取更多信息
      if (data.url && data.url.length > 0) {
        await this.parseUrlForPreview();
      }
      
      console.log('SaveShare: Final preview values:');
      console.log('  previewSourceApp:', this.previewSourceApp);
      console.log('  previewCoverImage:', this.previewCoverImage);
    }
    
    this.loadFolders();
    
    if (this.shareData !== null && this.shareData.title.length > 0) {
      const category = categoryService.classifyContent(this.shareData.title, this.shareData.text);
      this.detectedCategory = category.name;
    }
  }

  // 解析 URL 获取预览信息
  async parseUrlForPreview(): Promise<void> {
    if (!this.shareData || !this.shareData.url || this.shareData.url.length === 0) {
      console.log('SaveShare: parseUrlForPreview - no URL, skipping');
      return;
    }
    
    console.log('SaveShare: parseUrlForPreview - parsing URL:', this.shareData.url);
    
    try {
      const parsedInfo = await urlParserService.parseUrl(this.shareData.url);
      console.log('SaveShare: Parsed URL info:', JSON.stringify(parsedInfo));
      
      // 如果没有封面图片，使用解析得到的
      if ((!this.previewCoverImage || this.previewCoverImage.length === 0) && 
          parsedInfo.coverImage && parsedInfo.coverImage.length > 0) {
        this.previewCoverImage = parsedInfo.coverImage;
        console.log('SaveShare: Using parsed cover image:', this.previewCoverImage);
      }
      
      // 如果没有来源应用，使用解析得到的
      if ((!this.previewSourceApp || this.previewSourceApp.length === 0 || this.previewSourceApp === '未知应用') &&
          parsedInfo.sourceApp && parsedInfo.sourceApp.length > 0) {
        this.previewSourceApp = parsedInfo.sourceApp;
        console.log('SaveShare: Using parsed source app:', this.previewSourceApp);
      }
    } catch (error) {
      console.error('SaveShare: Failed to parse URL for preview:', error);
    }
  }

  async loadFolders(): Promise<void> {
    this.folders = await dataService.getFolders();
    this.primaryColor = themeService.getPrimaryColor();
  }

  // 根据分享内容判断类型
  private determineContentType(): 'article' | 'video' | 'image' | 'website' | 'other' {
    if (!this.shareData) return 'other';
    
    // 如果有图片 URI，可能是图片类型
    if (this.shareData.imageUri && this.shareData.imageUri.length > 0) {
      const ext = this.shareData.imageUri.toLowerCase();
      if (ext.includes('.jpg') || ext.includes('.jpeg') || ext.includes('.png') || 
          ext.includes('.gif') || ext.includes('.webp')) {
        return 'image';
      }
    }
    
    // 如果有 URL，可能是网站或视频
    if (this.shareData.url && this.shareData.url.length > 0) {
      const url = this.shareData.url.toLowerCase();
      if (url.includes('video') || url.includes('.mp4') || url.includes('.avi') ||
          url.includes('bilibili.com/video') || url.includes('douyin.com/video') ||
          url.includes('youtube.com/watch')) {
        return 'video';
      }
      return 'website';
    }
    
    // 如果有文本内容，可能是文章
    if (this.shareData.text && this.shareData.text.length > 100) {
      return 'article';
    }
    
    return 'other';
  }

  async saveFavorite(): Promise<void> {
    if (this.shareData === null) return;
    
    console.log('=== SaveShare saveFavorite ===');
    this.isSaving = true;
    
    // 使用预览中已设置的值作为默认值
    let coverImage = this.previewCoverImage || this.shareData.imageUri || '';
    let sourceApp = this.previewSourceApp || this.shareData.sourceApp || '';
    let sourcePackage = this.shareData.sourcePackage || '';
    let title = this.shareData.title || '';
    let contentType: 'article' | 'video' | 'image' | 'website' | 'other' = 'other';
    
    console.log('SaveShare: Initial values:');
    console.log('  coverImage:', coverImage);
    console.log('  sourceApp:', sourceApp);
    console.log('  sourcePackage:', sourcePackage);
    console.log('  title:', title);
    
    // 如果有 URL，尝试解析获取更多信息
    if (this.shareData.url && this.shareData.url.length > 0) {
      try {
        const parsedInfo = await urlParserService.parseUrl(this.shareData.url);
        console.log('SaveShare: Parsed URL info:', JSON.stringify(parsedInfo));
        
        // 如果没有封面图片，使用解析得到的
        if (!coverImage || coverImage.length === 0) {
          coverImage = parsedInfo.coverImage || '';
        }
        
        // 如果没有来源应用或来源应用是"未知应用"，使用解析得到的
        if (!sourceApp || sourceApp.length === 0 || sourceApp === '未知应用') {
          sourceApp = parsedInfo.sourceApp;
        }
        
        // 如果没有来源包名，使用解析得到的
        if (!sourcePackage || sourcePackage.length === 0) {
          sourcePackage = parsedInfo.sourcePackage || '';
        }
        
        // 使用解析得到的内容类型
        contentType = parsedInfo.type;
        
        // 如果没有标题，使用解析得到的
        if (!title || title.length === 0) {
          title = parsedInfo.title;
        }
      } catch (error) {
        console.error('SaveShare: Failed to parse URL:', error);
        contentType = this.determineContentType();
      }
    } else {
      // 没有 URL 时，根据分享内容判断类型
      contentType = this.determineContentType();
    }
    
    console.log('SaveShare: Final values:');
    console.log('  coverImage:', coverImage);
    console.log('  sourceApp:', sourceApp);
    console.log('  contentType:', contentType);
    
    const category = categoryService.classifyContent(
      this.shareData.title,
      this.shareData.text
    );
    
    const item: FavoriteItem = {
      id: `fav_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      title: title.length > 0 ? title : '无标题',
      sourceApp: sourceApp.length > 0 ? sourceApp : '未知应用',
      sourcePackage: sourcePackage || '',
      url: this.shareData.url,
      coverImage: coverImage.length > 0 ? coverImage : undefined,
      description: this.shareData.text.length > 0 ? this.shareData.text : undefined,
      folderId: this.selectedFolderId,
      category: category.id,
      createTime: Date.now(),
      updateTime: Date.now(),
      type: contentType
    };
    
    console.log('SaveShare: Saving favorite item:', JSON.stringify(item));
    await dataService.addFavorite(item);
    
    this.isSaving = false;
    this.showSuccess = true;
    
    // 清理AppStorage数据
    AppStorage.delete('pendingShareData');
    
    setTimeout(() => {
      this.exitApp();
    }, 1500);
  }

  exitApp(): void {
    const context = getContext(this) as common.UIAbilityContext;
    context.terminateSelf();
  }

  build() {
    Column() {
      if (this.showSuccess) {
        Column() {
          Text('✓')
            .fontSize(80)
            .fontColor(this.primaryColor)
            .margin({ bottom: 20 })
          
          Text('保存成功')
            .fontSize(24)
            .fontWeight(FontWeight.Bold)
            .fontColor('#333333')
          
          Text('已添加到收藏')
            .fontSize(16)
            .fontColor('#999999')
            .margin({ top: 8 })
        }
        .width('100%')
        .height('100%')
        .justifyContent(FlexAlign.Center)
      } else {
        Column() {
          // 标题栏
          Row() {
            Text('保存收藏')
              .fontSize(20)
              .fontWeight(FontWeight.Bold)
              .fontColor('#333333')
          }
          .width('100%')
          .padding({ left: 16, right: 16, top: 16, bottom: 16 })
          .backgroundColor('#FFFFFF')
          
          // 内容预览
          Column() {
            // 显示封面图片（优先使用解析得到的封面，其次使用分享数据中的图片）
            if (this.previewCoverImage.length > 0) {
              Image(this.previewCoverImage)
                .width('100%')
                .height(180)
                .objectFit(ImageFit.Cover)
                .borderRadius(12)
                .margin({ bottom: 16 })
                .onError(() => {
                  console.log('SaveShare: Failed to load preview cover image:', this.previewCoverImage);
                })
            } else if (this.shareData !== null && this.shareData.imageUri.length > 0) {
              Image(this.shareData.imageUri)
                .width('100%')
                .height(180)
                .objectFit(ImageFit.Cover)
                .borderRadius(12)
                .margin({ bottom: 16 })
            }
            
            Text(this.shareData !== null && this.shareData.title.length > 0 ? this.shareData.title : '无标题')
              .fontSize(18)
              .fontWeight(FontWeight.Medium)
              .fontColor('#333333')
              .maxLines(3)
              .textOverflow({ overflow: TextOverflow.Ellipsis })
              .width('100%')
            
            // 显示来源应用（优先使用解析得到的来源应用）
            Row() {
              Text('来源: ')
                .fontSize(14)
                .fontColor('#999999')
              Text(this.previewSourceApp.length > 0 ? this.previewSourceApp : 
                   (this.shareData !== null && this.shareData.sourceApp.length > 0 ? this.shareData.sourceApp : '未知来源'))
                .fontSize(14)
                .fontColor(this.primaryColor)
                .fontWeight(FontWeight.Medium)
            }
            .margin({ top: 8 })
            
            if (this.detectedCategory.length > 0) {
              Row() {
                Text('智能识别: ')
                  .fontSize(14)
                  .fontColor('#666666')
                Text(this.detectedCategory)
                  .fontSize(14)
                  .fontColor('#FFFFFF')
                  .backgroundColor(this.primaryColor)
                  .padding({ left: 8, right: 8, top: 2, bottom: 2 })
                  .borderRadius(4)
              }
              .margin({ top: 12 })
            }
          }
          .width('100%')
          .padding(16)
          .backgroundColor('#FFFFFF')
          .borderRadius(12)
          .margin(16)
          
          // 选择文件夹
          Column() {
            Text('选择收藏夹')
              .fontSize(16)
              .fontWeight(FontWeight.Medium)
              .fontColor('#333333')
              .width('100%')
              .margin({ bottom: 12 })
            
            List() {
              ForEach(this.folders, (folder: Folder) => {
                ListItem() {
                  Row() {
                    Text(folder.name)
                      .fontSize(16)
                      .fontColor('#333333')
                    
                    Blank()
                    
                    if (this.selectedFolderId === folder.id) {
                      Text('✓')
                        .fontSize(24)
                        .fontColor(this.primaryColor)
                    }
                  }
                  .width('100%')
                  .padding({ left: 16, right: 16, top: 12, bottom: 12 })
                  .backgroundColor(this.selectedFolderId === folder.id ? '#E8F5E9' : '#FFFFFF')
                  .borderRadius(8)
                  .onClick(() => {
                    this.selectedFolderId = folder.id;
                  })
                }
              })
            }
            .width('100%')
            .height(200)
          }
          .width('100%')
          .padding(16)
          .backgroundColor('#FFFFFF')
          .borderRadius(12)
          .margin({ left: 16, right: 16 })
          
          Blank()
          
          Button(this.isSaving ? '保存中...' : '保存')
            .width('90%')
            .height(48)
            .fontSize(18)
            .fontColor('#FFFFFF')
            .backgroundColor(this.isSaving ? '#CCCCCC' : this.primaryColor)
            .borderRadius(24)
            .margin({ bottom: 32 })
            .enabled(!this.isSaving)
            .onClick(() => {
              this.saveFavorite();
            })
        }
        .width('100%')
        .height('100%')
        .backgroundColor('#F5F5F5')
      }
    }
    .width('100%')
    .height('100%')
  }
}