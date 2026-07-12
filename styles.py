from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor
import sys

def apply_system_theme(app):
    """让应用程序跟随系统主题（深色/浅色）"""
    if sys.platform == "win32":
        # Windows 下可以尝试通过注册表获取，但简单起见使用默认
        pass
    # 设置基础调色板为跟随系统
    app.setStyle("Fusion")
    # 注意：PyQt6 默认会跟随系统，但可以手动调整
    palette = app.palette()
    # 获取系统主题色的方法较复杂，这里简单演示
    # 实际生产中可用 QStyleHints 等
    return palette

def get_button_style(color):
    """根据主题色返回按钮样式（仅为示例）"""
    return f"""
        QPushButton {{
            background-color: {color};
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            color: white;
        }}
        QPushButton:hover {{
            background-color: {color}80;
        }}
    """
