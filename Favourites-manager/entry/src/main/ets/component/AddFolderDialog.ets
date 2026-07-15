import { themeService } from '../service/ThemeService';

/**
 * 添加文件夹弹窗组件
 */
@Component
export struct AddFolderDialog {
  @State folderName: string = '';
  @State primaryColor: string = '#4CAF50';
  onConfirm: (name: string) => void = () => {};
  onCancel: () => void = () => {};

  aboutToAppear(): void {
    this.primaryColor = themeService.getPrimaryColor();
  }

  build() {
    Column() {
      // 遮罩层
      Column() {
        // 弹窗内容
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
                this.onCancel();
              })
            
            Button('确定')
              .width('45%')
              .height(44)
              .fontSize(16)
              .fontColor('#FFFFFF')
              .backgroundColor(this.folderName.length > 0 ? this.primaryColor : '#CCCCCC')
              .borderRadius(22)
              .enabled(this.folderName.length > 0)
              .onClick(() => {
                if (this.folderName.trim()) {
                  this.onConfirm(this.folderName.trim());
                }
              })
          }
          .width('100%')
          .justifyContent(FlexAlign.SpaceBetween)
          .margin({ top: 24 })
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
        this.onCancel();
      })
    }
    .width('100%')
    .height('100%')
  }
}