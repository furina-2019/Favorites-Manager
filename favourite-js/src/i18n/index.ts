import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './locales/en'
import zh from './locales/zh'

// Get saved language from localStorage
const getSavedLanguage = (): string => {
  try {
    const saved = localStorage.getItem('favourite-ui-config')
    if (saved) {
      const config = JSON.parse(saved)
      if (config.state && (config.state.language === 'zh' || config.state.language === 'en')) {
        return config.state.language
      }
    }
  } catch (e) {
    console.error('Failed to load language setting:', e)
  }
  return 'en' // Default to English
}

const savedLanguage = getSavedLanguage()

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      zh: { translation: zh },
    },
    lng: savedLanguage, // Use saved language
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  })

export default i18n
