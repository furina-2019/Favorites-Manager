import { themeService } from '../service/ThemeService';

/**
 * 2x4 服务卡片页面
 * 展示最新收藏和猜你想看
 */
let storageCard = new LocalStorage();

@Entry(storageCard)
@Component
struct WidgetCard {
  @LocalStorageProp('latestTitle') latestTitle: string = '暂无收藏';
  @LocalStorageProp('latestSource') latestSource: string = '';
  @LocalStorageProp('recommendTitle') recommendTitle: string = '暂无收藏';
  @LocalStorageProp('recommendSource') recommendSource: string = '';
  @LocalStorageProp('totalCount') totalCount: number = 0;
  @State primaryColor: string = '#4CAF50';

  aboutToAppear(): void {
    this.primaryColor = themeService.getPrimaryColor();
  }

  build() {
    Column() {
      // 标题栏
      Row() {
        Text('收藏夹')
          .fontSize(14)
          .fontWeight(FontWeight.Bold)
          .fontColor('#333333')
        
        Blank()
        
        Text(`${this.totalCount}个`)
          .fontSize(12)
          .fontColor('#999999')
      }
      .width('100%')
      .padding({ left: 12, right: 12, top: 8, bottom: 8 })
      
      // 内容区域 - 两列布局
      Row() {
        // 最新收藏
        Column() {
          Text('最新收藏')
            .fontSize(10)
            .fontColor(this.primaryColor)
            .margin({ bottom: 4 })
          
          Text(this.latestTitle)
            .fontSize(12)
            .fontColor('#333333')
            .maxLines(2)
            .textOverflow({ overflow: TextOverflow.Ellipsis })
            .width('100%')
          
          if (this.latestSource) {
            Text(this.latestSource)
              .fontSize(10)
              .fontColor('#999999')
              .margin({ top: 2 })
              .maxLines(1)
              .textOverflow({ overflow: TextOverflow.Ellipsis })
          }
        }
        .layoutWeight(1)
        .alignItems(HorizontalAlign.Start)
        .padding(8)
        .backgroundColor('#F5F5F5')
        .borderRadius(8)
        .margin({ right: 6 })
        .onClick(() => {
          postCardAction(this, {
            action: 'router',
            abilityName: 'EntryAbility',
            params: {
              target: 'latest'
            }
          });
        })
        
        // 猜你想看
        Column() {
          Text('猜你想看')
            .fontSize(10)
            .fontColor('#FF9800')
            .margin({ bottom: 4 })
          
          Text(this.recommendTitle)
            .fontSize(12)
            .fontColor('#333333')
            .maxLines(2)
            .textOverflow({ overflow: TextOverflow.Ellipsis })
            .width('100%')
          
          if (this.recommendSource) {
            Text(this.recommendSource)
              .fontSize(10)
              .fontColor('#999999')
              .margin({ top: 2 })
              .maxLines(1)
              .textOverflow({ overflow: TextOverflow.Ellipsis })
          }
        }
        .layoutWeight(1)
        .alignItems(HorizontalAlign.Start)
        .padding(8)
        .backgroundColor('#FFF8E1')
        .borderRadius(8)
        .margin({ left: 6 })
        .onClick(() => {
          postCardAction(this, {
            action: 'router',
            abilityName: 'EntryAbility',
            params: {
              target: 'recommend'
            }
          });
        })
      }
      .width('100%')
      .padding({ left: 12, right: 12, bottom: 8 })
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#FFFFFF')
    .borderRadius(16)
  }
}