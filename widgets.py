from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QScrollArea, QPushButton, QLineEdit, QHBoxLayout, QCheckBox, QTextEdit
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PyQt6.QtGui import QPixmap, QColor, QPainter, QFont, QIcon
import os
from background_manager import background_manager

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
        text_color = "white" if dark_mode else "#333"
        info_color = "#888" if dark_mode else "#999"
        char_color = "black" if dark_mode else "white"
        border_color = "#3c3c3c" if dark_mode else "#e0e0e0"
        bg_color = "#2b2b2b" if dark_mode else "white"
        
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
                color: {text_color};
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

    def __init__(self, item_id, title, cover_path, category, has_password=False, url_or_path="", lang="zh", summary="", parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.category = category
        self.has_password = has_password
        self.url_or_path = url_or_path
        self.lang = lang
        self.summary = summary
        self.is_selected = False
        self.multi_select_mode = False
        self.summary_expanded = False
        self.theme_color = "#0078d7"
        
        self.CARD_WIDTH = 200
        self.CARD_HEIGHT = 240
        self.SUMMARY_HEIGHT = 240

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.card_content = QWidget()
        self.card_content.setObjectName("card_content")
        self.card_layout = QVBoxLayout(self.card_content)
        self.card_layout.setContentsMargins(12, 12, 12, 12)
        self.card_layout.setSpacing(8)

        # 顶部勾选框和锁图标
        self.top_layout = QHBoxLayout()
        self.checkbox = QCheckBox()
        self.checkbox.setVisible(False)
        self.checkbox.stateChanged.connect(self.on_check_state_changed)
        self.top_layout.addWidget(self.checkbox)
        
        self.lock_label = QLabel("🔒")
        self.lock_label.setVisible(has_password)
        self.top_layout.addWidget(self.lock_label)
        
        self.top_layout.addStretch()
        self.card_layout.addLayout(self.top_layout)

        # 封面（宽长方形）
        self.cover_label = QLabel()
        self.cover_label.setObjectName("cover_label")
        self.cover_label.setFixedSize(176, 98)
        self.cover_label.setStyleSheet("background-color: #ddd; border-radius: 8px;")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_cover(cover_path)
        self.card_layout.addWidget(self.cover_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # 标题
        display_title = title[:18] + "..." if len(title) > 18 else title
        self.title_label = QLabel(display_title)
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumWidth(176)
        self.title_label.setToolTip(title)
        self.card_layout.addWidget(self.title_label)

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
        self.card_layout.addLayout(info_layout)

        # 摘要按钮（默认在底部）
        self.summary_button = QPushButton()
        self.summary_button.setObjectName("summary_button")
        self.summary_button.clicked.connect(self.toggle_summary)
        self.update_summary_button_text()
        self.summary_button.setVisible(bool(summary))
        self.card_layout.addWidget(self.summary_button)

        # 添加弹性空间，防止内容被压缩
        self.card_layout.addStretch()

        main_layout.addWidget(self.card_content)

        # 摘要内容面板（覆盖在卡片上方，从底部向上滑出）
        self.summary_panel = QWidget(self)
        self.summary_panel.setObjectName("summary_panel")
        self.summary_panel.setFixedSize(self.CARD_WIDTH, self.SUMMARY_HEIGHT)
        self.summary_panel.move(0, self.CARD_HEIGHT)
        self.summary_panel.setVisible(False)
        
        # 直接在摘要面板上使用布局
        self.summary_panel_layout = QVBoxLayout(self.summary_panel)
        self.summary_panel_layout.setContentsMargins(12, 12, 12, 12)
        self.summary_panel_layout.setSpacing(8)

        # 收起摘要按钮（在顶部，固定高度）
        self.close_summary_button = QPushButton()
        self.close_summary_button.setObjectName("close_summary_button")
        self.close_summary_button.clicked.connect(self.toggle_summary)
        self.close_summary_button.setFixedHeight(30)
        self.update_close_summary_button_text()
        self.summary_panel_layout.addWidget(self.close_summary_button)

        # 摘要文本区域（在下方，填充剩余空间）
        self.summary_text = QTextEdit()
        self.summary_text.setObjectName("summary_text")
        self.summary_text.setReadOnly(True)
        self.summary_text.setPlainText(summary)
        self.summary_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.summary_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # 设置最大高度，确保按钮不会被挤压
        self.summary_text.setMaximumHeight(self.SUMMARY_HEIGHT - 60)  # 减去边距和按钮高度
        self.summary_panel_layout.addWidget(self.summary_text, 1)

        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.update_theme(False)

    def load_cover(self, cover_path):
        self._cover_path = cover_path
        if cover_path:
            # 检查是否为预设封面类型
            if cover_path.startswith('preset://'):
                preset_type = cover_path.replace('preset://', '')
                from cover_presets import generate_preset_cover
                pixmap = generate_preset_cover(preset_type, QSize(176, 98))
                self.cover_label.setPixmap(pixmap)
            elif os.path.exists(cover_path):
                pixmap = QPixmap(cover_path)
                if pixmap.isNull():
                    # 尝试根据文件类型生成预设封面
                    from cover_presets import get_preset_type_for_file, generate_preset_cover
                    preset_type = get_preset_type_for_file(cover_path)
                    pixmap = generate_preset_cover(preset_type, QSize(176, 98))
                    self.cover_label.setPixmap(pixmap)
                else:
                    scaled_pixmap = pixmap.scaled(176, 98, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.cover_label.setPixmap(scaled_pixmap)
            else:
                # 路径不存在，尝试根据类型生成预设封面
                from cover_presets import get_preset_type_for_file, generate_preset_cover
                preset_type = get_preset_type_for_file(cover_path)
                pixmap = generate_preset_cover(preset_type, QSize(176, 98))
                self.cover_label.setPixmap(pixmap)
        else:
            # 没有封面，显示默认图标
            self.cover_label.setText("📷")

    def update_cover(self, cover_path):
        self.load_cover(cover_path)
        self.update_theme(self.is_dark_mode())
    
    def set_summary(self, summary):
        self.summary = summary
        self.summary_text.setPlainText(summary)
        self.summary_button.setVisible(bool(summary))
    
    def _get_arrow_icon(self, direction="up"):
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "icons", "arrow_on.svg")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if direction == "down":
                from PyQt6.QtGui import QTransform
                pixmap = pixmap.transformed(QTransform().rotate(180))
            return QIcon(pixmap)
        return None
    
    def update_summary_button_text(self):
        icon = self._get_arrow_icon("up")
        if icon:
            self.summary_button.setIcon(icon)
            self.summary_button.setIconSize(QSize(16, 16))
        
        if self.lang == "en":
            self.summary_button.setText("Summary")
        else:
            self.summary_button.setText("摘要")
    
    def update_close_summary_button_text(self):
        icon = self._get_arrow_icon("down")
        if icon:
            self.close_summary_button.setIcon(icon)
            self.close_summary_button.setIconSize(QSize(16, 16))
        
        if self.lang == "en":
            self.close_summary_button.setText("Collapse")
        else:
            self.close_summary_button.setText("收起摘要")
    
    def toggle_summary(self):
        self.summary_expanded = not self.summary_expanded
        
        if self.summary_expanded:
            self.animate_summary_open()
        else:
            self.animate_summary_close()
    
    def animate_summary_open(self):
        # 获取按钮起始位置（在卡片中的位置）
        button_start_y = self.summary_button.y()
        
        # 将摘要按钮移到摘要面板中（替换收起按钮）
        self.summary_button.setParent(self.summary_panel)
        self.summary_button.setVisible(True)
        
        # 获取收起按钮在摘要面板中的目标位置
        target_pos = self.close_summary_button.pos()
        
        # 隐藏收起按钮（暂时）
        self.close_summary_button.setVisible(False)
        
        # 创建按钮移动动画（从底部移动到顶部）
        self.button_move_animation = QPropertyAnimation(self.summary_button, b"pos")
        self.button_move_animation.setDuration(350)
        self.button_move_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.button_move_animation.setStartValue(QPoint(0, button_start_y))
        self.button_move_animation.setEndValue(target_pos)
        
        # 创建箭头旋转动画（180度）
        self.arrow_rotation_angle = 0
        
        def rotate_arrow(value):
            self.arrow_rotation_angle = value
            icon = self._get_arrow_icon("up")
            if icon:
                pixmap = icon.pixmap(16, 16)
                from PyQt6.QtGui import QTransform
                rotated_pixmap = pixmap.transformed(QTransform().rotate(value))
                self.summary_button.setIcon(QIcon(rotated_pixmap))
        
        self.arrow_animation = QPropertyAnimation()
        self.arrow_animation.setDuration(350)
        self.arrow_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.arrow_animation.setStartValue(0)
        self.arrow_animation.setEndValue(180)
        self.arrow_animation.valueChanged.connect(rotate_arrow)
        
        # 动画完成后更新按钮文本
        def on_button_finished():
            if self.lang == "en":
                self.summary_button.setText("Collapse")
            else:
                self.summary_button.setText("收起摘要")
        
        self.button_move_animation.finished.connect(on_button_finished)
        
        # 显示摘要面板并置于顶层
        self.summary_panel.setVisible(True)
        self.summary_panel.raise_()
        
        # 创建摘要面板向上滑入动画
        self.panel_animation = QPropertyAnimation(self.summary_panel, b"geometry")
        self.panel_animation.setDuration(350)
        self.panel_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.panel_animation.setStartValue(QRect(0, self.CARD_HEIGHT, self.CARD_WIDTH, 0))
        self.panel_animation.setEndValue(QRect(0, 0, self.CARD_WIDTH, self.SUMMARY_HEIGHT))
        
        # 同时播放所有动画
        self.button_move_animation.start()
        self.arrow_animation.start()
        self.panel_animation.start()
    
    def animate_summary_close(self):
        # 获取按钮当前位置（在摘要面板中）
        button_start_pos = self.summary_button.pos()
        
        # 创建按钮移动动画（从顶部移动到底部）
        self.button_move_animation = QPropertyAnimation(self.summary_button, b"pos")
        self.button_move_animation.setDuration(350)
        self.button_move_animation.setEasingCurve(QEasingCurve.Type.InQuad)
        self.button_move_animation.setStartValue(button_start_pos)
        self.button_move_animation.setEndValue(QPoint(0, self.CARD_HEIGHT - 40))
        
        # 创建箭头旋转动画（反向180度）
        def rotate_arrow_back(value):
            icon = self._get_arrow_icon("up")
            if icon:
                pixmap = icon.pixmap(16, 16)
                from PyQt6.QtGui import QTransform
                rotated_pixmap = pixmap.transformed(QTransform().rotate(180 - value))
                self.summary_button.setIcon(QIcon(rotated_pixmap))
        
        self.arrow_animation = QPropertyAnimation()
        self.arrow_animation.setDuration(350)
        self.arrow_animation.setEasingCurve(QEasingCurve.Type.InQuad)
        self.arrow_animation.setStartValue(0)
        self.arrow_animation.setEndValue(180)
        self.arrow_animation.valueChanged.connect(rotate_arrow_back)
        
        # 创建摘要面板向下滑出动画
        self.panel_animation = QPropertyAnimation(self.summary_panel, b"geometry")
        self.panel_animation.setDuration(350)
        self.panel_animation.setEasingCurve(QEasingCurve.Type.InQuad)
        self.panel_animation.setStartValue(QRect(0, 0, self.CARD_WIDTH, self.SUMMARY_HEIGHT))
        self.panel_animation.setEndValue(QRect(0, self.CARD_HEIGHT, self.CARD_WIDTH, 0))
        
        # 动画完成后恢复按钮
        def on_panel_finished():
            # 将按钮移回卡片布局
            self.summary_button.setParent(self.card_content)
            self.card_layout.addWidget(self.summary_button)
            
            # 更新按钮文本
            if self.lang == "en":
                self.summary_button.setText("Summary")
            else:
                self.summary_button.setText("摘要")
            
            # 重置图标
            self.update_summary_button_text()
            
            # 隐藏摘要面板
            self.summary_panel.setVisible(False)
        
        self.panel_animation.finished.connect(on_panel_finished)
        
        # 同时播放所有动画
        self.button_move_animation.start()
        self.arrow_animation.start()
        self.panel_animation.start()
    
    def update_theme(self, dark_mode):
        self._dark_mode = dark_mode
        text_color = "white" if dark_mode else "#333"
        info_color = "#888" if dark_mode else "#999"
        border_color = "#3c3c3c" if dark_mode else "#e0e0e0"
        
        # 更新主题色为全局主题色
        try:
            from main_window import MainWindow
            if hasattr(MainWindow, 'current_theme_color'):
                self.theme_color = MainWindow.current_theme_color.name()
        except ImportError:
            pass

        bg_color = "#2b2b2b" if dark_mode else "white"

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
                color: {text_color};
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
            #summary_button {{
                background-color: {self.theme_color};
                color: {text_color};
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            #summary_button:hover {{
                opacity: 0.8;
            }}
        """)

        # 摘要面板背景样式
        self.summary_panel.setStyleSheet(f"""
            QWidget#summary_panel {{
                background-color: {bg_color};
                border-radius: 12px;
                border: 1px solid {border_color};
            }}
        """)
        
        # 收起摘要按钮样式（遵循主题色）
        self.close_summary_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme_color};
                color: {text_color};
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
        """)
        
        # 摘要文本区域样式
        self.summary_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
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
