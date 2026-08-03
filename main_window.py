import os
import re
import webbrowser
import subprocess
import sqlite3
import sys
import json
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QScrollArea, QMessageBox, QFileDialog,
    QInputDialog, QStackedWidget, QLabel, QMenu, QApplication,
    QComboBox, QDialog, QDialogButtonBox, QCheckBox, QColorDialog,
    QFrame, QTextEdit, QSlider, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, QRect, QParallelAnimationGroup, QThread, QSize
from PyQt6.QtGui import QIcon, QPixmap, QAction, QDragEnterEvent, QDropEvent, QColor, QTransform, QPainter, QPalette

from database import Database
from widgets import FolderCard, ItemCard, ToastNotification
from background_manager import background_manager
from mindmap_view import MindmapView

def resource_path(relative_path):
    """获取资源的绝对路径，兼容开发环境和 PyInstaller 打包后的环境"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class CardContainerWidget(QWidget):
    """自定义卡片容器，确保背景不被父窗口覆盖，支持背景图片"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def update_background(self):
        """更新背景"""
        self.update()
        
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # 使用背景管理器渲染卡片区域背景
        background_manager.render_card_background(
            painter,
            self.rect(),
            MainWindow.current_theme_color,
            MainWindow.current_dark_mode
        )
        painter.end()

class DraggableHelpSidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.sidebar_start_x = 0
        self.sidebar_start_y = 0
        self.min_width = 200
        self.max_width = 400

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_start_x = event.globalPosition().x()
            self.drag_start_y = event.globalPosition().y()
            self.sidebar_start_x = self.geometry().x()
            self.sidebar_start_y = self.geometry().y()
            self.setCursor(Qt.CursorShape.SizeAllCursor)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            delta_x = event.globalPosition().x() - self.drag_start_x
            delta_y = event.globalPosition().y() - self.drag_start_y
            
            new_x = self.sidebar_start_x + delta_x
            new_y = self.sidebar_start_y + delta_y
            
            parent_rect = self.parent().geometry()
            
            if new_x < 0:
                new_x = 0
            if new_x + self.width() > parent_rect.width():
                new_x = parent_rect.width() - self.width()
            if new_y < 0:
                new_y = 0
            if new_y + self.height() > parent_rect.height():
                new_y = parent_rect.height() - self.height()
            
            self.setGeometry(int(new_x), int(new_y), self.width(), self.height())

    def mouseReleaseEvent(self, event):
        self.is_dragging = False
        self.setCursor(Qt.CursorShape.ArrowCursor)

class DraggableHelpButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.button_start_x = 0
        self.button_start_y = 0
        self.has_moved = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.has_moved = False
            self.drag_start_x = event.globalPosition().x()
            self.drag_start_y = event.globalPosition().y()
            self.button_start_x = self.geometry().x()
            self.button_start_y = self.geometry().y()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            delta_x = event.globalPosition().x() - self.drag_start_x
            delta_y = event.globalPosition().y() - self.drag_start_y
            
            if abs(delta_x) > 5 or abs(delta_y) > 5:
                self.is_dragging = True
                self.has_moved = True
                self.setCursor(Qt.CursorShape.SizeAllCursor)
                
                new_x = self.button_start_x + delta_x
                new_y = self.button_start_y + delta_y
                
                parent_rect = self.parent().geometry()
                
                if new_x < 0:
                    new_x = 0
                if new_x + self.width() > parent_rect.width():
                    new_x = parent_rect.width() - self.width()
                if new_y < 0:
                    new_y = 0
                if new_y + self.height() > parent_rect.height():
                    new_y = parent_rect.height() - self.height()
                
                self.move(int(new_x), int(new_y))
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_dragging:
            self.is_dragging = False
            self.has_moved = False
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.has_moved = False
            super().mouseReleaseEvent(event)

class DropArea(QLabel):
    file_dropped = pyqtSignal(str)

    def __init__(self, parent=None, hint="拖拽文件到此"):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setText(hint)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 2px dashed #aaa; border-radius: 8px; padding: 20px; background-color: #f0f0f0;")
        self.setFixedHeight(100)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("border: 2px solid #0078d7; background-color: #e6f7ff;")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("border: 2px dashed #aaa; background-color: #f0f0f0;")

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.file_dropped.emit(file_path)
        self.setStyleSheet("border: 2px dashed #aaa; background-color: #f0f0f0;")
        event.acceptProposedAction()

class FetchThread(QThread):
    finished = pyqtSignal(dict)  # 返回 {'title': str, 'category': str, 'cover': str}
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
            }
            # 允许重定向
            resp = requests.get(self.url, timeout=8, headers=headers, allow_redirects=True)
            resp.encoding = resp.apparent_encoding or 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')

            # 1. 提取标题：优先 og:title
            title = None
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                title = og_title['content'].strip()
            else:
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text().strip()
            if not title:
                title = self.url

            # 2. 自动识别类别
            category = self.extract_category(soup, self.url)

            # 3. 提取封面图片：优先 og:image
            cover = None
            
            # 策略1: 查找 og:image
            og_image = soup.find('meta', property='og:image')
            if not og_image:
                og_image = soup.find('meta', attrs={'name': 'og:image'})
            if not og_image:
                og_image = soup.find('meta', attrs={'name': 'image'})
            if og_image and og_image.get('content'):
                cover = og_image['content'].strip()
            
            # 策略2: 查找 Twitter Card 图片
            if not cover:
                twitter_image = soup.find('meta', property='twitter:image')
                if not twitter_image:
                    twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
                if twitter_image and twitter_image.get('content'):
                    cover = twitter_image['content'].strip()
            
            # 策略3: 查找 video 标签的 poster
            if not cover:
                video_tag = soup.find('video')
                if video_tag and video_tag.get('poster'):
                    cover = video_tag['poster'].strip()
            
            # 策略4: B站特定 - 查找缩略图脚本数据
            if not cover and 'bilibili' in self.url:
                import re
                script_tags = soup.find_all('script')
                for script in script_tags:
                    script_content = script.string
                    if script_content:
                        match = re.search(r'"pic":"([^"]+)"', script_content)
                        if match:
                            cover = match.group(1)
                            break
                        match = re.search(r'cover":"([^"]+)"', script_content)
                        if match:
                            cover = match.group(1)
                            break
            
            # 策略5: 使用封面提取器获取动态渲染的封面（支持抖音、快手、小红书等）
            if not cover:
                try:
                    from cover_extractor import extract_cover
                    cover = extract_cover(self.url)
                    print(f"[DEBUG] cover_extractor fetched cover: {cover}")
                except Exception as e:
                    print(f"[DEBUG] cover_extractor failed: {str(e)}")
            
            # 策略6: 查找带有特定类名的图片（视频缩略图）
            if not cover:
                thumbnail_selectors = [
                    'img.cover', 'img.thumbnail', 'img.video-cover',
                    'img[class*="cover"]', 'img[class*="thumbnail"]',
                    'meta[itemprop="image"]'
                ]
                for selector in thumbnail_selectors:
                    img_tag = soup.select_one(selector)
                    if img_tag:
                        if img_tag.has_attr('src'):
                            cover = img_tag['src'].strip()
                        elif img_tag.has_attr('content'):
                            cover = img_tag['content'].strip()
                        if cover:
                            break
            
            if cover:
                # 解码JSON转义字符（如 \u002F -> /）
                import codecs
                cover = codecs.decode(cover, 'unicode_escape')
                
                from urllib.parse import urljoin
                cover = urljoin(self.url, cover)
                # 处理B站图片URL，确保使用高清图
                if 'bilibili' in self.url and cover:
                    cover = cover.replace('/168x94/', '/360x203/').replace('/240x135/', '/360x203/')

            self.finished.emit({'title': title, 'category': category, 'cover': cover})
        except Exception as e:
            self.error.emit(str(e))

    def extract_category(self, soup, url):
        domain_map = {
            'github.com': 'programming',
            'stackoverflow.com': 'programming',
            'csdn.net': 'programming',
            'zhihu.com': 'qa',
            'bilibili.com': 'video',
            'youtube.com': 'video',
            'douyin.com': 'video',
            'weibo.com': 'social',
            'twitter.com': 'social',
            'cnblogs.com': 'blog',
            'jianshu.com': 'writing',
            'wikipedia.org': 'wiki',
            'baidu.com': 'search',
            'google.com': 'search',
            'bing.com': 'search',
            'taobao.com': 'shopping',
            'jd.com': 'shopping',
            'amazon.com': 'shopping',
            'netflix.com': 'movie',
            'iqiyi.com': 'movie',
            'youku.com': 'movie',
            'douban.com': 'movie',
            'qq.com': 'portal',
            'sina.com.cn': 'portal',
            '163.com': 'portal',
            'sohu.com': 'portal',
            'ifeng.com': 'news',
            'xinhuanet.com': 'news',
            'people.com.cn': 'news',
        }
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        # 优先域名映射
        for key, cat_key in domain_map.items():
            if key in domain:
                return cat_key
        # 尝试从 meta keywords 获取
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords = meta_keywords['content'].split(',')
            if keywords:
                first_keyword = keywords[0].strip().lower()
                # 如果包含常见类别词，尝试映射
                for key, cat in domain_map.items():
                    if key in first_keyword or first_keyword in key:
                        return cat
                # 否则返回第一个关键词（但可能不是标准键，会显示原文）
                return first_keyword
        return 'uncategorized'


