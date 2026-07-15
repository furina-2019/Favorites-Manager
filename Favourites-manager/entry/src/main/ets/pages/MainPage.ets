import { themeService } from '../service/ThemeService';
import { authService, UserInfo } from '../service/AuthService';
import { HomePage } from './HomePage';
import { MinePage } from './MinePage';

/**
 * 主页面 - 包含底部导航栏
 */
@Entry
@Component
struct MainPage {
  @State currentIndex: number = 0;
  @State primaryColor: string = '#4CAF50';
  private tabsController: TabsController = new TabsController();

  aboutToAppear(): void {
    this.primaryColor = themeService.getPrimaryColor();
  }

  @Builder
  TabBuilder(title: string, targetIndex: number, normalIcon: ResourceStr, selectedIcon: ResourceStr) {
    Column() {
      Image(this.currentIndex === targetIndex ? selectedIcon : normalIcon)
        .width(24)
        .height(24)
        .objectFit(ImageFit.Contain)
      
      Text(title)
        .fontSize(12)
        .fontColor(this.currentIndex === targetIndex ? this.primaryColor : '#999999')
        .margin({ top: 4 })
    }
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
    .onClick(() => {
      this.currentIndex = targetIndex;
      this.tabsController.changeIndex(targetIndex);
    })
  }

  build() {
    Tabs({ barPosition: BarPosition.End, controller: this.tabsController }) {
      TabContent() {
        HomePage()
      }
      .tabBar(this.TabBuilder('首页', 0, $r('app.media.ic_home'), $r('app.media.ic_home_filled')))

      TabContent() {
        MinePage()
      }
      .tabBar(this.TabBuilder('我的', 1, $r('app.media.ic_mine'), $r('app.media.ic_mine_filled')))
    }
    .width('100%')
    .height('100%')
    .barHeight(56)
    .scrollable(false)
    .animationDuration(200)
    .barBackgroundColor('#FFFFFF')
    .onChange((index: number) => {
      this.currentIndex = index;
    })
  }
}