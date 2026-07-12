import os
import re
import webbrowser
import subprocess
import sqlite3
import sys
from urllib.parse import urlparse

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QScrollArea, QMessageBox,
    QInputDialog, QStackedWidget, QLabel, QMenu, QApplication,
    QComboBox, QDialog, QDialogButtonBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QAction, QDragEnterEvent, QDropEvent

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
    file_dropped = pyqtSignal(str)  # 发出文件路径

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setText("拖拽文件到此")
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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("收藏管理器")
        self.setGeometry(100, 100, 1200, 800)
        self.db = Database()
        
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
        self.multi_select_mode = False          # 是否处于多选模式
        self.selected_item_ids = set()          # 已选中的项ID集合（可选，用于冗余）
        self.editing_item_id = None             # 正在编辑的收藏项ID
        self.editing_item_type = None
        
        # 页面2: 添加收藏项页面（横推动画进入）
        self.add_item_page = QWidget()
        self.setup_add_item_page()
        self.stacked_widget.addWidget(self.add_item_page)
        
        # 默认显示收藏夹页面
        self.stacked_widget.setCurrentIndex(0)
        self.current_folder_id = None
        
        # 应用系统主题（简化，实际可深度适配）
        self.apply_theme()

    def open_settings(self):
        """显示设置对话框（假页面，占位用）"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("设置")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("设置功能开发中..."))
        layout.addWidget(QLabel("这里可以配置："))
        layout.addWidget(QLabel("• 主题（跟随系统/浅色/深色）"))
        layout.addWidget(QLabel("• 数据存储路径"))
        layout.addWidget(QLabel("• 默认浏览器"))
        layout.addWidget(QLabel("• 其他选项"))
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.exec()
        
    def apply_theme(self):
        # 简化：设置窗口背景色跟随系统（浅色/深色检测略，可手动）
        # 使用 QApplication 的 palette
        app = QApplication.instance()
        palette = app.palette()
        self.setPalette(palette)
        
    def setup_folders_page(self):
        layout = QVBoxLayout(self.folders_page)

        # 顶部栏
        top_bar = QHBoxLayout()
        self.folder_search = QLineEdit()
        self.folder_search.setPlaceholderText("搜索收藏夹...")
        self.folder_search.textChanged.connect(self.filter_folders)
        top_bar.addWidget(self.folder_search)

        add_folder_btn = QPushButton("+ 添加收藏夹")
        add_folder_btn.clicked.connect(self.add_folder_dialog)
        top_bar.addWidget(add_folder_btn)

        # 设置按钮（添加在添加按钮右侧）
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(QIcon(resource_path("resources/icons/settings.png")))
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.clicked.connect(self.open_settings)
        top_bar.addWidget(self.settings_btn)

        layout.addLayout(top_bar)

        # 滚动区域（不变）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_widget = QWidget()
        self.folders_grid_layout = QGridLayout(scroll_widget)
        self.folders_grid_layout.setSpacing(20)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        self.load_folders()
        
    def resizeEvent(self, event):
        # 确保设置按钮位置正确
        self.settings_btn.move(self.width() - 50, 10)
        super().resizeEvent(event)
        
    def load_folders(self):
        # 清除现有卡片
        for i in reversed(range(self.folders_grid_layout.count())):
            widget = self.folders_grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        folders = self.db.get_folders()
        row, col = 0, 0
        for folder_id, name in folders:
            card = FolderCard(folder_id, name)
            # 连接左键单击信号
            card.clicked.connect(lambda fid=folder_id: self.open_folder(fid, name))
            # 右键菜单保持不变
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
        name, ok = QInputDialog.getText(self, "添加收藏夹", "请输入收藏夹名称:")
        if ok and name:
            self.db.add_folder(name)
            self.load_folders()
            
    def open_folder(self, folder_id, folder_name):
        """点击收藏夹卡片，横推动画进入详情页"""
        self.current_folder_id = folder_id
        self.current_folder_name = folder_name
        self.load_items_in_folder(folder_id)
        # 执行横推动画（从右向左滑入）
        self.animate_switch(1)  # 切换到 items_page

    def show_folder_context_menu(self, pos, folder_id, folder_name):
        menu = QMenu(self)
        rename_action = QAction("重命名", self)
        rename_action.triggered.connect(lambda: self.rename_folder(folder_id, folder_name))
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.delete_folder(folder_id))
        menu.addAction(rename_action)
        menu.addAction(delete_action)
        menu.exec(self.sender().mapToGlobal(pos))

    def rename_folder(self, folder_id, old_name):
        new_name, ok = QInputDialog.getText(self, "重命名收藏夹", "新名称:", text=old_name)
        if ok and new_name:
            self.db.rename_folder(folder_id, new_name)
            self.load_folders()  # 刷新列表

    def delete_folder(self, folder_id):
        reply = QMessageBox.question(self, "确认删除", "删除收藏夹会同时删除其中的所有收藏项，确定吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_folder(folder_id)
            self.load_folders()
            # 如果当前打开的就是该收藏夹，返回上一级
            if self.current_folder_id == folder_id:
                self.go_back_to_folders()
        
    def setup_items_page(self):
        """收藏夹内部页面：返回按钮、搜索框、筛选按钮、+收藏项按钮、收藏项网格"""
        layout = QVBoxLayout(self.items_page)
        
        # 顶部栏：返回按钮 + 搜索框 + 筛选按钮 + 添加收藏项按钮
        top_bar = QHBoxLayout()
        
        self.back_btn = QPushButton()
        self.back_btn.setIcon(QIcon(resource_path("resources/icons/back.png")))
        self.back_btn.setFixedSize(32, 32)
        self.back_btn.clicked.connect(self.go_back_to_folders)
        top_bar.addWidget(self.back_btn)
        
        self.item_search = QLineEdit()
        self.item_search.setPlaceholderText("搜索收藏项...")
        self.item_search.textChanged.connect(self.filter_items)
        top_bar.addWidget(self.item_search)
        
        self.filter_btn = QPushButton()
        self.filter_btn.setIcon(QIcon(resource_path("resources/icons/filter.png")))
        self.filter_btn.setFixedSize(32, 32)
        self.filter_btn.clicked.connect(self.show_category_menu)
        top_bar.addWidget(self.filter_btn)
        
        add_item_btn = QPushButton("+ 收藏项")
        add_item_btn.clicked.connect(self.open_add_item_page)
        top_bar.addWidget(add_item_btn)
        
        layout.addLayout(top_bar)
        
        # 收藏项区域（网格布局，类似小红书）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.items_grid_layout = QGridLayout(scroll_widget)
        self.items_grid_layout.setSpacing(15)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        # 底部多选栏（初始隐藏）
        self.multi_select_bar = QWidget()
        self.multi_select_bar.setVisible(False)
        bar_layout = QHBoxLayout(self.multi_select_bar)
        delete_selected_btn = QPushButton("删除选中")
        delete_selected_btn.clicked.connect(self.delete_selected_items)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.exit_multi_select_mode)
        bar_layout.addWidget(delete_selected_btn)
        bar_layout.addWidget(cancel_btn)
        layout.addWidget(self.multi_select_bar)
        
    def load_items_in_folder(self, folder_id):
        """加载指定收藏夹的收藏项"""
        # 清除现有项
        for i in reversed(range(self.items_grid_layout.count())):
            widget = self.items_grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        items = self.db.get_items_by_folder(folder_id)
        row, col = 0, 0
        for item_id, item_type, title, url, category, cover_path in items:
            card = ItemCard(item_id, title, cover_path,category)
            # 绑定单击信号（替代原来的 mousePressEvent 重写）
            card.clicked.connect(lambda _, url=url, itype=item_type: self.open_item(url, itype))
            # 右键菜单
            card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            card.customContextMenuRequested.connect(lambda pos, iid=item_id, t=title, u=url, cat=category, itype=item_type:
                                                     self.show_item_context_menu(pos, iid, t, u, cat, itype))
            self.items_grid_layout.addWidget(card, row, col)
            col += 1
            if col >= 4:  # 每行4个卡片
                col = 0
                row += 1
            # 如果之前处于多选模式，退出（避免残留）
        if self.multi_select_mode:
            self.exit_multi_select_mode()
        self.filter_by_category(self.current_category_filter)

    def open_item(self, url, item_type):
        """打开链接或文件"""
        self.exit_multi_select_mode()
        if item_type == "link":
            # 自动提取 URL（防止带标题）
            url = self.extract_url_from_text(url)
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            webbrowser.open(url)
        else:  # file
            if os.path.exists(url):
                os.startfile(url)
            else:
                QMessageBox.warning(self, "文件不存在", f"找不到文件：{url}")

    def extract_url_from_text(self, text):
        """从混合文本中提取第一个 http/https 链接"""
        pattern = r'https?://[^\s<>"\'{}|\\^`\[\]]+'
        match = re.search(pattern, text)
        return match.group(0) if match else text.strip()

    def show_item_context_menu(self, pos, item_id, title, url, category, item_type):
        menu = QMenu(self)
        edit_action = QAction("编辑", self)
        edit_action.triggered.connect(lambda: self.edit_item(item_id, title, url, category, item_type))
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.delete_item(item_id))
        multi_action = QAction("多选模式", self)
        multi_action.triggered.connect(self.enable_multi_select_mode)
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.addSeparator()
        menu.addAction(multi_action)
        menu.exec(self.sender().mapToGlobal(pos))

    def edit_item(self, item_id, title, url, category, item_type):
        self.editing_item_id = item_id
        self.editing_item_type = item_type
        self.open_add_item_page()   # 打开添加页面，但我们会填充现有数据
        # 填充数据（需在页面显示后执行，因此放在 open_add_item_page 之后）
        # 由于 open_add_item_page 会清空表单，我们延迟填充
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, lambda: self.populate_edit_form(title, url, category, item_type))

    def populate_edit_form(self, title, url, category, item_type):
        """填充编辑表单"""
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
                self.drop_area.setText(f"已选择: {os.path.basename(url)}")
            else:
                self.drop_area.setText("文件不存在，请重新拖拽")

    def delete_item(self, item_id):
        reply = QMessageBox.question(self, "确认删除", "确定删除该收藏项吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_item(item_id)
            self.load_items_in_folder(self.current_folder_id)
                
    def filter_items(self):
        text = self.item_search.text().strip().lower()
        for i in range(self.items_grid_layout.count()):
            widget = self.items_grid_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'title'):
                widget.setVisible(text in widget.title.lower())
                
    def show_category_menu(self):
        """显示类别菜单，从数据库获取当前收藏夹的所有类别"""
        if self.current_folder_id is None:
            return
        # 查询该收藏夹下所有不同的类别
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM items WHERE folder_id = ?", (self.current_folder_id,))
            categories = [row[0] for row in cursor.fetchall()]
        # 添加“全部”选项
        menu = QMenu(self)
        all_action = QAction("全部", self)
        all_action.triggered.connect(lambda: self.filter_by_category(None))
        menu.addAction(all_action)
        menu.addSeparator()
        for cat in categories:
            action = QAction(cat, self)
            action.triggered.connect(lambda checked, c=cat: self.filter_by_category(c))
            menu.addAction(action)
        menu.exec(self.filter_btn.mapToGlobal(self.filter_btn.rect().bottomLeft()))
        
    def filter_by_category(self, category):
        """根据类别筛选收藏项，category 为 None 表示显示全部"""
        self.current_category_filter = category
        # 遍历所有卡片，根据类别显示/隐藏
        for i in range(self.items_grid_layout.count()):
            widget = self.items_grid_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'category'):
                if category is None:
                    widget.setVisible(True)
                else:
                    widget.setVisible(widget.category == category)
        
    def go_back_to_folders(self):
        """返回收藏夹列表，横推动画"""
        self.exit_multi_select_mode()
        self.animate_switch(0)  # 切回 folders_page
        
    def open_add_item_page(self):
        """打开添加收藏项页面，横推动画"""
        # 清空链接表单
        self.link_url_edit.clear()
        self.link_title_edit.clear()
        self.link_category_edit.clear()
        # 清空文件表单
        self.file_title_edit.clear()
        self.file_category_edit.clear()
        self.dropped_file_path = None
        self.drop_area.setText("拖拽文件到此")
        # 重置类型为链接
        self.item_type_combo.setCurrentIndex(0)
        self.animate_switch(2)
        # 预先加载页面数据（类型选择等）
        self.animate_switch(2)  # 切换到 add_item_page
        
    def setup_add_item_page(self):
        """添加收藏项页面，支持链接和本地文件拖拽"""
        from PyQt6.QtWidgets import QComboBox, QStackedWidget, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QFrame
        from PyQt6.QtCore import Qt

        layout = QVBoxLayout(self.add_item_page)

        # 返回按钮
        back_btn = QPushButton("← 返回")
        back_btn.clicked.connect(lambda: self.animate_switch(1))
        layout.addWidget(back_btn)

        # 类型选择
        layout.addWidget(QLabel("收藏类型:"))
        self.item_type_combo = QComboBox()
        self.item_type_combo.addItems(["链接", "本地文件"])
        self.item_type_combo.currentIndexChanged.connect(self.switch_add_item_type)
        layout.addWidget(self.item_type_combo)

        # 堆叠表单
        self.add_item_stack = QStackedWidget()
        layout.addWidget(self.add_item_stack)

        # 创建链接表单页
        link_widget = QWidget()
        link_layout = QVBoxLayout(link_widget)
        self.link_url_edit = QLineEdit()
        self.link_url_edit.setPlaceholderText("输入链接URL")
        self.link_title_edit = QLineEdit()
        self.link_title_edit.setPlaceholderText("标题（可选）")
        self.link_category_edit = QLineEdit()
        self.link_category_edit.setPlaceholderText("类别")
        auto_btn = QPushButton("自动识别")
        auto_btn.clicked.connect(self.auto_fetch_link_info)
        link_layout.addWidget(QLabel("链接URL:"))
        link_layout.addWidget(self.link_url_edit)
        link_layout.addWidget(QLabel("标题:"))
        link_layout.addWidget(self.link_title_edit)
        link_layout.addWidget(QLabel("类别:"))
        link_layout.addWidget(self.link_category_edit)
        link_layout.addWidget(auto_btn)
        link_layout.addStretch()
        self.add_item_stack.addWidget(link_widget)
        self.link_url_edit.editingFinished.connect(self.clean_link_url)

        # 创建本地文件表单页
        file_widget = QWidget()
        file_layout = QVBoxLayout(file_widget)
        # 拖拽区域
        self.drop_area = DropArea()  # 自定义控件见下文
        self.drop_area.file_dropped.connect(self.on_file_dropped)
        file_layout.addWidget(QLabel("将文件拖拽到此区域:"))
        file_layout.addWidget(self.drop_area)
        # 可编辑的标题和类别
        file_layout.addWidget(QLabel("标题:"))
        self.file_title_edit = QLineEdit()
        self.file_title_edit.setPlaceholderText("自动填充，可修改")
        file_layout.addWidget(self.file_title_edit)
        file_layout.addWidget(QLabel("类别:"))
        self.file_category_edit = QLineEdit()
        self.file_category_edit.setPlaceholderText("自动填充，可修改")
        file_layout.addWidget(self.file_category_edit)
        file_layout.addStretch()
        self.add_item_stack.addWidget(file_widget)

        # 确认按钮
        confirm_btn = QPushButton("确认")
        confirm_btn.clicked.connect(self.add_item_confirm)
        layout.addWidget(confirm_btn)

        # 保存当前选择的文件路径
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
                card.checkbox.setChecked(False)   # 取消所有勾选
                card.is_selected = False          # 重置选中标记
        self.multi_select_bar.setVisible(True)

    def exit_multi_select_mode(self):
        """退出多选模式"""
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
            QMessageBox.information(self, "提示", "未选中任何项目")
            return
        reply = QMessageBox.question(self, "批量删除", f"确定删除 {len(selected_ids)} 个收藏项吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_items_by_ids(selected_ids)
            self.load_items_in_folder(self.current_folder_id)
            self.exit_multi_select_mode()

    def switch_add_item_type(self, index):
        """根据选择的类型切换堆叠页面"""
        self.add_item_stack.setCurrentIndex(index)

    def on_file_dropped(self, file_path):
        """文件拖入后自动填充标题和类别"""
        import os
        self.dropped_file_path = file_path
        # 自动填充标题：文件名（不含扩展名）
        basename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(basename)[0]
        self.file_title_edit.setText(name_without_ext)
        # 自动填充类别：扩展名（去掉点，大写）
        ext = os.path.splitext(file_path)[1].lstrip('.').upper()
        if ext:
            self.file_category_edit.setText(ext)
        else:
            self.file_category_edit.setText("文件")
        # 可以在拖拽区域显示文件信息
        self.drop_area.setText(f"已选择: {basename}")
        
    def auto_fetch_link_info(self):
        url = self.link_url_edit.text().strip()
        if not url:
            return
        # 模拟自动识别，实际可用 requests+BeautifulSoup 获取标题
        # 简化：从 url 提取域名作为标题
        import re
        match = re.search(r'https?://([^/]+)', url)
        if match:
            title = match.group(1)
            self.link_title_edit.setText(title)
        QMessageBox.information(self, "提示", "自动识别完成（模拟）")
        def extract_url_from_text(self, text):
            """从混合文本中提取第一个合法的 URL"""
            # 匹配 http:// 或 https:// 开头的 URL
            url_pattern = r'https?://[^\s<>"\'{}|\\^`\[\]]+'
            match = re.search(url_pattern, text)
            if match:
                return match.group(0)
            return text.strip()
        
    def add_item_confirm(self):
        if self.current_folder_id is None:
            QMessageBox.warning(self, "警告", "未选择收藏夹")
            return
        item_type = "link" if self.item_type_combo.currentText() == "链接" else "file"
        # 编辑模式
        if self.editing_item_id is not None:
            if item_type == "link":
                raw_url = self.link_url_edit.text().strip()
                url = self.extract_url_from_text(raw_url)
                if not url:
                    QMessageBox.warning(self, "警告", "请输入有效的链接")
                    return
                title = self.link_title_edit.text().strip() or url
                category = self.link_category_edit.text().strip() or "未分类"
                self.db.update_item(self.editing_item_id, title, url, category, "")
            else:
                if not self.dropped_file_path:
                    QMessageBox.warning(self, "警告", "请拖拽文件")
                    return
                title = self.file_title_edit.text().strip() or os.path.basename(self.dropped_file_path)
                category = self.file_category_edit.text().strip() or "文件"
                self.db.update_item(self.editing_item_id, title, self.dropped_file_path, category, "")
            QMessageBox.information(self, "成功", "收藏项已更新")
            self.editing_item_id = None
            self.editing_item_type = None
        else:
            if item_type == "link":
                url = self.link_url_edit.text().strip()
                url = self.extract_url_from_text(url)  # 自动清理
                if not url:
                    QMessageBox.warning(self, "警告", "请输入链接URL")
                    return
                # 规范化 URL
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                # 可选：使用 urllib.parse 进一步清洗
                from urllib.parse import urlparse
                parsed = urlparse(url)
                if not parsed.netloc:
                    QMessageBox.warning(self, "警告", "链接格式无效")
                    return
                title = self.link_title_edit.text().strip() or url
                category = self.link_category_edit.text().strip() or "未分类"
                cover_path = ""
                self.db.add_item(self.current_folder_id, item_type, title, url, category, cover_path)
            else:  # 本地文件
                if not self.dropped_file_path:
                    QMessageBox.warning(self, "警告", "请拖拽文件到指定区域")
                    return
                title = self.file_title_edit.text().strip() or os.path.basename(self.dropped_file_path)
                category = self.file_category_edit.text().strip() or "文件"
                cover_path = ""  # 可后续从文件提取图标
                # 保存文件路径（绝对路径）
                self.db.add_item(self.current_folder_id, item_type, title, self.dropped_file_path, category, cover_path)
            QMessageBox.information(self, "成功", "收藏项已添加")
        # 清空表单
        self.link_url_edit.clear()
        self.link_title_edit.clear()
        self.link_category_edit.clear()
        self.file_title_edit.clear()
        self.file_category_edit.clear()
        self.dropped_file_path = None
        self.drop_area.setText("拖拽文件到此")
        # 返回并刷新当前收藏夹的项
        self.load_items_in_folder(self.current_folder_id)
        self.animate_switch(1)
        self.animate_switch(1)
        
    def animate_switch(self, target_index):
        """横推动画切换堆叠视图"""
        current = self.stacked_widget.currentIndex()
        if current == target_index:
            return
        # 获取两个页面位置
        width = self.stacked_widget.width()
        # 目标页初始位置（右侧）
        target_widget = self.stacked_widget.widget(target_index)
        target_widget.move(width, 0)
        target_widget.show()
        # 动画移动当前页向左移出，目标页向左移入
        self.anim = QPropertyAnimation(self.stacked_widget, b"geometry")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        start_geom = self.stacked_widget.geometry()
        # 计算移动后的位置：当前页移动到 -width, 目标页移动到 0
        end_geom = self.stacked_widget.geometry()
        # 但我们不能直接移动 stacked_widget，而是移动内部页面？
        # 更简单：使用 QPropertyAnimation 对每个页面进行位置变化
        # 或者使用 QStackedWidget 自带的 setCurrentIndex 无动画，我们手动做动画：
        # 这里使用简化版：直接切换无动画，或自定义 QStackedWidget 子类实现滑动
        # 为简化代码，暂时不使用动画，后续可用 QPropertyAnimation 实现
        # 由于时间，直接设置索引
        self.stacked_widget.setCurrentIndex(target_index)
        # 真正实现需要额外工作量，这里预留接口