class MainWindow(QMainWindow):
    # 类变量保存当前主题色和显示模式
    current_theme_color = QColor("#0078d7")   # 默认蓝色
    current_dark_mode = False
    
    # 线程安全的信号定义
    summary_token_signal = pyqtSignal(str)    # 流式输出摘要token
    summary_result_signal = pyqtSignal(str)   # 最终摘要结果
    toast_signal = pyqtSignal(str)            # Toast提示消息
    category_translations = {
        "zh": {
            "programming": "编程",
            "qa": "问答",
            "video": "视频",
            "social": "社交",
            "blog": "博客",
            "writing": "写作",
            "wiki": "百科",
            "search": "搜索",
            "shopping": "购物",
            "movie": "影视",
            "portal": "门户",
            "news": "新闻",
            "uncategorized": "未分类"
        },
        "en": {
            "programming": "Programming",
            "qa": "Q&A",
            "video": "Video",
            "social": "Social",
            "blog": "Blog",
            "writing": "Writing",
            "wiki": "Wiki",
            "search": "Search",
            "shopping": "Shopping",
            "movie": "Movie",
            "portal": "Portal",
            "news": "News",
            "uncategorized": "Uncategorized"
        }
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("收藏管理器")
        self.setGeometry(100, 100, 1200, 800)
        self.anim_group = None
        self.db = Database()
        
        # 迁移旧的封面路径到持久化目录
        try:
            self.db.migrate_cover_paths()
        except Exception as e:
            print(f"[WARN] 封面路径迁移失败: {e}")
        
        # 连接线程安全信号
        self.summary_token_signal.connect(self._update_summary_stream)
        self.summary_result_signal.connect(self._set_summary_result)
        self.toast_signal.connect(self.show_toast)
        # 属性
        self.password_overlay = None
        self.password_sidebar = None
        self.password_anim = None
        self.password_callback = None  # 用于输入模式验证后的回调
        self.password_target_type = None
        self.password_target_id = None

        # 翻译
        config = self.load_config()
        self.current_lang = config.get("language", "zh")
        self.strings = {
            "zh": {
                "window_title": "收藏管理器",
                "folder_search_placeholder": "搜索收藏夹...",
                "add_folder_btn": "+ 添加收藏夹",
                "settings_title": "⚙ 设置",
                "display_settings": "显示设置",
                "language": "语言",
                "about": "关于",
                "display_title": "显示设置",
                "display_mode": "显示模式",
                "light_mode": "浅色",
                "dark_mode": "深色",
                "theme_color": "主题色",
                "select_color": "选择颜色",
                "about_title": "关于",
                "version": "版本: v0.1.1-beta",
                "open_source": "开源地址",
                "language_title": "语言",
                "chinese": "简体中文",
                "english": "English",
                "back_btn": "← 返回",
                "item_search_placeholder": "搜索收藏项...",
                "add_item_btn": "+ 收藏项",
                "delete_selected": "删除选中",
                "cancel": "取消",
                "confirm": "确认",
                "auto_fetch": "自动识别",
                "link_type": "链接",
                "file_type": "本地文件",
                "link_url": "链接URL:",
                "title_label": "标题:",
                "category_label": "类别:",
                "file_drop": "将文件拖拽到此区域:",
                "file_selected": "已选择:",
                "file_selected_prefix": "已选择: ",
                "file_not_exist": "文件不存在，请重新拖拽",
                "add_item_type": "收藏类型:",
                "item_type_link": "链接",
                "item_type_file": "本地文件",
                "drag_hint": "拖拽文件到此",
                "warning": "警告",
                "info": "提示",
                "confirm_delete": "确认删除",
                "delete_folder_confirm": "删除收藏夹会同时删除其中的所有收藏项，确定吗？",
                "delete_item_confirm": "确定删除该收藏项吗？",
                "multi_select_mode": "多选模式",
                "edit": "编辑",
                "delete": "删除",
                "rename": "重命名",
                "new_folder_name": "新名称:",
                "add_folder_dialog_title": "添加收藏夹",
                "add_folder_dialog_label": "请输入收藏夹名称:",
                "edit_item_dialog": "编辑收藏项",
                "rename_folder_dialog_title": "重命名收藏夹",
                "rename_folder_dialog_label": "新名称:",
                "batch_delete_confirm": "确定删除 {0} 个收藏项吗？",
                "no_item_selected": "未选中任何项目",
                "success_add": "收藏项已添加",
                "success_update": "收藏项已更新",
                "warning_no_folder": "未选择收藏夹",
                "warning_invalid_link": "链接格式无效",
                "warning_empty_link": "请输入链接URL",
                "warning_empty_url": "请输入有效的链接",
                "warning_drag_file": "请拖拽文件",
                "warning_drag_file_to_area": "请拖拽文件到指定区域",
                "file_not_found": "文件不存在",
                "file_not_found_msg": "找不到文件：{0}",
                "auto_fetch_complete": "自动识别完成（模拟）",
                "open_link": "打开链接",
                "open_file": "打开文件",
                "filter_all": "全部",
                "category_filter": "类别筛选",
                "select_theme_color": "选择主题色",
                "link_url_placeholder": "输入链接URL",
                "title_placeholder": "标题（可选）",
                "category_placeholder": "类别",
                "file_title_placeholder": "自动填充，可修改",
                "set_password": "设置密码",
                "change_password": "更改密码",
                "remove_password": "取消密码",
                "input_password": "输入密码",
                "new_password": "新密码",
                "confirm_new_password": "确认新密码",
                "old_password": "原密码",
                "enter_old_password": "请输入原密码",
                "enter_password": "请输入密码",
                "password_cannot_be_empty": "密码不能为空",
                "passwords_do_not_match": "两次密码输入不一致",
                "old_password_incorrect": "原密码错误",
                "password_incorrect": "密码错误，请重试",
                "back": "← 返回",
                "fetching": "获取中...",
                "auto_fetch_success": "已获取标题：{0}\n自动识别类别：{1}",
                "uncategorized": "未分类",
                "cover_label": "封面:",
                "cover_url_placeholder": "封面URL或本地路径",
                "select_cover": "选择封面",
                "select_cover_hint": "选择本地图片文件作为封面",
                "browse_files": "浏览文件",
                "no_file_selected": "未选择文件",
                "local_file": "本地文件",
                "preset_cover": "预设封面",
                "confirm": "确认",
                "cancel": "取消",
                "summary_label": "摘要:",
                "summary_placeholder": "输入摘要...",
                "ai_summary_btn": "AI生成摘要",
                "ai_generating": "AI生成中...",
                "error": "错误",
                "download_failed": "下载失败：",
                "bg_settings": "大背景设置",
                "main_theme_opacity": "主题色透明度",
                "main_bg_image": "背景图片",
                "main_bg_image_opacity": "背景图片透明度",
                
                "main_bg_strategy": "背景策略",
                "bg_stretch": "拉伸",
                "bg_tile": "平铺",
                "bg_center": "居中",
                "bg_fill": "填充",
                "bg_fit": "适应",
                "select_bg_image": "选择背景图片",
                "remove_bg_image": "移除背景图片",
                "card_bg_settings": "卡片区域背景设置",
                "card_bg_enabled": "启用卡片背景",
                "card_theme_opacity": "主题色透明度",
                "card_bg_image": "背景图片",
                "card_bg_image_opacity": "背景图片透明度",
                
                "card_bg_strategy": "背景策略",
                
                # 思维导图相关
                "edit_mode": "编辑模式",
                "exit_edit_mode": "退出编辑模式",
                "summary_btn": "摘要",
                "mindmap_title": "思维导图视图",
                "password_success": "密码设置成功!",
                "password_change_success": "密码修改成功!",
                "password_remove_success": "密码已移除!",
                "password_operation_failed": "密码操作失败",
                "cannot_open_url": "无法打开链接",
                "cannot_open_url_detail": "打开URL失败",
                "category_management": "分类管理",
                "no_categories": "暂无分类",
                "rename_category": "重命名",
                "delete_category": "删除",
                "add_category": "+ 添加分类",
                "rename_category_dialog_title": "重命名分类",
                "rename_category_dialog_label": "请输入新名称：",
                "rename_failed": "重命名失败",
                "delete_category_confirm": "确定要删除分类「{0}」吗？\n该分类下的项目将被设为「未分类」。",
                "delete_failed": "删除失败",
                "category_exists": "分类「{0}」已存在！",
                "add_failed": "添加失败",
                "new_category_dialog_title": "添加分类",
                "new_category_dialog_label": "请输入新分类名称：",
                "drag_success": "拖拽成功",
                "drag_success_msg": "成功将项目移动到「{0}」分类",
                "password": "密码",
                "error_title": "错误",
                "confirm_delete": "确认删除",
                "delete_item_confirm": "确定要删除该项目吗？",
                "password_action_failed": "密码操作失败",
                "invalid_input": "请输入有效的密码",
                "passwords_do_not_match": "两次输入的密码不一致",
                "passwords_match": "两次输入的密码一致",
                "password_too_short": "密码至少需要4个字符",
                "password_cannot_be_empty": "密码不能为空",
                "incorrect_password": "密码不正确",
                "old_password_incorrect": "原密码不正确",
                "unlock_failed": "解锁失败",
                "unlock_failed_detail": "解密内容失败",
                "info": "提示",
                "error": "错误",
                "password_incorrect": "密码不正确",
                "summary_title": "📝 摘要",
                "type_link": "链接",
                "type_file": "本地文件"
            },
            "en": {
               "window_title": "Favorites Manager",
                "folder_search_placeholder": "Search folders...",
                "add_folder_btn": "+ Add Folder",
                "settings_title": "⚙ Settings",
                "display_settings": "Display Settings",
                "language": "Language",
                "about": "About",
                "display_title": "Display Settings",
                "display_mode": "Display Mode",
                "light_mode": "Light",
                "dark_mode": "Dark",
                "theme_color": "Theme Color",
                "select_color": "Choose Color",
                "about_title": "About",
                "version": "Version: v0.1.1-beta",
                "open_source": "Open Source",
                "language_title": "Language",
                "chinese": "Simplified Chinese",
                "english": "English",
                "back_btn": "← Back",
                "item_search_placeholder": "Search items...",
                "add_item_btn": "+ Add Item",
                "delete_selected": "Delete Selected",
                "cancel": "Cancel",
                "confirm": "Confirm",
                "auto_fetch": "Auto Fetch",
                "link_type": "Link",
                "file_type": "Local File",
                "link_url": "URL:",
                "title_label": "Title:",
                "category_label": "Category:",
                "file_drop": "Drag file here:",
                "file_selected": "Selected:",
                "file_selected_prefix": "Selected: ",
                "file_not_exist": "File not exists, please re-drag",
                "add_item_type": "Type:",
                "item_type_link": "Link",
                "item_type_file": "Local File",
                "drag_hint": "Drag file here",
                "warning": "Warning",
                "info": "Info",
                "confirm_delete": "Confirm Delete",
                "delete_folder_confirm": "Deleting folder will also delete all items inside. Are you sure?",
                "delete_item_confirm": "Are you sure to delete this item?",
                "multi_select_mode": "Multi-select mode",
                "edit": "Edit",
                "delete": "Delete",
                "rename": "Rename",
                "new_folder_name": "New name:",
                "add_folder_dialog_title": "Add Folder",
                "add_folder_dialog_label": "Enter folder name:",
                "edit_item_dialog": "Edit Item",
                "rename_folder_dialog_title": "Rename Folder",
                "rename_folder_dialog_label": "New name:",
                "batch_delete_confirm": "Are you sure to delete {0} items?",
                "no_item_selected": "No item selected",
                "success_add": "Item added successfully",
                "success_update": "Item updated successfully",
                "warning_no_folder": "No folder selected",
                "warning_invalid_link": "Invalid link format",
                "warning_empty_link": "Please enter a URL",
                "warning_empty_url": "Please enter a valid link",
                "warning_drag_file": "Please drag a file",
                "warning_drag_file_to_area": "Please drag file to the area",
                "file_not_found": "File not found",
                "file_not_found_msg": "File not found: {0}",
                "auto_fetch_complete": "Auto fetch completed (simulated)",
                "open_link": "Open Link",
                "open_file": "Open File",
                "filter_all": "All",
                "category_filter": "Category Filter",
                "select_theme_color": "Select Theme Color",
                "link_url_placeholder": "Enter URL",
                "title_placeholder": "Title (optional)",
                "category_placeholder": "Category",
                "file_title_placeholder": "Auto-filled, editable",
                "set_password": "Set Password",
                "change_password": "Change Password",
                "remove_password": "Remove Password",
                "input_password": "Enter Password",
                "new_password": "New Password",
                "confirm_new_password": "Confirm New Password",
                "old_password": "Old Password",
                "enter_old_password": "Enter Old Password",
                "enter_password": "Enter Password",
                "password_cannot_be_empty": "Password cannot be empty",
                "passwords_do_not_match": "Passwords do not match",
                "old_password_incorrect": "Old password incorrect",
                "password_incorrect": "Password incorrect, please try again",
                "back": "← back",
                "fetching": "Fetching...",
                "auto_fetch_success": "Fetched title: {0}\nAuto-detected category: {1}",
                "uncategorized": "Uncategorized",
                "cover_label": "Cover:",
                "cover_url_placeholder": "Cover URL or local path",
                "select_cover": "Select Cover",
                "select_cover_hint": "Select local image file as cover",
                "browse_files": "Browse Files",
                "no_file_selected": "No file selected",
                "local_file": "Local File",
                "preset_cover": "Preset Cover",
                "confirm": "Confirm",
                "cancel": "Cancel",
                "summary_label": "Summary:",
                "summary_placeholder": "Enter summary...",
                "ai_summary_btn": "AI Generate Summary",
                "ai_generating": "AI generating...",
                "error": "Error",
                "download_failed": "Download failed: ",
                "bg_settings": "Main Background",
                "main_theme_opacity": "Theme Color Opacity",
                "main_bg_image": "Background Image",
                "main_bg_image_opacity": "Background Image Opacity",
                
                "main_bg_strategy": "Background Strategy",
                "bg_stretch": "Stretch",
                "bg_tile": "Tile",
                "bg_center": "Center",
                "bg_fill": "Fill",
                "bg_fit": "Fit",
                "select_bg_image": "Select Background Image",
                "remove_bg_image": "Remove Background Image",
                "card_bg_settings": "Card Area Background",
                "card_bg_enabled": "Enable Card Background",
                "card_theme_opacity": "Theme Color Opacity",
                "card_bg_image": "Background Image",
                "card_bg_image_opacity": "Background Image Opacity",
                
                "card_bg_strategy": "Background Strategy",
                
                # Mind map related
                "edit_mode": "Edit Mode",
                "exit_edit_mode": "Exit Edit Mode",
                "summary_btn": "S",
                "mindmap_title": "Mind Map View",
                "password_success": "Password set successfully!",
                "password_change_success": "Password changed successfully!",
                "password_remove_success": "Password removed!",
                "password_operation_failed": "Password operation failed",
                "cannot_open_url": "Cannot open link",
                "cannot_open_url_detail": "Failed to open URL",
                "category_management": "Category Management",
                "no_categories": "No categories",
                "rename_category": "Rename",
                "delete_category": "Delete",
                "add_category": "+ Add Category",
                "rename_category_dialog_title": "Rename Category",
                "rename_category_dialog_label": "Enter new name:",
                "rename_failed": "Rename failed",
                "delete_category_confirm": "Are you sure to delete category '{0}'?\nItems in this category will be set to 'Uncategorized'.",
                "delete_failed": "Delete failed",
                "category_exists": "Category '{0}' already exists!",
                "add_failed": "Add failed",
                "new_category_dialog_title": "Add Category",
                "new_category_dialog_label": "Enter category name:",
                "drag_success": "Drag Success",
                "drag_success_msg": "Successfully moved item to '{0}' category",
                "password": "Password",
                "error_title": "Error",
                "confirm_delete": "Confirm Delete",
                "delete_item_confirm": "Are you sure to delete this item?",
                "password_action_failed": "Password action failed",
                "invalid_input": "Please enter a valid password",
                "passwords_do_not_match": "Passwords do not match",
                "passwords_match": "Passwords match",
                "password_too_short": "Password must be at least 4 characters",
                "password_cannot_be_empty": "Password cannot be empty",
                "incorrect_password": "Incorrect password",
                "old_password_incorrect": "Old password is incorrect",
                "unlock_failed": "Unlock Failed",
                "unlock_failed_detail": "Failed to decrypt content",
                "info": "Info",
                "error": "Error",
                "password_incorrect": "Incorrect password",
                "summary_title": "📝 Summary",
                "type_link": "Links",
                "type_file": "Files"
            }
        }

        # 设置主题色和暗黑模式
        color_str = config.get("theme_color", "#0078d7")
        MainWindow.current_theme_color = QColor(color_str)
        MainWindow.current_dark_mode = config.get("dark_mode", False)

        # 中心控件: 使用 QStackedWidget 实现横推动画切换
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # 页面0: 收藏夹列表页
        self.folders_page = QWidget()
        self.folders_page.setObjectName("page")
        self.setup_folders_page()
        self.stacked_widget.addWidget(self.folders_page)

        # 页面1: 某个收藏夹内部的详情页（收藏项列表）
        self.items_page = QWidget()
        self.items_page.setObjectName("page")
        self.setup_items_page()
        self.stacked_widget.addWidget(self.items_page)
        self.current_category_filter = None
        self.multi_select_mode = False
        self.selected_item_ids = set()
        self.editing_item_id = None
        self.editing_item_type = None

        # 页面2: 添加收藏项页面
        self.add_item_page = QWidget()
        self.add_item_page.setObjectName("page")
        self.setup_add_item_page()
        self.stacked_widget.addWidget(self.add_item_page)

        # 页面3: 思维导图页面
        self.mindmap_page = QWidget()
        self.mindmap_page.setObjectName("page")
        self.mindmap_layout = QVBoxLayout(self.mindmap_page)
        self.mindmap_layout.setContentsMargins(0, 0, 0, 0)
        self.stacked_widget.addWidget(self.mindmap_page)
        self.current_mindmap_view = None

        self.stacked_widget.setCurrentIndex(0)
        self.current_folder_id = None
        self.current_folder_name = ""

        # 设置侧边栏相关属性
        self.settings_sidebars = []        # 存储当前打开的侧边栏（从外到内）
        self.settings_overlay = None       # 遮罩
        self.settings_animations = []      # 动画对象（用于清理）

        # 帮助内容（不同页面有不同的帮助文档）
        self.help_content = {
            "zh": {
                "folders": """<h3>收藏夹列表</h3>
<p>欢迎使用收藏夹管理应用！</p>
<p><strong>功能说明：</strong></p>
<ul>
<li>点击收藏夹卡片可进入查看其中的收藏项</li>
<li>右键点击收藏夹可进行重命名或删除操作</li>
<li>使用顶部搜索框可快速查找收藏夹</li>
<li>点击右下角"+"按钮可添加新收藏夹</li>
</ul>
<p><strong>设置说明：</strong></p>
<ul>
<li>点击左上角菜单按钮打开设置侧边栏</li>
<li>设置包含显示设置和语言设置</li>
<li>语言设置：支持中文和英文切换</li>
<li>主题设置：支持深色和浅色模式切换</li>
<li>背景管理：可设置大背景和卡片区域背景的颜色或图片</li>
</ul>""",
                "items": """<h3>收藏项列表</h3>
<p>这里显示选中收藏夹中的所有收藏项。</p>
<p><strong>功能说明：</strong></p>
<ul>
<li>点击收藏项可打开链接或文件</li>
<li>右键点击可进行编辑或删除操作</li>
<li>支持批量选择模式（Ctrl+点击多选）</li>
<li>使用分类筛选可过滤显示特定类型的收藏项</li>
<li>点击左上角"←"按钮返回收藏夹列表</li>
</ul>
<p><strong>摘要功能：</strong></p>
<ul>
<li>每个收藏项卡片下方有"打开摘要"按钮</li>
<li>点击按钮可展开查看该收藏项的摘要内容</li>
<li>摘要内容过多时支持滚动浏览</li>
<li>再次点击"收起摘要"按钮可关闭摘要面板</li>
</ul>""",
                "add_item": """<h3>添加收藏项</h3>
<p>在此页面添加新的收藏项。</p>
<p><strong>添加链接：</strong></p>
<ul>
<li>输入网址链接</li>
<li>可选输入标题和分类</li>
<li>点击"自动获取"可自动填充标题和分类</li>
<li>支持主流网站封面自动获取（bilibili、抖音、YouTube、小红书等）</li>
</ul>
<p><strong>添加文件：</strong></p>
<ul>
<li>点击浏览按钮选择文件</li>
<li>或直接拖拽文件到指定区域</li>
<li>文件标题会自动填充</li>
</ul>
<p><strong>摘要设置：</strong></p>
<ul>
<li>在摘要输入框中手动输入收藏项的摘要内容</li>
<li>对于本地文件，点击"AI生成摘要"按钮可自动生成摘要</li>
<li>AI摘要使用本地Qwen2.5模型，支持流式输出</li>
<li>AI生成内容会自动对应当前应用语言</li>
</ul>
<p><strong>封面设置：</strong></p>
<ul>
<li>点击"选择封面"按钮可设置收藏项封面</li>
<li>支持从网络图片、本地图片或预设封面中选择</li>
<li>预设封面包含文档、图片、视频、音乐等16种类型</li>
<li>封面支持主题色适配</li>
</ul>""",
                "settings": """<h3>设置</h3>
<p>在此页面配置应用的各项设置。</p>
<p><strong>基础设置：</strong></p>
<ul>
<li>语言设置：支持中文和英文切换</li>
<li>主题设置：支持深色和浅色模式切换</li>
<li>主题色设置：可自定义应用主题颜色</li>
</ul>
<p><strong>背景管理：</strong></p>
<ul>
<li>大背景设置：可设置应用整体背景颜色或图片</li>
<li>大背景透明度：调整背景颜色的透明度（默认60%）</li>
<li>大背景图片：可选择本地图片作为背景</li>
<li>大背景图片透明度：调整背景图片的透明度</li>
<li>卡片区域背景设置：可设置卡片展示区域的背景颜色或图片</li>
<li>卡片区域透明度：调整卡片区域背景颜色的透明度（默认40%）</li>
<li>背景策略：支持拉伸、平铺、居中、填充、适应等模式</li>
</ul>
<p><strong>AI设置：</strong></p>
<ul>
<li>API地址：设置AI模型的API地址</li>
<li>API密钥：输入AI服务的访问密钥</li>
<li>模型选择：选择使用的AI模型</li>
<li>温度设置：调整AI生成内容的随机性</li>
<li>最大token数：限制AI生成内容的长度</li>
</ul>""",
                "mindmap": """<h3>思维导图视图</h3>
<p>思维导图以可视化方式展示收藏夹的层级结构。</p>
<p><strong>层级结构：</strong></p>
<ul>
<li><strong>中心节点</strong>：显示收藏夹名称（红色圆形卡片）</li>
<li><strong>第一级分支</strong>：收藏项的类别（绿色圆角矩形）</li>
<li><strong>第二级分支</strong>：按类型分类（链接/本地文件，绿色圆角矩形）</li>
<li><strong>第三级分支</strong>：具体的收藏项（蓝色矩形加三角形）</li>
</ul>
<p><strong>基础操作：</strong></p>
<ul>
<li>点击节点可展开或收起其子节点</li>
<li>默认展开到第二级（收藏项类型）</li>
<li>鼠标悬停在收藏项节点上可预览封面</li>
<li>点击收藏项节点可查看摘要内容</li>
<li>滚轮可缩放视图，按住鼠标左键可拖动视图</li>
</ul>
<p><strong>编辑模式：</strong></p>
<ul>
<li>点击顶部"编辑"按钮进入编辑模式</li>
<li>编辑模式下可以右键点击收藏项进行编辑或删除</li>
<li>再次点击按钮退出编辑模式</li>
</ul>
<p><strong>分类管理：</strong></p>
<ul>
<li>点击顶部"分类"按钮打开分类管理面板</li>
<li>可以添加、重命名或删除分类</li>
<li>删除分类后，该分类下的项目将设为"未分类"</li>
</ul>
<p><strong>筛选与搜索：</strong></p>
<ul>
<li>点击顶部"筛选"按钮可按分类筛选收藏项</li>
<li>使用搜索框可以按标题快速查找收藏项</li>
</ul>
<p><strong>密码保护：</strong></p>
<ul>
<li>在编辑模式下右键点击收藏项可设置密码</li>
<li>设置密码后，查看收藏项内容需要输入密码</li>
<li>可以修改或移除已设置的密码</li>
</ul>
<p><strong>拖拽功能：</strong></p>
<ul>
<li>在编辑模式下，可以拖拽收藏项到不同分类</li>
<li>拖拽后收藏项的分类将更新</li>
</ul>""",
            },
            "en": {
                "folders": """<h3>Folder List</h3>
<p>Welcome to the bookmark management app!</p>
<p><strong>Features:</strong></p>
<ul>
<li>Click a folder card to view its items</li>
<li>Right-click a folder to rename or delete</li>
<li>Use the search box to find folders quickly</li>
<li>Click the "+" button to add a new folder</li>
</ul>
<p><strong>Settings:</strong></p>
<ul>
<li>Click the menu button in the top-left corner to open settings sidebar</li>
<li>Settings include Display Settings and Language Settings</li>
<li>Language: Switch between Chinese and English</li>
<li>Theme: Switch between dark and light mode</li>
<li>Background Management: Set main background and card area background color or image</li>
</ul>""",
                "items": """<h3>Item List</h3>
<p>This shows all items in the selected folder.</p>
<p><strong>Features:</strong></p>
<ul>
<li>Click an item to open the link or file</li>
<li>Right-click to edit or delete</li>
<li>Supports multi-select mode (Ctrl+click)</li>
<li>Use category filter to show specific types</li>
<li>Click the "←" button to return to folder list</li>
</ul>
<p><strong>Summary Feature:</strong></p>
<ul>
<li>Each item card has an "Open Summary" button at the bottom</li>
<li>Click to expand and view the item's summary</li>
<li>Scrollable when summary content is too long</li>
<li>Click "Close Summary" button to collapse the panel</li>
</ul>""",
                "add_item": """<h3>Add Item</h3>
<p>Add new items here.</p>
<p><strong>Add Link:</strong></p>
<ul>
<li>Enter URL</li>
<li>Optional: enter title and category</li>
<li>Click "Auto Fetch" to fill title and category automatically</li>
<li>Supports auto cover fetching from mainstream websites (Bilibili, Douyin, YouTube, Xiaohongshu, etc.)</li>
</ul>
<p><strong>Add File:</strong></p>
<ul>
<li>Click browse button to select file</li>
<li>Or drag file to the drop area</li>
<li>File title is auto-filled</li>
</ul>
<p><strong>Summary Settings:</strong></p>
<ul>
<li>Manually enter summary content in the summary input box</li>
<li>For local files, click "AI Generate Summary" to auto-generate</li>
<li>AI summary uses local Qwen2.5 model with streaming output</li>
<li>AI-generated content automatically matches current app language</li>
</ul>
<p><strong>Cover Settings:</strong></p>
<ul>
<li>Click "Select Cover" to set item cover</li>
<li>Supports web images, local images, or preset covers</li>
<li>16 preset cover types including document, image, video, music, etc.</li>
<li>Covers support theme color adaptation</li>
</ul>""",
                "settings": """<h3>Settings</h3>
<p>Configure various app settings here.</p>
<p><strong>Basic Settings:</strong></p>
<ul>
<li>Language: Switch between Chinese and English</li>
<li>Theme: Switch between dark and light mode</li>
<li>Theme Color: Customize the app theme color</li>
</ul>
<p><strong>Background Management:</strong></p>
<ul>
<li>Main Background: Set app overall background color or image</li>
<li>Main Background Opacity: Adjust background color opacity (default 60%)</li>
<li>Main Background Image: Select local image as background</li>
<li>Main Background Image Opacity: Adjust background image opacity</li>
<li>Card Area Background: Set card display area background color or image</li>
<li>Card Area Opacity: Adjust card area background opacity (default 40%)</li>
<li>Background Strategy: Support stretch, tile, center, fill, fit modes</li>
</ul>
<p><strong>AI Settings:</strong></p>
<ul>
<li>API Address: Set AI model API address</li>
<li>API Key: Enter AI service access key</li>
<li>Model Selection: Select AI model to use</li>
<li>Temperature: Adjust randomness of AI-generated content</li>
<li>Max Tokens: Limit length of AI-generated content</li>
</ul>""",
                "mindmap": """<h3>Mind Map View</h3>
<p>The mind map visually displays the hierarchy of your favorites.</p>
<p><strong>Hierarchy:</strong></p>
<ul>
<li><strong>Center Node</strong>: Folder name (red circle)</li>
<li><strong>Level 1 Branches</strong>: Categories (green rounded rectangles)</li>
<li><strong>Level 2 Branches</strong>: Types (Links/Files, green rounded rectangles)</li>
<li><strong>Level 3 Branches</strong>: Individual items (blue rectangles with triangles)</li>
</ul>
<p><strong>Basic Operations:</strong></p>
<ul>
<li>Click a node to expand or collapse its children</li>
<li>Default expansion shows up to level 2 (types)</li>
<li>Hover over an item node to preview its cover</li>
<li>Click an item node to view its summary</li>
<li>Use mouse wheel to zoom, drag to pan the view</li>
</ul>
<p><strong>Edit Mode:</strong></p>
<ul>
<li>Click the "Edit" button at the top to enter edit mode</li>
<li>In edit mode, right-click items to edit or delete</li>
<li>Click the button again to exit edit mode</li>
</ul>
<p><strong>Category Management:</strong></p>
<ul>
<li>Click the "Categories" button at the top to open category management panel</li>
<li>Add, rename, or delete categories</li>
<li>When deleting a category, items in that category will be set to "Uncategorized"</li>
</ul>
<p><strong>Filter and Search:</strong></p>
<ul>
<li>Click the "Filter" button at the top to filter items by category</li>
<li>Use the search box to quickly find items by title</li>
</ul>
<p><strong>Password Protection:</strong></p>
<ul>
<li>In edit mode, right-click items to set passwords</li>
<li>After setting a password, entering it is required to view item content</li>
<li>Passwords can be changed or removed</li>
</ul>
<p><strong>Drag and Drop:</strong></p>
<ul>
<li>In edit mode, drag items to different categories</li>
<li>The item's category will be updated after dragging</li>
</ul>"""
            }
        }

        # 帮助按钮和侧边栏
        self._init_help_button()

        self.apply_theme()

        self.apply_language()

    def show_toast(self, message):
        toast = ToastNotification(self)
        toast.show_message(message)

    def load_config(self):
        """加载配置文件，返回包含 language, theme_color, dark_mode 和背景设置的字典"""
        config_path = "config.json"
        default_config = {
            "language": "zh",
            "theme_color": "#0078d7",
            "dark_mode": False,
            "theme_opacity": 0.4,
            "bg_image_path": "",
            "bg_image_opacity": 0.5,
            
            "bg_strategy": "stretch"
        }
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 合并默认值，保证所有字段存在
                for key in default_config:
                    if key not in data:
                        data[key] = default_config[key]
                # 加载背景设置
                background_manager.load_config(data)
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            background_manager.load_config(default_config)
            return default_config

    # ---------- 帮助按钮和侧边栏相关方法 ----------
    def _init_help_button(self):
        """初始化帮助按钮和思维导图按钮（可拖拽）"""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect

        self.help_btn = DraggableHelpButton(self)
        self.help_btn.setFixedSize(48, 48)
        self.help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 设置圆形样式
        self.help_btn.setStyleSheet("""
            QPushButton {
                border-radius: 24px;
                background-color: #0078d7;
                border: none;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004a85;
            }
        """)
        
        # 加载帮助图标
        icon_path = resource_path("resources/icons/help.svg")
        if os.path.exists(icon_path):
            self.help_btn.setIcon(QIcon(icon_path))
            self.help_btn.setIconSize(QSize(24, 24))  # 缩小图标尺寸
        else:
            self.help_btn.setText("?")
        
        self.help_btn.clicked.connect(self.open_help)
        self.help_btn.raise_()

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.help_btn.setGraphicsEffect(shadow)

        # 初始化思维导图按钮（在帮助按钮上方）
        self.mindmap_btn = DraggableHelpButton(self)
        self.mindmap_btn.setFixedSize(48, 48)
        self.mindmap_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 设置圆形样式，颜色跟随主题色
        theme_color = MainWindow.current_theme_color.name()
        self.mindmap_btn.setStyleSheet(f"""
            QPushButton {{
                border-radius: 24px;
                background-color: {theme_color};
                border: none;
            }}
            QPushButton:hover {{
                background-color: {theme_color}CC;
            }}
            QPushButton:pressed {{
                background-color: {theme_color}99;
            }}
        """)
        
        # 加载思维导图图标
        mindmap_icon_path = resource_path("resources/icons/mindmap.svg")
        if os.path.exists(mindmap_icon_path):
            self.mindmap_btn.setIcon(QIcon(mindmap_icon_path))
            self.mindmap_btn.setIconSize(QSize(24, 24))  # 缩小图标尺寸
        else:
            self.mindmap_btn.setText("🗺️")
        
        self.mindmap_btn.clicked.connect(self.open_mindmap)
        self.mindmap_btn.raise_()

        # 添加阴影效果
        mindmap_shadow = QGraphicsDropShadowEffect()
        mindmap_shadow.setBlurRadius(10)
        mindmap_shadow.setOffset(2, 2)
        mindmap_shadow.setColor(QColor(0, 0, 0, 150))
        self.mindmap_btn.setGraphicsEffect(mindmap_shadow)

        # 初始位置（右下角）
        self._update_help_button_position()

    def _update_help_button_position(self):
        """更新帮助按钮和思维导图按钮位置（始终在右下角）"""
        margin = 20
        button_size = self.help_btn.width()
        spacing = 10  # 两个按钮之间的间距
        
        # 帮助按钮位置（右下角）
        help_x = self.width() - button_size - margin
        help_y = self.height() - button_size - margin
        self.help_btn.move(help_x, help_y)
        self.help_btn.raise_()
        
        # 思维导图按钮位置（在帮助按钮上方）
        if hasattr(self, 'mindmap_btn'):
            mindmap_x = help_x
            mindmap_y = help_y - button_size - spacing
            self.mindmap_btn.move(mindmap_x, mindmap_y)
            self.mindmap_btn.raise_()

    def resizeEvent(self, event):
        """窗口大小改变时更新帮助按钮位置"""
        super().resizeEvent(event)
        if hasattr(self, 'help_btn'):
            self._update_help_button_position()

    def paintEvent(self, event):
        """重写paintEvent来渲染背景"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 使用背景管理器渲染大背景
        background_manager.render_main_background(
            painter,
            self.rect(),
            MainWindow.current_theme_color,
            MainWindow.current_dark_mode
        )
        
        painter.end()

    def open_help(self):
        """打开帮助侧边栏"""
        if hasattr(self, 'help_overlay') and self.help_overlay is not None:
            self.close_help()
            return

        # 遮罩
        self.help_overlay = QWidget(self)
        self.help_overlay.setGeometry(0, 0, self.width(), self.height())
        self.help_overlay.setStyleSheet("background-color: rgba(0,0,0,0.3);")
        self.help_overlay.mousePressEvent = lambda e: self.close_help()
        self.help_overlay.raise_()
        self.help_overlay.show()

        # 创建帮助侧边栏
        sidebar = self._create_help_sidebar()
        sidebar.setParent(self)
        sidebar.setFixedWidth(300)
        sidebar.setGeometry(self.width(), 0, 300, self.height())
        sidebar.raise_()
        sidebar.show()

        self.help_sidebar = sidebar

        # 移入动画
        anim = QPropertyAnimation(sidebar, b"geometry")
        anim.setDuration(300)
        anim.setStartValue(QRect(self.width(), 0, 300, self.height()))
        anim.setEndValue(QRect(self.width() - 300, 0, 300, self.height()))
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self.help_anim = anim

    def close_help(self):
        """关闭帮助侧边栏"""
        if not hasattr(self, 'help_sidebar') or self.help_sidebar is None:
            return

        sidebar = self.help_sidebar
        
        # 移出动画
        anim = QPropertyAnimation(sidebar, b"geometry")
        anim.setDuration(300)
        anim.setStartValue(QRect(self.width() - 300, 0, 300, self.height()))
        anim.setEndValue(QRect(self.width(), 0, 300, self.height()))
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.finished.connect(self._cleanup_help)
        anim.start()
        self.help_anim = anim

    def _cleanup_help(self):
        """清理帮助侧边栏"""
        if hasattr(self, 'help_sidebar') and self.help_sidebar:
            self.help_sidebar.deleteLater()
            self.help_sidebar = None
        if hasattr(self, 'help_overlay') and self.help_overlay:
            self.help_overlay.deleteLater()
            self.help_overlay = None
        if hasattr(self, 'help_anim'):
            self.help_anim = None

    def _create_help_sidebar(self):
        """创建帮助侧边栏（可拖拽）"""
        sidebar = DraggableHelpSidebar(self)
        
        bg_color = "#f5f5f5" if not MainWindow.current_dark_mode else "#2b2b2b"
        text_color = "#333" if not MainWindow.current_dark_mode else "#fff"
        border_color = "#ccc" if not MainWindow.current_dark_mode else "#444"
        
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                color: {text_color};
                border-left: 1px solid {border_color};
            }}
            QLabel {{
                color: {text_color};
            }}
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setStyleSheet(f"background-color: {bg_color}; border-bottom: 1px solid {border_color};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(10)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                font-size: 18px;
                color: {text_color};
            }}
            QPushButton:hover {{
                background-color: rgba(0,0,0,0.1);
                border-radius: 50%;
            }}
        """)
        close_btn.clicked.connect(self.close_help)

        title = QLabel(self.strings[self.current_lang].get("help_title", "帮助"))
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        header_layout.addWidget(close_btn)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addWidget(header)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)

        current_page = self._get_current_page()
        lang = self.current_lang
        content_list = self.help_content.get(lang, self.help_content.get("zh", {}))
        content_html = content_list.get(current_page, "")

        if not content_html:
            content_html = "<p>该页面暂无帮助信息。</p>"

        content_label = QLabel(content_html)
        content_label.setStyleSheet(f"font-size: 14px; line-height: 1.6; color: {text_color};")
        content_label.setWordWrap(True)
        content_label.setOpenExternalLinks(True)

        content_layout.addWidget(content_label)
        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

        return sidebar

    def _get_current_page(self):
        """获取当前页面标识"""
        index = self.stacked_widget.currentIndex()
        if index == 0:
            return "folders"
        elif index == 1:
            return "items"
        elif index == 2:
            return "add_item"
        elif index == 3:
            return "mindmap"
        return "folders"

    # ---------- 设置侧边栏相关方法 ----------
    def open_settings(self):
        if self.settings_overlay is not None:
            self.close_all_settings()
            return

        self.settings_overlay = QWidget(self)
        self.settings_overlay.setGeometry(0, 0, self.width(), self.height())
        self.settings_overlay.setStyleSheet("background-color: rgba(0,0,0,0.3);")
        self.settings_overlay.mousePressEvent = lambda e: self.close_all_settings()
        self.settings_overlay.raise_()
        self.settings_overlay.show()

        menu_sidebar = self.create_settings_menu()
        menu_sidebar.setParent(self)
        menu_sidebar.setFixedWidth(280)
        menu_sidebar.setGeometry(self.width(), 0, 280, self.height())
        menu_sidebar.raise_()
        menu_sidebar.show()

        self.settings_sidebars = [menu_sidebar]
        self.show_sidebar_animation(menu_sidebar, start_x=self.width(), end_x=self.width() - 280)
        self.apply_theme()

    def close_all_settings(self):
        """关闭所有设置侧边栏和遮罩"""
        for sidebar in self.settings_sidebars:
            sidebar.close()
        self.settings_sidebars.clear()
        if self.settings_overlay:
            self.settings_overlay.close()
            self.settings_overlay = None
        # 停止所有动画（如果有）
        for anim in self.settings_animations:
            anim.stop()
        self.settings_animations.clear()

    def create_settings_menu(self):
        sidebar = QWidget(self)
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-right: 1px solid #ccc;
            }
            QPushButton {
                text-align: left;
                padding: 12px 20px;
                border: none;
                border-bottom: 1px solid #ddd;
                background-color: transparent;
                font-size: 14px;
                qproperty-iconAlignment: AlignLeft;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题
        title = QLabel(self.strings[self.current_lang]["settings_title"])
        title.setStyleSheet("padding: 16px 20px; font-size: 18px; font-weight: bold; border-bottom: 2px solid #ccc;")
        layout.addWidget(title)

        # 选项按钮（带箭头）
        btn_display = QPushButton(self.strings[self.current_lang]["display_settings"])
        btn_display.setIcon(QIcon(resource_path("resources/icons/arrow_left.svg")))
        btn_display.setIconSize(QSize(16, 16))
        btn_display.setObjectName("settings_menu_btn")
        btn_display.clicked.connect(lambda: self.on_settings_menu_btn_clicked(btn_display, "display"))
        layout.addWidget(btn_display)

        btn_language = QPushButton(self.strings[self.current_lang]["language"])
        btn_language.setIcon(QIcon(resource_path("resources/icons/arrow_left.svg")))
        btn_language.setIconSize(QSize(16, 16))
        btn_language.setObjectName("settings_menu_btn")
        btn_language.clicked.connect(lambda: self.on_settings_menu_btn_clicked(btn_language, "language"))
        layout.addWidget(btn_language)

        btn_about = QPushButton(self.strings[self.current_lang]["about"])
        btn_about.setIcon(QIcon(resource_path("resources/icons/arrow_left.svg")))
        btn_about.setIconSize(QSize(16, 16))
        btn_about.setObjectName("settings_menu_btn")
        btn_about.clicked.connect(lambda: self.on_settings_menu_btn_clicked(btn_about, "about"))
        layout.addWidget(btn_about)

        # 保存按钮引用用于动画控制
        self.settings_menu_btns = {
            "display": btn_display,
            "language": btn_language,
            "about": btn_about
        }

        layout.addStretch()
        return sidebar

    def on_settings_menu_btn_clicked(self, btn, option_name):
        """处理设置菜单按钮点击（包含箭头动画）"""
        # 如果当前有子侧边栏
        if len(self.settings_sidebars) >= 2:
            current_sub = self.settings_sidebars[-1]
            if current_sub.property("option_name") == option_name:
                # 相同选项：收回动画，箭头旋转回左
                self._rotate_button_icon(btn, 0)  # 旋转回0度（左箭头）
                self.remove_last_sidebar()
                return
            else:
                # 不同选项：直接关闭当前子，不保留动画
                current_sub.close()
                self.settings_sidebars.pop()
                for anim in self.settings_animations:
                    anim.stop()
                self.settings_animations.clear()
                # 重置所有按钮箭头
                for b in self.settings_menu_btns.values():
                    self._rotate_button_icon(b, 0)

        # 创建新的子侧边栏，箭头旋转180度（右箭头）
        self._rotate_button_icon(btn, 180)
        self.toggle_sub_sidebar(option_name)

    def _rotate_button_icon(self, btn, angle):
        """旋转按钮图标"""
        icon_path = resource_path("resources/icons/arrow_left.svg")
        if not os.path.exists(icon_path):
            return
        
        pixmap = QPixmap(icon_path)
        if pixmap.isNull():
            return
        
        # 获取当前旋转角度
        start_angle = btn._current_rotation if hasattr(btn, '_current_rotation') else 0
        end_angle = angle
        
        # 如果已经是目标角度，直接设置
        if start_angle == end_angle:
            return
        
        btn._current_rotation = end_angle
        
        # 创建动画
        step = 10  # 每次旋转的角度
        steps = abs(end_angle - start_angle) // step
        if steps == 0:
            steps = 1
        
        def rotate_step(current_step):
            if current_step > steps:
                return
            current_angle = start_angle + (end_angle - start_angle) * (current_step / steps)
            transform = QTransform().rotate(current_angle)
            rotated_pixmap = pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            btn.setIcon(QIcon(rotated_pixmap))
            QTimer.singleShot(10, lambda: rotate_step(current_step + 1))
        
        rotate_step(0)

    def on_display_settings_clicked(self):
        """处理点击“显示设置”（兼容旧调用）"""
        btn = self.settings_menu_btns.get("display")
        if btn:
            self.on_settings_menu_btn_clicked(btn, "display")

    def on_about_settings_clicked(self):
        """处理点击“关于”（兼容旧调用）"""
        btn = self.settings_menu_btns.get("about")
        if btn:
            self.on_settings_menu_btn_clicked(btn, "about")

    def toggle_sub_sidebar(self, option_name):
        # 如果当前有子侧边栏
        if len(self.settings_sidebars) >= 2:
            current_sub = self.settings_sidebars[-1]
            if current_sub.property("option_name") == option_name:
                # 相同选项：收回动画
                self.remove_last_sidebar()
                return
            else:
                # 不同选项：直接关闭当前子，不保留动画
                current_sub.close()
                self.settings_sidebars.pop()
                for anim in self.settings_animations:
                    anim.stop()
                self.settings_animations.clear()

        # 创建新的子侧边栏
        parent_sidebar = self.settings_sidebars[-1]
        if option_name == "display":
            sub_sidebar = self.create_display_sidebar()
        elif option_name == "language": 
            sub_sidebar = self.create_language_sidebar()
        else:
            sub_sidebar = self.create_about_sidebar()
        sub_sidebar.setProperty("option_name", option_name)

        sub_sidebar.setParent(self)
        sub_sidebar.setFixedWidth(280)
        parent_rect = parent_sidebar.geometry()
        start_x = parent_rect.right()                  # 从父右侧外部开始
        end_x = parent_rect.left() - sub_sidebar.width()  # 停在父左侧

        sub_sidebar.setGeometry(start_x, parent_rect.y(), sub_sidebar.width(), self.height())
        sub_sidebar.stackUnder(parent_sidebar)         # 关键：确保父在子上方
        sub_sidebar.show()

        self.settings_sidebars.append(sub_sidebar)
        self.show_sidebar_animation(sub_sidebar, start_x=start_x, end_x=end_x)
        self.apply_theme()
    def remove_last_sidebar(self):
        """移除最内层侧边栏（收回）"""
        if len(self.settings_sidebars) <= 1:
            return  # 不能移除主菜单
        sidebar = self.settings_sidebars.pop()
        self.hide_sidebar_animation(sidebar, callback=sidebar.close)

    def create_display_sidebar(self):
        sidebar = QWidget(self)
        sidebar.setFixedWidth(280)
        
        dark = MainWindow.current_dark_mode
        bg_color = "#2b2b2b" if dark else "#ffffff"
        text_color = "#ffffff" if dark else "#333333"
        border_color = "#555555" if dark else "#cccccc"
        alt_bg = "#3c3c3c" if dark else "#f5f5f5"
        
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-left: 1px solid {border_color};
            }}
            QLabel {{
                padding: 8px 16px;
                color: {text_color};
            }}
            QComboBox, QPushButton {{
                margin: 4px 16px;
                padding: 6px;
                border: 1px solid {border_color};
                border-radius: 4px;
                background-color: {alt_bg};
                color: {text_color};
            }}
            QPushButton:hover {{
                background-color: rgba(0,0,0,0.1);
            }}
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                width: 6px;
                background-color: {alt_bg};
            }}
            QScrollBar::handle:vertical {{
                background-color: {border_color};
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #888;
            }}
            QCheckBox {{
                margin: 4px 16px;
                color: {text_color};
            }}
            QSlider::groove:horizontal {{
                height: 4px;
                background: {border_color};
                border-radius: 2px;
                margin: 4px 16px;
            }}
            QSlider::handle:horizontal {{
                background: {MainWindow.current_theme_color.name()};
                width: 14px;
                height: 14px;
                border-radius: 7px;
                margin: -5px 0;
            }}
            QLineEdit {{
                margin: 4px 16px;
                padding: 4px 6px;
                border: 1px solid {border_color};
                border-radius: 3px;
                background-color: {alt_bg};
                color: {text_color};
                font-size: 12px;
                max-width: 50px;
            }}
        """)
        
        # 创建滚动区域
        scroll_area = QScrollArea(sidebar)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 创建内容区域
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        scroll_area.setWidget(content_widget)

        # 标题（带返回指示）
        title = QLabel(self.strings[self.current_lang]["display_title"])
        title.setStyleSheet("padding: 16px; font-size: 16px; font-weight: bold; border-bottom: 1px solid #ddd;")
        layout.addWidget(title)

        # 显示模式
        layout.addWidget(QLabel(self.strings[self.current_lang]["display_mode"]))
        mode_combo = QComboBox()
        mode_combo.addItems([
            self.strings[self.current_lang]["light_mode"],
            self.strings[self.current_lang]["dark_mode"]
        ])
        mode_combo.setCurrentIndex(1 if MainWindow.current_dark_mode else 0)
        mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        layout.addWidget(mode_combo)

        # 主题色
        layout.addWidget(QLabel(self.strings[self.current_lang]["theme_color"]))
        color_btn = QPushButton(self.strings[self.current_lang]["select_color"])
        # 给颜色按钮设置 objectName，便于主题识别（见下文说明）
        color_btn.setObjectName("color_picker_btn")
        color_btn.clicked.connect(self.on_color_picker_clicked)

        color_preview = QLabel()
        color_preview.setFixedHeight(20)
        color_preview.setStyleSheet(f"background-color: {MainWindow.current_theme_color.name()}; border: 1px solid #888;")
        color_preview.setProperty("color_preview", True)
        layout.addWidget(color_preview)
        layout.addWidget(color_btn)

        # 背景设置分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("margin: 10px 16px; color: #ddd;")
        layout.addWidget(separator)

        # ===== 大背景设置 =====
        bg_title = QLabel(self.strings[self.current_lang]["bg_settings"])
        bg_title.setStyleSheet("padding: 8px 16px; font-size: 14px; font-weight: bold;")
        layout.addWidget(bg_title)

        # 大背景主题色透明度
        layout.addWidget(QLabel(self.strings[self.current_lang]["main_theme_opacity"]))
        main_opacity_row = QHBoxLayout()
        self.main_theme_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.main_theme_opacity_slider.setRange(0, 100)
        self.main_theme_opacity_slider.setValue(int(background_manager.main_theme_opacity * 100))
        self.main_theme_opacity_slider.setFixedWidth(180)
        self.main_theme_opacity_slider.valueChanged.connect(self.on_main_theme_opacity_changed)
        
        self.main_theme_opacity_edit = QLineEdit()
        self.main_theme_opacity_edit.setText(f"{int(background_manager.main_theme_opacity * 100)}")
        self.main_theme_opacity_edit.setFixedWidth(50)
        self.main_theme_opacity_edit.editingFinished.connect(self.on_main_theme_opacity_edit_finished)
        
        main_opacity_row.addWidget(self.main_theme_opacity_slider)
        main_opacity_row.addWidget(self.main_theme_opacity_edit)
        layout.addLayout(main_opacity_row)

        # 大背景图片选择
        layout.addWidget(QLabel(self.strings[self.current_lang]["main_bg_image"]))
        main_bg_image_row = QHBoxLayout()
        self.main_bg_image_btn = QPushButton(self.strings[self.current_lang]["select_bg_image"])
        self.main_bg_image_btn.clicked.connect(self.on_select_main_bg_image_clicked)
        main_bg_image_row.addWidget(self.main_bg_image_btn)
        
        if background_manager.main_bg_image_path:
            self.remove_main_bg_btn = QPushButton(self.strings[self.current_lang]["remove_bg_image"])
            self.remove_main_bg_btn.clicked.connect(self.on_remove_main_bg_image_clicked)
            main_bg_image_row.addWidget(self.remove_main_bg_btn)
        layout.addLayout(main_bg_image_row)

        # 大背景图片透明度
        layout.addWidget(QLabel(self.strings[self.current_lang]["main_bg_image_opacity"]))
        main_bg_opacity_row = QHBoxLayout()
        self.main_bg_image_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.main_bg_image_opacity_slider.setRange(0, 100)
        self.main_bg_image_opacity_slider.setValue(int(background_manager.main_bg_image_opacity * 100))
        self.main_bg_image_opacity_slider.setFixedWidth(180)
        self.main_bg_image_opacity_slider.valueChanged.connect(self.on_main_bg_image_opacity_changed)
        
        self.main_bg_image_opacity_edit = QLineEdit()
        self.main_bg_image_opacity_edit.setText(f"{int(background_manager.main_bg_image_opacity * 100)}")
        self.main_bg_image_opacity_edit.setFixedWidth(50)
        self.main_bg_image_opacity_edit.editingFinished.connect(self.on_main_bg_image_opacity_edit_finished)
        
        main_bg_opacity_row.addWidget(self.main_bg_image_opacity_slider)
        main_bg_opacity_row.addWidget(self.main_bg_image_opacity_edit)
        layout.addLayout(main_bg_opacity_row)

        # 大背景策略
        layout.addWidget(QLabel(self.strings[self.current_lang]["main_bg_strategy"]))
        self.main_bg_strategy_combo = QComboBox()
        strategies = [
            ("stretch", self.strings[self.current_lang]["bg_stretch"]),
            ("tile", self.strings[self.current_lang]["bg_tile"]),
            ("center", self.strings[self.current_lang]["bg_center"]),
            ("fill", self.strings[self.current_lang]["bg_fill"]),
            ("fit", self.strings[self.current_lang]["bg_fit"])
        ]
        for key, label in strategies:
            self.main_bg_strategy_combo.addItem(label, key)
            if key == background_manager.main_bg_strategy:
                self.main_bg_strategy_combo.setCurrentText(label)
        self.main_bg_strategy_combo.currentIndexChanged.connect(self.on_main_bg_strategy_changed)
        layout.addWidget(self.main_bg_strategy_combo)

        # ===== 卡片区域背景设置 =====
        card_separator = QFrame()
        card_separator.setFrameShape(QFrame.Shape.HLine)
        card_separator.setStyleSheet("margin: 10px 16px; color: #ddd;")
        layout.addWidget(card_separator)

        card_bg_title = QLabel(self.strings[self.current_lang]["card_bg_settings"])
        card_bg_title.setStyleSheet("padding: 8px 16px; font-size: 14px; font-weight: bold;")
        layout.addWidget(card_bg_title)

        # 卡片区域主题色透明度
        layout.addWidget(QLabel(self.strings[self.current_lang]["card_theme_opacity"]))
        card_opacity_row = QHBoxLayout()
        self.card_theme_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.card_theme_opacity_slider.setRange(0, 100)
        self.card_theme_opacity_slider.setValue(int(background_manager.card_theme_opacity * 100))
        self.card_theme_opacity_slider.setFixedWidth(180)
        self.card_theme_opacity_slider.valueChanged.connect(self.on_card_theme_opacity_changed)
        
        self.card_theme_opacity_edit = QLineEdit()
        self.card_theme_opacity_edit.setText(f"{int(background_manager.card_theme_opacity * 100)}")
        self.card_theme_opacity_edit.setFixedWidth(50)
        self.card_theme_opacity_edit.editingFinished.connect(self.on_card_theme_opacity_edit_finished)
        
        card_opacity_row.addWidget(self.card_theme_opacity_slider)
        card_opacity_row.addWidget(self.card_theme_opacity_edit)
        layout.addLayout(card_opacity_row)

        # 卡片区域背景图片选择
        layout.addWidget(QLabel(self.strings[self.current_lang]["card_bg_image"]))
        card_bg_image_row = QHBoxLayout()
        self.card_bg_image_btn = QPushButton(self.strings[self.current_lang]["select_bg_image"])
        self.card_bg_image_btn.clicked.connect(self.on_select_card_bg_image_clicked)
        card_bg_image_row.addWidget(self.card_bg_image_btn)
        
        if background_manager.card_bg_image_path:
            self.remove_card_bg_btn = QPushButton(self.strings[self.current_lang]["remove_bg_image"])
            self.remove_card_bg_btn.clicked.connect(self.on_remove_card_bg_image_clicked)
            card_bg_image_row.addWidget(self.remove_card_bg_btn)
        layout.addLayout(card_bg_image_row)

        # 卡片区域背景图片透明度
        layout.addWidget(QLabel(self.strings[self.current_lang]["card_bg_image_opacity"]))
        card_bg_opacity_row = QHBoxLayout()
        self.card_bg_image_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.card_bg_image_opacity_slider.setRange(0, 100)
        self.card_bg_image_opacity_slider.setValue(int(background_manager.card_bg_image_opacity * 100))
        self.card_bg_image_opacity_slider.setFixedWidth(180)
        self.card_bg_image_opacity_slider.valueChanged.connect(self.on_card_bg_image_opacity_changed)
        
        self.card_bg_image_opacity_edit = QLineEdit()
        self.card_bg_image_opacity_edit.setText(f"{int(background_manager.card_bg_image_opacity * 100)}")
        self.card_bg_image_opacity_edit.setFixedWidth(50)
        self.card_bg_image_opacity_edit.editingFinished.connect(self.on_card_bg_image_opacity_edit_finished)
        
        card_bg_opacity_row.addWidget(self.card_bg_image_opacity_slider)
        card_bg_opacity_row.addWidget(self.card_bg_image_opacity_edit)
        layout.addLayout(card_bg_opacity_row)

        # 卡片区域背景策略
        layout.addWidget(QLabel(self.strings[self.current_lang]["card_bg_strategy"]))
        self.card_bg_strategy_combo = QComboBox()
        for key, label in strategies:
            self.card_bg_strategy_combo.addItem(label, key)
            if key == background_manager.card_bg_strategy:
                self.card_bg_strategy_combo.setCurrentText(label)
        self.card_bg_strategy_combo.currentIndexChanged.connect(self.on_card_bg_strategy_changed)
        layout.addWidget(self.card_bg_strategy_combo)

        layout.addStretch()
        
        # 将滚动区域添加到侧边栏
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        sidebar_layout.addWidget(scroll_area)
        
        return sidebar

    def create_about_sidebar(self):
        sidebar = QWidget(self)
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-left: 1px solid #ccc;
            }
            QLabel {
                padding: 8px 16px;
            }
            a {
                color: #0078d7;
                text-decoration: none;
            }
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel(self.strings[self.current_lang]["about_title"])
        title.setStyleSheet("padding: 16px; font-size: 16px; font-weight: bold; border-bottom: 1px solid #ddd;")
        layout.addWidget(title)

        version_label = QLabel(self.strings[self.current_lang]["version"])
        layout.addWidget(version_label)

        url_label = QLabel(
            f'<a href="https://github.com/furina-2019/Favorites-Manager">{self.strings[self.current_lang]["open_source"]}</a>'
        )
        url_label.setOpenExternalLinks(True)
        url_label.setStyleSheet("padding: 8px 16px;")
        layout.addWidget(url_label)

        layout.addStretch()
        return sidebar

    def show_sidebar_animation(self, widget, start_x, end_x):
        """水平滑动动画（从 start_x 到 end_x）"""
        anim = QPropertyAnimation(widget, b"geometry")
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        start_geom = widget.geometry()
        start_geom.moveLeft(start_x)
        end_geom = widget.geometry()
        end_geom.moveLeft(end_x)
        anim.setStartValue(start_geom)
        anim.setEndValue(end_geom)
        anim.start()
        self.settings_animations.append(anim)
        anim.finished.connect(lambda: self.settings_animations.remove(anim))

    def hide_sidebar_animation(self, widget, callback=None):
        if len(self.settings_sidebars) >= 2:
            parent = self.settings_sidebars[-2]
            # 终点：父菜单的右侧 + 自身宽度（完全移出右侧）
            end_x = parent.geometry().right() + widget.width()
        else:
            end_x = self.width()   # 移出窗口右侧
        anim = QPropertyAnimation(widget, b"geometry")
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        start_geom = widget.geometry()
        end_geom = widget.geometry()
        end_geom.moveLeft(end_x)
        anim.setStartValue(start_geom)
        anim.setEndValue(end_geom)
        anim.start()
        self.settings_animations.append(anim)
        if callback:
            anim.finished.connect(callback)
        anim.finished.connect(lambda: self.settings_animations.remove(anim))

    # ---------- 设置功能响应 ----------
    def on_mode_changed(self, index):
        dark_mode = (index == 1)
        MainWindow.current_dark_mode = dark_mode
        self.apply_theme()
        self.save_config()

    def on_color_picker_clicked(self):
        color = QColorDialog.getColor(MainWindow.current_theme_color, self,
                                      self.strings[self.current_lang]["select_theme_color"])
        if color.isValid():
            MainWindow.current_theme_color = color
            self.apply_theme()
            self.save_config()
            # 更新侧边栏中的颜色预览
            for sidebar in self.settings_sidebars:
                for child in sidebar.findChildren(QLabel):
                    if child.property("color_preview"):
                        child.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #888;")

    # ---------- 大背景设置相关方法 ----------
    def on_main_theme_opacity_changed(self, value):
        """大背景主题色透明度滑块变化"""
        background_manager.main_theme_opacity = value / 100.0
        self.main_theme_opacity_edit.setText(str(value))
        self.update_background()
        self.save_config()

    def on_main_theme_opacity_edit_finished(self):
        """大背景主题色透明度文本框编辑完成"""
        try:
            value = int(self.main_theme_opacity_edit.text())
            value = max(0, min(100, value))
            background_manager.main_theme_opacity = value / 100.0
            self.main_theme_opacity_slider.setValue(value)
            self.update_background()
            self.save_config()
        except ValueError:
            self.main_theme_opacity_edit.setText(str(int(background_manager.main_theme_opacity * 100)))

    def on_select_main_bg_image_clicked(self):
        """选择大背景图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.strings[self.current_lang]["select_bg_image"],
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if file_path:
            background_manager.main_bg_image_path = file_path
            self.update_background()
            self.save_config()
            # 更新UI
            if hasattr(self, 'remove_main_bg_btn'):
                self.remove_main_bg_btn.deleteLater()
            self.remove_main_bg_btn = QPushButton(self.strings[self.current_lang]["remove_bg_image"])
            self.remove_main_bg_btn.clicked.connect(self.on_remove_main_bg_image_clicked)
            # 将按钮添加到布局中
            for sidebar in self.settings_sidebars:
                for child in sidebar.findChildren(QHBoxLayout):
                    if self.main_bg_image_btn in [child.itemAt(i).widget() for i in range(child.count())]:
                        child.addWidget(self.remove_main_bg_btn)
                        break

    def on_remove_main_bg_image_clicked(self):
        """移除大背景图片"""
        background_manager.main_bg_image_path = ""
        self.update_background()
        self.save_config()
        if hasattr(self, 'remove_main_bg_btn'):
            self.remove_main_bg_btn.deleteLater()
            delattr(self, 'remove_main_bg_btn')

    def on_main_bg_image_opacity_changed(self, value):
        """大背景图片透明度滑块变化"""
        background_manager.main_bg_image_opacity = value / 100.0
        self.main_bg_image_opacity_edit.setText(str(value))
        self.update_background()
        self.save_config()

    def on_main_bg_image_opacity_edit_finished(self):
        """大背景图片透明度文本框编辑完成"""
        try:
            value = int(self.main_bg_image_opacity_edit.text())
            value = max(0, min(100, value))
            background_manager.main_bg_image_opacity = value / 100.0
            self.main_bg_image_opacity_slider.setValue(value)
            self.update_background()
            self.save_config()
        except ValueError:
            self.main_bg_image_opacity_edit.setText(str(int(background_manager.main_bg_image_opacity * 100)))

    def on_main_bg_strategy_changed(self, index):
        """大背景策略变化"""
        strategy = self.main_bg_strategy_combo.currentData()
        background_manager.main_bg_strategy = strategy
        self.update_background()
        self.save_config()

    # ---------- 卡片区域背景设置相关方法 ----------
    def on_card_bg_enabled_changed(self, state):
        """卡片区域背景启用状态变化"""
        background_manager.card_bg_enabled = (state == Qt.CheckState.Checked)
        self.update_background()
        self.save_config()

    def on_card_theme_opacity_changed(self, value):
        """卡片区域主题色透明度滑块变化"""
        background_manager.card_theme_opacity = value / 100.0
        self.card_theme_opacity_edit.setText(str(value))
        self.update_background()
        self.save_config()

    def on_card_theme_opacity_edit_finished(self):
        """卡片区域主题色透明度文本框编辑完成"""
        try:
            value = int(self.card_theme_opacity_edit.text())
            value = max(0, min(100, value))
            background_manager.card_theme_opacity = value / 100.0
            self.card_theme_opacity_slider.setValue(value)
            self.update_background()
            self.save_config()
        except ValueError:
            self.card_theme_opacity_edit.setText(str(int(background_manager.card_theme_opacity * 100)))

    def on_select_card_bg_image_clicked(self):
        """选择卡片区域背景图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.strings[self.current_lang]["select_bg_image"],
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if file_path:
            background_manager.card_bg_image_path = file_path
            self.update_background()
            self.save_config()
            # 更新UI
            if hasattr(self, 'remove_card_bg_btn'):
                self.remove_card_bg_btn.deleteLater()
            self.remove_card_bg_btn = QPushButton(self.strings[self.current_lang]["remove_bg_image"])
            self.remove_card_bg_btn.clicked.connect(self.on_remove_card_bg_image_clicked)
            # 将按钮添加到布局中
            for sidebar in self.settings_sidebars:
                for child in sidebar.findChildren(QHBoxLayout):
                    if self.card_bg_image_btn in [child.itemAt(i).widget() for i in range(child.count())]:
                        child.addWidget(self.remove_card_bg_btn)
                        break

    def on_remove_card_bg_image_clicked(self):
        """移除卡片区域背景图片"""
        background_manager.card_bg_image_path = ""
        self.update_background()
        self.save_config()
        if hasattr(self, 'remove_card_bg_btn'):
            self.remove_card_bg_btn.deleteLater()
            delattr(self, 'remove_card_bg_btn')

    def on_card_bg_image_opacity_changed(self, value):
        """卡片区域背景图片透明度滑块变化"""
        background_manager.card_bg_image_opacity = value / 100.0
        self.card_bg_image_opacity_edit.setText(str(value))
        self.update_background()
        self.save_config()

    def on_card_bg_image_opacity_edit_finished(self):
        """卡片区域背景图片透明度文本框编辑完成"""
        try:
            value = int(self.card_bg_image_opacity_edit.text())
            value = max(0, min(100, value))
            background_manager.card_bg_image_opacity = value / 100.0
            self.card_bg_image_opacity_slider.setValue(value)
            self.update_background()
            self.save_config()
        except ValueError:
            self.card_bg_image_opacity_edit.setText(str(int(background_manager.card_bg_image_opacity * 100)))

    def on_card_bg_strategy_changed(self, index):
        """卡片区域背景策略变化"""
        strategy = self.card_bg_strategy_combo.currentData()
        background_manager.card_bg_strategy = strategy
        self.update_background()
        self.save_config()

    def update_background(self):
        """更新背景"""
        self.apply_theme()
        self.update_folder_cards_background()
        self.update_item_cards_background()

    def update_folder_cards_background(self):
        """更新收藏夹卡片背景"""
        for card in self.findChildren(FolderCard):
            card.update_theme(MainWindow.current_dark_mode)

    def update_item_cards_background(self):
        """更新收藏项卡片背景"""
        for card in self.findChildren(ItemCard):
            card.update_theme(MainWindow.current_dark_mode)

    def apply_theme(self):
        color = MainWindow.current_theme_color
        color_str = color.name()
        dark = MainWindow.current_dark_mode
        bg_color = "#2b2b2b" if dark else "#ffffff"
        text_color = "#ffffff" if dark else "#000000"
        alt_bg = "#3c3c3c" if dark else "#f5f5f5"
        border_color = "#555" if dark else "#ccc"
        hover_bg = f"{color_str}40"

        # 主窗口背景设置为透明（自定义背景通过paintEvent渲染）
        self.setStyleSheet(f"QMainWindow {{ background-color: transparent; color: {text_color}; }}")

        # 三个主要页面设置为透明，让自定义背景显示出来
        for page in (self.folders_page, self.items_page, self.add_item_page):
            page.setStyleSheet(f"QWidget#page {{ background-color: transparent; color: {text_color}; }}")

        # 搜索框
        search_box_style = f"""
            QLineEdit {{
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 6px;
                background-color: {bg_color};
                color: {text_color};
            }}
            QLineEdit:focus {{
                border-bottom: 3px solid {color_str};
            }}
        """
        for obj_name in ("folder_search", "item_search", "link_url_edit", "link_title_edit",
                         "link_category_edit", "file_title_edit", "file_category_edit"):
            widget = getattr(self, obj_name, None)
            if widget:
                widget.setStyleSheet(search_box_style)

        # 普通按钮（包括设置按钮）：背景主题色，文字颜色随深浅模式
        button_style = f"""
            QPushButton {{
                border: 2px solid {color_str};
                border-radius: 4px;
                padding: 6px 12px;
                background-color: {color_str};
                color: {text_color};
            }}
            QPushButton:hover {{
                background-color: {color_str}80;
            }}
        """
        for widget in self.findChildren(QPushButton):
            # 跳过侧边栏内的菜单按钮（它们有透明背景）
            if any(widget.isAncestorOf(sb) for sb in self.settings_sidebars):
                continue
            # 跳过帮助按钮（它有自己的圆形样式）
            if hasattr(self, 'help_btn') and widget == self.help_btn:
                continue
            widget.setStyleSheet(button_style)
        
        # 更新帮助按钮样式（保持圆形）
        if hasattr(self, 'help_btn'):
            self.help_btn.setStyleSheet(f"""
                QPushButton {{
                    border-radius: 24px;
                    background-color: {color_str};
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {color_str}CC;
                }}
                QPushButton:pressed {{
                    background-color: {color_str}AA;
                }}
            """)

        # 更新思维导图按钮样式（保持圆形，跟随主题色）
        if hasattr(self, 'mindmap_btn'):
            self.mindmap_btn.setStyleSheet(f"""
                QPushButton {{
                    border-radius: 24px;
                    background-color: {color_str};
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {color_str}CC;
                }}
                QPushButton:pressed {{
                    background-color: {color_str}AA;
                }}
            """)

        # FolderCard 和 ItemCard 使用 update_theme 方法更新主题
        for card in self.findChildren(FolderCard):
            card.update_theme(dark)
        for card in self.findChildren(ItemCard):
            card.update_theme(dark)

        # 更新卡片展示容器背景（使用背景管理器的设置）
        def update_container_background(container_name):
            container = self.findChild(CardContainerWidget, container_name)
            if container:
                container.update_background()
        
        update_container_background("folders_container")
        update_container_background("items_container")

        # 滚动区域背景
        scroll_style = f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
        """
        for scroll in self.findChildren(QScrollArea):
            scroll.setStyleSheet(scroll_style)

        # 拖拽区域
        drop_style = f"""
            border: 2px dashed {border_color};
            border-radius: 8px;
            padding: 20px;
            background-color: {alt_bg};
            color: {text_color};
        """
        for drop in self.findChildren(DropArea):
            drop.setStyleSheet(drop_style)

        # 侧边栏（主菜单和子菜单）
        if self.settings_sidebars:
            sidebar_style = f"""
                QWidget {{
                    background-color: {alt_bg};
                    color: {text_color};
                    border-left: 1px solid {border_color};
                }}
                QPushButton {{
                    text-align: left;
                    padding: 12px 20px;
                    border: none;
                    border-bottom: 1px solid {border_color};
                    background-color: transparent;
                    color: {text_color};
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: {hover_bg};
                }}
                QLabel {{
                    color: {text_color};
                }}
                QComboBox {{
                    margin: 4px 16px;
                    padding: 6px;
                    border: 1px solid {border_color};
                    border-radius: 4px;
                    background-color: {bg_color};
                    color: {text_color};
                }}
                QComboBox QAbstractItemView {{
                    background-color: {bg_color};
                    color: {text_color};
                    selection-background-color: {color_str};
                }}
            """
            for sidebar in self.settings_sidebars:
                sidebar.setStyleSheet(sidebar_style)
                # 特殊按钮“选择颜色”使用主题色背景，文字白色（因为主题色可能浅，白色更清晰）
                for btn in sidebar.findChildren(QPushButton):
                    if btn.objectName() == "color_picker_btn":
                        btn.setStyleSheet(f"""
                            background-color: {color_str};
                            color: white;
                            border: 1px solid {border_color};
                            border-radius: 4px;
                            padding: 6px;
                        """)
                # 颜色预览标签
                for label in sidebar.findChildren(QLabel):
                    if label.property("color_preview"):
                        label.setStyleSheet(f"background-color: {color_str}; border: 1px solid {border_color};")
        # 密码侧边栏
        if self.password_sidebar:
            # 复制侧边栏样式
            sidebar_style = f"""
                QWidget {{
                    background-color: {alt_bg};
                    color: {text_color};
                    border-right: 1px solid {border_color};
                }}
                QPushButton {{
                    text-align: left;
                    padding: 8px 16px;
                    border: none;
                    background-color: transparent;
                    color: {text_color};
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: {hover_bg};
                }}
                QLabel {{
                    color: {text_color};
                }}
                QLineEdit {{
                    border: 1px solid {border_color};
                    border-radius: 4px;
                    padding: 6px;
                    background-color: {bg_color};
                    color: {text_color};
                }}
                QLineEdit:focus {{
                    border-bottom: 3px solid {color_str};
                }}
                QPushButton#confirm_btn {{
                    background-color: {color_str};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px;
                }}
            """
            self.password_sidebar.setStyleSheet(sidebar_style)
        
        # 触发主窗口重绘，更新背景
        self.update()

    def save_config(self):
        config_path = "config.json"
        data = {
            "language": self.current_lang,
            "theme_color": MainWindow.current_theme_color.name(),
            "dark_mode": MainWindow.current_dark_mode
        }
        # 添加背景设置
        data.update(background_manager.save_config())
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def on_language_settings_clicked(self):
        self.toggle_sub_sidebar("language")

    def create_language_sidebar(self):
        sidebar = QWidget(self)
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-left: 1px solid #ccc;
            }
            QPushButton {
                text-align: left;
                padding: 12px 20px;
                border: none;
                border-bottom: 1px solid #ddd;
                background-color: transparent;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        title = QLabel(self.strings[self.current_lang]["language_title"])
        title.setStyleSheet("padding: 16px; font-size: 16px; font-weight: bold; border-bottom: 1px solid #ddd;")
        layout.addWidget(title)

        btn_zh = QPushButton(self.strings[self.current_lang]["chinese"])
        btn_zh.clicked.connect(lambda: self.set_language("zh"))
        layout.addWidget(btn_zh)

        btn_en = QPushButton(self.strings[self.current_lang]["english"])
        btn_en.clicked.connect(lambda: self.set_language("en"))
        layout.addWidget(btn_en)

        layout.addStretch()
        return sidebar

    def set_language(self, lang):
        if lang == self.current_lang:
            return
        self.current_lang = lang
        self.apply_language()
        self.save_config()
        self.close_all_settings()

    def apply_language(self):
        # 更新窗口标题
        self.setWindowTitle(self.strings[self.current_lang]["window_title"])

        # 更新搜索框占位符
        for obj_name, placeholder_key in [("folder_search", "folder_search_placeholder"),
                                          ("item_search", "item_search_placeholder"),
                                          ("link_cover_edit", "cover_url_placeholder"),
                                          ("file_cover_edit", "cover_url_placeholder"),
                                          ("link_summary_edit", "summary_placeholder"),
                                          ("file_summary_edit", "summary_placeholder")]:
            widget = getattr(self, obj_name, None)
            if widget:
                widget.setPlaceholderText(self.strings[self.current_lang][placeholder_key])

        for obj_name, text_key in [
            ("add_folder_btn", "add_folder_btn"),
            ("add_item_btn", "add_item_btn"),
            ("confirm_btn", "confirm"),  # 添加收藏项页面中的确认按钮
            ("auto_fetch_btn", "auto_fetch"),
            ("link_cover_btn", "select_cover"),
            ("file_cover_btn", "select_cover"),
        ]:
            widget = self.findChild(QPushButton, obj_name)
            if widget:
                widget.setText(self.strings[self.current_lang][text_key])

        #返回按钮
        back_btn_add = self.findChild(QPushButton, "back_btn_add_item")
        if back_btn_add:
            back_btn_add.setText(self.strings[self.current_lang]["back_btn"])

        # 更新添加项页面中的标签
        label_map = {
            "label_link_url": "link_url",
            "label_link_title": "title_label",
            "label_link_category": "category_label",
            "label_link_cover": "cover_label",
            "label_link_summary": "summary_label",
            "label_file_drop": "file_drop",
            "label_file_title": "title_label",
            "label_file_category": "category_label",
            "label_file_cover": "cover_label",
            "label_file_summary": "summary_label",
        }
        for obj_name, text_key in label_map.items():
            label = self.findChild(QLabel, obj_name)
            if label:
                label.setText(self.strings[self.current_lang][text_key])

        delete_btn = self.findChild(QPushButton, "delete_selected_btn")
        if delete_btn:
            delete_btn.setText(self.strings[self.current_lang]["delete_selected"])
        cancel_btn = self.findChild(QPushButton, "cancel_btn")
        if cancel_btn:
            cancel_btn.setText(self.strings[self.current_lang]["cancel"])

        # 更新添加项页面
        back_btn = self.findChild(QPushButton, "back_btn")  # 如果返回按钮有 objectName
        # 但返回按钮用了图标，可能没有文本，可忽略

        # 更新类型下拉框
        if hasattr(self, 'item_type_combo'):
            self.item_type_combo.clear()
            self.item_type_combo.addItems([
                self.strings[self.current_lang]["item_type_link"],
                self.strings[self.current_lang]["item_type_file"]
            ])

        # 更新确认按钮
        confirm_btn = self.findChild(QPushButton, "confirm_btn")
        if confirm_btn:
            confirm_btn.setText(self.strings[self.current_lang]["confirm"])

        # 更新自动识别按钮
        if hasattr(self, 'auto_fetch_btn'):
            self.auto_fetch_btn.setText(self.strings[self.current_lang]["auto_fetch"])

        # 更新拖拽区域的提示文字（若未选择文件则显示提示，否则保留已选文件名）
        if hasattr(self, 'drop_area'):
            if self.dropped_file_path:
                # 如果已拖拽文件，更新前缀
                self.drop_area.setText(
                    self.strings[self.current_lang]["file_selected_prefix"] +
                    os.path.basename(self.dropped_file_path)
                )
            else:
                self.drop_area.setText(self.strings[self.current_lang]["drag_hint"])

        if hasattr(self, 'file_category_edit'):
            self.file_category_edit.setPlaceholderText(self.strings[self.current_lang]["category_placeholder"])

        # 更新添加项页面的占位符
        if hasattr(self, 'link_url_edit'):
            self.link_url_edit.setPlaceholderText(self.strings[self.current_lang]["link_url_placeholder"])
        if hasattr(self, 'link_title_edit'):
            self.link_title_edit.setPlaceholderText(self.strings[self.current_lang]["title_placeholder"])
        if hasattr(self, 'link_category_edit'):
            self.link_category_edit.setPlaceholderText(self.strings[self.current_lang]["category_placeholder"])
        if hasattr(self, 'file_title_edit'):
            self.file_title_edit.setPlaceholderText(self.strings[self.current_lang]["file_title_placeholder"])
        if hasattr(self, 'file_category_edit'):
            self.file_category_edit.setPlaceholderText(self.strings[self.current_lang]["category_placeholder"])

        # 更新收藏夹卡片的语言
        for card in self.findChildren(FolderCard):
            card.update_language(self.current_lang)

        # 更新思维导图视图的语言
        if hasattr(self, 'current_mindmap_view') and self.current_mindmap_view:
            self.current_mindmap_view.update_language(self.current_lang)


    def setup_folders_page(self):
        layout = QVBoxLayout(self.folders_page)

        top_bar = QHBoxLayout()
        self.folder_search = QLineEdit()
        self.folder_search.setObjectName("folder_search")
        self.folder_search.setPlaceholderText("搜索收藏夹...")
        self.folder_search.textChanged.connect(self.filter_folders)
        top_bar.addWidget(self.folder_search)

        add_folder_btn = QPushButton(self.strings[self.current_lang]["add_folder_btn"])
        add_folder_btn.setObjectName("add_folder_btn")
        add_folder_btn.clicked.connect(self.add_folder_dialog)
        top_bar.addWidget(add_folder_btn)

        # 设置按钮
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(QIcon(resource_path("resources/icons/settings.png")))
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.clicked.connect(self.open_settings)
        top_bar.addWidget(self.settings_btn)

        layout.addLayout(top_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_widget = CardContainerWidget()
        scroll_widget.setObjectName("folders_container")
        self.folders_grid_layout = QGridLayout(scroll_widget)
        self.folders_grid_layout.setSpacing(3)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        self.load_folders()

    def load_folders(self):
        for i in reversed(range(self.folders_grid_layout.count())):
            widget = self.folders_grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        folders = self.db.get_folders()
        row, col = 0, 0
        for folder_id, name, pwd_hash, created_at in folders:
            has_password = pwd_hash is not None
            item_count = self.db.get_folder_item_count(folder_id)
            card = FolderCard(folder_id, name, has_password, item_count, created_at, self.current_lang)
            card.clicked.connect(lambda fid=folder_id: self.open_folder(fid, name))
            card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            card.customContextMenuRequested.connect(lambda pos, fid=folder_id, n=name: self.show_folder_context_menu(pos, fid, n))
            self.folders_grid_layout.addWidget(card, row, col)
            col += 1
            if col >= 5:
                col = 0
                row += 1

    def filter_folders(self):
        text = self.folder_search.text().strip().lower()
        for i in range(self.folders_grid_layout.count()):
            widget = self.folders_grid_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'folder_name'):
                widget.setVisible(text in widget.folder_name.lower())

    def add_folder_dialog(self):
        """打开添加收藏夹侧边栏"""
        # 如果已经打开，先关闭
        if hasattr(self, 'add_folder_sidebar') and self.add_folder_sidebar is not None:
            return

        # 创建遮罩
        self.add_folder_overlay = QWidget(self)
        self.add_folder_overlay.setGeometry(0, 0, self.width(), self.height())
        self.add_folder_overlay.setStyleSheet("background-color: rgba(0,0,0,0.3);")
        self.add_folder_overlay.mousePressEvent = lambda e: self.close_add_folder_sidebar()
        self.add_folder_overlay.raise_()
        self.add_folder_overlay.show()

        # 创建侧边栏
        sidebar = self.create_add_folder_sidebar()
        sidebar.setParent(self)
        sidebar.setFixedWidth(300)
        sidebar.setGeometry(self.width(), 0, 300, self.height())
        sidebar.raise_()
        sidebar.show()

        self.add_folder_sidebar = sidebar

        # 侧边栏移入动画（存储为实例变量防止垃圾回收）
        self.add_folder_open_anim = QPropertyAnimation(sidebar, b"geometry")
        self.add_folder_open_anim.setDuration(300)
        self.add_folder_open_anim.setStartValue(QRect(self.width(), 0, 300, self.height()))
        self.add_folder_open_anim.setEndValue(QRect(self.width() - 300, 0, 300, self.height()))
        self.add_folder_open_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.add_folder_open_anim.start()

    def create_add_folder_sidebar(self):
        """创建添加收藏夹侧边栏"""
        sidebar = QWidget(self)
        
        dark = MainWindow.current_dark_mode
        bg_color = "#2b2b2b" if dark else "#ffffff"
        text_color = "#ffffff" if dark else "#333333"
        border_color = "#555555" if dark else "#cccccc"
        alt_bg = "#3c3c3c" if dark else "#f5f5f5"
        color_str = MainWindow.current_theme_color.name()
        
        sidebar.setStyleSheet(f"""
            QWidget#add_folder_sidebar {{
                background-color: {bg_color};
                color: {text_color};
                border-left: 1px solid {border_color};
            }}
            QLabel {{
                color: {text_color};
            }}
            QLineEdit {{
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 8px;
                margin: 4px 16px;
                background-color: {alt_bg};
                color: {text_color};
            }}
            QLineEdit:focus {{
                border-color: {color_str};
            }}
            QPushButton {{
                margin: 4px 16px;
                padding: 8px;
                border-radius: 4px;
                font-size: 14px;
                border: none;
            }}
        """)
        sidebar.setObjectName("add_folder_sidebar")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题栏
        header = QWidget()
        header.setStyleSheet(f"background-color: {alt_bg}; border-bottom: 1px solid {border_color};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(10)

        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                font-size: 18px;
                color: {text_color};
            }}
            QPushButton:hover {{
                background-color: rgba(0,0,0,0.1);
                border-radius: 50%;
            }}
        """)
        close_btn.clicked.connect(self.close_add_folder_sidebar)

        # 标题
        title = QLabel(self.strings[self.current_lang]["add_folder_dialog_title"])
        title.setStyleSheet("font-size: 16px; font-weight: bold;")

        header_layout.addWidget(close_btn)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addWidget(header)

        # 输入区域
        input_area = QWidget()
        input_layout = QVBoxLayout(input_area)
        input_layout.setContentsMargins(16, 24, 16, 24)
        input_layout.setSpacing(16)

        # 标签
        label = QLabel(self.strings[self.current_lang]["add_folder_dialog_label"])
        label.setStyleSheet("font-size: 14px;")
        input_layout.addWidget(label)

        # 输入框
        self.folder_name_edit = QLineEdit()
        self.folder_name_edit.setPlaceholderText(self.strings[self.current_lang]["new_folder_name"])
        self.folder_name_edit.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 10px 12px;
                margin: 0;
                background-color: {alt_bg};
                color: {text_color};
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {color_str};
                outline: none;
            }}
        """)
        input_layout.addWidget(self.folder_name_edit)

        # 按钮区域
        button_layout = QVBoxLayout()
        button_layout.setSpacing(8)

        # 确定按钮（主题色，与全局按钮样式一致）
        confirm_btn = QPushButton(self.strings[self.current_lang]["confirm"])
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid {color_str};
                border-radius: 4px;
                padding: 8px 16px;
                background-color: {color_str};
                color: {text_color};
                font-size: 14px;
                margin: 0;
            }}
            QPushButton:hover {{
                background-color: {color_str}80;
            }}
        """)
        confirm_btn.clicked.connect(self.on_add_folder_confirm)
        button_layout.addWidget(confirm_btn)

        # 取消按钮（与全局按钮样式一致）
        cancel_btn = QPushButton(self.strings[self.current_lang]["cancel"])
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid {color_str};
                border-radius: 4px;
                padding: 8px 16px;
                background-color: {color_str};
                color: {text_color};
                font-size: 14px;
                margin: 0;
            }}
            QPushButton:hover {{
                background-color: {color_str}80;
            }}
        """)
        cancel_btn.clicked.connect(self.close_add_folder_sidebar)
        button_layout.addWidget(cancel_btn)

        input_layout.addLayout(button_layout)
        layout.addWidget(input_area)
        layout.addStretch()

        # 设置输入框焦点
        QTimer.singleShot(100, self.folder_name_edit.setFocus)

        return sidebar

    def close_add_folder_sidebar(self):
        """关闭添加收藏夹侧边栏"""
        if not hasattr(self, 'add_folder_sidebar') or self.add_folder_sidebar is None:
            return

        sidebar = self.add_folder_sidebar
        overlay = self.add_folder_overlay
        
        # 侧边栏移出动画（存储为实例变量防止垃圾回收）
        self.add_folder_close_anim = QPropertyAnimation(sidebar, b"geometry")
        self.add_folder_close_anim.setDuration(300)
        self.add_folder_close_anim.setStartValue(QRect(self.width() - 300, 0, 300, self.height()))
        self.add_folder_close_anim.setEndValue(QRect(self.width(), 0, 300, self.height()))
        self.add_folder_close_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.add_folder_close_anim.finished.connect(lambda: self._cleanup_add_folder_sidebar(sidebar, overlay))
        self.add_folder_close_anim.start()

    def _cleanup_add_folder_sidebar(self, sidebar=None, overlay=None):
        """清理添加收藏夹侧边栏"""
        if sidebar:
            sidebar.deleteLater()
        if hasattr(self, 'add_folder_sidebar'):
            self.add_folder_sidebar = None
            
        if overlay:
            overlay.deleteLater()
        if hasattr(self, 'add_folder_overlay'):
            self.add_folder_overlay = None

    def on_add_folder_confirm(self):
        """确认添加收藏夹"""
        name = self.folder_name_edit.text().strip()
        if name:
            self.db.add_folder(name)
            # 强制刷新页面
            QTimer.singleShot(0, self.load_folders)
            self.close_add_folder_sidebar()

    def open_folder(self, folder_id, folder_name):
        pwd_hash = self.db.get_folder_password_hash(folder_id)
        if pwd_hash is not None:
            self.show_password_input('folder', folder_id,
                                     lambda: self._open_folder_after_verify(folder_id, folder_name))
        else:
            self._open_folder_after_verify(folder_id, folder_name)

    def _open_folder_after_verify(self, folder_id, folder_name):
        self.current_folder_id = folder_id
        self.current_folder_name = folder_name
        self.load_items_in_folder(folder_id)
        self.switch_to_page(1)

    def show_folder_context_menu(self, pos, folder_id, folder_name):
        card = self.sender()
        has_password = card.has_password if hasattr(card, 'has_password') else False

        menu = QMenu(self)
        rename_action = QAction(self.strings[self.current_lang]["rename"], self)
        rename_action.triggered.connect(lambda: self.rename_folder(folder_id, folder_name))
        menu.addAction(rename_action)

        if has_password:
            change_pwd_action = QAction(self.strings[self.current_lang]["change_password"], self)
            change_pwd_action.triggered.connect(lambda: self.open_password_change('folder', folder_id))
            menu.addAction(change_pwd_action)

            remove_pwd_action = QAction(self.strings[self.current_lang]["remove_password"], self)
            remove_pwd_action.triggered.connect(lambda: self.open_password_remove('folder', folder_id))
            menu.addAction(remove_pwd_action)
        else:
            set_pwd_action = QAction(self.strings[self.current_lang]["set_password"], self)
            set_pwd_action.triggered.connect(lambda: self.open_password_setup('folder', folder_id))
            menu.addAction(set_pwd_action)

        delete_action = QAction(self.strings[self.current_lang]["delete"], self)
        delete_action.triggered.connect(lambda: self.delete_folder(folder_id))
        menu.addAction(delete_action)

        menu.exec(self.sender().mapToGlobal(pos))

    def rename_folder(self, folder_id, old_name):
        new_name, ok = QInputDialog.getText(self, self.strings[self.current_lang]["rename_folder_dialog_title"], self.strings[self.current_lang]["rename_folder_dialog_label"], text=old_name)
        if ok and new_name:
            self.db.rename_folder(folder_id, new_name)
            self.load_folders()

    def delete_folder(self, folder_id):
        reply = QMessageBox.question(self, self.strings[self.current_lang]["confirm_delete"], self.strings[self.current_lang]["delete_folder_confirm"],
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_folder(folder_id)
            self.load_folders()
            if self.current_folder_id == folder_id:
                self.go_back_to_folders()

    def setup_items_page(self):
        layout = QVBoxLayout(self.items_page)

        top_bar = QHBoxLayout()
        self.back_btn = QPushButton()
        self.back_btn.setObjectName("back_btn")
        self.back_btn.setIcon(QIcon(resource_path("resources/icons/back.png")))
        self.back_btn.setFixedSize(32, 32)
        self.back_btn.clicked.connect(self.go_back_to_folders)
        top_bar.addWidget(self.back_btn)

        self.item_search = QLineEdit()
        self.item_search.setObjectName("item_search")
        self.item_search.setPlaceholderText("搜索收藏项...")
        self.item_search.textChanged.connect(self.filter_items)
        top_bar.addWidget(self.item_search)

        self.filter_btn = QPushButton()
        self.filter_btn.setIcon(QIcon(resource_path("resources/icons/filter.png")))
        self.filter_btn.setFixedSize(32, 32)
        self.filter_btn.clicked.connect(self.show_category_menu)
        top_bar.addWidget(self.filter_btn)

        add_item_btn = QPushButton(self.strings[self.current_lang]["add_item_btn"])
        add_item_btn.setObjectName("add_item_btn")
        add_item_btn.clicked.connect(self.open_add_item_page)
        top_bar.addWidget(add_item_btn)

        layout.addLayout(top_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = CardContainerWidget()
        scroll_widget.setObjectName("items_container")
        self.items_grid_layout = QGridLayout(scroll_widget)
        self.items_grid_layout.setSpacing(15)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        self.multi_select_bar = QWidget()
        self.multi_select_bar.setVisible(False)
        bar_layout = QHBoxLayout(self.multi_select_bar)
        delete_selected_btn = QPushButton(self.strings[self.current_lang]["delete_selected"])
        delete_selected_btn.setObjectName("delete_selected_btn")
        delete_selected_btn.clicked.connect(self.delete_selected_items)
        cancel_btn = QPushButton(self.strings[self.current_lang]["cancel"])
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.clicked.connect(self.exit_multi_select_mode)
        bar_layout.addWidget(delete_selected_btn)
        bar_layout.addWidget(cancel_btn)
        layout.addWidget(self.multi_select_bar)

    def load_items_in_folder(self, folder_id):
        # 清空原有卡片
        for i in reversed(range(self.items_grid_layout.count())):
            widget = self.items_grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        items = self.db.get_items_by_folder(folder_id)
        row, col = 0, 0
        for item_data in items:
            item_id, item_type, title, url, category, cover_path, pwd_hash = item_data[:7]
            summary = item_data[7] if len(item_data) > 7 else ""
            has_password = pwd_hash is not None
            card = ItemCard(item_id, title, cover_path, category, has_password, url, self.current_lang, summary)
            card.clicked.connect(lambda _, iid=item_id: self.open_item_by_id(iid))
            card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            card.customContextMenuRequested.connect(
                lambda pos, iid=item_id, t=title, u=url, cat=category, itype=item_type:
                self.show_item_context_menu(pos, iid, t, u, cat, itype))
            card.update_theme(MainWindow.current_dark_mode)
            self.items_grid_layout.addWidget(card, row, col)
            col += 1
            if col >= 4:
                col = 0
                row += 1
        if self.multi_select_mode:
            self.exit_multi_select_mode()
        self.filter_by_category(self.current_category_filter)
        
    def open_item(self, url, item_type, item_id=None):
        self.exit_multi_select_mode()
        if item_type == "link":
            url = self.extract_url_from_text(url)
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            webbrowser.open(url)
        else:
            if os.path.exists(url):
                os.startfile(url)
            else:
                self.show_toast(self.strings[self.current_lang]["file_not_found_msg"].format(url))

    def open_item_by_id(self, item_id):
        # 从数据库获取该条目的信息（需要新增方法 get_item_by_id）
        item = self.db.get_item_by_id(item_id)  # 返回 (item_type, title, url, category, cover_path, password_hash, summary)
        if item is None:
            return
        item_type, title, url, category, cover_path, pwd_hash = item[:6]
        if pwd_hash is not None:
            self.show_password_input('item', item_id,
                                     lambda: self._open_item_after_verify(url, item_type))
        else:
            self._open_item_after_verify(url, item_type)

    def _open_item_after_verify(self, url, item_type):
        # 原来的 open_item 逻辑
        if item_type == "link":
            url = self.extract_url_from_text(url)
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            webbrowser.open(url)
        else:
            if os.path.exists(url):
                os.startfile(url)
            else:
                self.show_toast(self.strings[self.current_lang]["file_not_found_msg"].format(url))

    def extract_url_from_text(self, text):
        pattern = r'https?://[^\s<>"\'{}|\\^`\[\]]+'
        match = re.search(pattern, text)
        return match.group(0) if match else text.strip()

    def show_item_context_menu(self, pos, item_id, title, url, category, item_type):
        card = self.sender()
        has_password = card.has_password if hasattr(card, 'has_password') else False
        menu = QMenu(self)
        edit_action = QAction(self.strings[self.current_lang]["edit"], self)
        edit_action.triggered.connect(lambda: self.edit_item(item_id, title, url, category, item_type))
        delete_action = QAction(self.strings[self.current_lang]["delete"], self)
        delete_action.triggered.connect(lambda: self.delete_item(item_id))

        if has_password:
            change_pwd_action = QAction(self.strings[self.current_lang]["change_password"], self)
            change_pwd_action.triggered.connect(lambda: self.open_password_change('item', item_id))
            menu.addAction(change_pwd_action)

            remove_pwd_action = QAction(self.strings[self.current_lang]["remove_password"], self)
            remove_pwd_action.triggered.connect(lambda: self.open_password_remove('item', item_id))
            menu.addAction(remove_pwd_action)
        else:
            set_pwd_action = QAction(self.strings[self.current_lang]["set_password"], self)
            set_pwd_action.triggered.connect(lambda: self.open_password_setup('item', item_id))
            menu.addAction(set_pwd_action)

        multi_action = QAction(self.strings[self.current_lang]["multi_select_mode"], self)
        multi_action.triggered.connect(self.enable_multi_select_mode)
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        # 插入密码选项
        if has_password:
            menu.addAction(change_pwd_action)
            menu.addAction(remove_pwd_action)
        else:
            menu.addAction(set_pwd_action)
        menu.addSeparator()
        menu.addAction(multi_action)
        menu.exec(self.sender().mapToGlobal(pos))

    def edit_item(self, item_id, title, url, category, item_type):
        self.editing_item_id = item_id
        self.editing_item_type = item_type
        item_data = self.db.get_item_by_id(item_id)
        summary = item_data[6] if item_data and len(item_data) > 6 else ""
        self.open_add_item_page()
        QTimer.singleShot(50, lambda: self.populate_edit_form(title, url, category, item_type, summary))

    def populate_edit_form(self, title, url, category, item_type, summary=""):
        if item_type == "link":
            self.item_type_combo.setCurrentIndex(0)
            self.link_url_edit.setText(url)
            self.link_title_edit.setText(title)
            self.link_category_edit.setText(category)
            if hasattr(self, 'link_summary_edit'):
                self.link_summary_edit.setPlainText(summary)
        else:
            self.item_type_combo.setCurrentIndex(1)
            self.dropped_file_path = url
            self.file_title_edit.setText(title)
            self.file_category_edit.setText(category)
            if hasattr(self, 'file_summary_edit'):
                self.file_summary_edit.setPlainText(summary)
            if os.path.exists(url):
                self.drop_area.setText(self.strings[self.current_lang]["file_selected_prefix"] + os.path.basename(url))
            else:
                self.drop_area.setText(self.strings[self.current_lang]["file_not_exist_hint"])

    def delete_item(self, item_id):
        reply = QMessageBox.question(self, self.strings[self.current_lang]["confirm_delete"], self.strings[self.current_lang]["delete_item_confirm"],
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_item(item_id)
            self.load_items_in_folder(self.current_folder_id)

    def filter_items(self):
        text = self.item_search.text().strip().lower()
        for i in range(self.items_grid_layout.count()):
            widget = self.items_grid_layout.itemAt(i).widget()
            if widget and isinstance(widget, ItemCard):
                # 获取标题文本
                title_text = widget.title_label.text().lower()
                widget.setVisible(text in title_text)

    def show_category_menu(self):
        if self.current_folder_id is None:
            return
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM items WHERE folder_id = ?", (self.current_folder_id,))
            categories = [row[0] for row in cursor.fetchall()]
        menu = QMenu(self)
        all_action = QAction(self.strings[self.current_lang]["filter_all"], self)
        all_action.triggered.connect(lambda: self.filter_by_category(None))
        menu.addAction(all_action)
        menu.addSeparator()
        for cat in categories:
            action = QAction(cat, self)
            action.triggered.connect(lambda checked, c=cat: self.filter_by_category(c))
            menu.addAction(action)
        menu.exec(self.filter_btn.mapToGlobal(self.filter_btn.rect().bottomLeft()))

    def filter_by_category(self, category):
        self.current_category_filter = category
        for i in range(self.items_grid_layout.count()):
            widget = self.items_grid_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'category'):
                if category is None:
                    widget.setVisible(True)
                else:
                    widget.setVisible(widget.category == category)

    def go_back_to_folders(self):
        self.exit_multi_select_mode()
        self.switch_to_page(0)

    def open_mindmap(self):
        """打开思维导图页面"""
        if self.current_folder_id is None:
            self.show_toast(self.strings[self.current_lang]["warning_no_folder"])
            return
        
        # 获取当前收藏夹名称
        folders = self.db.get_folders()
        folder_name = ""
        for folder in folders:
            if folder[0] == self.current_folder_id:
                folder_name = folder[1]
                break
        
        if not folder_name:
            folder_name = "未命名收藏夹"
        
        self.current_folder_name = folder_name
        
        # 创建思维导图视图
        if self.current_mindmap_view:
            self.current_mindmap_view.setParent(None)
            self.current_mindmap_view.deleteLater()
            self.current_mindmap_view = None
        
        self.current_mindmap_view = MindmapView(self.db, self.current_folder_id, folder_name, strings=self.strings, current_lang=self.current_lang)
        self.current_mindmap_view.back_requested.connect(self.close_mindmap)
        self.current_mindmap_view.add_item_requested.connect(self.open_add_item_page)
        self.current_mindmap_view.edit_item_requested.connect(self.edit_item_from_mindmap)
        self.current_mindmap_view.refresh_view_requested.connect(self.refresh_current_view)
        
        # 添加到布局
        self.mindmap_layout.addWidget(self.current_mindmap_view)
        
        # 切换到思维导图页面
        self.switch_to_page(3)

    def close_mindmap(self):
        """关闭思维导图页面"""
        self.switch_to_page(1)  # 返回到收藏项页面
    
    def edit_item_from_mindmap(self, data):
        """从思维导图编辑收藏项"""
        if not data:
            return
        item_id = data.get('id')
        title = data.get('title', '')
        url = data.get('url', '')
        category = data.get('category', '')
        item_type = data.get('item_type', 'link')
        # 调用现有的 edit_item 方法
        self.edit_item(item_id, title, url, category, item_type)

    def switch_to_page(self, target_index):
        current_index = self.stacked_widget.currentIndex()
        if current_index == target_index:
            return
        # 取消正在进行的动画
        if self.anim_group and self.anim_group.state() == QPropertyAnimation.State.Running:
            self.anim_group.stop()

        # 确定方向：目标 > 当前 => 新页面从右滑入；否则从左滑入
        direction = 'right' if target_index > current_index else 'left'

        current_widget = self.stacked_widget.widget(current_index)
        target_widget = self.stacked_widget.widget(target_index)
        width = self.stacked_widget.width()
        height = self.stacked_widget.height()

        # 设置目标页初始位置
        if direction == 'right':
            target_widget.setGeometry(width, 0, width, height)
        else:
            target_widget.setGeometry(-width, 0, width, height)
        target_widget.show()
        target_widget.raise_()

        # 创建动画组
        self.anim_group = QParallelAnimationGroup()

        # 当前页动画
        anim_cur = QPropertyAnimation(current_widget, b"geometry")
        start_cur = current_widget.geometry()
        if direction == 'right':
            end_cur = QRect(-width, 0, width, height)
        else:
            end_cur = QRect(width, 0, width, height)
        anim_cur.setStartValue(start_cur)
        anim_cur.setEndValue(end_cur)
        anim_cur.setDuration(300)
        anim_cur.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # 目标页动画
        anim_tgt = QPropertyAnimation(target_widget, b"geometry")
        start_tgt = target_widget.geometry()
        end_tgt = QRect(0, 0, width, height)
        anim_tgt.setStartValue(start_tgt)
        anim_tgt.setEndValue(end_tgt)
        anim_tgt.setDuration(300)
        anim_tgt.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.anim_group.addAnimation(anim_cur)
        self.anim_group.addAnimation(anim_tgt)
        self.anim_group.finished.connect(lambda: self._finish_switch(target_index))
        self.anim_group.start()

    def _finish_switch(self, target_index):
        self.stacked_widget.setCurrentIndex(target_index)
        self.anim_group = None
        
        # 根据页面类型设置按钮可见性
        # 帮助按钮在所有页面可见，思维导图按钮只在收藏项页面可见
        if hasattr(self, 'mindmap_btn'):
            self.mindmap_btn.setVisible(target_index == 1)  # 只在收藏项页面可见
        if hasattr(self, 'help_btn'):
            self.help_btn.setVisible(True)  # 帮助按钮在所有页面可见
        
        # 确保按钮位置正确
        self._update_help_button_position()
        
        # 切换到收藏项页面时自动刷新列表
        if target_index == 1 and self.current_folder_id is not None:
            self.load_items_in_folder(self.current_folder_id)
        
        # 切换到文件夹列表页面时刷新
        if target_index == 0:
            self.load_folders()

    def open_add_item_page(self):
        self.link_url_edit.clear()
        self.link_title_edit.clear()
        self.link_category_edit.clear()
        self.file_title_edit.clear()
        self.file_category_edit.clear()
        self.dropped_file_path = None
        self.drop_area.setText(self.strings[self.current_lang]["drag_hint"])
        self.item_type_combo.setCurrentIndex(0)
        self.switch_to_page(2)

    def setup_add_item_page(self):
        from PyQt6.QtWidgets import QComboBox, QStackedWidget, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QFrame
        from PyQt6.QtCore import Qt

        layout = QVBoxLayout(self.add_item_page)

        back_btn = QPushButton(self.strings[self.current_lang]["back_btn"])
        back_btn.setObjectName("back_btn_add_item")
        back_btn.clicked.connect(lambda: self.switch_to_page(1))
        layout.addWidget(back_btn)

        layout.addWidget(QLabel(self.strings[self.current_lang]["add_item_type"]))
        self.item_type_combo = QComboBox()
        self.item_type_combo.addItems([self.strings[self.current_lang]["item_type_link"], self.strings[self.current_lang]["item_type_file"]])
        self.item_type_combo.currentIndexChanged.connect(self.switch_add_item_type)
        layout.addWidget(self.item_type_combo)

        self.add_item_stack = QStackedWidget()
        layout.addWidget(self.add_item_stack)

        link_widget = QWidget()
        link_layout = QVBoxLayout(link_widget)
        self.link_url_edit = QLineEdit()
        self.link_url_edit.setObjectName("link_url_edit")
        self.link_url_edit.setPlaceholderText(self.strings[self.current_lang]["link_url_placeholder"])
        self.link_title_edit = QLineEdit()
        self.link_title_edit.setObjectName("link_title_edit")
        self.link_title_edit.setPlaceholderText(self.strings[self.current_lang]["title_placeholder"])
        self.link_category_edit = QLineEdit()
        self.link_category_edit.setObjectName("link_category_edit")
        self.link_category_edit.setPlaceholderText(self.strings[self.current_lang]["category_placeholder"])
        auto_btn = QPushButton(self.strings[self.current_lang]["auto_fetch"])
        auto_btn.setObjectName("auto_fetch_btn")
        auto_btn.clicked.connect(self.auto_fetch_link_info)
        self.auto_fetch_btn = auto_btn  # 保存为实例属性
        label = QLabel(self.strings[self.current_lang]["link_url"])
        label.setObjectName("label_link_url")
        link_layout.addWidget(label)
        link_layout.addWidget(self.link_url_edit)
        link_title_label = QLabel(self.strings[self.current_lang]["title_label"])
        link_title_label.setObjectName("label_link_title")
        link_layout.addWidget(link_title_label)
        link_layout.addWidget(self.link_title_edit)
        link_category_label = QLabel(self.strings[self.current_lang]["category_label"])
        link_category_label.setObjectName("label_link_category")
        link_layout.addWidget(link_category_label)
        link_layout.addWidget(self.link_category_edit)
        
        link_cover_label = QLabel(self.strings[self.current_lang].get("cover_label", "Cover:"))
        link_cover_label.setObjectName("label_link_cover")
        link_layout.addWidget(link_cover_label)
        self.link_cover_edit = QLineEdit()
        self.link_cover_edit.setObjectName("link_cover_edit")
        self.link_cover_edit.setPlaceholderText(self.strings[self.current_lang].get("cover_url_placeholder", "Cover URL or local path"))
        link_layout.addWidget(self.link_cover_edit)
        
        link_cover_btn = QPushButton(self.strings[self.current_lang].get("select_cover", "Select Cover"))
        link_cover_btn.setObjectName("link_cover_btn")
        link_cover_btn.clicked.connect(self.select_cover_for_item)
        link_layout.addWidget(link_cover_btn)
        
        link_summary_label = QLabel(self.strings[self.current_lang].get("summary_label", "Summary:"))
        link_summary_label.setObjectName("label_link_summary")
        link_layout.addWidget(link_summary_label)
        self.link_summary_edit = QTextEdit()
        self.link_summary_edit.setObjectName("link_summary_edit")
        self.link_summary_edit.setPlaceholderText(self.strings[self.current_lang].get("summary_placeholder", "Enter summary..."))
        self.link_summary_edit.setMaximumHeight(100)
        link_layout.addWidget(self.link_summary_edit)
        
        link_layout.addWidget(auto_btn)
        link_layout.addStretch()
        self.add_item_stack.addWidget(link_widget)
        self.link_url_edit.editingFinished.connect(self.clean_link_url)

        file_widget = QWidget()
        file_layout = QVBoxLayout(file_widget)
        self.drop_area = DropArea(self.strings[self.current_lang]["drag_hint"])
        self.drop_area.file_dropped.connect(self.on_file_dropped)
        file_drop_label = QLabel(self.strings[self.current_lang]["file_drop"])
        file_drop_label.setObjectName("label_file_drop")
        file_layout.addWidget(file_drop_label)
        file_layout.addWidget(self.drop_area)
        file_title_label = QLabel(self.strings[self.current_lang]["title_label"])
        file_title_label.setObjectName("label_file_title")
        file_layout.addWidget(file_title_label)
        self.file_title_edit = QLineEdit()
        self.file_title_edit.setObjectName("file_title_edit")
        self.file_title_edit.setPlaceholderText(self.strings[self.current_lang]["file_title_placeholder"])
        file_layout.addWidget(self.file_title_edit)
        file_layout.addWidget(QLabel(self.strings[self.current_lang]["category_label"]))
        self.file_category_edit = QLineEdit()
        file_category_label = QLabel(self.strings[self.current_lang]["category_label"])
        file_category_label.setObjectName("label_file_category")
        file_layout.addWidget(file_category_label)
        self.file_category_edit.setPlaceholderText(self.strings[self.current_lang]["category_placeholder"])
        file_layout.addWidget(self.file_category_edit)
        
        file_cover_label = QLabel(self.strings[self.current_lang].get("cover_label", "Cover:"))
        file_cover_label.setObjectName("label_file_cover")
        file_layout.addWidget(file_cover_label)
        self.file_cover_edit = QLineEdit()
        self.file_cover_edit.setObjectName("file_cover_edit")
        self.file_cover_edit.setPlaceholderText(self.strings[self.current_lang].get("cover_url_placeholder", "Cover URL or local path"))
        file_layout.addWidget(self.file_cover_edit)
        
        file_cover_btn = QPushButton(self.strings[self.current_lang].get("select_cover", "Select Cover"))
        file_cover_btn.setObjectName("file_cover_btn")
        file_cover_btn.clicked.connect(self.select_cover_for_item)
        file_layout.addWidget(file_cover_btn)
        
        file_summary_label = QLabel(self.strings[self.current_lang].get("summary_label", "Summary:"))
        file_summary_label.setObjectName("label_file_summary")
        file_layout.addWidget(file_summary_label)
        self.file_summary_edit = QTextEdit()
        self.file_summary_edit.setObjectName("file_summary_edit")
        self.file_summary_edit.setPlaceholderText(self.strings[self.current_lang].get("summary_placeholder", "Enter summary..."))
        self.file_summary_edit.setMaximumHeight(100)
        file_layout.addWidget(self.file_summary_edit)
        
        self.ai_summary_btn = QPushButton(self.strings[self.current_lang].get("ai_summary_btn", "AI Generate Summary"))
        self.ai_summary_btn.setObjectName("ai_summary_btn")
        self.ai_summary_btn.clicked.connect(self.generate_ai_summary)
        file_layout.addWidget(self.ai_summary_btn)
        
        file_layout.addStretch()
        self.add_item_stack.addWidget(file_widget)

        confirm_btn = QPushButton(self.strings[self.current_lang]["confirm"])
        confirm_btn.setObjectName("confirm_btn")
        confirm_btn.clicked.connect(self.add_item_confirm)
        layout.addWidget(confirm_btn)

        self.dropped_file_path = None

    def clean_link_url(self):
        raw = self.link_url_edit.text()
        cleaned = self.extract_url_from_text(raw)
        if cleaned != raw:
            self.link_url_edit.setText(cleaned)

    def enable_multi_select_mode(self):
        self.multi_select_mode = True
        for i in range(self.items_grid_layout.count()):
            card = self.items_grid_layout.itemAt(i).widget()
            if isinstance(card, ItemCard):
                card.set_multi_select_mode(True)
                card.checkbox.setChecked(False)
                card.is_selected = False
        self.multi_select_bar.setVisible(True)

    def exit_multi_select_mode(self):
        self.multi_select_mode = False
        for i in range(self.items_grid_layout.count()):
            card = self.items_grid_layout.itemAt(i).widget()
            if isinstance(card, ItemCard):
                card.set_multi_select_mode(False)
        self.multi_select_bar.setVisible(False)

    def delete_selected_items(self):
        selected_ids = []
        for i in range(self.items_grid_layout.count()):
            card = self.items_grid_layout.itemAt(i).widget()
            if isinstance(card, ItemCard) and card.checkbox.isChecked():
                selected_ids.append(card.item_id)
        if not selected_ids:
            self.show_toast(self.strings[self.current_lang]["no_item_selected"])
            return
        reply = QMessageBox.question(self, self.strings[self.current_lang]["confirm_delete"],
                                     self.strings[self.current_lang]["batch_delete_confirm"].format(len(selected_ids)),
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.exit_multi_select_mode()
            self.db.delete_items_by_ids(selected_ids)
            self.load_items_in_folder(self.current_folder_id)

    def switch_add_item_type(self, index):
        self.add_item_stack.setCurrentIndex(index)

    def on_file_dropped(self, file_path):
        import os
        self.dropped_file_path = file_path
        basename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(basename)[0]
        self.file_title_edit.setText(name_without_ext)
        ext = os.path.splitext(file_path)[1].lstrip('.').upper()
        if ext:
            self.file_category_edit.setText(ext)
        else:
            self.file_category_edit.setText(self.strings[self.current_lang]["default_file_category"])
        self.drop_area.setText(self.strings[self.current_lang]["file_selected_prefix"] + basename)

    def auto_fetch_link_info(self):
        url = self.link_url_edit.text().strip()
        if not url:
            self.show_toast(self.strings[self.current_lang]["warning_empty_link"])
            return
        url = self.extract_url_from_text(url)
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        self.auto_fetch_btn.setEnabled(False)
        self.auto_fetch_btn.setText(self.strings[self.current_lang]["fetching"])

        self.fetch_thread = FetchThread(url)
        self.fetch_thread.finished.connect(self.on_fetch_finished)
        self.fetch_thread.error.connect(self.on_fetch_error)
        self.fetch_thread.start()

    def on_fetch_finished(self, result):
        title = result.get('title', '')
        category_key = result.get('category', 'uncategorized')
        cover = result.get('cover', '')
        category_display = self.category_translations[self.current_lang].get(category_key, category_key)
        print(f"[DEBUG] Auto fetch result: title={title}, category={category_display}, cover={cover}")
        if title:
            self.link_title_edit.setText(title)
        if category_display:
            self.link_category_edit.setText(category_display)
        if cover:
            self.link_cover_edit.setText(cover)
            print(f"[DEBUG] Cover URL set to: {cover}")
        else:
            print(f"[DEBUG] No cover found")
        self.auto_fetch_btn.setEnabled(True)
        self.auto_fetch_btn.setText(self.strings[self.current_lang]["auto_fetch"])
        self.show_toast(self.strings[self.current_lang]["auto_fetch_success"].format(title, category_display))

    def on_fetch_error(self, error_msg):
        self.auto_fetch_btn.setEnabled(True)
        self.auto_fetch_btn.setText(self.strings[self.current_lang]["auto_fetch"])
        self.show_toast(f"获取失败：{error_msg}\n请检查网络或链接是否正确。")

    def add_item_confirm(self):
        if self.current_folder_id is None:
            self.show_toast(self.strings[self.current_lang]["warning_no_folder"])
            return
        item_type = "link" if self.item_type_combo.currentIndex() == 0 else "file"
        cover_path = ""
        if item_type == "link":
            cover_path = getattr(self, 'link_cover_edit', None) and self.link_cover_edit.text().strip() or ""
        else:
            cover_path = getattr(self, 'file_cover_edit', None) and self.file_cover_edit.text().strip() or ""
        
        if cover_path and cover_path.startswith(('http://', 'https://')):
            import warnings
            from urllib3.exceptions import InsecureRequestWarning
            warnings.filterwarnings('ignore', category=InsecureRequestWarning)
            
            # 创建持久化的封面存储目录
            covers_dir = os.path.join(os.path.expanduser('~'), '.favourite', 'covers')
            os.makedirs(covers_dir, exist_ok=True)
            
            image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.avif')
            
            from urllib.parse import urlparse
            parsed = urlparse(cover_path)
            path_lower = parsed.path.lower()
            
            is_image_url = any(path_lower.endswith(ext) for ext in image_extensions)
            
            actual_image_url = cover_path
            
            if not is_image_url:
                try:
                    from cover_extractor import extract_cover
                    actual_image_url = extract_cover(cover_path)
                    
                    if not actual_image_url:
                        self.show_toast(self.strings[self.current_lang].get("download_failed", "Download failed: ") + "无法从页面中提取封面图片")
                        return
                except Exception as e:
                    self.show_toast(self.strings[self.current_lang].get("download_failed", "Download failed: ") + f"提取封面失败: {str(e)}")
                    return
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'identity'
            }
            
            # 根据域名设置正确的 Referer
            if 'hdslb.com' in actual_image_url or 'bilibili' in actual_image_url:
                headers['Referer'] = 'https://www.bilibili.com/'
            elif 'douyinpic' in actual_image_url or 'douyin' in actual_image_url:
                headers['Referer'] = 'https://www.douyin.com/'
            elif 'xiaohongshu' in actual_image_url:
                headers['Referer'] = 'https://www.xiaohongshu.com/'
            
            try:
                print(f"[DEBUG] Downloading cover from: {actual_image_url}")
                response = requests.get(actual_image_url, timeout=8, headers=headers, allow_redirects=True, stream=True, verify=False)
                response.raise_for_status()
                
                # 使用持久化目录存储临时文件
                temp_path = os.path.join(covers_dir, f"temp_{self.current_folder_id}_{hash(cover_path)}.tmp")
                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                from PIL import Image
                with Image.open(temp_path) as img:
                    target_w, target_h = 360, 200
                    img_w, img_h = img.size
                    
                    print(f"[DEBUG] Original image: {img_w}x{img_h}")
                    
                    scale_w = target_w / img_w
                    scale_h = target_h / img_h
                    scale = max(scale_w, scale_h)
                    
                    new_w = max(int(img_w * scale), target_w)
                    new_h = max(int(img_h * scale), target_h)
                    
                    img = img.resize((new_w, new_h), Image.LANCZOS)
                    print(f"[DEBUG] Resized to: {new_w}x{new_h}")
                    
                    left = max(0, (new_w - target_w) // 2)
                    top = max(0, (new_h - target_h) // 2)
                    right = min(new_w, left + target_w)
                    bottom = min(new_h, top + target_h)
                    
                    img = img.crop((left, top, right, bottom))
                    print(f"[DEBUG] Cropped to: {img.size[0]}x{img.size[1]}")
                    
                    png_path = os.path.join(covers_dir, f"cover_{self.current_folder_id}_{hash(cover_path)}.png")
                    img.save(png_path, 'PNG')
                
                # 删除临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
                cover_path = png_path
                print(f"[DEBUG] Cover downloaded and saved to persistent storage")
            except Exception as e:
                print(f"[DEBUG] Cover download failed: {str(e)}")
                self.show_toast(self.strings[self.current_lang].get("download_failed", "Download failed: ") + str(e))
                return
        
        summary = ""
        if item_type == "link":
            summary = getattr(self, 'link_summary_edit', None) and self.link_summary_edit.toPlainText().strip() or ""
        else:
            summary = getattr(self, 'file_summary_edit', None) and self.file_summary_edit.toPlainText().strip() or ""
        
        if self.editing_item_id is not None:
            if item_type == "link":
                raw_url = self.link_url_edit.text().strip()
                url = self.extract_url_from_text(raw_url)
                if not url:
                    self.show_toast(self.strings[self.current_lang]["warning_empty_url"])
                    return
                title = self.link_title_edit.text().strip() or url
                category = self.link_category_edit.text().strip() or self.strings[self.current_lang]["default_category"]
                self.db.update_item(self.editing_item_id, title, url, category, cover_path, summary)
            else:
                if not self.dropped_file_path:
                    self.show_toast(self.strings[self.current_lang]["warning_drag_file"])
                    return
                title = self.file_title_edit.text().strip() or os.path.basename(self.dropped_file_path)
                category = self.file_category_edit.text().strip() or self.strings[self.current_lang]["default_file_category"]
                self.db.update_item(self.editing_item_id, title, self.dropped_file_path, category, cover_path, summary)
            self.show_toast(self.strings[self.current_lang]["success_update"])
            self.editing_item_id = None
            self.editing_item_type = None
            self.switch_to_page(1)
        else:
            if item_type == "link":
                url = self.link_url_edit.text().strip()
                url = self.extract_url_from_text(url)
                if not url:
                    self.show_toast(self.strings[self.current_lang]["warning_empty_link"])
                    return
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                from urllib.parse import urlparse
                parsed = urlparse(url)
                if not parsed.netloc:
                    self.show_toast(self.strings[self.current_lang]["warning_invalid_link"])
                    return
                title = self.link_title_edit.text().strip() or url
                category = self.link_category_edit.text().strip() or "未分类"
                self.db.add_item(self.current_folder_id, item_type, title, url, category, cover_path, summary)
            else:
                if not self.dropped_file_path:
                    self.show_toast(self.strings[self.current_lang]["warning_drag_file_to_area"])
                    return
                title = self.file_title_edit.text().strip() or os.path.basename(self.dropped_file_path)
                category = self.file_category_edit.text().strip() or "文件"
                self.db.add_item(self.current_folder_id, item_type, title, self.dropped_file_path, category, cover_path, summary)
            self.show_toast(self.strings[self.current_lang]["success_add"])
            self.switch_to_page(1)
        self.link_url_edit.clear()
        self.link_title_edit.clear()
        self.link_category_edit.clear()
        self.link_cover_edit.clear()
        if hasattr(self, 'link_summary_edit'):
            self.link_summary_edit.clear()
        self.file_title_edit.clear()
        self.file_category_edit.clear()
        self.file_cover_edit.clear()
        if hasattr(self, 'file_summary_edit'):
            self.file_summary_edit.clear()
        self.dropped_file_path = None
        self.drop_area.setText(self.strings[self.current_lang]["drag_hint"])
        self.load_items_in_folder(self.current_folder_id)

    def select_cover_for_item(self):
        """选择封面（整合文件选择和预设封面）"""
        from cover_presets import PRESET_COVERS, generate_preset_cover
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QScrollArea, QWidget, QTabWidget, QFileDialog
        from PyQt6.QtCore import QSize
        
        dialog = QDialog(self)
        dialog.setWindowTitle(self.strings[self.current_lang].get("select_cover", "Select Cover"))
        dialog.setFixedSize(450, 450)
        
        tab_widget = QTabWidget()
        
        # === 文件选择选项卡 ===
        file_tab = QWidget()
        file_layout = QVBoxLayout(file_tab)
        
        file_label = QLabel(self.strings[self.current_lang].get("select_cover_hint", "选择本地图片文件作为封面"))
        file_layout.addWidget(file_label)
        
        file_btn = QPushButton(self.strings[self.current_lang].get("browse_files", "浏览文件"))
        file_layout.addWidget(file_btn)
        
        self.selected_file_path = ""
        self.selected_file_label = QLabel(self.strings[self.current_lang].get("no_file_selected", "未选择文件"))
        self.selected_file_label.setStyleSheet("color: #666; font-size: 12px;")
        file_layout.addWidget(self.selected_file_label)
        
        file_layout.addStretch()
        
        def browse_file():
            file_path, _ = QFileDialog.getOpenFileName(self, 
                                                       self.strings[self.current_lang].get("select_cover", "Select Cover Image"),
                                                       "",
                                                       "Image Files (*.png *.jpg *.jpeg *.gif *.bmp *.svg)")
            if file_path:
                self.selected_file_path = file_path
                self.selected_file_label.setText(file_path)
        
        file_btn.clicked.connect(browse_file)
        tab_widget.addTab(file_tab, self.strings[self.current_lang].get("local_file", "本地文件"))
        
        # === 预设封面选项卡 ===
        preset_tab = QWidget()
        preset_layout = QVBoxLayout(preset_tab)
        preset_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建固定大小的内容区域，确保4列按钮居中
        content_widget = QWidget()
        content_widget.setFixedWidth(392)  # 4 * 90 + 3 * 12 = 392
        
        grid_layout = QGridLayout(content_widget)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(12)
        
        row = 0
        col = 0
        for preset_type, info in PRESET_COVERS.items():
            # 生成封面预览
            pixmap = generate_preset_cover(preset_type, QSize(80, 50))
            
            # 创建自定义按钮Widget
            btn_widget = QWidget()
            btn_widget.setFixedSize(90, 70)
            btn_widget.setStyleSheet("""
                QWidget {
                    border-radius: 6px;
                    background-color: #f0f0f0;
                }
                QWidget:hover {
                    background-color: #e0e0e0;
                }
                QWidget:pressed {
                    background-color: #d0d0d0;
                }
            """)
            
            # 创建按钮内部布局
            btn_layout = QVBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(2)
            
            # 添加弹性空间（上下各一个）
            btn_layout.addStretch()
            
            # 设置图标（居中，不拉伸）
            icon_label = QLabel()
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setFixedSize(80, 50)
            icon_label.setScaledContents(False)
            btn_layout.addWidget(icon_label)
            
            # 获取预设名称（支持多语言）
            name = info["name"].get(self.current_lang, info["name"].get("zh", "未知"))
            
            # 创建名称标签（居中）
            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setStyleSheet("font-size: 11px; color: #333;")
            btn_layout.addWidget(name_label)
            
            # 添加弹性空间
            btn_layout.addStretch()
            
            # 点击事件（使用鼠标释放事件）
            btn_widget.mouseReleaseEvent = lambda event, pt=preset_type: self.on_cover_selected(f"preset://{pt}", dialog)
            
            grid_layout.addWidget(btn_widget, row, col)
            col += 1
            if col >= 4:
                col = 0
                row += 1
        
        # 将内容区域放在居中布局中
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(content_widget)
        center_layout.addStretch()
        
        # 将居中布局放在滚动区域中
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.addLayout(center_layout)
        scroll_layout.addStretch()
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_content)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        preset_layout.addWidget(scroll_area)
        
        tab_widget.addTab(preset_tab, self.strings[self.current_lang].get("preset_cover", "预设封面"))
        
        # === 底部按钮 ===
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton(self.strings[self.current_lang].get("confirm", "确认"))
        ok_btn.clicked.connect(lambda: self.on_cover_selected(self.selected_file_path, dialog))
        cancel_btn = QPushButton(self.strings[self.current_lang].get("cancel", "取消"))
        cancel_btn.clicked.connect(dialog.close)
        
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        
        # === 主布局 ===
        main_layout = QVBoxLayout(dialog)
        main_layout.addWidget(tab_widget)
        main_layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def on_cover_selected(self, cover_path, dialog):
        """封面选择完成"""
        if not cover_path:
            dialog.close()
            return
        
        mode = "link" if self.item_type_combo.currentIndex() == 0 else "file"
        if mode == "link":
            self.link_cover_edit.setText(cover_path)
        else:
            self.file_cover_edit.setText(cover_path)
        dialog.close()

    def generate_ai_summary(self):
        print(f"[DEBUG] generate_ai_summary called")
        print(f"[DEBUG] dropped_file_path: {self.dropped_file_path}")
        
        if not self.dropped_file_path:
            self.show_toast(self.strings[self.current_lang].get("warning_drag_file", "请先拖拽文件"))
            print(f"[DEBUG] dropped_file_path is empty")
            return
        
        if not os.path.exists(self.dropped_file_path):
            self.show_toast(self.strings[self.current_lang].get("file_not_found", "文件不存在"))
            print(f"[DEBUG] file not found: {self.dropped_file_path}")
            return
        
        print(f"[DEBUG] file exists: {self.dropped_file_path}")
        
        # 获取当前语言
        language = self.current_lang
        print(f"[DEBUG] language: {language}")
        
        # 清空之前的摘要内容
        self.file_summary_edit.setPlainText("")
        
        # 禁用按钮并显示加载提示
        self.ai_summary_btn.setEnabled(False)
        self.ai_summary_btn.setText(self.strings[self.current_lang].get("ai_generating", "AI生成中..."))
        
        # 流式输出回调函数（使用信号机制实现线程安全）
        def stream_callback(token):
            self.summary_token_signal.emit(token)
        
        # 在新线程中执行AI生成，避免阻塞UI
        def generate_in_thread():
            print(f"[DEBUG] generate_in_thread started")
            try:
                from summary_generator import generate_summary_with_ai_from_file
                
                # 使用流式输出
                print(f"[DEBUG] calling generate_summary_with_ai_from_file with streaming")
                summary = generate_summary_with_ai_from_file(
                    self.dropped_file_path, 
                    language=language,
                    callback=stream_callback  # 启用流式回调
                )
                print(f"[DEBUG] summary result: {summary[:50] if summary else 'None'}")
                
                # 安全网：如果流式输出失败，直接设置最终结果
                if summary:
                    self.summary_result_signal.emit(summary)
                    if language == "zh":
                        self.toast_signal.emit("AI摘要生成成功")
                    else:
                        self.toast_signal.emit("AI summary generated successfully")
                else:
                    if language == "zh":
                        self.toast_signal.emit("无法生成摘要，请检查文件内容")
                    else:
                        self.toast_signal.emit("Cannot generate summary, please check file content")
            except Exception as e:
                print(f"[DEBUG] AI summary generation failed: {str(e)}")
                import traceback
                traceback.print_exc()
                if language == "zh":
                    self.toast_signal.emit(f"AI摘要生成失败: {str(e)}")
                else:
                    self.toast_signal.emit(f"AI summary generation failed: {str(e)}")
            finally:
                # 恢复按钮状态（线程安全）
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(0, self._reset_ai_button)
        
        # 启动新线程
        import threading
        thread = threading.Thread(target=generate_in_thread)
        thread.daemon = True
        thread.start()
        print(f"[DEBUG] thread started")
    
    def _update_summary_stream(self, token):
        """流式更新摘要文本（追加模式）"""
        current_text = self.file_summary_edit.toPlainText()
        self.file_summary_edit.setPlainText(current_text + token)
    
    def _set_summary_result(self, summary):
        """设置最终摘要结果（作为流式输出失败时的安全网）"""
        current_text = self.file_summary_edit.toPlainText()
        # 如果当前文本为空或与最终结果不一致，直接设置
        if not current_text or current_text != summary:
            self.file_summary_edit.setPlainText(summary)
    
    def _reset_ai_button(self):
        """线程安全的按钮状态重置"""
        self.ai_summary_btn.setEnabled(True)
        self.ai_summary_btn.setText(self.strings[self.current_lang].get("ai_summary_btn", "AI生成摘要"))

    def resizeEvent(self, event):
        if self.settings_overlay:
            self.settings_overlay.setGeometry(0, 0, self.width(), self.height())
        # 更新所有侧边栏的高度
        for sidebar in self.settings_sidebars:
            sidebar.setFixedHeight(self.height())
        # 如果主菜单存在且没有子菜单，确保其紧贴右边缘
        if len(self.settings_sidebars) == 1:
            main_menu = self.settings_sidebars[0]
            main_menu.move(self.width() - main_menu.width(), 0)
        super().resizeEvent(event)
        if self.password_overlay:
            self.password_overlay.setGeometry(0, 0, self.width(), self.height())
        if self.password_sidebar:
            # 如果侧边栏已显示，更新其高度（宽度固定）
            self.password_sidebar.setFixedHeight(self.height())
            # 确保其左侧位置正确（0）
            self.password_sidebar.move(0, 0)

    def _create_password_sidebar(self, mode, target_type, target_id, callback=None):
        """
        mode: 'setup', 'change', 'remove', 'input'
        target_type: 'folder' or 'item'
        target_id: 对应的 id
        callback: 仅 input 模式使用，验证成功后调用
        """
        sidebar = QWidget(self)
        sidebar.setFixedWidth(300)
        sidebar.setStyleSheet("background-color: #f5f5f5; border-right: 1px solid #ccc;")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 返回按钮
        back_btn = QPushButton(self.strings[self.current_lang]["back"])
        back_btn.clicked.connect(self.close_password_sidebar)
        layout.addWidget(back_btn)

        # 标题
        title = QLabel()
        if mode == 'setup':
            title.setText(self.strings[self.current_lang]["set_password"])
        elif mode == 'change':
            title.setText(self.strings[self.current_lang]["change_password"])
        elif mode == 'remove':
            title.setText(self.strings[self.current_lang]["remove_password"])
        elif mode == 'input':
            title.setText(self.strings[self.current_lang]["input_password"])
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # 错误提示
        self.password_error_label = QLabel()
        self.password_error_label.setStyleSheet("color: red;")
        self.password_error_label.setVisible(False)
        layout.addWidget(self.password_error_label)

        # 根据模式动态添加输入框
        self.password_inputs = []  # 存储所有 QLineEdit
        if mode == 'setup':
            layout.addWidget(QLabel(self.strings[self.current_lang]["new_password"] + ":"))
            pwd1 = QLineEdit();
            pwd1.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(pwd1)
            layout.addWidget(QLabel(self.strings[self.current_lang]["confirm_new_password"] + ":"))
            pwd2 = QLineEdit();
            pwd2.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(pwd2)
            self.password_inputs = [pwd1, pwd2]
        elif mode == 'change':
            layout.addWidget(QLabel(self.strings[self.current_lang]["old_password"] + ":"))
            old_pwd = QLineEdit();
            old_pwd.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(old_pwd)
            layout.addWidget(QLabel(self.strings[self.current_lang]["new_password"] + ":"))
            new_pwd1 = QLineEdit();
            new_pwd1.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(new_pwd1)
            layout.addWidget(QLabel(self.strings[self.current_lang]["confirm_new_password"] + ":"))
            new_pwd2 = QLineEdit();
            new_pwd2.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(new_pwd2)
            self.password_inputs = [old_pwd, new_pwd1, new_pwd2]
        elif mode == 'remove':
            layout.addWidget(QLabel(self.strings[self.current_lang]["enter_old_password"] + ":"))
            pwd = QLineEdit();
            pwd.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(pwd)
            self.password_inputs = [pwd]
        elif mode == 'input':
            layout.addWidget(QLabel(self.strings[self.current_lang]["enter_password"] + ":"))
            pwd = QLineEdit();
            pwd.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(pwd)
            self.password_inputs = [pwd]

        # 确认按钮
        confirm_btn = QPushButton(self.strings[self.current_lang]["confirm"])
        confirm_btn.setObjectName("confirm_btn")  # 添加这一行
        confirm_btn.clicked.connect(lambda: self._on_password_confirm(mode, target_type, target_id, callback))
        layout.addWidget(confirm_btn)

        layout.addStretch()
        return sidebar

    def _on_password_confirm(self, mode, target_type, target_id, callback):
        # 获取所有输入框的内容
        inputs = [edit.text().strip() for edit in self.password_inputs]
        # 根据模式验证
        if mode == 'setup':
            if len(inputs) != 2:
                return
            if not inputs[0] or not inputs[1]:
                self._show_password_error(self.strings[self.current_lang]["password_cannot_be_empty"])
                return
            if inputs[0] != inputs[1]:
                self._show_password_error(self.strings[self.current_lang]["passwords_do_not_match"])
                return
            # 设置密码
            if target_type == 'folder':
                self.db.set_folder_password(target_id, inputs[0])
            else:
                self.db.set_item_password(target_id, inputs[0])
            self._close_password_sidebar_and_refresh()
        elif mode == 'change':
            if len(inputs) != 3:
                return
            old, new1, new2 = inputs
            # 验证原密码
            if target_type == 'folder':
                if not self.db.verify_folder_password(target_id, old):
                    self._show_password_error(self.strings[self.current_lang]["old_password_incorrect"])
                    return
                self.db.set_folder_password(target_id, new1)
            else:
                if not self.db.verify_item_password(target_id, old):
                    self._show_password_error(self.strings[self.current_lang]["old_password_incorrect"])
                    return
                self.db.set_item_password(target_id, new1)
            if not new1 or not new2:
                self._show_password_error(self.strings[self.current_lang]["password_cannot_be_empty"])
                return
            if new1 != new2:
                self._show_password_error(self.strings[self.current_lang]["passwords_do_not_match"])
                return
            # 更新密码
            if target_type == 'folder':
                self.db.set_folder_password(target_id, new1)
            else:
                self.db.set_item_password(target_id, new1)
            self._close_password_sidebar_and_refresh()
        elif mode == 'remove':
            if len(inputs) != 1:
                return
            pwd = inputs[0]
            if target_type == 'folder':
                if not self.db.verify_folder_password(target_id, pwd):
                    self._show_password_error(self.strings[self.current_lang]["password_incorrect"])
                    return
                self.db.remove_folder_password(target_id)
            else:
                if not self.db.verify_item_password(target_id, pwd):
                    self._show_password_error(self.strings[self.current_lang]["password_incorrect"])
                    return
                self.db.remove_item_password(target_id)
            self._close_password_sidebar_and_refresh()
        elif mode == 'input':
            if len(inputs) != 1:
                return
            pwd = inputs[0]
            valid = False
            if target_type == 'folder':
                valid = self.db.verify_folder_password(target_id, pwd)
            else:
                valid = self.db.verify_item_password(target_id, pwd)
            if valid:
                self.close_password_sidebar()
                if callback:
                    callback()
            else:
                self._show_password_error(self.strings[self.current_lang]["password_incorrect"])

    def _show_password_error(self, msg):
        self.password_error_label.setText(msg)
        self.password_error_label.setVisible(True)

    def _close_password_sidebar_and_refresh(self):
        self.close_password_sidebar()
        # 刷新当前视图以更新锁图标
        self.refresh_current_view()

    def refresh_current_view(self):
        """刷新当前视图 - 同时刷新收藏项列表的数据"""
        # 无论在哪个页面，都刷新收藏项列表（密码状态可能已改变）
        if self.current_folder_id is not None:
            self.load_items_in_folder(self.current_folder_id)
        
        # 如果当前在文件夹列表页，也刷新它
        index = self.stacked_widget.currentIndex()
        if index == 0:
            self.load_folders()

    def open_password_setup(self, target_type, target_id):
        self._show_password_sidebar('setup', target_type, target_id)

    def open_password_change(self, target_type, target_id):
        self._show_password_sidebar('change', target_type, target_id)

    def open_password_remove(self, target_type, target_id):
        self._show_password_sidebar('remove', target_type, target_id)

    def show_password_input(self, target_type, target_id, callback):
        self._show_password_sidebar('input', target_type, target_id, callback)

    def _show_password_sidebar(self, mode, target_type, target_id, callback=None):
        # 如果已有侧边栏，先关闭
        self.close_password_sidebar()

        # 遮罩
        self.password_overlay = QWidget(self)
        self.password_overlay.setGeometry(0, 0, self.width(), self.height())
        self.password_overlay.setStyleSheet("background-color: rgba(0,0,0,0.3);")
        self.password_overlay.mousePressEvent = lambda e: self.close_password_sidebar()
        self.password_overlay.raise_()
        self.password_overlay.show()

        # 侧边栏
        sidebar = self._create_password_sidebar(mode, target_type, target_id, callback)
        sidebar.setParent(self)
        width = sidebar.width()
        height = self.height()
        # 初始位置：完全在左侧外
        sidebar.setGeometry(-width, 0, width, height)
        sidebar.raise_()
        sidebar.show()

        self.password_sidebar = sidebar

        # 动画滑入
        anim = QPropertyAnimation(sidebar, b"geometry")
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.setStartValue(sidebar.geometry())
        anim.setEndValue(QRect(0, 0, width, height))
        anim.start()
        self.password_anim = anim

        self.apply_theme()

    def close_password_sidebar(self):
        if self.password_sidebar is None:
            return
        sidebar = self.password_sidebar
        width = sidebar.width()
        anim = QPropertyAnimation(sidebar, b"geometry")
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.setStartValue(sidebar.geometry())
        anim.setEndValue(QRect(-width, 0, width, self.height()))
        anim.finished.connect(self._cleanup_password_sidebar)
        anim.start()
        self.password_anim = anim

    def _cleanup_password_sidebar(self):
        if self.password_sidebar:
            self.password_sidebar.deleteLater()
            self.password_sidebar = None
        if self.password_overlay:
            self.password_overlay.deleteLater()
            self.password_overlay = None
        if self.password_anim:
            self.password_anim = None
        self.password_error_label = None
        self.password_inputs = []
