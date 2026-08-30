import { join } from 'path';
import { defineConfig } from '@capawesome/capacitor-electron/config';

export default defineConfig({
  window: {
    width: 1200,
    height: 800,
  },
  hooks: {
    windowFactory(options) {
      // __dirname at runtime is the *compiled* output dir (electron/build/).
      // preload.js lives one level up in electron/preload.js.
      options.webPreferences = {
        ...options.webPreferences,
        preload: join(__dirname, '..', 'preload.js'),
        contextIsolation: true,
        nodeIntegration: false,
      };
      const { BrowserWindow } = require('electron');
      return new BrowserWindow(options);
    },
  },
});
