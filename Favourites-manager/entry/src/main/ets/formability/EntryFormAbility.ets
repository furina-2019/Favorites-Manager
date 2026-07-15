import { FormExtensionAbility, formProvider, formBindingData, formInfo } from '@kit.FormKit';
import { Want } from '@kit.AbilityKit';
import { hilog } from '@kit.PerformanceAnalysisKit';
import { dataService } from '../service/DataService';
import { common } from '@kit.AbilityKit';
import { BusinessError } from '@kit.BasicServicesKit';

const DOMAIN = 0x0000;
const TAG = 'EntryFormAbility';

/**
 * 卡片数据类
 */
class FormDataClass {
  latestTitle: string = '';
  latestSource: string = '';
  recommendTitle: string = '';
  recommendSource: string = '';
  totalCount: number = 0;
}

/**
 * 服务卡片能力类
 */
export default class EntryFormAbility extends FormExtensionAbility {
  
  onAddForm(want: Want): formBindingData.FormBindingData {
    hilog.info(DOMAIN, TAG, 'onAddForm');
    
    const formId = want.parameters?.[formInfo.FormParam.IDENTITY_KEY] as string;
    const formName = want.parameters?.[formInfo.FormParam.NAME_KEY] as string;
    
    hilog.info(DOMAIN, TAG, `formId: ${formId}, formName: ${formName}`);
    
    // 初始化DataService并注册formId
    this.initDataService();
    if (formId) {
      dataService.registerFormId(formId);
      hilog.info(DOMAIN, TAG, `Registered formId: ${formId}`);
    }
    
    const formData = new FormDataClass();
    formData.latestTitle = '加载中...';
    formData.latestSource = '';
    formData.recommendTitle = '加载中...';
    formData.recommendSource = '';
    formData.totalCount = 0;
    
    // 立即更新卡片数据
    this.updateFormData(formId).catch((error: BusinessError) => {
      hilog.error(DOMAIN, TAG, `Failed to update form data on add: ${JSON.stringify(error)}`);
    });
    
    return formBindingData.createFormBindingData(formData);
  }

  async onUpdateForm(formId: string): Promise<void> {
    hilog.info(DOMAIN, TAG, `onUpdateForm: ${formId}`);
    await this.updateFormData(formId);
  }

  onRemoveForm(formId: string): void {
    hilog.info(DOMAIN, TAG, `onRemoveForm: ${formId}`);
    // 取消注册formId
    dataService.unregisterFormId(formId);
  }

  onFormEvent(formId: string, message: string): void {
    hilog.info(DOMAIN, TAG, `onFormEvent: ${formId}, message: ${message}`);
  }

  /**
   * 初始化DataService
   */
  private initDataService(): void {
    // FormExtensionContext无法直接转换为UIAbilityContext
    // 卡片服务依赖主Ability初始化DataService
    hilog.info(DOMAIN, TAG, 'FormExtension cannot initialize DataService directly');
  }

  /**
   * 更新卡片数据
   */
  private async updateFormData(formId: string): Promise<void> {
    try {
      const latest = await dataService.getLatestFavorite();
      const recommend = await dataService.getRecommendFavorite();
      const allFavorites = await dataService.getFavorites();
      
      const formData = new FormDataClass();
      formData.latestTitle = latest?.title ?? '暂无收藏';
      formData.latestSource = latest?.sourceApp ?? '';
      formData.recommendTitle = recommend?.title ?? '暂无收藏';
      formData.recommendSource = recommend?.sourceApp ?? '';
      formData.totalCount = allFavorites.length;
      
      const bindingData = formBindingData.createFormBindingData(formData);
      await formProvider.updateForm(formId, bindingData);
      hilog.info(DOMAIN, TAG, `Updated form ${formId}`);
    } catch (error) {
      hilog.error(DOMAIN, TAG, `updateFormData failed: ${JSON.stringify(error)}`);
    }
  }
}