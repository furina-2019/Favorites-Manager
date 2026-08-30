// electron/preload.js
// Preload script: exposes a safe storage API to the renderer via contextBridge.
// The renderer cannot access Node.js APIs directly – it calls window.electronAPI.*

const { contextBridge } = require('electron');
const fs = require('fs');
const os = require('os');
const path = require('path');

// ---------------------------------------------------------------------------
// Resolve data directory (mirrors the old storage.ts logic)
// ---------------------------------------------------------------------------
function getDataDir() {
  const home = os.homedir();
  const platform = os.platform();

  if (platform === 'win32') {
    return path.join(
      process.env.LOCALAPPDATA || path.join(home, 'AppData', 'Local'),
      'Favourites-Manager'
    );
  } else if (platform === 'darwin') {
    return path.join(home, 'Library', 'Application Support', 'Favourites-Manager');
  } else {
    return path.join(home, '.local', 'share', 'Favourites-Manager');
  }
}

const dataDir = getDataDir();
const dataFile = path.join(dataDir, 'data.json');

// Ensure directory exists
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

// ---------------------------------------------------------------------------
// In-memory cache + debounced flush
// ---------------------------------------------------------------------------
let cache = {};
let saveTimer = null;

// Load existing data on startup
if (fs.existsSync(dataFile)) {
  try {
    cache = JSON.parse(fs.readFileSync(dataFile, 'utf-8'));
    console.log(`[Preload] Loaded data from ${dataFile}`);
  } catch (err) {
    console.error('[Preload] Failed to parse data file, starting fresh:', err);
    cache = {};
  }
} else {
  console.log(`[Preload] No data file found, creating fresh at ${dataFile}`);
}

function doFlush() {
  try {
    fs.writeFileSync(dataFile, JSON.stringify(cache, null, 2), 'utf-8');
  } catch (err) {
    console.error('[Preload] Failed to write data file:', err);
  }
}

function scheduleSave() {
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    saveTimer = null;
    doFlush();
  }, 300);
}

// ---------------------------------------------------------------------------
// Expose API to the renderer
// ---------------------------------------------------------------------------
contextBridge.exposeInMainWorld('electronAPI', {
  getItem(key) {
    return cache[key] ?? null;
  },
  setItem(key, value) {
    cache[key] = value;
    scheduleSave();
  },
  removeItem(key) {
    delete cache[key];
    scheduleSave();
  },
  // Force an immediate flush (e.g. before quitting)
  flush() {
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = null;
    doFlush();
  },
});
