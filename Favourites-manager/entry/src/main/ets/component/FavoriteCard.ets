import { FavoriteItem, DEFAULT_CATEGORIES } from '../model/FavoriteItem';

/**
 * 收藏卡片组件
 * 类似小红书/B站的瀑布流卡片样式
 */
@Component
export struct FavoriteCard {
  @Prop item: FavoriteItem = {} as FavoriteItem;
  @Prop isSelectMode: boolean = false;
  @Prop isSelected: boolean = false;
  onItemClick: (item: FavoriteItem) => void = () => {};
  onItemLongPress: (item: FavoriteItem) => void = () => {};
  onItemSelect: (item: FavoriteItem, selected: boolean) => void = () => {};

  getCategoryColor(): string {
    const category = DEFAULT_CATEGORIES.find(c => c.id === this.item.category);
    return category?.color || '#9E9E9E';
  }

  getTypeIcon(): string {
    switch (this.item.type) {
      case 'video':
        return '🎬';
      case 'article':
        return '📄';
      case 'image':
        return '🖼️';
      default:
        return '🔗';
    }
  }

  getSourceAppIcon(): string {
    const sourceApp = this.item.sourceApp.toLowerCase();
    if (sourceApp.includes('哔哩哔哩') || sourceApp.includes('bilibili')) {
      return '📺';
    } else if (sourceApp.includes('抖音') || sourceApp.includes('douyin')) {
      return '🎵';
    } else if (sourceApp.includes('小红书')) {
      return '📕';
    } else if (sourceApp.includes('知乎')) {
      return '💡';
    } else if (sourceApp.includes('微博')) {
      return '🐦';
    } else if (sourceApp.includes('微信')) {
      return '💬';
    } else if (sourceApp.includes('youtube')) {
      return '▶️';
    } else if (sourceApp.includes('twitter')) {
      return '🐦';
    } else if (sourceApp.includes('淘宝') || sourceApp.includes('天猫') || sourceApp.includes('京东')) {
      return '🛒';
    } else if (sourceApp.includes('浏览器') || sourceApp.includes('chrome') || sourceApp.includes('safari')) {
      return '🌐';
    } else {
      return '📱';
    }
  }

