import os
import re
import webbrowser
import subprocess
import sqlite3
import sys
import json
from urllib.parse import urlparse

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QScrollArea, QMessageBox,
    QInputDialog, QStackedWidget, QLabel, QMenu, QApplication,
    QComboBox, QDialog, QDialogButtonBox, QCheckBox, QColorDialog,
    QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, QRect,QParallelAnimationGroup
from PyQt6.QtGui import QIcon, QPixmap, QAction, QDragEnterEvent, QDropEvent, QColor

from database import Database
from widgets import FolderCard, ItemCard

def resource_path(relative_path):
    """获取资源的绝对路径，兼容开发环境和 PyInstaller 打包后的环境"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

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


class MainWindow(QMainWindow):
    # 类变量保存当前主题色和显示模式
    current_theme_color = QColor("#0078d7")   # 默认蓝色
    current_dark_mode = False

    def __init__(self):
        super().__init__()
        self.setWindowTitle("收藏管理器")
        self.setGeometry(100, 100, 1200, 800)
        self.anim_group = None
        self.db = Database()

        # 翻译
        self.current_lang = "zh"  # 默认中文
        # 加载保存的语言偏好
        saved_lang = self.load_language_preference()
        if saved_lang:
            self.current_lang = saved_lang
        self.strings = {
            "zh": {
                "window_title": "收藏管理器",
                "folder_search_placeholder": "搜索收藏夹...",
                "add_folder_btn": "+ 添加收藏夹",
                "settings_title": "⚙ 设置",
                "display_settings": "显示设置",
                "language": "语言",
                "about": "关于",
                "display_title": "← 显示设置",
                "display_mode": "显示模式",
                "light_mode": "浅色",
                "dark_mode": "深色",
                "theme_color": "主题色",
                "select_color": "选择颜色",
                "about_title": "← 关于",
                "version": "版本: v0.0.2-beta",
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
            },
            "en": {
               "window_title": "Favorites Manager",
                "folder_search_placeholder": "Search folders...",
                "add_folder_btn": "+ Add Folder",
                "settings_title": "⚙ Settings",
                "display_settings": "Display Settings",
                "language": "Language",
                "about": "About",
                "display_title": "← Display Settings",
                "display_mode": "Display Mode",
                "light_mode": "Light",
                "dark_mode": "Dark",
                "theme_color": "Theme Color",
                "select_color": "Choose Color",
                "about_title": "← About",
                "version": "Version: v0.0.2-beta",
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
            }
        }

        # 中心控件: 使用 QStackedWidget 实现横推动画切换
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # 页面0: 收藏夹列表页
        self.folders_page = QWidget()
        self.setup_folders_page()
        self.stacked_widget.addWidget(self.folders_page)

        # 页面1: 某个收藏夹内部的详情页（收藏项列表）
        self.items_page = QWidget()
        self.setup_items_page()
        self.stacked_widget.addWidget(self.items_page)
        self.current_category_filter = None
        self.multi_select_mode = False
        self.selected_item_ids = set()
        self.editing_item_id = None
        self.editing_item_type = None

        # 页面2: 添加收藏项页面
        self.add_item_page = QWidget()
        self.setup_add_item_page()
        self.stacked_widget.addWidget(self.add_item_page)

        self.stacked_widget.setCurrentIndex(0)
        self.current_folder_id = None

        # 设置侧边栏相关属性
        self.settings_sidebars = []        # 存储当前打开的侧边栏（从外到内）
        self.settings_overlay = None       # 遮罩
        self.settings_animations = []      # 动画对象（用于清理）

        self.apply_theme()

        self.apply_language()

    def load_language_preference(self):
        """从配置文件加载语言偏好"""
        config_path = "config.json"
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                lang = data.get("language")
                if lang in ("zh", "en"):
                    return lang
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return None

    def save_language_preference(self, lang):
        """保存语言偏好到配置文件"""
        config_path = "config.json"
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump({"language": lang}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

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

        # 选项按钮
        btn_display = QPushButton(self.strings[self.current_lang]["display_settings"])
        btn_display.clicked.connect(self.on_display_settings_clicked)
        layout.addWidget(btn_display)

        btn_language = QPushButton(self.strings[self.current_lang]["language"])
        btn_language.clicked.connect(self.on_language_settings_clicked)
        layout.addWidget(btn_language)

        btn_about = QPushButton(self.strings[self.current_lang]["about"])
        btn_about.clicked.connect(self.on_about_settings_clicked)
        layout.addWidget(btn_about)

        layout.addStretch()
        return sidebar

    def on_display_settings_clicked(self):
        """处理点击“显示设置”"""
        self.toggle_sub_sidebar("display")

    def on_about_settings_clicked(self):
        """处理点击“关于”"""
        self.toggle_sub_sidebar("about")

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
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-left: 1px solid #ccc;
            }
            QLabel {
                padding: 8px 16px;
            }
            QComboBox, QPushButton {
                margin: 4px 16px;
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 标题（带返回指示）
        title = QLabel("← " + self.strings[self.current_lang]["display_title"])
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

        layout.addStretch()
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

        title = QLabel("← " + self.strings[self.current_lang]["about_title"])
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
        """显示模式切换"""
        dark_mode = (index == 1)  # 1: 深色
        MainWindow.current_dark_mode = dark_mode
        self.apply_theme()

    def on_color_picker_clicked(self):
        """弹出颜色选择对话框"""
        color = QColorDialog.getColor(MainWindow.current_theme_color, self, self.strings[self.current_lang]["select_theme_color"])
        if color.isValid():
            MainWindow.current_theme_color = color
            self.apply_theme()
            # 更新侧边栏中的颜色预览
            for sidebar in self.settings_sidebars:
                for child in sidebar.findChildren(QLabel):
                    if child.property("color_preview"):
                        child.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #888;")

    def apply_theme(self):
        color = MainWindow.current_theme_color
        color_str = color.name()
        dark = MainWindow.current_dark_mode
        bg_color = "#2b2b2b" if dark else "#ffffff"
        text_color = "#ffffff" if dark else "#000000"
        alt_bg = "#3c3c3c" if dark else "#f5f5f5"
        border_color = "#555" if dark else "#ccc"
        hover_bg = f"{color_str}40"

        # 主窗口
        self.setStyleSheet(f"QMainWindow {{ background-color: {bg_color}; color: {text_color}; }}")

        # 三个主要页面
        for page in (self.folders_page, self.items_page, self.add_item_page):
            page.setStyleSheet(f"background-color: {bg_color}; color: {text_color};")

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
            widget.setStyleSheet(button_style)

        # 卡片
        card_style = f"""
            border: 1px solid {color_str};
            border-radius: 8px;
            background-color: {alt_bg};
        """
        for card in self.findChildren((FolderCard, ItemCard)):
            card.setStyleSheet(card_style)

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
        self.save_language_preference(lang)
        self.close_all_settings()  # 切换后关闭设置侧边栏

    def apply_language(self):
        # 更新窗口标题
        self.setWindowTitle(self.strings[self.current_lang]["window_title"])

        # 更新搜索框占位符
        for obj_name, placeholder_key in [("folder_search", "folder_search_placeholder"),
                                          ("item_search", "item_search_placeholder")]:
            widget = getattr(self, obj_name, None)
            if widget:
                widget.setPlaceholderText(self.strings[self.current_lang][placeholder_key])

        for obj_name, text_key in [
            ("add_folder_btn", "add_folder_btn"),
            ("add_item_btn", "add_item_btn"),
            ("confirm_btn", "confirm"),  # 添加收藏项页面中的确认按钮
            ("auto_fetch_btn", "auto_fetch"),
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
            "label_file_drop": "file_drop",
            "label_file_title": "title_label",
            "label_file_category": "category_label",
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
        auto_btn = self.findChild(QPushButton, "auto_fetch_btn")
        if auto_btn:
            auto_btn.setText(self.strings[self.current_lang]["auto_fetch"])

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
        scroll_widget = QWidget()
        self.folders_grid_layout = QGridLayout(scroll_widget)
        self.folders_grid_layout.setSpacing(20)
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
        for folder_id, name in folders:
            card = FolderCard(folder_id, name)
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
        name, ok = QInputDialog.getText(self, self.strings[self.current_lang]["add_folder_dialog_title"], self.strings[self.current_lang]["add_folder_dialog_label"])
        if ok and name:
            self.db.add_folder(name)
            self.load_folders()

    def open_folder(self, folder_id, folder_name):
        self.current_folder_id = folder_id
        self.current_folder_name = folder_name
        self.load_items_in_folder(folder_id)
        self.switch_to_page(1)

    def show_folder_context_menu(self, pos, folder_id, folder_name):
        menu = QMenu(self)
        rename_action = QAction(self.strings[self.current_lang]["rename"], self)
        rename_action.triggered.connect(lambda: self.rename_folder(folder_id, folder_name))
        delete_action = QAction(self.strings[self.current_lang]["delete"], self)
        delete_action.triggered.connect(lambda: self.delete_folder(folder_id))
        menu.addAction(rename_action)
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
        scroll_widget = QWidget()
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
        for i in reversed(range(self.items_grid_layout.count())):
            widget = self.items_grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        items = self.db.get_items_by_folder(folder_id)
        row, col = 0, 0
        for item_id, item_type, title, url, category, cover_path in items:
            card = ItemCard(item_id, title, cover_path, category)
            card.clicked.connect(lambda _, url=url, itype=item_type: self.open_item(url, itype))
            card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            card.customContextMenuRequested.connect(lambda pos, iid=item_id, t=title, u=url, cat=category, itype=item_type:
                                                     self.show_item_context_menu(pos, iid, t, u, cat, itype))
            self.items_grid_layout.addWidget(card, row, col)
            col += 1
            if col >= 4:
                col = 0
                row += 1
        if self.multi_select_mode:
            self.exit_multi_select_mode()
        self.filter_by_category(self.current_category_filter)

    def open_item(self, url, item_type):
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
                QMessageBox.warning(self, self.strings[self.current_lang]["file_not_found"], fself.strings[self.current_lang]["file_not_found_msg"].format(url))

    def extract_url_from_text(self, text):
        pattern = r'https?://[^\s<>"\'{}|\\^`\[\]]+'
        match = re.search(pattern, text)
        return match.group(0) if match else text.strip()

    def show_item_context_menu(self, pos, item_id, title, url, category, item_type):
        menu = QMenu(self)
        edit_action = QAction(self.strings[self.current_lang]["edit"], self)
        edit_action.triggered.connect(lambda: self.edit_item(item_id, title, url, category, item_type))
        delete_action = QAction(self.strings[self.current_lang]["delete"], self)
        delete_action.triggered.connect(lambda: self.delete_item(item_id))
        multi_action = QAction(self.strings[self.current_lang]["multi_select_mode"], self)
        multi_action.triggered.connect(self.enable_multi_select_mode)
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.addSeparator()
        menu.addAction(multi_action)
        menu.exec(self.sender().mapToGlobal(pos))

    def edit_item(self, item_id, title, url, category, item_type):
        self.editing_item_id = item_id
        self.editing_item_type = item_type
        self.open_add_item_page()
        QTimer.singleShot(50, lambda: self.populate_edit_form(title, url, category, item_type))

    def populate_edit_form(self, title, url, category, item_type):
        if item_type == "link":
            self.item_type_combo.setCurrentIndex(0)
            self.link_url_edit.setText(url)
            self.link_title_edit.setText(title)
            self.link_category_edit.setText(category)
        else:
            self.item_type_combo.setCurrentIndex(1)
            self.dropped_file_path = url
            self.file_title_edit.setText(title)
            self.file_category_edit.setText(category)
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
            QMessageBox.information(self, self.strings[self.current_lang]["info"], self.strings[self.current_lang]["no_item_selected"])
            return
        reply = QMessageBox.question(self, self.strings[self.current_lang]["confirm_delete"], fself.strings[self.current_lang]["batch_delete_confirm"].format(len(selected_ids)),
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_items_by_ids(selected_ids)
            self.load_items_in_folder(self.current_folder_id)
            self.exit_multi_select_mode()

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
            return
        import re
        match = re.search(r'https?://([^/]+)', url)
        if match:
            title = match.group(1)
            self.link_title_edit.setText(title)
        QMessageBox.information(self, self.strings[self.current_lang]["info"], self.strings[self.current_lang]["auto_fetch_complete"])

    def add_item_confirm(self):
        if self.current_folder_id is None:
            QMessageBox.warning(self, self.strings[self.current_lang]["warning"], self.strings[self.current_lang]["warning_no_folder"])
            return
        item_type = "link" if self.item_type_combo.currentIndex() == 0 else "file"
        if self.editing_item_id is not None:
            if item_type == "link":
                raw_url = self.link_url_edit.text().strip()
                url = self.extract_url_from_text(raw_url)
                if not url:
                    QMessageBox.warning(self, self.strings[self.current_lang]["warning"], self.strings[self.current_lang]["warning_empty_url"])
                    return
                title = self.link_title_edit.text().strip() or url
                category = self.link_category_edit.text().strip() or self.strings[self.current_lang]["default_category"]
                self.db.update_item(self.editing_item_id, title, url, category, "")
            else:
                if not self.dropped_file_path:
                    QMessageBox.warning(self, self.strings[self.current_lang]["warning"], self.strings[self.current_lang]["warning_drag_file"])
                    return
                title = self.file_title_edit.text().strip() or os.path.basename(self.dropped_file_path)
                category = self.file_category_edit.text().strip() or self.strings[self.current_lang]["default_file_category"]
                self.db.update_item(self.editing_item_id, title, self.dropped_file_path, category, "")
            QMessageBox.information(self, self.strings[self.current_lang]["info"], self.strings[self.current_lang]["success_update"])
            self.editing_item_id = None
            self.editing_item_type = None
        else:
            if item_type == "link":
                url = self.link_url_edit.text().strip()
                url = self.extract_url_from_text(url)
                if not url:
                    QMessageBox.warning(self, self.strings[self.current_lang]["warning"], self.strings[self.current_lang]["warning_empty_link"])
                    return
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                from urllib.parse import urlparse
                parsed = urlparse(url)
                if not parsed.netloc:
                    QMessageBox.warning(self, self.strings[self.current_lang]["warning"], self.strings[self.current_lang]["warning_invalid_link"])
                    return
                title = self.link_title_edit.text().strip() or url
                category = self.link_category_edit.text().strip() or "未分类"
                cover_path = ""
                self.db.add_item(self.current_folder_id, item_type, title, url, category, cover_path)
            else:
                if not self.dropped_file_path:
                    QMessageBox.warning(self, self.strings[self.current_lang]["warning"], self.strings[self.current_lang]["warning_drag_file_to_area"])
                    return
                title = self.file_title_edit.text().strip() or os.path.basename(self.dropped_file_path)
                category = self.file_category_edit.text().strip() or "文件"
                cover_path = ""
                self.db.add_item(self.current_folder_id, item_type, title, self.dropped_file_path, category, cover_path)
            QMessageBox.information(self, self.strings[self.current_lang]["info"], self.strings[self.current_lang]["success_add"])
        self.link_url_edit.clear()
        self.link_title_edit.clear()
        self.link_category_edit.clear()
        self.file_title_edit.clear()
        self.file_category_edit.clear()
        self.dropped_file_path = None
        self.drop_area.setText(self.strings[self.current_lang]["drag_hint"])
        self.load_items_in_folder(self.current_folder_id)
        self.switch_to_page(1)

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
