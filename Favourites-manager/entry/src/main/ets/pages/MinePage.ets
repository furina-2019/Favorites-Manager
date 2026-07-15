import { router } from '@kit.ArkUI';
import { loginComponentManager, LoginWithHuaweiIDButton } from '@kit.AccountKit';
import { BusinessError } from '@kit.BasicServicesKit';
import { themeService, ThemeEventType } from '../service/ThemeService';
import { authService, AuthEventType, UserInfo } from '../service/AuthService';
import { emitter } from '@kit.BasicServicesKit';

/**
 * 我的页面 - 包含华为账号登录和主题设置
 */
@Component
export struct MinePage {
  @State primaryColor: string = '#4CAF50';
  @State currentThemeColor: string = '#4CAF50';
  @State isLoggedIn: boolean = false;
  @State currentUser: UserInfo | null = null;
  @State showColorPicker: boolean = false;
  
  // 华为账号登录控制器
  private loginController: loginComponentManager.LoginWithHuaweiIDButtonController = 
    new loginComponentManager.LoginWithHuaweiIDButtonController()
      .onClickLoginWithHuaweiIDButton((error: BusinessError, response: loginComponentManager.HuaweiIDCredential) => {
        if (error) {
          console.error('华为账号登录失败:', error.code, error.message);
          return;
        }
        if (response) {
          console.log('华为账号登录成功，Authorization Code:', response.authorizationCode);
          // 这里可以处理登录成功后的业务逻辑，比如获取用户信息
          this.handleLoginSuccess();
        }
      });

  aboutToAppear(): void {
    this.primaryColor = themeService.getPrimaryColor();
    this.currentThemeColor = themeService.getPrimaryColor();
    this.isLoggedIn = authService.isLoggedIn();
    this.currentUser = authService.getCurrentUser();
    
    // 订阅主题变更事件
    let themeEvent: emitter.InnerEvent = { eventId: ThemeEventType.THEME_CHANGED };
    emitter.on(themeEvent, () => {
      this.primaryColor = themeService.getPrimaryColor();
      this.currentThemeColor = themeService.getPrimaryColor();
    });
    
    // 订阅登录状态变更事件
    let loginEvent: emitter.InnerEvent = { eventId: AuthEventType.LOGIN_SUCCESS };
    emitter.on(loginEvent, () => {
      this.isLoggedIn = true;
      this.currentUser = authService.getCurrentUser();
    });
    
    let logoutEvent: emitter.InnerEvent = { eventId: AuthEventType.LOGOUT_SUCCESS };
    emitter.on(logoutEvent, () => {
      this.isLoggedIn = false;
      this.currentUser = null;
    });
  }

  aboutToDisappear(): void {
    emitter.off(ThemeEventType.THEME_CHANGED);
    emitter.off(AuthEventType.LOGIN_SUCCESS);
    emitter.off(AuthEventType.LOGOUT_SUCCESS);
  }

  // 处理登录成功
  private async handleLoginSuccess(): Promise<void> {
    const userInfo = await authService.loginWithHuaweiID();
    if (userInfo) {
      this.isLoggedIn = true;
      this.currentUser = userInfo;
      console.log('用户登录成功:', userInfo.displayName);
    }
  }

  // 处理登出
  private async handleLogout(): Promise<void> {
    try {
      await authService.logout();
      this.isLoggedIn = false;
      this.currentUser = null;
      console.log('用户已登出');
    } catch (error) {
      console.error('登出失败:', error);
    }
  }

  // 跳转到主题设置页面
  private navigateToThemeSettings(): void {
    router.pushUrl({
      url: 'pages/Settings',
      params: {}
    });
  }

  // 使用预设主题
  private async usePresetTheme(themeName: string): Promise<void> {
    await themeService.usePresetTheme(themeName);
    this.currentThemeColor = themeService.getPrimaryColor();
  }

  // 自定义主题色
  private async applyCustomColor(): Promise<void> {
    await themeService.setPrimaryColor(this.currentThemeColor);
  }

  @Builder
  UserInfoCard() {
    Column() {
      // 用户头像
      if (this.currentUser?.avatarUri) {
        Image(this.currentUser.avatarUri)
          .width(80)
          .height(80)
          .borderRadius(40)
          .objectFit(ImageFit.Cover)
          .margin({ bottom: 12 })
      } else {
        Circle()
          .width(80)
          .height(80)
          .fill(this.primaryColor)
          .margin({ bottom: 12 })
      }
      
      // 用户信息
      Text(this.currentUser?.displayName || '未登录')
        .fontSize(20)
        .fontWeight(FontWeight.Bold)
        .fontColor('#333333')
        .margin({ bottom: 4 })
      
      if (this.currentUser?.email) {
        Text(this.currentUser.email)
          .fontSize(14)
          .fontColor('#666666')
          .margin({ bottom: 8 })
      }
      
      if (this.currentUser?.phoneNumber) {
        Text(this.currentUser.phoneNumber)
          .fontSize(14)
          .fontColor('#666666')
          .margin({ bottom: 8 })
      }
      
      // 华为账号ID
      if (this.currentUser?.openID) {
        Text(`华为账号: ${this.currentUser.openID.substring(0, 8)}...`)
          .fontSize(12)
          .fontColor('#999999')
      }
    }
    .width('100%')
    .padding(24)
    .backgroundColor('#FFFFFF')
    .borderRadius(16)
    .shadow({
      radius: 8,
      color: '#1A000000',
      offsetX: 0,
      offsetY: 2
    })
    .margin({ bottom: 20 })
  }

