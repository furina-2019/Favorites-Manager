import { Colors } from '@kit.ArkUI';

interface RGB {
  r: number;
  g: number;
  b: number;
}

interface HSL {
  h: number;
  s: number;
  l: number;
}

/**
 * 色环选择器组件
 */
@Component
export struct ColorPickerComponent {
  @State selectedColor: string = '#4CAF50';
  @Link color: string;
  
  // 预设颜色数组
  private presetColors: string[] = [
    '#FF5252', '#FF4081', '#E040FB', '#7C4DFF', '#536DFE',
    '#448AFF', '#40C4FF', '#18FFFF', '#64FFDA', '#69F0AE',
    '#B2FF59', '#EEFF41', '#FFFF00', '#FFD740', '#FFAB40',
    '#FF6E40', '#FF3D00', '#795548', '#9E9E9E', '#607D8B',
    '#4CAF50', '#2196F3', '#9C27B0', '#FF9800', '#E91E63'
  ];
  
  // 色环角度计算
  private colorsPerRing: number = 12;
  private ringRadius: number = 120;
  private colorRadius: number = 20;
  
  // HSL颜色值
  @State private hue: number = 120; // 色相 0-360
  @State private saturation: number = 50; // 饱和度 0-100
  @State private light: number = 50; // 亮度 0-100 (重命名brightness为light)
  
  aboutToAppear(): void {
    // 初始化颜色值
    this.updateColorFromHex(this.selectedColor);
  }
  
  // 从十六进制颜色更新HSL值
  private updateColorFromHex(hexColor: string): void {
    const rgb = this.hexToRgb(hexColor);
    if (rgb) {
      const hsl = this.rgbToHsl(rgb.r, rgb.g, rgb.b);
      this.hue = hsl.h;
      this.saturation = hsl.s;
      this.light = hsl.l;
    }
  }
  
  // 从HSL值更新颜色
  private updateColorFromHsl(): void {
    const rgb = this.hslToRgb(this.hue, this.saturation, this.light);
    this.selectedColor = this.rgbToHex(rgb.r, rgb.g, rgb.b);
    this.color = this.selectedColor;
  }
  
  // 十六进制转RGB
  private hexToRgb(hex: string): RGB | null {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null;
  }
  
  // RGB转十六进制
  private rgbToHex(r: number, g: number, b: number): string {
    return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
  }
  
  // RGB转HSL
  private rgbToHsl(r: number, g: number, b: number): HSL {
    r /= 255;
    g /= 255;
    b /= 255;
    
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let h = 0, s = 0, l = (max + min) / 2;
    
    if (max !== min) {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      
      switch (max) {
        case r: h = (g - b) / d + (g < b ? 6 : 0); break;
        case g: h = (b - r) / d + 2; break;
        case b: h = (r - g) / d + 4; break;
      }
      h /= 6;
    }
    
    return {
      h: Math.round(h * 360),
      s: Math.round(s * 100),
      l: Math.round(l * 100)
    };
  }
  
  // HSL转RGB
  private hslToRgb(h: number, s: number, l: number): RGB {
    h /= 360;
    s /= 100;
    l /= 100;
    
    let r: number, g: number, b: number;
    
    if (s === 0) {
      r = g = b = l;
    } else {
      const hue2rgb = (p: number, q: number, t: number): number => {
        if (t < 0) t += 1;
        if (t > 1) t -= 1;
        if (t < 1/6) return p + (q - p) * 6 * t;
        if (t < 1/2) return q;
        if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
        return p;
      };
      
      const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
      const p = 2 * l - q;
      
      r = hue2rgb(p, q, h + 1/3);
      g = hue2rgb(p, q, h);
      b = hue2rgb(p, q, h - 1/3);
    }
    
    return {
      r: Math.round(r * 255),
      g: Math.round(g * 255),
      b: Math.round(b * 255)
    };
  }
  
