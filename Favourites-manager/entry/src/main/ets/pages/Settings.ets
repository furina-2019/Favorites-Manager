import { router } from '@kit.ArkUI';
import { themeService } from '../service/ThemeService';
import { ColorPickerComponent } from '../component/ColorPicker';

/**
 * 设置页面
 */
@Entry
@Component
struct Settings {
  @State currentThemeColor: string = '#4CAF50';
  @State showColorPicker: boolean = false;
  
  async aboutToAppear(): Promise<void> {
    this.currentThemeColor = themeService.getPrimaryColor();
  }
  
  // 使用预设主题
  async usePresetTheme(themeName: string): Promise<void> {
    await themeService.usePresetTheme(themeName);
    this.currentThemeColor = themeService.getPrimaryColor();
  }
  
  // 自定义主题色
  async applyCustomColor(): Promise<void> {
    await themeService.setPrimaryColor(this.currentThemeColor);
  }
  
  build() {
    Stack() {
      Column() {
        // 标题栏
        Row() {
          Text('←')
            .fontSize(24)
            .fontColor('#333333')
            .margin({ left: 16 })
            .onClick(() => {
              router.back();
            })
          
          Text('主题设置')
            .fontSize(20)
            .fontWeight(FontWeight.Bold)
            .fontColor('#333333')
            .layoutWeight(1)
            .textAlign(TextAlign.Center)
            .margin({ right: 40 })
        }
        .width('100%')
        .height(56)
        .backgroundColor('#FFFFFF')
        .border({ width: 1, color: '#E0E0E0' })
        
        Scroll() {
          Column() {
            // 当前主题预览
            Column() {
              Text('当前主题色')
                .fontSize(16)
                .fontWeight(FontWeight.Medium)
                .fontColor('#333333')
                .margin({ bottom: 12 })
                .width('100%')
                .textAlign(TextAlign.Start)
              
              Row() {
                Circle()
                  .width(64)
                  .height(64)
                  .fill(this.currentThemeColor)
                  .border({ width: 2, color: '#E0E0E0' })
                  .shadow({ radius: 4, color: '#33000000', offsetX: 0, offsetY: 2 })
                  .margin({ right: 16 })
                
                Column() {
                  Text(this.currentThemeColor)
                    .fontSize(18)
                    .fontWeight(FontWeight.Bold)
                    .fontColor('#333333')
                    .margin({ bottom: 4 })
                  
                  Text('点击下方按钮自定义')
                    .fontSize(14)
                    .fontColor('#999999')
                }
                .layoutWeight(1)
              }
              .width('100%')
              .padding(16)
              .backgroundColor('#FFFFFF')
              .borderRadius(12)
            }
            .width('100%')
            .padding(20)
            
            // 预设主题
            Column() {
              Text('预设主题')
                .fontSize(16)
                .fontWeight(FontWeight.Medium)
                .fontColor('#333333')
                .margin({ bottom: 16 })
                .width('100%')
                .textAlign(TextAlign.Start)
              
              Grid() {
                GridItem() {
                  Column() {
                    Circle()
                      .width(48)
                      .height(48)
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
                  .padding(8)
                }
                
                GridItem() {
                  Column() {
                    Circle()
                      .width(48)
                      .height(48)
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
                  .padding(8)
                }
                
                GridItem() {
                  Column() {
                    Circle()
                      .width(48)
                      .height(48)
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
                  .padding(8)
                }
                
                GridItem() {
                  Column() {
                    Circle()
                      .width(48)
                      .height(48)
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
                  .padding(8)
                }
                
                GridItem() {
                  Column() {
                    Circle()
                      .width(48)
                      .height(48)
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
                  .padding(8)
                }
                
                GridItem() {
                  Column() {
                    Circle()
                      .width(48)
                      .height(48)
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
                  .padding(8)
                }
              }
              .columnsTemplate('1fr 1fr 1fr')
              .rowsGap(16)
              .columnsGap(16)
              .width('100%')
            }
            .width('100%')
            .padding({ left: 20, right: 20, bottom: 24 })
            
            // 自定义颜色按钮
            Button('自定义主题色')
              .width('90%')
              .height(48)
              .fontSize(16)
              .fontWeight(FontWeight.Medium)
              .fontColor('#FFFFFF')
              .backgroundColor('#4CAF50')
              .borderRadius(24)
              .onClick(() => {
                this.showColorPicker = true;
              })
              .margin({ bottom: 24 })
            
            // 应用按钮
            Button('应用主题')
              .width('90%')
              .height(48)
              .fontSize(16)
              .fontWeight(FontWeight.Medium)
              .fontColor('#FFFFFF')
              .backgroundColor(this.currentThemeColor)
              .borderRadius(24)
              .onClick(() => {
                this.applyCustomColor();
                router.back();
              })
          }
          .width('100%')
          .alignItems(HorizontalAlign.Center)
        }
        .width('100%')
        .layoutWeight(1)
        .scrollBar(BarState.Off)
        .backgroundColor('#F5F5F5')
      }
      .width('100%')
      .height('100%')
      .backgroundColor('#F5F5F5')
      
      // 色环选择器弹窗
      if (this.showColorPicker) {
        Column() {
          Column() {
            Row() {
              Text('选择主题色')
                .fontSize(18)
                .fontWeight(FontWeight.Bold)
                .fontColor('#333333')
                .layoutWeight(1)
              
              Text('×')
                .fontSize(24)
                .fontColor('#666666')
                .onClick(() => {
                  this.showColorPicker = false;
                })
            }
            .width('100%')
            .padding({ left: 24, right: 24, top: 20, bottom: 20 })
            .border({ width: 1, color: '#E0E0E0', style: BorderStyle.Solid })
            
            ColorPickerComponent({ color: $currentThemeColor })
          }
          .width('90%')
          .backgroundColor('#FFFFFF')
          .borderRadius(24)
          .shadow({ radius: 24, color: '#66000000', offsetX: 0, offsetY: 8 })
          
          // 操作按钮
          Row() {
            Button('取消')
              .width('48%')
              .height(48)
              .fontSize(16)
              .fontColor('#666666')
              .backgroundColor('#F0F0F0')
              .borderRadius(24)
              .onClick(() => {
                this.showColorPicker = false;
              })
            
            Button('确定')
              .width('48%')
              .height(48)
              .fontSize(16)
              .fontColor('#FFFFFF')
              .backgroundColor(this.currentThemeColor)
              .borderRadius(24)
              .onClick(() => {
                this.showColorPicker = false;
                this.applyCustomColor();
              })
          }
          .width('90%')
          .margin({ top: 16 })
        }
        .width('100%')
        .height('100%')
        .justifyContent(FlexAlign.Center)
        .alignItems(HorizontalAlign.Center)
        .backgroundColor('#80000000')
        .onClick(() => {
          this.showColorPicker = false;
        })
      }
    }
    .width('100%')
    .height('100%')
  }
}