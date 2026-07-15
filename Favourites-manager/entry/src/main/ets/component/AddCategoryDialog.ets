import { Category } from '../model/FavoriteItem';

/**
 * 添加分类对话框组件
 */
@Component
export struct AddCategoryDialog {
  @State categoryName: string = '';
  @State keywords: string = '';
  @State color: string = '#4CAF50';
  @State icon: string = '📝';
  @State showError: boolean = false;
  @State errorMessage: string = '';

  onConfirm: (category: Category) => void = () => {};
  onCancel: () => void = () => {};

  // 预定义颜色选项
  private colorOptions: string[] = [
    '#4CAF50', // 绿色
    '#2196F3', // 蓝色
    '#FF9800', // 橙色
    '#9C27B0', // 紫色
    '#E91E63', // 粉色
    '#00BCD4', // 青色
    '#795548', // 棕色
    '#607D8B', // 灰色
  ];

  // 预定义图标选项
  private iconOptions: string[] = [
    '📝', '📚', '🎨', '🎮', '🎵', '🎬', '🍔', '✈️',
    '💼', '🏠', '💪', '💰', '💻', '📱', '🎯', '❤️'
  ];

  /**
   * 验证表单
   */
  private validateForm(): boolean {
    if (!this.categoryName.trim()) {
      this.showError = true;
      this.errorMessage = '请输入分类名称';
      return false;
    }

    if (this.categoryName.trim().length > 20) {
      this.showError = true;
      this.errorMessage = '分类名称不能超过20个字符';
      return false;
    }

    this.showError = false;
    this.errorMessage = '';
    return true;
  }

  /**
   * 处理确认
   */
  private handleConfirm(): void {
    if (!this.validateForm()) {
      return;
    }

    const keywordsArray = this.keywords
      .split(/[,，\s]+/)
      .map(k => k.trim())
      .filter(k => k.length > 0);

    const newCategory: Category = {
      id: `custom_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name: this.categoryName.trim(),
      keywords: keywordsArray,
      icon: this.icon,
      color: this.color
    };

    this.onConfirm(newCategory);
    this.resetForm();
  }

  /**
   * 重置表单
   */
  private resetForm(): void {
    this.categoryName = '';
    this.keywords = '';
    this.color = '#4CAF50';
    this.icon = '📝';
    this.showError = false;
    this.errorMessage = '';
  }

  /**
   * 处理取消
   */
  private handleCancel(): void {
    this.resetForm();
    this.onCancel();
  }

  @Builder
  ColorPicker() {
    Column() {
      Text('选择颜色')
        .fontSize(14)
        .fontColor('#666666')
        .margin({ bottom: 8 })
        .width('100%')
        .textAlign(TextAlign.Start)

      Grid() {
        ForEach(this.colorOptions, (color: string, index: number) => {
          GridItem() {
            Column() {
              if (this.color === color) {
                Text('✓')
                  .fontSize(16)
                  .fontColor('#FFFFFF')
              }
            }
            .width(32)
            .height(32)
            .backgroundColor(color)
            .borderRadius(16)
            .justifyContent(FlexAlign.Center)
            .onClick(() => {
              this.color = color;
            })
          }
        })
      }
      .columnsTemplate('1fr 1fr 1fr 1fr')
      .rowsGap(8)
      .columnsGap(8)
      .width('100%')
    }
    .width('100%')
    .margin({ bottom: 16 })
  }

  @Builder
  IconPicker() {
    Column() {
      Text('选择图标')
        .fontSize(14)
        .fontColor('#666666')
        .margin({ bottom: 8 })
        .width('100%')
        .textAlign(TextAlign.Start)

      Grid() {
        ForEach(this.iconOptions, (icon: string, index: number) => {
          GridItem() {
            Column() {
              Text(icon)
                .fontSize(20)
                .fontColor(this.icon === icon ? '#FFFFFF' : '#333333')
            }
            .width(40)
            .height(40)
            .backgroundColor(this.icon === icon ? this.color : '#F0F0F0')
            .borderRadius(16)
            .justifyContent(FlexAlign.Center)
            .onClick(() => {
              this.icon = icon;
            })
          }
        })
      }
      .columnsTemplate('1fr 1fr 1fr 1fr')
      .rowsGap(8)
      .columnsGap(8)
      .width('100%')
    }
    .width('100%')
    .margin({ bottom: 16 })
  }

  build() {
    Column() {
      // 标题
      Text('新建分类')
        .fontSize(20)
        .fontWeight(FontWeight.Bold)
        .fontColor('#333333')
        .margin({ bottom: 24 })

      // 分类名称
      Column() {
        Text('分类名称')
          .fontSize(14)
          .fontColor('#666666')
          .margin({ bottom: 8 })
          .width('100%')
          .textAlign(TextAlign.Start)

        TextInput({ placeholder: '请输入分类名称（如：工作、学习）', text: this.categoryName })
          .width('100%')
          .height(44)
          .fontSize(16)
          .backgroundColor('#F5F5F5')
          .borderRadius(8)
          .padding({ left: 12, right: 12 })
          .onChange((value: string) => {
            this.categoryName = value;
            if (this.showError) {
              this.showError = false;
            }
          })
      }
      .width('100%')
      .margin({ bottom: 16 })

      // 关键词
      Column() {
        Text('关键词（可选）')
          .fontSize(14)
          .fontColor('#666666')
          .margin({ bottom: 8 })
          .width('100%')
          .textAlign(TextAlign.Start)

        TextInput({ 
          placeholder: '用逗号分隔关键词，如：工作,会议,项目', 
          text: this.keywords 
        })
          .width('100%')
          .height(44)
          .fontSize(16)
          .backgroundColor('#F5F5F5')
          .borderRadius(8)
          .padding({ left: 12, right: 12 })
          .onChange((value: string) => {
            this.keywords = value;
          })
      }
      .width('100%')
      .margin({ bottom: 16 })

      // 颜色选择器
      this.ColorPicker()

      // 图标选择器
      this.IconPicker()

      // 错误提示
      if (this.showError) {
        Text(this.errorMessage)
          .fontSize(14)
          .fontColor('#FF5252')
          .margin({ bottom: 16 })
          .width('100%')
          .textAlign(TextAlign.Start)
      }

      // 按钮区域
      Row() {
        Button('取消')
          .width('45%')
          .height(44)
          .fontSize(16)
          .fontColor('#666666')
          .backgroundColor('#F0F0F0')
          .borderRadius(22)
          .onClick(() => {
            this.handleCancel();
          })

        Button('确定')
          .width('45%')
          .height(44)
          .fontSize(16)
          .fontColor('#FFFFFF')
          .backgroundColor('#4CAF50')
          .borderRadius(22)
          .onClick(() => {
            this.handleConfirm();
          })
      }
      .width('100%')
      .justifyContent(FlexAlign.SpaceBetween)
      .margin({ top: 8 })
    }
    .width('85%')
    .padding(24)
    .backgroundColor('#FFFFFF')
    .borderRadius(16)
    .shadow({
      radius: 16,
      color: '#40000000',
      offsetX: 0,
      offsetY: 4
    })
  }
}