  @Builder
  ColorRing() {
    Column() {
      // 中心颜色预览
      Circle()
        .width(80)
        .height(80)
        .fill(this.selectedColor)
        .stroke('#FFFFFF')
        .strokeWidth(2)
        .shadow({ radius: 8, color: '#33000000', offsetX: 0, offsetY: 4 })
      
      // 色环 - 使用简单的布局而不是复杂的数学计算
      Stack() {
        // 第一圈颜色
        ForEach(this.presetColors.slice(0, 12), (color: string, index: number) => {
          Circle()
            .width(this.colorRadius * 2)
            .height(this.colorRadius * 2)
            .fill(color)
            .stroke('#FFFFFF')
            .strokeWidth(2)
            .shadow({ radius: 2, color: '#33000000', offsetX: 0, offsetY: 2 })
            .position({ 
              x: (index % 3) * 80 + 20, 
              y: Math.floor(index / 3) * 80 + 20 
            })
            .onClick(() => {
              this.selectedColor = color;
              this.color = color;
              this.updateColorFromHex(color);
            })
        })
        
        // 第二圈颜色
        ForEach(this.presetColors.slice(12), (color: string, index: number) => {
          Circle()
            .width(this.colorRadius * 2)
            .height(this.colorRadius * 2)
            .fill(color)
            .stroke('#FFFFFF')
            .strokeWidth(2)
            .shadow({ radius: 2, color: '#33000000', offsetX: 0, offsetY: 2 })
            .position({ 
              x: (index % 3) * 80 + 60, 
              y: Math.floor(index / 3) * 80 + 60 
            })
            .onClick(() => {
              this.selectedColor = color;
              this.color = color;
              this.updateColorFromHex(color);
            })
        })
      }
      .width(280)
      .height(280)
    }
    .width('100%')
    .alignItems(HorizontalAlign.Center)
    .padding(32)
  }
  
  @Builder
  ColorSlider() {
    Column() {
      Text('颜色选择器')
        .fontSize(16)
        .fontWeight(FontWeight.Medium)
        .fontColor('#333333')
        .margin({ bottom: 16 })
        .width('100%')
        .textAlign(TextAlign.Start)
      
      // 色相滑块
      Row() {
        Text('H')
          .fontSize(14)
          .fontColor('#666666')
          .width(24)
        
        Slider({
          value: this.hue,
          min: 0,
          max: 360,
          step: 1,
          style: SliderStyle.OutSet
        })
          .width('100%')
          .height(32)
          .trackColor('#E0E0E0')
          .selectedColor('#4CAF50')
          .onChange((value: number) => {
            this.hue = value;
            this.updateColorFromHsl();
          })
      }
      .width('100%')
      .margin({ bottom: 12 })
      
      // 饱和度滑块
      Row() {
        Text('S')
          .fontSize(14)
          .fontColor('#666666')
          .width(24)
        
        Slider({
          value: this.saturation,
          min: 0,
          max: 100,
          step: 1,
          style: SliderStyle.OutSet
        })
          .width('100%')
          .height(32)
          .trackColor('#E0E0E0')
          .selectedColor('#4CAF50')
          .onChange((value: number) => {
            this.saturation = value;
            this.updateColorFromHsl();
          })
      }
      .width('100%')
      .margin({ bottom: 12 })
      
      // 亮度滑块
      Row() {
        Text('B')
          .fontSize(14)
          .fontColor('#666666')
          .width(24)
        
        Slider({
          value: this.light,
          min: 0,
          max: 100,
          step: 1,
          style: SliderStyle.OutSet
        })
          .width('100%')
          .height(32)
          .trackColor('#E0E0E0')
          .selectedColor('#4CAF50')
          .onChange((value: number) => {
            this.light = value;
            this.updateColorFromHsl();
          })
      }
      .width('100%')
    }
    .width('100%')
    .padding({ left: 24, right: 24, bottom: 24 })
  }
  
  build() {
    Column() {
      this.ColorRing()
      this.ColorSlider()
    }
    .width('100%')
  }
}