  build() {
    Column() {
      // 封面图片区域
      Stack({ alignContent: Alignment.BottomStart }) {
        if (this.item.coverImage) {
          Image(this.item.coverImage)
            .width('100%')
            .aspectRatio(this.item.type === 'video' ? 16 / 9 : 4 / 3)
            .objectFit(ImageFit.Cover)
            .borderRadius({ topLeft: 12, topRight: 12 })
            .onError(() => {
              console.log('Failed to load cover image:', this.item.coverImage);
            })
            .onComplete(() => {
              console.log('Cover image loaded successfully:', this.item.coverImage);
            })
        } else {
          // 无封面时显示占位
          Column() {
            Text(this.getTypeIcon())
              .fontSize(40)
          }
          .width('100%')
          .aspectRatio(4 / 3)
          .backgroundColor('#F0F0F0')
          .justifyContent(FlexAlign.Center)
          .borderRadius({ topLeft: 12, topRight: 12 })
        }
        
        // 多选模式下显示选择框（左上角）
        if (this.isSelectMode) {
          Row() {
            if (this.isSelected) {
              Text('✓')
                .fontSize(14)
                .fontColor('#FFFFFF')
            }
          }
          .width(22)
          .height(22)
          .backgroundColor(this.isSelected ? '#FF6B6B' : 'rgba(255, 255, 255, 0.8)')
          .borderRadius(11)
          .border(this.isSelected ? undefined : { width: 2, color: '#CCCCCC' })
          .justifyContent(FlexAlign.Center)
          .position({ x: 8, y: 8 })
        }
        
        // 类型标签（居中）- 非多选模式显示
        if (this.item.type === 'video' && !this.isSelectMode) {
          Row() {
            Text('▶')
              .fontSize(16)
              .fontColor('#FFFFFF')
          }
          .width(32)
          .height(32)
          .backgroundColor('rgba(0,0,0,0.5)')
          .borderRadius(16)
          .justifyContent(FlexAlign.Center)
        }
        
        // 分类标签（右上角）- 非多选模式显示
        if (!this.isSelectMode) {
          Text(this.getCategoryLabel())
            .fontSize(10)
            .fontColor('#FFFFFF')
            .backgroundColor(this.getCategoryColor())
            .padding({ left: 6, right: 6, top: 2, bottom: 2 })
            .borderRadius(4)
            .position({ x: '100%', y: 8 })
            .translate({ x: '-100%' })
        }
        
        // 来源应用名称（左下角，在封面图片内部）- 非多选模式显示
        if (!this.isSelectMode && this.item.sourceApp && this.item.sourceApp.length > 0 && this.item.sourceApp !== '未知应用') {
          Row() {
            Text(this.getSourceAppIcon())
              .fontSize(10)
              .fontColor('#FFFFFF')
              .margin({ right: 2 })
            Text(this.item.sourceApp)
              .fontSize(10)
              .fontColor('#FFFFFF')
              .maxLines(1)
              .textOverflow({ overflow: TextOverflow.Ellipsis })
              .constraintSize({ maxWidth: 100 })
          }
          .padding({ left: 6, right: 6, top: 2, bottom: 2 })
          .backgroundColor('rgba(0, 0, 0, 0.6)')
          .borderRadius(4)
          .margin({ left: 8, bottom: 8 })
        }
      }
      .width('100%')
      
      // 文字信息区域
      Column() {
        // 标题
        Text(this.item.title)
          .fontSize(14)
          .fontWeight(FontWeight.Medium)
          .fontColor('#333333')
          .maxLines(2)
          .textOverflow({ overflow: TextOverflow.Ellipsis })
          .width('100%')
          .lineHeight(20)
        
        // 时间
        Text(this.formatTime(this.item.createTime))
          .fontSize(12)
          .fontColor('#CCCCCC')
          .margin({ top: 8 })
      }
      .width('100%')
      .padding(10)
      .alignItems(HorizontalAlign.Start)
    }
    .width('100%')
    .backgroundColor('#FFFFFF')
    .borderRadius(12)
    .shadow({
      radius: 4,
      color: '#1A000000',
      offsetX: 0,
      offsetY: 2
    })
    .opacity(this.isSelectMode && this.isSelected ? 0.8 : 1)
    .border(this.isSelectMode && this.isSelected ? { width: 2, color: '#FF6B6B' } : undefined)
    .onClick(() => {
      if (this.isSelectMode) {
        // 多选模式下切换选中状态
        this.onItemSelect(this.item, !this.isSelected);
      } else {
        this.onItemClick(this.item);
      }
    })
    .gesture(
      LongPressGesture({ repeat: false })
        .onAction(() => {
          if (!this.isSelectMode) {
            this.onItemLongPress(this.item);
          }
        })
    )
  }

  getCategoryLabel(): string {
    const category = DEFAULT_CATEGORIES.find(c => c.id === this.item.category);
    return category?.name || '其他';
  }

  formatTime(timestamp: number): string {
    const now = Date.now();
    const diff = now - timestamp;
    const minute = 60 * 1000;
    const hour = 60 * minute;
    const day = 24 * hour;
    
    if (diff < minute) {
      return '刚刚';
    } else if (diff < hour) {
      return `${Math.floor(diff / minute)}分钟前`;
    } else if (diff < day) {
      return `${Math.floor(diff / hour)}小时前`;
    } else if (diff < 7 * day) {
      return `${Math.floor(diff / day)}天前`;
    } else {
      const date = new Date(timestamp);
      return `${date.getMonth() + 1}/${date.getDate()}`;
    }
  }
}