  @Builder
  ThemePreviewCard() {
    Column() {
      Row() {
        Text('当前主题色')
          .fontSize(16)
          .fontWeight(FontWeight.Medium)
          .fontColor('#333333')
          .layoutWeight(1)
        
        Circle()
          .width(32)
          .height(32)
          .fill(this.currentThemeColor)
          .border({ width: 2, color: '#E0E0E0' })
      }
      .width('100%')
      .padding({ bottom: 16 })
      
      // 预设主题
      Grid() {
        // 绿色主题
        GridItem() {
          Column() {
            Circle()
              .width(40)
              .height(40)
              .fill('#4CAF50')
              .border({ width: 2, color: this.currentThemeColor === '#4CAF50' ? '#4CAF50' : '#E0E0E0' })
              .onClick(() => {
                this.usePresetTheme('green');
              })
            
            Text('绿色')
              .fontSize(12)
              .fontColor('#666666')
              .margin({ top: 8 })
          }
          .width('100%')
          .alignItems(HorizontalAlign.Center)
        }
        
        // 蓝色主题
        GridItem() {
          Column() {
            Circle()
              .width(40)
              .height(40)
              .fill('#2196F3')
              .border({ width: 2, color: this.currentThemeColor === '#2196F3' ? '#2196F3' : '#E0E0E0' })
              .onClick(() => {
                this.usePresetTheme('blue');
              })
            
            Text('蓝色')
              .fontSize(12)
              .fontColor('#666666')
              .margin({ top: 8 })
          }
          .width('100%')
          .alignItems(HorizontalAlign.Center)
        }
        
        // 紫色主题
        GridItem() {
          Column() {
            Circle()
              .width(40)
              .height(40)
              .fill('#9C27B0')
              .border({ width: 2, color: this.currentThemeColor === '#9C27B0' ? '#9C27B0' : '#E0E0E0' })
              .onClick(() => {
                this.usePresetTheme('purple');
              })
            
            Text('紫色')
              .fontSize(12)
              .fontColor('#666666')
              .margin({ top: 8 })
          }
          .width('100%')
          .alignItems(HorizontalAlign.Center)
        }
        
        // 橙色主题
        GridItem() {
          Column() {
            Circle()
              .width(40)
              .height(40)
              .fill('#FF9800')
              .border({ width: 2, color: this.currentThemeColor === '#FF9800' ? '#FF9800' : '#E0E0E0' })
              .onClick(() => {
                this.usePresetTheme('orange');
              })
            
            Text('橙色')
              .fontSize(12)
              .fontColor('#666666')
              .margin({ top: 8 })
          }
          .width('100%')
          .alignItems(HorizontalAlign.Center)
        }
        
        // 粉色主题
        GridItem() {
          Column() {
            Circle()
              .width(40)
              .height(40)
              .fill('#E91E63')
              .border({ width: 2, color: this.currentThemeColor === '#E91E63' ? '#E91E63' : '#E0E0E0' })
              .onClick(() => {
                this.usePresetTheme('pink');
              })
            
            Text('粉色')
              .fontSize(12)
              .fontColor('#666666')
              .margin({ top: 8 })
          }
          .width('100%')
          .alignItems(HorizontalAlign.Center)
        }
        
        // 青色主题
        GridItem() {
          Column() {
            Circle()
              .width(40)
              .height(40)
              .fill('#00BCD4')
              .border({ width: 2, color: this.currentThemeColor === '#00BCD4' ? '#00BCD4' : '#E0E0E0' })
              .onClick(() => {
                this.usePresetTheme('cyan');
              })
            
            Text('青色')
              .fontSize(12)
              .fontColor('#666666')
              .margin({ top: 8 })
          }
          .width('100%')
          .alignItems(HorizontalAlign.Center)
        }
      }
      .columnsTemplate('1fr 1fr 1fr')
      .rowsGap(12)
      .columnsGap(12)
      .width('100%')
      .margin({ bottom: 16 })
      
      // 自定义主题按钮
      Button('自定义主题色')
        .width('100%')
        .height(44)
        .fontSize(16)
        .fontWeight(FontWeight.Medium)
        .fontColor('#FFFFFF')
        .backgroundColor(this.primaryColor)
        .borderRadius(22)
        .onClick(() => {
          this.showColorPicker = true;
        })
        .margin({ bottom: 8 })
      
      // 应用主题按钮
      Button('应用主题')
        .width('100%')
        .height(44)
        .fontSize(16)
        .fontWeight(FontWeight.Medium)
        .fontColor('#FFFFFF')
        .backgroundColor(this.currentThemeColor)
        .borderRadius(22)
        .onClick(() => {
          this.applyCustomColor();
        })
    }
    .width('100%')
    .padding(20)
    .backgroundColor('#FFFFFF')
    .borderRadius(16)
    .shadow({
      radius: 8,
      color: '#1A000000',
      offsetX: 0,
      offsetY: 2
    })
    .margin({ bottom: 20 })
  }

