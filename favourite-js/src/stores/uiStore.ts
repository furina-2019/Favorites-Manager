import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Config {
  language: 'zh' | 'en'
  themeColor: string
  darkMode: boolean
}

interface UIState extends Config {
  setLanguage: (lang: 'zh' | 'en') => void
  setThemeColor: (color: string) => void
  setDarkMode: (dark: boolean) => void
  toggleDarkMode: () => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      language: 'en',
      themeColor: '#0078d7',
      darkMode: false,
      
      setLanguage: (lang) => set({ language: lang }),
      setThemeColor: (color) => set({ themeColor: color }),
      setDarkMode: (dark) => set({ darkMode: dark }),
      toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
    }),
    {
      name: 'favourite-ui-config',
    }
  )
)
