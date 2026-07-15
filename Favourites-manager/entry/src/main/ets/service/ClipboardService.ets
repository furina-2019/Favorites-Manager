import pasteboard from '@ohos.pasteboard';
import { BusinessError } from '@kit.BasicServicesKit';

/**
 * 剪贴板服务
 */
export class ClipboardService {
  private static instance: ClipboardService;

  private constructor() {}

  static getInstance(): ClipboardService {
    if (!ClipboardService.instance) {
      ClipboardService.instance = new ClipboardService();
    }
    return ClipboardService.instance;
  }

  /**
   * 获取剪贴板文本
   */
  async getClipboardText(): Promise<string | null> {
    try {
      const pasteData = await pasteboard.getSystemPasteboard().getData();
      if (pasteData) {
        return pasteData.getPrimaryText() as string;
      }
      return null;
    } catch (error) {
      console.error('Failed to get clipboard text:', JSON.stringify(error));
      return null;
    }
  }

  /**
   * 设置剪贴板文本
   */
  async setClipboardText(text: string): Promise<boolean> {
    try {
      const pasteData: pasteboard.PasteData = pasteboard.createPlainTextData(text);
      await pasteboard.getSystemPasteboard().setData(pasteData);
      return true;
    } catch (error) {
      console.error('Failed to set clipboard text:', JSON.stringify(error));
      return false;
    }
  }

  /**
   * 检查剪贴板中是否有URL
   */
  async hasUrlInClipboard(): Promise<boolean> {
    const text = await this.getClipboardText();
    if (!text) return false;
    
    // 简单的URL检测
    const urlPattern = /https?:\/\/[^\s]+|www\.[^\s]+/gi;
    return urlPattern.test(text);
  }

  /**
   * 清空剪贴板
   */
  async clearClipboard(): Promise<boolean> {
    try {
      await pasteboard.getSystemPasteboard().clear();
      return true;
    } catch (error) {
      console.error('Failed to clear clipboard:', JSON.stringify(error));
      return false;
    }
  }

  /**
   * 监听剪贴板变化
   * 注意：HarmonyOS目前没有直接的剪贴板变化监听API
   * 可以使用轮询或系统事件监听
   */
  async checkClipboardChange(oldText: string | null): Promise<boolean> {
    const newText = await this.getClipboardText();
    return newText !== oldText;
  }
}

export const clipboardService = ClipboardService.getInstance();