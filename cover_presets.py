from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtCore import Qt, QSize
import os

# 预设封面配置
PRESET_COVERS = {
    "doc": {
        "name": {"zh": "文档", "en": "Document"},
        "icon": "📄",
        "bg_color": "#f5f5f5",
        "text_color": "#333333"
    },
    "pdf": {
        "name": {"zh": "PDF", "en": "PDF"},
        "icon": "📕",
        "bg_color": "#e74c3c",
        "text_color": "#ffffff"
    },
    "image": {
        "name": {"zh": "图片", "en": "Image"},
        "icon": "🖼️",
        "bg_color": "#9b59b6",
        "text_color": "#ffffff"
    },
    "video": {
        "name": {"zh": "视频", "en": "Video"},
        "icon": "🎬",
        "bg_color": "#e67e22",
        "text_color": "#ffffff"
    },
    "music": {
        "name": {"zh": "音乐", "en": "Music"},
        "icon": "🎵",
        "bg_color": "#3498db",
        "text_color": "#ffffff"
    },
    "code": {
        "name": {"zh": "代码", "en": "Code"},
        "icon": "💻",
        "bg_color": "#2c3e50",
        "text_color": "#ffffff"
    },
    "folder": {
        "name": {"zh": "文件夹", "en": "Folder"},
        "icon": "📁",
        "bg_color": "#f39c12",
        "text_color": "#ffffff"
    },
    "url": {
        "name": {"zh": "链接", "en": "Link"},
        "icon": "🔗",
        "bg_color": "#1abc9c",
        "text_color": "#ffffff"
    },
    "archive": {
        "name": {"zh": "压缩包", "en": "Archive"},
        "icon": "📦",
        "bg_color": "#7f8c8d",
        "text_color": "#ffffff"
    },
    "program": {
        "name": {"zh": "程序", "en": "Program"},
        "icon": "⚙️",
        "bg_color": "#34495e",
        "text_color": "#ffffff"
    },
    "excel": {
        "name": {"zh": "表格", "en": "Excel"},
        "icon": "📊",
        "bg_color": "#27ae60",
        "text_color": "#ffffff"
    },
    "powerpoint": {
        "name": {"zh": "演示", "en": "PowerPoint"},
        "icon": "📈",
        "bg_color": "#d35400",
        "text_color": "#ffffff"
    },
    "text": {
        "name": {"zh": "文本", "en": "Text"},
        "icon": "📝",
        "bg_color": "#ecf0f1",
        "text_color": "#2c3e50"
    },
    "email": {
        "name": {"zh": "邮件", "en": "Email"},
        "icon": "📧",
        "bg_color": "#0077b6",
        "text_color": "#ffffff"
    },
    "calendar": {
        "name": {"zh": "日历", "en": "Calendar"},
        "icon": "📅",
        "bg_color": "#0284c7",
        "text_color": "#ffffff"
    },
    "note": {
        "name": {"zh": "笔记", "en": "Note"},
        "icon": "📌",
        "bg_color": "#fbbf24",
        "text_color": "#451a03"
    }
}

