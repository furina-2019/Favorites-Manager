// Platform detection utility
// Auto-detects whether the app is running on PC (Electron), Android, or Web

export type Platform = 'electron' | 'android' | 'web'

let _platform: Platform | null = null

/**
 * Detects the current platform based on navigator.userAgent.
 * - Electron: user agent contains "Electron"
 * - Android: user agent contains "Android"
 * - Web: fallback
 */
export function getPlatform(): Platform {
  if (_platform) return _platform

  if (typeof navigator !== 'undefined') {
    const ua = navigator.userAgent
    if (ua.includes('Electron')) {
      _platform = 'electron'
      return _platform
    }
    if (ua.includes('Android')) {
      _platform = 'android'
      return _platform
    }
  }

  _platform = 'web'
  return _platform
}

/** Convenience checks */
export const isElectron = (): boolean => getPlatform() === 'electron'
export const isAndroid = (): boolean => getPlatform() === 'android'
