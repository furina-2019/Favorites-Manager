// Type declarations for the Electron preload bridge.
// The preload script (electron/preload.js) exposes window.electronAPI
// via contextBridge – the renderer can call it but has no access to Node.js.

interface ElectronAPI {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
  removeItem(key: string): void
  flush(): void
}

interface Window {
  electronAPI?: ElectronAPI
}
