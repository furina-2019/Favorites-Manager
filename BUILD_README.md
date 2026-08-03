# Favourite 发布说明

## 目录结构

```
dist/
├── Favourite/          # 程序文件夹 (推荐)
│   ├── Favourite.exe   # 双击运行
│   ├── _internal/      # 运行时依赖 (不要删除！)
│   ├── resources/      # 资源文件
│   └── *.gguf          # AI 模型文件 (可选)
└── Favourite.zip       # 压缩包分发版
```

## 两种打包模式对比

### 模式 A: 文件夹版 (Onedir) ⭐ 推荐

**打包命令：**
```bash
# 使用批处理脚本 (自动打包+压缩)
build_release.bat

# 或手动命令
python -m PyInstaller Favourite.spec --clean --noconfirm
```

**使用方法：**
1. 用户下载 `Favourite.zip`
2. 解压到任意目录
3. 双击 `Favourite.exe` 直接运行

**优点：**
- 启动速度快 (无需解压到临时目录)
- AI 模型可独立替换/添加
- 内存占用少
- 文件可见，用户知道程序在做什么

**缺点：**
- 看起来是"文件夹"而非单个 exe
- 需要压缩包分发

### 模式 B: 单文件版 (Onefile)

**打包命令：**
```bash
python -m PyInstaller Favourite_onefile.spec --clean --noconfirm
```

**使用方法：**
1. 用户下载 `Favourite.exe`
2. 双击直接运行

**注意事项：**
- 首次启动需要 3-10 秒解压到临时目录
- 如果 AI 模型不嵌入 exe，需要放在 exe 同目录
- 杀毒软件可能误报 (因为是自解压程序)
- 不包含 AI 功能时 exe 约 60-80MB
- 包含 AI 功能时 exe 可能超过 500MB

## 用户分发指南

### 推荐方式: ZIP 压缩包

1. 运行 `build_release.bat`
2. 上传 `dist/Favourite.zip` 到 GitHub Releases 或网盘
3. 在下载页面说明：
   > 📦 **下载说明**
   > 
   > 1. 下载 Favourite.zip
   > 2. 右键解压到任意文件夹
   > 3. 双击 Favourite.exe 运行
   > 
   > 💡 AI 模型可从 [模型下载页] 下载后放在 exe 同目录

### 备选方式: 安装程序

使用 Inno Setup 或 NSIS 创建 Windows 安装程序：
- 创建开始菜单快捷方式
- 添加控制面板卸载选项
- 自动处理文件关联
- 创建桌面图标

## Windows SmartScreen 警告

首次运行未签名的程序会看到"Windows 已保护你的电脑"警告。解决方法：

1. **临时方法：** 点击"更多信息" → "仍要运行"
2. **长期方法：** 
   - 购买代码签名证书 (约 $200/年)
   - 将软件提交到 Microsoft 安全门户建立信誉
   - 在发布页说明："首次运行请点击'更多信息'→'仍要运行'"

## 常见问题

**Q: 为什么程序需要 _internal 文件夹？**
A: _internal 包含 Python 运行时、Qt 库和所有依赖。单独的 exe 只是启动器，没有它程序无法运行。

**Q: 能不能做成绿色版？**
A: 文件夹版就是绿色版！不写注册表，不安装，解压即用。

**Q: 模型文件放哪里？**
A: 放在 exe 同目录，程序会自动搜索。支持 .gguf 格式。