# 文件扩展名到预设类型的映射
EXTENSION_MAP = {
    # 文档
    '.doc': 'doc',
    '.docx': 'doc',
    '.odt': 'doc',
    '.rtf': 'doc',
    
    # PDF
    '.pdf': 'pdf',
    
    # 图片
    '.jpg': 'image',
    '.jpeg': 'image',
    '.png': 'image',
    '.gif': 'image',
    '.bmp': 'image',
    '.svg': 'image',
    '.webp': 'image',
    '.tiff': 'image',
    '.ico': 'image',
    
    # 视频
    '.mp4': 'video',
    '.avi': 'video',
    '.mkv': 'video',
    '.mov': 'video',
    '.wmv': 'video',
    '.flv': 'video',
    '.webm': 'video',
    '.m4v': 'video',
    
    # 音乐
    '.mp3': 'music',
    '.wav': 'music',
    '.flac': 'music',
    '.ogg': 'music',
    '.m4a': 'music',
    '.wma': 'music',
    
    # 代码
    '.py': 'code',
    '.java': 'code',
    '.cpp': 'code',
    '.c': 'code',
    '.h': 'code',
    '.js': 'code',
    '.ts': 'code',
    '.html': 'code',
    '.css': 'code',
    '.json': 'code',
    '.xml': 'code',
    '.go': 'code',
    '.rs': 'code',
    '.php': 'code',
    
    # 表格
    '.xls': 'excel',
    '.xlsx': 'excel',
    '.csv': 'excel',
    '.ods': 'excel',
    
    # 演示
    '.ppt': 'powerpoint',
    '.pptx': 'powerpoint',
    '.odp': 'powerpoint',
    
    # 压缩包
    '.zip': 'archive',
    '.rar': 'archive',
    '.7z': 'archive',
    '.tar': 'archive',
    '.gz': 'archive',
    '.bz2': 'archive',
    
    # 程序
    '.exe': 'program',
    '.msi': 'program',
    '.dll': 'program',
    '.bat': 'program',
    '.cmd': 'program',
    
    # 文本
    '.txt': 'text',
    '.md': 'text',
    '.log': 'text',
    
    # 邮件
    '.eml': 'email',
    '.msg': 'email',
    
    # 日历
    '.ics': 'calendar'
}


def generate_preset_cover(preset_type, size=QSize(180, 100)):
    """
    生成预设封面图片
    
    Args:
        preset_type (str): 预设类型，如 'doc', 'pdf', 'image' 等
        size (QSize): 封面尺寸，默认 180x100
    
    Returns:
        QPixmap: 生成的封面图片
    """
    preset = PRESET_COVERS.get(preset_type)
    if not preset:
        preset = PRESET_COVERS['url']  # 默认使用链接类型
    
    pixmap = QPixmap(size)
    painter = QPainter(pixmap)
    
    # 设置抗锯齿
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # 绘制背景
    bg_color = QColor(preset['bg_color'])
    painter.fillRect(0, 0, size.width(), size.height(), bg_color)
    
    # 绘制圆角矩形背景
    painter.setBrush(QBrush(bg_color))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(0, 0, size.width(), size.height(), 8, 8)
    
    # 根据尺寸动态计算字体大小
    # 图标大小为容器的 70%
    max_icon_size = min(size.width(), size.height()) * 0.7
    font_size = max(int(max_icon_size), 16)
    
    # 绘制图标（使用系统默认字体）
    icon_font = QFont()
    icon_font.setPointSize(font_size)
    painter.setFont(icon_font)
    
    text_color = QColor(preset['text_color'])
    painter.setPen(text_color)
    
    # 计算图标位置（居中）
    icon_rect = painter.fontMetrics().boundingRect(preset['icon'])
    icon_x = (size.width() - icon_rect.width()) // 2
    icon_y = (size.height() - icon_rect.height()) // 2 + icon_rect.height()
    
    painter.drawText(icon_x, icon_y, preset['icon'])
    
    painter.end()
    return pixmap


def get_preset_type_for_file(file_path):
    """
    根据文件路径获取预设封面类型
    
    Args:
        file_path (str): 文件路径
    
    Returns:
        str: 预设类型
    """
    ext = os.path.splitext(file_path)[1].lower()
    return EXTENSION_MAP.get(ext, 'url')


def get_all_preset_types():
    """
    获取所有预设封面类型
    
    Returns:
        list: 预设类型列表
    """
    return list(PRESET_COVERS.keys())


def get_preset_info(preset_type):
    """
    获取预设封面信息
    
    Args:
        preset_type (str): 预设类型
    
    Returns:
        dict: 预设信息，包含 name, icon, bg_color, text_color
    """
    return PRESET_COVERS.get(preset_type, PRESET_COVERS['url'])


def save_preset_cover(preset_type, save_path, size=QSize(180, 100)):
    """
    保存预设封面到文件
    
    Args:
        preset_type (str): 预设类型
        save_path (str): 保存路径
        size (QSize): 封面尺寸
    
    Returns:
        bool: 是否保存成功
    """
    try:
        pixmap = generate_preset_cover(preset_type, size)
        return pixmap.save(save_path)
    except:
        return False
