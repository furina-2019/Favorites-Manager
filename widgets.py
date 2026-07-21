from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QScrollArea, QPushButton, QLineEdit, QHBoxLayout, QCheckBox
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QColor, QPainter
import os

class FolderCard(QWidget):
    clicked = pyqtSignal(int)

    COLORS = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4",
        "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F",
        "#BB8FCE", "#85C1E9", "#F8B500", "#00CED1"
    ]

    def __init__(self, folder_id, folder_name, has_password=False, item_count=0, created_at=None, lang="zh", parent=None):
        super().__init__(parent)
        self.setObjectName("folder_card")
        self.folder_id = folder_id
        self.folder_name = folder_name
        self.has_password = has_password
        self.item_count = item_count
        self.created_at = created_at
        self.lang = lang
        self.color = FolderCard.COLORS[hash(folder_name) % len(FolderCard.COLORS)]

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.card_content = QWidget()
        self.card_content.setObjectName("card_content")
        content_layout = QVBoxLayout(self.card_content)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(8)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)
        
        self.lock_label = QLabel("🔒")
        self.lock_label.setFixedSize(20, 20)
        self.lock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lock_label.setVisible(has_password)
        top_layout.addWidget(self.lock_label)
        top_layout.addStretch()
        content_layout.addLayout(top_layout)

        self.icon_container = QWidget()
        self.icon_container.setFixedSize(56, 56)
        
        icon_layout = QVBoxLayout(self.icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        first_char = folder_name[0] if folder_name else "?"
        self.char_label = QLabel(first_char)
        self.char_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(self.char_label)
        
        content_layout.addWidget(self.icon_container, alignment=Qt.AlignmentFlag.AlignCenter)

        display_name = folder_name[:12] + "..." if len(folder_name) > 12 else folder_name
        self.name_label = QLabel(display_name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setToolTip(folder_name)
        content_layout.addWidget(self.name_label)

        item_label = "items" if lang == "en" else "项"
        info_text = f"{item_count} {item_label}"
        if created_at:
            info_text += f" · {created_at[:10]}"
        self.info_label = QLabel(info_text)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setWordWrap(True)
        content_layout.addWidget(self.info_label)

        main_layout.addWidget(self.card_content)

        self.setFixedSize(180, 220)
        self.update_theme(False)

    def set_has_password(self, has_password):
        self.has_password = has_password
        self.lock_label.setVisible(has_password)
    
    def update_language(self, lang):
        self.lang = lang
        item_label = "items" if lang == "en" else "项"
        info_text = f"{self.item_count} {item_label}"
        if self.created_at:
            info_text += f" · {self.created_at[:10]}"
        self.info_label.setText(info_text)
    
    def update_theme(self, dark_mode):
        bg_color = "#2b2b2b" if dark_mode else "white"
        text_color = "white" if dark_mode else "#333"
        info_color = "#888" if dark_mode else "#999"
        char_color = "black" if dark_mode else "white"
        border_color = "#3c3c3c" if dark_mode else "#e0e0e0"
        
        self.setStyleSheet(f"""
            #folder_card {{
                background-color: transparent;
                border: none;
            }}
        """)
        
        self.card_content.setStyleSheet(f"""
            #card_content {{
                background-color: {bg_color};
                border-radius: 12px;
                border: 1px solid {border_color};
            }}
            #card_content QLabel {{
                background-color: transparent;
            }}
            #card_content QWidget {{
                background-color: transparent;
            }}
        """)
        
        self.icon_container.setStyleSheet(f"background-color: {self.color}; border-radius: 10px;")
        
        self.card_content.setGraphicsEffect(None)
        
        self.name_label.setStyleSheet(f"font-size: 14px; font-weight: 500; color: {text_color};")
        self.char_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {char_color};")
        self.info_label.setStyleSheet(f"font-size: 12px; color: {info_color};")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.folder_id)
        else:
            super().mousePressEvent(event)  # 让右键事件继续传递，以便触发右键菜单

class ItemCard(QWidget):
    clicked = pyqtSignal(int)

    def __init__(self, item_id, title, cover_path, category, has_password=False, url_or_path="", lang="zh", parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.category = category
        self.has_password = has_password
        self.url_or_path = url_or_path
        self.lang = lang
        self.is_selected = False
        self.multi_select_mode = False

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.card_content = QWidget()
        self.card_content.setObjectName("card_content")
        card_layout = QVBoxLayout(self.card_content)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(8)

        # 顶部勾选框和锁图标
        top_layout = QHBoxLayout()
        self.checkbox = QCheckBox()
        self.checkbox.setVisible(False)
        self.checkbox.stateChanged.connect(self.on_check_state_changed)
        top_layout.addWidget(self.checkbox)
        
        self.lock_label = QLabel("🔒")
        self.lock_label.setVisible(has_password)
        top_layout.addWidget(self.lock_label)
        
        top_layout.addStretch()
        card_layout.addLayout(top_layout)

        # 封面（宽长方形）
        self.cover_label = QLabel()
        self.cover_label.setObjectName("cover_label")
        self.cover_label.setFixedSize(180, 100)
        self.cover_label.setStyleSheet("background-color: #ddd; border-radius: 8px;")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_cover(cover_path)
        card_layout.addWidget(self.cover_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # 标题
        display_title = title[:18] + "..." if len(title) > 18 else title
        self.title_label = QLabel(display_title)
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumWidth(180)
        self.title_label.setToolTip(title)
        card_layout.addWidget(self.title_label)

        # 分类和URL/路径信息
        info_layout = QHBoxLayout()
        self.category_label = QLabel(f"� {category}")
        self.category_label.setStyleSheet("font-size: 12px;")
        info_layout.addWidget(self.category_label)
        
        info_layout.addStretch()
        
        self.path_label = QLabel()
        self.path_label.setStyleSheet("font-size: 11px;")
        if url_or_path:
            if len(url_or_path) > 20:
                self.path_label.setText("..." + url_or_path[-20:])
            else:
                self.path_label.setText(url_or_path)
        info_layout.addWidget(self.path_label)
        card_layout.addLayout(info_layout)

        main_layout.addWidget(self.card_content)

        self.setFixedSize(200, 210)
        self.update_theme(False)

    def load_cover(self, cover_path):
        self._cover_path = cover_path
        if cover_path and os.path.exists(cover_path):
            pixmap = QPixmap(cover_path)
            if pixmap.isNull():
                self.cover_label.setText("📷")
            else:
                scaled_pixmap = pixmap.scaled(180, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.cover_label.setPixmap(scaled_pixmap)
        else:
            self.cover_label.setText("📷")

    def update_cover(self, cover_path):
        self.load_cover(cover_path)
        self.update_theme(self.is_dark_mode())
    
    def update_theme(self, dark_mode):
        self._dark_mode = dark_mode
        bg_color = "#2b2b2b" if dark_mode else "white"
        text_color = "white" if dark_mode else "#333"
        info_color = "#888" if dark_mode else "#999"
        border_color = "#3c3c3c" if dark_mode else "#e0e0e0"

        self.setStyleSheet(f"""
            #item_card {{
                background-color: transparent;
                border: none;
            }}
        """)

        cover_bg = "#333" if dark_mode else "#ddd"
        self.card_content.setStyleSheet(f"""
            #card_content {{
                background-color: {bg_color};
                border-radius: 12px;
                border: 1px solid {border_color};
            }}
            #card_content QLabel:not(#cover_label) {{
                background-color: transparent;
            }}
            #cover_label {{
                background-color: {cover_bg};
                border-radius: 8px;
            }}
            #card_content QWidget {{
                background-color: transparent;
            }}
            #card_content QCheckBox {{
                color: {text_color};
            }}
        """)

        self.title_label.setStyleSheet(f"font-size: 14px; font-weight: 500; color: {text_color};")
        self.category_label.setStyleSheet(f"font-size: 12px; color: {info_color};")
        self.path_label.setStyleSheet(f"font-size: 11px; color: {info_color};")
        
        if hasattr(self, '_cover_path') and self._cover_path:
            self.load_cover(self._cover_path)

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

    def update_theme(self, dark_mode):
        self._dark_mode = dark_mode
        bg_color = "#2b2b2b" if dark_mode else "white"
        text_color = "white" if dark_mode else "#333"
        info_color = "#888" if dark_mode else "#999"
        border_color = "#3c3c3c" if dark_mode else "#e0e0e0"

        self.setStyleSheet(f"""
            #item_card {{
                background-color: transparent;
                border: none;
            }}
        """)

        cover_bg = "#333" if dark_mode else "#ddd"
        self.card_content.setStyleSheet(f"""
            #card_content {{
                background-color: {bg_color};
                border-radius: 12px;
                border: 1px solid {border_color};
            }}
            #card_content QLabel:not(#cover_label) {{
                background-color: transparent;
            }}
            #cover_label {{
                background-color: {cover_bg};
                border-radius: 8px;
            }}
            #card_content QWidget {{
                background-color: transparent;
            }}
            #card_content QCheckBox {{
                color: {text_color};
            }}
        """)

        self.title_label.setStyleSheet(f"font-size: 14px; font-weight: 500; color: {text_color};")
        self.category_label.setStyleSheet(f"font-size: 12px; color: {info_color};")
        self.path_label.setStyleSheet(f"font-size: 11px; color: {info_color};")

    def is_dark_mode(self):
        return getattr(self, '_dark_mode', False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.multi_select_mode:
                new_checked = not self.checkbox.isChecked()
                self.checkbox.setChecked(new_checked)
                self.is_selected = new_checked
            else:
                self.clicked.emit(self.item_id)
        else:
            super().mousePressEvent(event)


class ToastNotification(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 20, 36, 20)
        
        self.label = QLabel()
        self.label.setStyleSheet("color: white; font-size: 15px;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(50, 50, 50, 0.9);
                border-radius: 10px;
                padding: 8px;
            }
        """)
        
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.fade_out)
    
    def show_message(self, message):
        self.label.setText(message)
        self.adjustSize()
        
        parent_geo = self.parent().geometry()
        center_x = parent_geo.x() + parent_geo.width() // 2 - self.width() // 2
        center_y = parent_geo.y() + parent_geo.height() // 2 - self.height() // 2
        self.move(center_x, center_y)
        
        self.setWindowOpacity(0)
        self.show()
        
        self.animation.stop()
        self.animation.setDuration(400)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.finished.connect(lambda: self.timer.start(1000))
        self.animation.start()
    
    def fade_out(self):
        self.animation.stop()
        self.animation.setDuration(1000)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.finished.connect(self.close)
        self.animation.start()
