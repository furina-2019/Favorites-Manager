import { router } from '@kit.ArkUI';
import { themeService } from '../service/ThemeService';

/**
 * 添加菜单组件 - 合并添加收藏夹和收藏链接功能
 */
@Component
export struct AddMenu {
  @State showMenu: boolean = false;
  @State showAddFolderDialog: boolean = false;
  @State folderName: string = '';
  @State primaryColor: string = '#4CAF50';
  onAddFolder: (name: string) => void = () => {};
  onNavigateToCreateFavorite: () => void = () => {};
  
  aboutToAppear(): void {
    this.primaryColor = themeService.getPrimaryColor();
  }
  
  // 重置对话框状态
  private resetDialog(): void {
    this.folderName = '';
    this.showAddFolderDialog = false;
  }
  
  build() {
    Stack() {
      // 浮动按钮
      Button('+')
        .width(56)
        .height(56)
        .fontSize(32)
        .fontColor('#FFFFFF')
        .backgroundColor(this.primaryColor)
        .borderRadius(28)
        .shadow({ radius: 8, color: '#33000000', offsetX: 0, offsetY: 4 })
        .position({ x: '100%', y: '100%' })
        .translate({ x: -72, y: -88 })
        .onClick(() => {
          this.showMenu = !this.showMenu;
        })
      
      // 菜单弹窗
      if (this.showMenu) {
        Column() {
          Column() {
            // 菜单项1: 添加收藏链接
            Row() {
              Text('🔗')
                .fontSize(20)
                .margin({ right: 12 })
              
              Text('添加收藏链接')
                .fontSize(16)
                .fontColor('#333333')
                .layoutWeight(1)
            }
            .width('100%')
            .height(56)
            .padding({ left: 20, right: 20 })
            .backgroundColor('#FFFFFF')
            .onClick(() => {
              this.showMenu = false;
              this.onNavigateToCreateFavorite();
            })
            
            // 分隔线
            Divider()
              .strokeWidth(1)
              .color('#F0F0F0')
              .width('100%')
            
            // 菜单项2: 添加收藏夹
            Row() {
              Text('📁')
                .fontSize(20)
                .margin({ right: 12 })
              
              Text('添加收藏夹')
                .fontSize(16)
                .fontColor('#333333')
                .layoutWeight(1)
            }
            .width('100%')
            .height(56)
            .padding({ left: 20, right: 20 })
            .backgroundColor('#FFFFFF')
            .onClick(() => {
              this.showMenu = false;
              this.showAddFolderDialog = true;
            })
            
            // 分隔线
            Divider()
              .strokeWidth(1)
              .color('#F0F0F0')
              .width('100%')
            

          }
          .width(200)
          .backgroundColor('#FFFFFF')
          .borderRadius(16)
          .shadow({ radius: 16, color: '#33000000', offsetX: 0, offsetY: 4 })
          .position({ x: '100%', y: '100%' })
          .translate({ x: -280, y: -200 })
        }
        .width('100%')
        .height('100%')
        .onClick(() => {
          this.showMenu = false;
        })
      }
      
      // 添加文件夹弹窗
      if (this.showAddFolderDialog) {
        Column() {
          Column() {
            Text('新建收藏夹')
              .fontSize(20)
              .fontWeight(FontWeight.Bold)
              .fontColor('#333333')
              .margin({ bottom: 20 })
            
            TextInput({ placeholder: '请输入文件夹名称', text: this.folderName })
              .width('100%')
              .height(48)
              .fontSize(16)
              .backgroundColor('#F5F5F5')
              .borderRadius(8)
              .padding({ left: 16, right: 16 })
              .onChange((value: string) => {
                this.folderName = value;
              })
            
            Row() {
              Button('取消')
                .width('45%')
                .height(44)
                .fontSize(16)
                .fontColor('#666666')
                .backgroundColor('#F0F0F0')
                .borderRadius(22)
                .onClick(() => {
                  this.resetDialog();
                })
              
              Button('确定')
                .width('45%')
                .height(44)
                .fontSize(16)
                .fontColor('#FFFFFF')
                .backgroundColor(this.folderName.length > 0 ? this.primaryColor : '#CCCCCC')
                .borderRadius(22)
                .onClick(() => {
                  if (this.folderName.length > 0) {
                    this.onAddFolder(this.folderName);
                    this.resetDialog();
                  }
                })
            }
            .width('100%')
            .justifyContent(FlexAlign.SpaceBetween)
            .margin({ top: 24 })
          }
          .width('80%')
          .padding(24)
          .backgroundColor('#FFFFFF')
          .borderRadius(16)
          .shadow({ radius: 16, color: '#33000000', offsetX: 0, offsetY: 4 })
        }
        .width('100%')
        .height('100%')
        .justifyContent(FlexAlign.Center)
        .alignItems(HorizontalAlign.Center)
        .backgroundColor('#80000000')
        .onClick(() => {
          this.resetDialog();
        })
      }
    }
    .width('100%')
    .height('100%')
    .hitTestBehavior(this.showMenu || this.showAddFolderDialog ? HitTestMode.Default : HitTestMode.Transparent)
  }
}