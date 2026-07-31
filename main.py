import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTranslator, QLocale
from main_window import MainWindow

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def load_translator(app, language):
    """加载Qt翻译文件"""
    # 创建翻译器
    translator = QTranslator(app)
    
    # 尝试加载Qt内置翻译文件
    # Qt的翻译文件路径通常在Qt安装目录下的translations文件夹
    import PyQt6
    qt_dir = os.path.dirname(PyQt6.__file__)
    translations_dir = os.path.join(qt_dir, "Qt6", "translations")
    
    if language == "zh" or language == "zh_CN":
        lang_code = "zh_CN"
    else:
        lang_code = "en"
    
    # 尝试加载qtbase翻译（包含QColorDialog等控件的翻译）
    qt_translation_file = f"qtbase_{lang_code}.qm"
    qt_translation_path = os.path.join(translations_dir, qt_translation_file)
    
    if os.path.exists(qt_translation_path):
        if translator.load(qt_translation_path):
            app.installTranslator(translator)
            print(f"[DEBUG] Loaded Qt translation: {qt_translation_file}")
        else:
            print(f"[DEBUG] Failed to load Qt translation: {qt_translation_file}")
    else:
        print(f"[DEBUG] Qt translation file not found: {qt_translation_path}")
    
    # 设置应用语言环境
    locale = QLocale(lang_code)
    QLocale.setDefault(locale)
    
    return translator

if __name__ == "__main__":
    browsers_path = resource_path("browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
    print(f"[DEBUG] PLAYWRIGHT_BROWSERS_PATH set to: {browsers_path}")
    
    app = QApplication(sys.argv)
    
    # 加载配置文件获取语言设置
    config_path = resource_path("config.json")
    language = "zh"
    try:
        import json
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            language = config.get("language", "zh")
    except:
        pass
    
    # 加载翻译
    load_translator(app, language)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
