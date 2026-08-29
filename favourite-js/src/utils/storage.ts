// Unified storage abstraction.
// On Electron (PC): delegates to the preload script's file-backed storage
//   via window.electronAPI (data lives in <AppData>/Local/Favourites-Manager/data.json)
// On Android / Web: delegates to the built-in localStorage.

import { isElectron } from './platform'

// ---------------------------------------------------------------------------
// Interface (mirrors the subset of Storage we actually use)
// ---------------------------------------------------------------------------
interface StorageBackend {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
  removeItem(key: string): void
}

// ---------------------------------------------------------------------------
// Electron backend – calls into the preload script via contextBridge
// ---------------------------------------------------------------------------
class ElectronStorage implements StorageBackend {
  getItem(key: string): string | null {
    // @ts-ignore – exposed by preload.js via contextBridge
    return window.electronAPI.getItem(key)
  }

  setItem(key: string, value: string): void {
    // @ts-ignore
    window.electronAPI.setItem(key, value)
  }

  removeItem(key: string): void {
    // @ts-ignore
    window.electronAPI.removeItem(key)
  }
}

// ---------------------------------------------------------------------------
// Singleton accessor
// ---------------------------------------------------------------------------
let _backend: StorageBackend | null = null

function getBackend(): StorageBackend {
  if (_backend) return _backend

  // @ts-ignore – exposed by preload.js via contextBridge
  if (isElectron() && typeof window.electronAPI !== 'undefined') {
    _backend = new ElectronStorage()
  } else {
    _backend = localStorage
  }

  return _backend
}

/**
 * Drop-in replacement for `localStorage` throughout the app.
 * On PC it writes to a JSON file in AppData via the preload script;
 * on Android it uses localStorage.
 */
export const storage = {
  getItem: (key: string): string | null => getBackend().getItem(key),
  setItem: (key: string, value: string): void => getBackend().setItem(key, value),
  removeItem: (key: string): void => getBackend().removeItem(key),
}
