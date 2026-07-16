from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QScrollArea, QPushButton, QLineEdit, QHBoxLayout, QCheckBox
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap
import os

class FolderCard(QWidget):
    clicked = pyqtSignal(int)

    def __init__(self, folder_id, folder_name, has_password=False, parent=None):
        super().__init__(parent)
        self.folder_id = folder_id
        self.folder_name = folder_name
        self.has_password = has_password
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel()
        icon_label.setFixedSize(64, 64)
        icon_label.setStyleSheet("background-color: #e0e0e0; border-radius: 8px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setText("📁")
        layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

        name_layout = QHBoxLayout()
        self.lock_label = QLabel("🔒")
        self.lock_label.setVisible(has_password)
        name_layout.addWidget(self.lock_label)

        name_label = QLabel(folder_name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_layout.addWidget(name_label)
        name_layout.addStretch()
        layout.addLayout(name_layout)

        self.setLayout(layout)
        self.setFixedSize(120, 120)
        self.setStyleSheet("""...""")

    def set_has_password(self, has_password):
        self.has_password = has_password
        self.lock_label.setVisible(has_password)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.folder_id)
        else:
            super().mousePressEvent(event)  # 让右键事件继续传递，以便触发右键菜单

class ItemCard(QWidget):
    clicked = pyqtSignal(int)

    def __init__(self, item_id, title, cover_path, category, has_password=False, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.category = category
        self.has_password = has_password
        self.is_selected = False
        self.multi_select_mode = False

        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(5, 5, 5, 5)

        # 顶部勾选框
        top_layout = QHBoxLayout()
        self.checkbox = QCheckBox()
        self.checkbox.setVisible(False)
        self.checkbox.stateChanged.connect(self.on_check_state_changed)
        top_layout.addWidget(self.checkbox)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # 封面
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(200, 150)
        self.cover_label.setStyleSheet("background-color: #ddd; border-radius: 8px;")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if cover_path and os.path.exists(cover_path):
            pixmap = QPixmap(cover_path).scaled(200, 150, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.cover_label.setPixmap(pixmap)
        else:
            self.cover_label.setText("📷")
        layout.addWidget(self.cover_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # 标题行（锁 + 标题）
        title_layout = QHBoxLayout()
        self.lock_label = QLabel("🔒")
        self.lock_label.setVisible(has_password)
        title_layout.addWidget(self.lock_label)

        self.title_label = QLabel(title)
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumWidth(200)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        self.setLayout(layout)
        self.setFixedSize(210, 200)
        self.setStyleSheet("""...""")

    def set_has_password(self, has_password):
        self.has_password = has_password
        self.lock_label.setVisible(has_password)

    def on_check_state_changed(self, state):
        self.is_selected = (state == Qt.CheckState.Checked)

    def set_multi_select_mode(self, enabled):
        """启用/禁用多选模式"""
        self.multi_select_mode = enabled
        self.checkbox.setVisible(enabled)
        if not enabled:
            self.checkbox.setChecked(False)
            self.is_selected = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.multi_select_mode:
                # 手动切换勾选状态
                new_checked = not self.checkbox.isChecked()
                self.checkbox.setChecked(new_checked)
                self.is_selected = new_checked
            else:
                self.clicked.emit(self.item_id)
        else:
            super().mousePressEvent(event) # 让右键事件传递，以便触发自定义右键菜单
