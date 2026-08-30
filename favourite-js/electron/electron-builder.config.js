/** @type {import('electron-builder').Configuration} */
module.exports = {
  appId: 'com.fuqian.favourites',
  productName: '收藏管理器',
  win: {
    target: 'nsis', 
    icon: 'icon.ico' 
  },
  directories: {
    output: 'dist',
    buildResources: 'assets',
  },
  files: [
    'build/**/*',
    'app/**/*',
    'generated/**/*',
    'preload.js',
    'package.json',
    // Platform runtime + plugins, prepared by `capacitor-electron vendor`.
    { from: 'vendor/node_modules', to: 'node_modules' },
  ],
};