  @Builder
  MenuItem(icon: string, title: string, onClick: () => void) {
    Row() {
      Text(icon)
        .fontSize(20)
        .margin({ right: 16 })
      
      Text(title)
        .fontSize(16)
        .fontColor('#333333')
        .layoutWeight(1)
      
      Text('›')
        .fontSize(20)
        .fontColor('#999999')
    }
    .width('100%')
    .height(56)
    .padding({ left: 20, right: 16 })
    .backgroundColor('#FFFFFF')
    .onClick(onClick)
  }

  build() {
    Column() {
      // 标题栏
      Row() {
        Text('我的')
          .fontSize(28)
          .fontWeight(FontWeight.Bold)
          .fontColor('#333333')
          .margin({ left: 20 })
      }
      .width('100%')
      .height(56)
      .backgroundColor('#FFFFFF')
      .justifyContent(FlexAlign.Start)
      .alignItems(VerticalAlign.Center)
      
      Scroll() {
        Column() {
          // 用户信息区域
          Column() {
            if (this.isLoggedIn && this.currentUser) {
              this.UserInfoCard()
            } else {
              // 未登录时显示登录按钮
              Column() {
                Text('登录华为账号')
                  .fontSize(18)
                  .fontWeight(FontWeight.Bold)
                  .fontColor('#333333')
                  .margin({ bottom: 16 })
                
                Text('登录后可同步收藏到云端')
                  .fontSize(14)
                  .fontColor('#666666')
                  .margin({ bottom: 24 })
                
                // 华为账号登录按钮
                LoginWithHuaweiIDButton({
                  params: {
                    style: loginComponentManager.Style.BUTTON_RED,
                    borderRadius: 24,
                    loginType: loginComponentManager.LoginType.ID,
                    supportDarkMode: true
                  },
                  controller: this.loginController
                })
                .width('100%')
                .height(48)
              }
              .width('100%')
              .padding(24)
              .backgroundColor('#FFFFFF')
              .borderRadius(16)
              .shadow({
                radius: 8,
                color: '#1A000000',
                offsetX: 0,
                offsetY: 2
              })
              .margin({ bottom: 20 })
            }
          }
          .padding({ left: 20, right: 20 })
          
          // 主题设置
          Column() {
            Text('主题设置')
              .fontSize(18)
              .fontWeight(FontWeight.Bold)
              .fontColor('#333333')
              .margin({ left: 20, bottom: 16 })
              .width('100%')
              .textAlign(TextAlign.Start)
            
            this.ThemePreviewCard()
          }
          .width('100%')
          .margin({ bottom: 20 })
          
          // 功能菜单
          Column() {
            Text('功能')
              .fontSize(18)
              .fontWeight(FontWeight.Bold)
              .fontColor('#333333')
              .margin({ left: 20, bottom: 16 })
              .width('100%')
              .textAlign(TextAlign.Start)
            
            // 主题设置菜单项
            this.MenuItem('🎨', '主题设置', () => {
              this.navigateToThemeSettings();
            })
            
            Divider()
              .strokeWidth(1)
              .color('#F0F0F0')
              .width('100%')
            
            // 关于菜单项
            this.MenuItem('ℹ️', '关于', () => {
              // TODO: 跳转到关于页面
              console.log('关于');
            })
            
            Divider()
              .strokeWidth(1)
              .color('#F0F0F0')
              .width('100%')
            
            // 退出登录菜单项（仅登录时显示）
            if (this.isLoggedIn) {
              this.MenuItem('🚪', '退出登录', () => {
                this.handleLogout();
              })
            }
          }
          .width('100%')
          .padding({ bottom: 40 })
        }
        .width('100%')
      }
      .width('100%')
      .layoutWeight(1)
      .scrollBar(BarState.Off)
      .backgroundColor('#F5F5F5')
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
  }
}