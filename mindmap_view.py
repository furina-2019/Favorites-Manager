import math
import os
import sys
import webbrowser

def resource_path(relative_path):
    """获取资源的绝对路径"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QGraphicsView, QGraphicsScene, QGraphicsObject,
    QGraphicsRectItem, QGraphicsTextItem,
    QFrame, QToolTip, QMenu, QLineEdit, QInputDialog, QMessageBox,
    QScrollArea, QListWidget, QListWidgetItem, QApplication
)
from PyQt6.QtCore import (
    Qt, QPointF, QRectF, QRect, QPropertyAnimation, QEasingCurve,
    pyqtSignal, pyqtProperty, QTimer, QSize, QParallelAnimationGroup,
    QSequentialAnimationGroup, QAbstractAnimation, QVariantAnimation
)
from PyQt6.QtGui import (
    QColor, QPen, QBrush, QFont, QPolygonF, QPainter, QPixmap, 
    QPainterPath, QCursor, QIcon, QAction, QFontMetrics
)


class CloseOverlay(QWidget):
    """点击可关闭的遮罩层"""
    def __init__(self, close_callback, parent=None):
        super().__init__(parent)
        self.close_callback = close_callback
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.close_callback:
                self.close_callback()
            event.accept()
        else:
            super().mousePressEvent(event)

class CustomGraphicsView(QGraphicsView):
    """自定义 QGraphicsView，支持拖动和平移"""
    
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.dragging = False
        self.last_pos = None
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setMouseTracking(True)
        self._edit_mode = False
    
    @property
    def edit_mode(self):
        return self._edit_mode
    
    @edit_mode.setter
    def edit_mode(self, value):
        self._edit_mode = value
        if value:
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
    
    def contextMenuEvent(self, event):
        """空白区域右键菜单 - 只有当点击位置没有item时才显示"""
        pos = event.pos()
        item = self.itemAt(pos)
        if item is not None:
            # 如果有 item，让 item 处理右键事件
            super().contextMenuEvent(event)
            return
        
        # 空白区域才显示编辑模式菜单
        menu = QMenu(self)
        edit_action = QAction(self.parent().tr("edit_mode") if not self._edit_mode else self.parent().tr("exit_edit_mode"), self)
        edit_action.triggered.connect(lambda: self._on_toggle_edit_mode())
        menu.addAction(edit_action)
        menu.exec(event.globalPos())
    
    def _on_toggle_edit_mode(self):
        """通知父 MindmapView 切换编辑模式"""
        parent = self.parent()
        while parent and not isinstance(parent, MindmapView):
            parent = parent.parent()
        if parent:
            parent.toggle_edit_mode()
    
    def mousePressEvent(self, event):
        if event.button() in [Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton]:
            self.dragging = True
            self.last_pos = event.position().toPoint()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.dragging and self.last_pos:
            current_pos = event.position().toPoint()
            delta = current_pos - self.last_pos
            self.last_pos = current_pos
            
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() in [Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton]:
            self.dragging = False
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class MindmapNodeBase(QGraphicsObject):
    """思维导图节点基类 - 支持动画"""
    
    node_expanded = pyqtSignal()
    node_collapsed = pyqtSignal()
    node_clicked = pyqtSignal(object)
    node_hovered = pyqtSignal(object)
    node_unhovered = pyqtSignal()
    
    def __init__(self, text, level, data=None):
        super().__init__()
        self.text = text
        self.level = level
        self.data = data
        self.is_expanded = level < 2
        self.children_nodes = []
        self.parent_connection = None
        self._opacity = 1.0
        self._scale = 1.0
        self._appearance_scale = 1.0  # 用于出现动画的缩放
        
        # 原始位置（用于飘动效果）
        self._original_pos = QPointF()
        self._float_offset = QPointF()
        
        # 设置必要的标志
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsFocusable, True)
        self.setAcceptHoverEvents(True)
        
        # 确保初始缩放正确
        self.setScale(1.0)
    
    @pyqtProperty(float)
    def node_scale(self):
        return self._appearance_scale
    
    @node_scale.setter
    def node_scale(self, value):
        self._appearance_scale = value
        self.setScale(value * self._scale)
    
    def get_node_color(self):
        if self.level == 0:
            return QColor("#E74C3C")
        elif self.level == 1:
            return QColor("#27AE60")
        elif self.level == 2:
            return QColor("#27AE60")
        else:
            return QColor("#3498DB")
    
    def get_shadow_color(self):
        if self.level == 0:
            return QColor(231, 76, 60, 80)
        elif self.level == 1:
            return QColor(39, 174, 96, 80)
        elif self.level == 2:
            return QColor(39, 174, 96, 80)
        else:
            return QColor(52, 152, 219, 80)
    
    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.node_expanded.emit()
        else:
            self.node_collapsed.emit()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.node_clicked.emit(self.data)
            self.toggle_expand()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def hoverEnterEvent(self, event):
        self._scale = 1.1
        self.setScale(self._appearance_scale * 1.1)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        self._scale = 1.0
        self.setScale(self._appearance_scale)
        super().hoverLeaveEvent(event)


class CenterNode(MindmapNodeBase):
    """中心节点 - 圆形卡片"""
    
    def __init__(self, text, data=None):
        super().__init__(text, 0, data)
        self.width = 160
        self.height = 100
    
    def boundingRect(self):
        return QRectF(-self.width/2 - 5, -self.height/2 - 5, self.width + 10, self.height + 10)
    
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity)
        
        # 绘制阴影
        shadow_color = self.get_shadow_color()
        painter.setBrush(QBrush(shadow_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(
            -self.width/2 + 4, -self.height/2 + 4,
            self.width, self.height
        ))
        
        # 绘制圆形
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.setPen(QPen(self.get_node_color(), 3))
        painter.drawEllipse(QRectF(
            -self.width/2, -self.height/2,
            self.width, self.height
        ))
        
        # 绘制文字
        painter.setPen(self.get_node_color())
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        painter.setFont(font)
        
        display_text = self.text
        if len(display_text) > 10:
            display_text = display_text[:9] + "..."
            
        painter.drawText(
            QRectF(-self.width/2 + 10, -self.height/2 + 5, self.width - 20, self.height - 10),
            Qt.AlignmentFlag.AlignCenter,
            display_text
        )


class RectNode(MindmapNodeBase):
    """圆角矩形节点 - 用于第一、二级分支"""
    
    def __init__(self, text, level, data=None):
        super().__init__(text, level, data)
        self.width = 140
        self.height = 40
    
    def boundingRect(self):
        return QRectF(-self.width/2 - 5, -self.height/2 - 5, self.width + 10, self.height + 10)
    
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity)
        
        # 绘制阴影
        shadow_color = self.get_shadow_color()
        painter.setBrush(QBrush(shadow_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(
            QRectF(-self.width/2 + 3, -self.height/2 + 3,
                   self.width, self.height), 8, 8
        )
        
        # 绘制圆角矩形
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.setPen(QPen(self.get_node_color(), 2))
        painter.drawRoundedRect(
            QRectF(-self.width/2, -self.height/2,
                   self.width, self.height), 8, 8
        )
        
        # 绘制文字
        painter.setPen(self.get_node_color())
        font = QFont()
        font.setBold(True)
        font.setPointSize(11)
        painter.setFont(font)
        
        display_text = self.text
        if len(display_text) > 12:
            display_text = display_text[:11] + "..."
            
        painter.drawText(
            QRectF(-self.width/2 + 10, -self.height/2 + 3, self.width - 20, self.height - 6),
            Qt.AlignmentFlag.AlignCenter,
            display_text
        )


class ItemNode(MindmapNodeBase):
    """收藏项节点 - 矩形加三角形"""
    
    def __init__(self, text, data=None, view=None):
        super().__init__(text, 3, data)
        self.view = view
        self.width = 140  # 增大宽度
        self.height = 55   # 增大高度
        self.triangle_size = 12  # 增大三角形
        self.summary_visible = False
        self.summary_btn_width = 28  # 增大按钮宽度
        self.summary_btn_height = 18  # 按钮高度
        
        # 摘要框相关
        self.summary_box = None
        self.summary_background = None
        self.summary_max_width = 300
        
        # 拖拽相关
        self._drag_start_pos = None
        self._is_dragging = False
        
        # 设置 ToolTip
        self._update_tooltip()
    
    def tr(self, key):
        """获取翻译文本"""
        if self.view and hasattr(self.view, 'tr'):
            return self.view.tr(key)
        return key
    
    def _update_tooltip(self):
        """更新 tooltip 内容"""
        if self.data:
            tooltip_parts = []
            
            # 添加标题
            if self.data.get('title'):
                tooltip_parts.append(f"<b>{self.data['title']}</b>")
            
            # 添加 URL
            if self.data.get('url'):
                url = self.data['url']
                if len(url) > 50:
                    url = url[:47] + "..."
                tooltip_parts.append(f"<span style='color: gray;'>{url}</span>")
            
            # 添加摘要
            if self.data.get('summary'):
                summary = self.data['summary']
                if len(summary) > 150:
                    summary = summary[:147] + "..."
                tooltip_parts.append(f"<span style='color: #666;'>{summary}</span>")
            
            if tooltip_parts:
                self.setToolTip("<br><br>".join(tooltip_parts))
        else:
            self.setToolTip("")
    
    def show_summary(self):
        """显示摘要框 - 使用动画"""
        try:
            if self.view and hasattr(self.view, '_show_summary_with_animation'):
                self.view._show_summary_with_animation(self)
            else:
                # 备用方案：直接显示
                self._show_summary_direct()
        except Exception as e:
            print(f"[ERROR] show_summary failed: {e}")
    
    def _show_summary_direct(self):
        """直接显示摘要（备用方案）"""
        if not self.data or not self.data.get('summary'):
            return
        
        if self.summary_box:
            self.hide_summary_direct()
        
        summary_text = self.data['summary']
        
        self.summary_background = QGraphicsRectItem()
        self.summary_background.setBrush(QBrush(QColor(230, 245, 255)))
        self.summary_background.setPen(QPen(QColor("#3498DB"), 2))
        
        self.summary_box = QGraphicsTextItem()
        self.summary_box.setHtml(f"""
            <div style="max-width: {self.summary_max_width}px; padding: 10px;">
                <h4 style="margin: 0 0 8px 0; color: #3498DB;">{self.tr('summary_title')}</h4>
                <p style="margin: 0; color: #333; font-size: 12px; line-height: 1.5;">{summary_text}</p>
            </div>
        """)
        self.summary_box.setTextWidth(self.summary_max_width)
        
        summary_width = self.summary_box.boundingRect().width()
        summary_height = self.summary_box.boundingRect().height()
        
        x = self.width / 2 + 15
        y = -summary_height / 2
        
        self.summary_box.setPos(x, y)
        self.summary_background.setPos(x - 8, y - 8)
        self.summary_background.setRect(0, 0, summary_width + 16, summary_height + 16)
        
        self.summary_background.setParentItem(self)
        self.summary_box.setParentItem(self)
        
        self.summary_background.setZValue(10)
        self.summary_box.setZValue(11)
        
        self.summary_visible = True
        self.update()
    
    def hide_summary(self):
        """隐藏摘要框 - 使用动画"""
        try:
            if self.view and hasattr(self.view, '_hide_summary_with_animation'):
                self.view._hide_summary_with_animation(self)
            else:
                self.hide_summary_direct()
        except Exception as e:
            print(f"[ERROR] hide_summary failed: {e}")
    
    def hide_summary_direct(self):
        """直接隐藏摘要（备用方案）"""
        if self.summary_background:
            self.summary_background.setParentItem(None)
            self.summary_background = None
        if self.summary_box:
            self.summary_box.setParentItem(None)
            self.summary_box = None
        self.summary_visible = False
        self.update()
    
    def toggle_summary(self):
        """切换摘要显示"""
        if self.summary_visible:
            self.hide_summary()
        else:
            self.show_summary()
    
    def boundingRect(self):
        # 增加足够的空间以适应悬停时的1.1倍放大效果
        extra_w = self.width * 0.3  # 30%额外宽度
        extra_h = self.height * 0.3  # 30%额外高度
        return QRectF(-self.width/2 - extra_w, -self.height/2 - extra_h, 
                      self.width + extra_w * 2, self.height + extra_h * 2)
    
    def get_summary_button_rect(self):
        btn_x = self.width/2 - self.triangle_size - self.summary_btn_width - 2
        btn_y = self.height/2 - self.summary_btn_height - 2
        return QRectF(btn_x, btn_y, self.summary_btn_width, self.summary_btn_height)
    
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity)
        
        # 绘制阴影
        shadow_color = self.get_shadow_color()
        painter.setBrush(QBrush(shadow_color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # 主体阴影
        painter.drawRect(
            QRectF(-self.width/2 + 3, -self.height/2 + 3,
                   self.width - self.triangle_size, self.height)
        )
        
        # 三角形阴影
        triangle_shadow = QPolygonF([
            QPointF(self.width/2 - self.triangle_size + 3, -self.height/2 + 3),
            QPointF(self.width/2 + 3, 3),
            QPointF(self.width/2 - self.triangle_size + 3, self.height/2 + 3)
        ])
        painter.drawPolygon(triangle_shadow)
        
        # 绘制主体
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.setPen(QPen(self.get_node_color(), 2))
        
        # 主体矩形
        painter.drawRect(
            QRectF(-self.width/2, -self.height/2,
                   self.width - self.triangle_size, self.height)
        )
        
        # 三角形
        triangle = QPolygonF([
            QPointF(self.width/2 - self.triangle_size, -self.height/2),
            QPointF(self.width/2, 0),
            QPointF(self.width/2 - self.triangle_size, self.height/2)
        ])
        painter.drawPolygon(triangle)
        
        # 绘制标题（蓝色）
        painter.setPen(QColor("#3498DB"))
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        
        display_text = self.text
        if len(display_text) > 12:
            display_text = display_text[:11] + "..."
            
        painter.drawText(
            QRectF(-self.width/2 + 5, -self.height/2 + 3, self.width - self.triangle_size - self.summary_btn_width - 10, 15),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            display_text
        )
        
        # 绘制收藏时间（淡灰色）
        if self.data and 'created_at' in self.data:
            painter.setPen(QColor("#AAAAAA"))
            font.setBold(False)
            font.setPointSize(7)
            painter.setFont(font)
            created_at = self.data.get('created_at', '')
            if created_at:
                time_text = created_at[:10] if len(created_at) > 10 else created_at
                painter.drawText(
                    QRectF(-self.width/2 + 5, 0, self.width - self.triangle_size - self.summary_btn_width - 10, 15),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    time_text
                )
        
        # 绘制摘要按钮 - 改为圆角矩形
        btn_rect = self.get_summary_button_rect()
        painter.setBrush(QBrush(QColor("#CCCCCC")) if self.summary_visible else QBrush(QColor("#3498DB")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(btn_rect, 4, 4)
        
        painter.setPen(QColor("#FFFFFF"))
        font = QFont()
        font.setBold(True)
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, self.tr("summary_btn"))
        
        # 绘制锁图标（密码保护的项目）
        if self.data and self.data.get('password_hash'):
            lock_rect = QRectF(
                -self.width/2 + 4,
                self.height/2 - 16,
                14, 14
            )
            painter.setPen(QPen(QColor("#888888"), 1))
            painter.setBrush(QBrush(QColor("#EEEEEE")))
            painter.drawRoundedRect(lock_rect, 3, 3)
            painter.setPen(QColor("#666666"))
            lock_font = QFont()
            lock_font.setPointSize(8)
            painter.setFont(lock_font)
            painter.drawText(lock_rect, Qt.AlignmentFlag.AlignCenter, "🔒")
    
    def mousePressEvent(self, event):
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                local_pos = event.pos()
                btn_rect = self.get_summary_button_rect()
                
                # 检查是否点击了摘要按钮区域
                if btn_rect.contains(local_pos):
                    if self.data and self.data.get('summary'):
                        self.toggle_summary()
                    event.accept()
                    return
                
                if self.summary_visible:
                    self.hide_summary()
                
                # 编辑模式：自定义拖拽开始
                if self.view and self.view.edit_mode:
                    self._drag_start_pos = event.scenePos()
                    self._drag_moved = False
                    self._last_highlight_node = None
                    self._original_pos = self.pos()
                    self._is_dragging = True
                    event.accept()
                    return
                
                # 正常模式：检查是否有密码
                if self.data and self.data.get('password_hash'):
                    # 有密码，显示密码输入界面
                    if self.view and hasattr(self.view, '_show_password_sidebar'):
                        self.view._show_password_sidebar('input', self.data, lambda: self.view._open_item_url(self.data))
                else:
                    # 没有密码，直接发送点击信号
                    self.node_clicked.emit(self.data)
                event.accept()
            else:
                # 右键等其他情况
                QGraphicsObject.mousePressEvent(self, event)
        except Exception as e:
            print(f"[ERROR] mousePressEvent: {e}")
    
    def mouseMoveEvent(self, event):
        try:
            # 编辑模式：自定义拖拽
            if self.view and self.view.edit_mode and hasattr(self, '_is_dragging') and self._is_dragging:
                if self._drag_start_pos is not None:
                    delta = event.scenePos() - self._drag_start_pos
                    if delta.manhattanLength() > 5:
                        self._drag_moved = True
                        # 直接更新位置，完全自定义
                        new_pos = self._original_pos + (event.scenePos() - self._drag_start_pos)
                        self.setPos(new_pos)
                        self.update()
                        # 更新预览
                        self._update_drag_preview(event.scenePos())
                        event.accept()
                        return
            # 非拖拽情况，调用QGraphicsObject的实现
            QGraphicsObject.mouseMoveEvent(self, event)
        except Exception as e:
            print(f"[ERROR] mouseMoveEvent: {e}")
    
    def mouseReleaseEvent(self, event):
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                if hasattr(self, '_is_dragging') and self._is_dragging:
                    self._is_dragging = False
                    
                    # 清除预览高亮
                    if self._last_highlight_node:
                        self._last_highlight_node.setScale(1.0)
                        self._last_highlight_node.setZValue(0)
                        self._last_highlight_node.update()
                        self._last_highlight_node = None
                    
                    if self._drag_moved:
                        # 拖拽完成，检查是否有效放置
                        if self.view and hasattr(self.view, '_check_item_drop'):
                            success = self.view._check_item_drop(self)
                            if not success:
                                # 放置失败，恢复原位
                                self.setPos(self._original_pos)
                    else:
                        # 点击而非拖拽，恢复原位
                        self.setPos(self._original_pos)
                    
                    self._drag_start_pos = None
                    self._drag_moved = False
                    self._original_pos = None
                    event.accept()
                    return
            QGraphicsObject.mouseReleaseEvent(self, event)
        except Exception as e:
            print(f"[ERROR] mouseReleaseEvent: {e}")
    
    def _update_drag_preview(self, scene_pos):
        """更新拖拽预览 - 高亮目标类别节点"""
        if not self.view or not hasattr(self.view, 'nodes'):
            return
        
        current_category = self.data.get('category') if self.data else None
        
        # 找到最近的类别节点
        best_node = None
        best_distance = float('inf')
        threshold = 200
        
        for node in self.view.nodes:
            if isinstance(node, RectNode) and node.level == 1:
                node_category = node.text
                if node_category == current_category:
                    continue
                
                node_pos = node.scenePos()
                dx = scene_pos.x() - node_pos.x()
                dy = scene_pos.y() - node_pos.y()
                distance = math.sqrt(dx * dx + dy * dy)
                if distance < best_distance and distance < threshold:
                    best_distance = distance
                    best_node = node
        
        # 恢复之前高亮节点的样式
        if self._last_highlight_node and self._last_highlight_node != best_node:
            self._last_highlight_node.setScale(1.0)
            self._last_highlight_node.setZValue(0)
            self._last_highlight_node.update()
        
        # 高亮新的目标节点
        if best_node:
            best_node.setScale(1.15)
            best_node.setZValue(50)
            best_node.update()
            self._last_highlight_node = best_node
        elif self._last_highlight_node:
            self._last_highlight_node = None
    
    def mouseReleaseEvent(self, event):
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                if self.view and self.view.edit_mode and self._drag_start_pos is not None:
                    # 恢复可能的预览高亮
                    if self._last_highlight_node:
                        self._last_highlight_node.setScale(1.0)
                        self._last_highlight_node.setZValue(0)
                        self._last_highlight_node.update()
                        self._last_highlight_node = None
                    
                    if self._drag_moved:
                        # 拖拽结束，检查是否需要移动
                        if self.view and hasattr(self.view, '_check_item_drop'):
                            self.view._check_item_drop(self)
                    else:
                        # 点击而非拖拽，恢复位置
                        self.setPos(self._original_pos)
                    
                    self._drag_start_pos = None
                    self._drag_moved = False
                    self._original_pos = None
                    event.accept()
                    return
            super().mouseReleaseEvent(event)
        except Exception as e:
            print(f"[ERROR] mouseReleaseEvent failed: {e}")
            import traceback
            traceback.print_exc()
    
    def contextMenuEvent(self, event):
        """右键菜单"""
        if not self.data:
            return
        
        # 获取翻译函数
        def tr(key):
            if self.view and hasattr(self.view, 'tr'):
                return self.view.tr(key)
            return key
        
        menu = QMenu()
        item_id = self.data.get('id')
        has_password = bool(self.data.get('password_hash'))
        
        # 编辑
        edit_action = QAction(tr("edit"), menu)
        edit_action.triggered.connect(lambda: self._on_edit_item())
        menu.addAction(edit_action)
        
        # 删除
        delete_action = QAction(tr("delete"), menu)
        delete_action.triggered.connect(lambda: self._on_delete_item())
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        # 密码选项
        if has_password:
            change_pwd_action = QAction(tr("change_password"), menu)
            change_pwd_action.triggered.connect(lambda: self._on_change_password())
            menu.addAction(change_pwd_action)
            
            remove_pwd_action = QAction(tr("remove_password"), menu)
            remove_pwd_action.triggered.connect(lambda: self._on_remove_password())
            menu.addAction(remove_pwd_action)
        else:
            set_pwd_action = QAction(tr("set_password"), menu)
            set_pwd_action.triggered.connect(lambda: self._on_set_password())
            menu.addAction(set_pwd_action)
        
        menu.exec(event.screenPos())
    
    def _on_edit_item(self):
        if self.view and hasattr(self.view, 'edit_item'):
            self.view.edit_item(self)
    
    def _on_delete_item(self):
        if self.view and hasattr(self.view, 'delete_item'):
            self.view.delete_item(self)
    
    def _on_set_password(self):
        """打开设置密码侧边栏"""
        if self.view and hasattr(self.view, '_show_password_sidebar'):
            self.view._show_password_sidebar('set', self.data)
    
    def _on_change_password(self):
        """打开修改密码侧边栏"""
        if self.view and hasattr(self.view, '_show_password_sidebar'):
            self.view._show_password_sidebar('change', self.data)
    
    def _on_remove_password(self):
        """打开移除密码侧边栏"""
        if self.view and hasattr(self.view, '_show_password_sidebar'):
            self.view._show_password_sidebar('remove', self.data)
    
    def hoverEnterEvent(self, event):
        try:
            # 视觉反馈：放大节点并置顶
            self._scale = 1.15
            self.setScale(self._appearance_scale * self._scale)
            self.setZValue(100)  # 置顶
            self.update()
            
            # 发出信号显示封面预览
            self.node_hovered.emit(self.data)
        except Exception as e:
            print(f"[ERROR] hoverEnterEvent failed: {e}")
    
    def hoverLeaveEvent(self, event):
        try:
            # 恢复原状
            self._scale = 1.0
            self.setScale(self._appearance_scale)
            self.setZValue(0)  # 恢复层级
            self.update()
            
            # 发出信号隐藏封面预览
            self.node_unhovered.emit()
        except Exception as e:
            print(f"[ERROR] hoverLeaveEvent failed: {e}")


class ConnectionCurve(QGraphicsObject):
    """贝塞尔曲线连接线 - 简单淡入淡出"""
    
    def __init__(self, source, target, level=1):
        super().__init__()
        self.source = source
        self.target = target
        self.level = level
        self._full_path = QPainterPath()
        self.update_path()
        self.setZValue(-1)
    
    def boundingRect(self):
        return self._full_path.boundingRect().adjusted(-10, -10, 10, 10)
    
    def get_pen(self):
        pen = QPen()
        pen.setWidth(3)
        if self.level == 0:
            pen.setColor(QColor(231, 76, 60))
        elif self.level == 1:
            pen.setColor(QColor(39, 174, 96))
        else:
            pen.setColor(QColor(52, 152, 219))
        pen.setStyle(Qt.PenStyle.SolidLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        return pen
    
    def update_path(self):
        source_pos = self.source.sceneBoundingRect().center()
        target_pos = self.target.sceneBoundingRect().center()
        
        self._full_path = QPainterPath(source_pos)
        
        dx = target_pos.x() - source_pos.x()
        dy = target_pos.y() - source_pos.y()
        
        ctrl_offset = abs(dx) * 0.5
        if ctrl_offset < 30:
            ctrl_offset = 30
        
        ctrl1 = QPointF(source_pos.x() + ctrl_offset, source_pos.y())
        ctrl2 = QPointF(target_pos.x() - ctrl_offset, target_pos.y())
        
        self._full_path.cubicTo(ctrl1, ctrl2, target_pos)
        self.update()
    
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self.get_pen())
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self._full_path)


class SummaryPopup(QFrame):
    """摘要弹出框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("summary_popup")
        self.setStyleSheet("""
            QFrame#summary_popup {
                background-color: white;
                border: 2px solid #3498DB;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("color: #333; font-size: 12px;")
        self.summary_label.setMaximumWidth(200)
        layout.addWidget(self.summary_label)
        
        self.hide()
    
    def show_summary(self, summary_text):
        if summary_text:
            self.summary_label.setText(summary_text)
            self.adjustSize()
            self.show()
            
    def hide_summary(self):
        self.hide()


class CoverPreviewPopup(QFrame):
    """封面预览弹出框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cover_preview")
        self.setStyleSheet("""
            QFrame#cover_preview {
                background-color: white;
                border: 2px solid #3498DB;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(200, 120)
        self.cover_label.setStyleSheet("border-radius: 4px;")
        self.cover_label.setScaledContents(True)
        layout.addWidget(self.cover_label)
        
        self.title_label = QLabel()
        self.title_label.setStyleSheet("color: #333; font-size: 11px; font-weight: bold;")
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumWidth(200)
        layout.addWidget(self.title_label)
        
        self.hide()
    
    def show_preview(self, cover_path, title, summary=""):
        pixmap = QPixmap(cover_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(200, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
            self.cover_label.setPixmap(scaled_pixmap)
        self.title_label.setText(title)
        
        if summary:
            self.title_label.setToolTip(summary)
        
        self.adjustSize()
        self.show()
        self.raise_()
    
    def hide_preview(self):
        self.hide()


class MindmapView(QWidget):
    """思维导图视图"""
    
    back_requested = pyqtSignal()
    add_item_requested = pyqtSignal()
    edit_item_requested = pyqtSignal(object)
    refresh_view_requested = pyqtSignal()  # 新增：刷新主视图信号
    
    def __init__(self, db, folder_id, folder_name, strings=None, current_lang="zh", parent=None):
        super().__init__(parent)
        self.db = db
        self.folder_id = folder_id
        self.folder_name = folder_name
        self.strings = strings or {}
        self.current_lang = current_lang
        self.nodes = []
        self.connections = []
        self.summary_popup = None
        self.cover_preview = None
        self.current_summary_node = None
        self.edit_mode = False
        self.category_sidebar = None
        self.category_overlay = None
        self._active_animations = []  # 保存动画引用防止GC
        self._is_initial_build = True
        self.init_ui()
        self.load_data()
    
    def tr(self, key):
        """获取翻译文本"""
        lang_strings = self.strings.get(self.current_lang, self.strings.get("zh", {}))
        return lang_strings.get(key, key)
    
    def update_language(self, lang):
        """更新语言并刷新UI"""
        self.current_lang = lang
        
        # 保存当前的展开/折叠状态
        expanded_nodes = set()
        collapsed_nodes = set()
        for node in self.nodes:
            if hasattr(node, 'is_expanded'):
                if node.is_expanded:
                    expanded_nodes.add(node.text)
                else:
                    collapsed_nodes.add(node.text)
        
        # 更新顶部栏的返回按钮
        back_btn = self.findChild(QPushButton, "back_btn")
        if back_btn:
            back_btn.setText(self.tr("back"))
        
        # 更新顶部栏的标题
        title_label = self.findChild(QLabel, "mindmap_title_label")
        if title_label:
            title_label.setText(self.tr("mindmap_title"))
        
        # 更新搜索框占位符
        if hasattr(self, 'search_edit') and self.search_edit:
            self.search_edit.setPlaceholderText(self.tr("item_search_placeholder"))
        
        # 更新添加按钮
        add_btn = self.findChild(QPushButton, "add_item_btn")
        if add_btn:
            add_btn.setText(self.tr("add_item_btn"))
        
        # 重新构建思维导图以应用新语言
        self._rebuild_mindmap()
        
        # 恢复展开/折叠状态
        for node in self.nodes:
            if hasattr(node, 'is_expanded'):
                if node.text in expanded_nodes:
                    node.is_expanded = True
                elif node.text in collapsed_nodes:
                    node.is_expanded = False
        
        # 重新展开之前展开的节点
        for node in self.nodes:
            if hasattr(node, 'is_expanded') and node.is_expanded:
                if hasattr(node, 'expand'):
                    node.expand()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 顶部栏 - 与收藏项展示页面样式一致
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(15, 10, 15, 10)
        
        back_btn = QPushButton(self.tr("back"))
        back_btn.setObjectName("back_btn")
        back_btn.setFixedSize(80, 36)
        back_btn.clicked.connect(self.back_requested.emit)
        top_bar.addWidget(back_btn)
        
        title_label = QLabel(self.tr("mindmap_title"))
        title_label.setObjectName("mindmap_title_label")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        top_bar.addWidget(title_label)
        
        top_bar.addStretch()
        
        layout.addLayout(top_bar)
        
        # 工具栏（筛选、搜索、添加）- 与收藏项展示页面样式一致
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(15, 0, 15, 10)
        toolbar.setSpacing(10)
        
        # 搜索框 - 与收藏项展示页面样式一致
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("item_search")
        self.search_edit.setPlaceholderText(self.tr("item_search_placeholder"))
        self.search_edit.setFixedHeight(32)
        self.search_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                color: #333;
            }
            QLineEdit:focus {
                border-bottom: 3px solid #3498DB;
            }
        """)
        self.search_edit.textChanged.connect(self._filter_items)
        toolbar.addWidget(self.search_edit)
        
        # 筛选按钮 - 与收藏项展示页面样式一致
        self.filter_btn = QPushButton()
        self.filter_btn.setObjectName("filter_btn")
        self.filter_btn.setFixedSize(32, 32)
        self.filter_btn.setIcon(QIcon(resource_path("resources/icons/filter.png")))
        self.filter_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid #3498DB;
                border-radius: 4px;
                padding: 4px;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #3498DB;
            }
        """)
        self.filter_btn.clicked.connect(self._show_filter_menu)
        toolbar.addWidget(self.filter_btn)
        
        # 添加按钮 - 与收藏项展示页面样式一致
        add_btn = QPushButton(self.tr("add_item_btn"))
        add_btn.setObjectName("add_item_btn")
        add_btn.setFixedHeight(32)
        add_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid #3498DB;
                border-radius: 4px;
                padding: 6px 12px;
                background-color: #3498DB;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        add_btn.clicked.connect(self.add_item_requested.emit)
        toolbar.addWidget(add_btn)
        
        layout.addLayout(toolbar)
        
        # 场景和视图
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-3000, -3000, 6000, 6000)
        
        self.view = CustomGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setBackgroundBrush(QBrush(QColor("#F8F9FA")))
        self.view.setStyleSheet("QGraphicsView { border: none; background: #F8F9FA; }")
        self.view.wheelEvent = self.wheel_event
        
        layout.addWidget(self.view)
        
        # 创建封面预览弹窗
        self.cover_preview = CoverPreviewPopup(self.view)
        
    def wheel_event(self, event):
        factor = 1.15
        if event.angleDelta().y() > 0:
            self.view.scale(factor, factor)
        else:
            self.view.scale(1/factor, 1/factor)
    
    def load_data(self):
        items = self.db.get_items_by_folder(self.folder_id)
        
        categories = {}
        for item in items:
            item_id, item_type, title, url, category, cover_path, pwd_hash, summary, created_at = item
            category = category or "未分类"
            
            if category not in categories:
                categories[category] = {'link': [], 'file': []}
            
            item_data = {
                'id': item_id,
                'title': title,
                'url': url,
                'category': category,
                'cover_path': cover_path,
                'summary': summary or "",
                'item_type': item_type,
                'created_at': created_at or "",
                'password_hash': pwd_hash
            }
            
            if item_type in categories[category]:
                categories[category][item_type].append(item_data)
        
        for category_name in categories:
            for type_key in categories[category_name]:
                categories[category_name][type_key].sort(key=lambda x: x['title'])
        
        self.build_mindmap(categories)
    
    def build_mindmap(self, categories):
        self.scene.clear()
        self.nodes = []
        self.connections = []
        self._is_initial_build = True
        self._animation_delay = 0  # 动画延迟计数器
        
        # 创建中心节点
        center_node = CenterNode(self.folder_name)
        center_node.setPos(0, 0)
        center_node._original_pos = QPointF(0, 0)
        center_node._node_depth = 0
        self.scene.addItem(center_node)
        self.nodes.append(center_node)
        
        sorted_categories = sorted(categories.items(), key=lambda x: x[0])
        
        # 计算每个类别下的总收藏项数量
        category_counts = []
        for category_name, type_items in sorted_categories:
            count = len(type_items.get('link', [])) + len(type_items.get('file', []))
            category_counts.append(count)
        
        num_categories = len(sorted_categories)
        total_items = sum(category_counts)
        
        # 计算每个类别需要的角度空间 - 增大角度
        angles_needed = [20 + count * 4 for count in category_counts]
        total_angle = sum(angles_needed)
        
        # 如果总角度超过360度，按比例缩小
        if total_angle > 360:
            scale_factor = 360 / total_angle
            angles_needed = [angle * scale_factor for angle in angles_needed]
            total_angle = 360
        
        # 计算半径 - 增大半径以获得更大间距
        if total_items > 50:
            radius_level1 = 700
        elif total_items > 30:
            radius_level1 = 600
        elif total_items > 15:
            radius_level1 = 550
        else:
            radius_level1 = 500
        
        # 计算起始角度，使布局居中
        current_angle = -90  # 从顶部开始
        
        for i, (category_name, type_items) in enumerate(sorted_categories):
            half_angle = angles_needed[i] / 2
            angle = current_angle + half_angle
            
            angle_rad = angle * math.pi / 180
            x = radius_level1 * math.cos(angle_rad)
            y = radius_level1 * math.sin(angle_rad)
            
            category_node = RectNode(category_name, level=1, data={'category': category_name})
            category_node.setPos(x, y)
            category_node._original_pos = QPointF(x, y)
            category_node._node_depth = 1
            self.scene.addItem(category_node)
            self.nodes.append(category_node)
            
            conn = ConnectionCurve(center_node, category_node, level=0)
            conn.setOpacity(1)  # 初始直接显示
            category_node.parent_connection = conn
            self.scene.addItem(conn)
            self.connections.append(conn)
            
            category_node.node_expanded.connect(
                lambda node=category_node, items=type_items: self._expand_category(node, items, animated=True))
            category_node.node_collapsed.connect(
                lambda node=category_node: self._collapse_category(node))
            
            # 初始展开类别，创建类型节点
            self._expand_category(category_node, type_items, animated=False)
            
            # 手动展开所有子节点以显示完整结构
            for type_node in category_node.children_nodes:
                type_key = type_node.data.get('type')
                if type_key and type_key in type_items:
                    self._expand_type(type_node, type_items[type_key], animated=False)
            
            current_angle += angles_needed[i]
        
        # 结束初始构建状态
        self._is_initial_build = False
        
        # 设置视图中心为原点（中心节点位置）
        self.view.resetTransform()
        self.view.centerOn(0, 0)
        
        # 调用进入动画
        QTimer.singleShot(100, self._play_entry_animation)
        
        # 启动飘动效果定时器
        self._float_timer = QTimer(self)
        self._float_timer.timeout.connect(self._update_floating_positions)
        self._float_timer.start(3000)  # 每3秒更新一次
    
    def _play_entry_animation(self):
        """播放进入动画 - 所有节点从中心展开"""
        self._is_initial_build = False
        
        print("[DEBUG] Starting entry animation...")
        
        # 首先把所有非中心节点移到中心位置并设为不可见
        for node in self.nodes:
            if hasattr(node, '_node_depth') and node._node_depth > 0:
                node.setPos(0, 0)  # 移到中心
                node.node_scale = 0.01  # 缩小
                node.update()  # 立即重绘
        
        # 然后创建动画让它们从中心展开
        for node in self.nodes:
            if hasattr(node, '_node_depth') and node._node_depth > 0:
                # 延迟根据节点深度
                delay = node._node_depth * 200  # 增加延迟
                
                def start_node_animation(n=node, delay_val=delay):
                    print(f"[DEBUG] Starting animation for node: {n.text}, depth={n._node_depth}, delay={delay_val}")
                    
                    # 位置动画 - 从中心移动到目标位置
                    pos_anim = QPropertyAnimation(n, b'pos')
                    pos_anim.setDuration(600)  # 增加时间
                    pos_anim.setStartValue(QPointF(0, 0))
                    pos_anim.setEndValue(n._original_pos)
                    pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                    
                    # 缩放动画 - 从小到大
                    scale_anim = QPropertyAnimation(n, b'node_scale')
                    scale_anim.setDuration(600)
                    scale_anim.setStartValue(0.01)
                    scale_anim.setEndValue(1.0)
                    scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)
                    
                    # 并行播放两个动画
                    anim_group = QParallelAnimationGroup(self)
                    anim_group.addAnimation(pos_anim)
                    anim_group.addAnimation(scale_anim)
                    
                    # 保存引用
                    self._active_animations.append(anim_group)
                    anim_group.finished.connect(lambda: self._cleanup_animation(anim_group))
                    anim_group.start()
                
                QTimer.singleShot(delay, start_node_animation)
        
        for conn in self.connections:
            # 连接淡入动画
            conn.setOpacity(0)
            
            # 延迟根据连接层级
            delay = conn.level * 200 + 100  # 增加延迟
            
            def start_conn_animation(c=conn, delay_val=delay):
                print(f"[DEBUG] Starting connection animation, level={c.level}, delay={delay_val}")
                
                path_anim = QPropertyAnimation(c, b'opacity')
                path_anim.setDuration(500)  # 增加时间
                path_anim.setStartValue(0.0)
                path_anim.setEndValue(1.0)
                path_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                
                # 保存引用
                self._active_animations.append(path_anim)
                path_anim.finished.connect(lambda: self._cleanup_animation(path_anim))
                path_anim.start()
            
            QTimer.singleShot(delay, start_conn_animation)
    
    def _animate_node_appear_along_path(self, node, target_pos, source_node, delay=0):
        """让节点沿着连接曲线从父节点移动到目标位置"""
        node.setPos(source_node.pos())
        node.node_scale = 0.01
        node._original_pos = target_pos
        
        def start_animation():
            # 立即重绘确保起始状态可见
            node.update()
            
            anim_group = QParallelAnimationGroup(self)
            
            # 位置动画 - 从父节点位置移动到目标位置
            pos_anim = QPropertyAnimation(node, b'pos')
            pos_anim.setDuration(600)  # 增加时间
            pos_anim.setStartValue(source_node.pos())
            pos_anim.setEndValue(target_pos)
            pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            
            # 缩放动画 - 从小到大
            scale_anim = QPropertyAnimation(node, b'node_scale')
            scale_anim.setDuration(600)
            scale_anim.setStartValue(0.01)
            scale_anim.setEndValue(1.0)
            scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)
            
            anim_group.addAnimation(pos_anim)
            anim_group.addAnimation(scale_anim)
            
            # 保存引用防止 GC
            self._active_animations.append(anim_group)
            anim_group.finished.connect(lambda: self._cleanup_animation(anim_group))
            anim_group.start()
        
        if delay > 0:
            QTimer.singleShot(delay, start_animation)
        else:
            start_animation()
    
    def _animate_connection_draw(self, conn, delay=0):
        """连接曲线淡入动画"""
        def start_animation():
            # 立即重绘确保起始状态可见
            conn.update()
            
            path_anim = QPropertyAnimation(conn, b'opacity')
            path_anim.setDuration(500)  # 增加时间
            path_anim.setStartValue(0.0)
            path_anim.setEndValue(1.0)
            path_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            
            # 保存引用防止 GC
            self._active_animations.append(path_anim)
            path_anim.finished.connect(lambda: self._cleanup_animation(path_anim))
            path_anim.start()
        
        if delay > 0:
            QTimer.singleShot(delay, start_animation)
        else:
            start_animation()
    
    def _cleanup_animation(self, anim):
        """清理已完成的动画"""
        if anim in self._active_animations:
            self._active_animations.remove(anim)
    
    def _animate_node_disappear(self, node):
        """节点消失动画"""
        anim_group = QParallelAnimationGroup(self)
        
        scale_anim = QPropertyAnimation(node, b'node_scale')
        scale_anim.setDuration(250)
        scale_anim.setStartValue(node.node_scale)
        scale_anim.setEndValue(0.01)
        scale_anim.setEasingCurve(QEasingCurve.Type.InBack)
        
        anim_group.addAnimation(scale_anim)
        
        # 保存动画引用防止 GC
        self._active_animations.append(anim_group)
        anim_group.finished.connect(lambda: self._cleanup_animation(anim_group))
        
        # 动画结束后移除节点
        anim_group.finished.connect(lambda: self._remove_node_safe(node))
        anim_group.start()
    
    def _animate_connection_undraw(self, conn):
        """连接曲线淡出动画"""
        path_anim = QPropertyAnimation(conn, b'opacity')
        path_anim.setDuration(250)
        path_anim.setStartValue(conn.opacity())
        path_anim.setEndValue(0.0)
        path_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        
        # 保存动画引用防止 GC
        self._active_animations.append(path_anim)
        path_anim.finished.connect(lambda: self._cleanup_animation(path_anim))
        path_anim.finished.connect(lambda: self._remove_connection_safe(conn))
        path_anim.start()
    
    def _remove_node_safe(self, node):
        """安全移除节点"""
        if node.scene():
            self.scene.removeItem(node)
            if node in self.nodes:
                self.nodes.remove(node)
    
    def _remove_connection_safe(self, conn):
        """安全移除连接"""
        if conn.scene():
            self.scene.removeItem(conn)
            if conn in self.connections:
                self.connections.remove(conn)
    
    def _expand_category(self, category_node, type_items, animated=True):
        # 始终使用同步删除，确保位置正确
        self._clear_children(category_node, animate=False)
        category_node.is_expanded = True
        
        # 使用原始位置计算，避免位置错误
        category_pos = category_node._original_pos if hasattr(category_node, '_original_pos') else category_node.pos()
        dx = category_pos.x()
        dy = category_pos.y()
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance < 1:
            direction_x, direction_y = 1, 0
        else:
            direction_x = dx / distance
            direction_y = dy / distance
        
        perp_x = -direction_y
        perp_y = direction_x
        
        type_keys = []
        if type_items.get('link'):
            type_keys.append(('link', self.tr('type_link')))
        if type_items.get('file'):
            type_keys.append(('file', self.tr('type_file')))
        
        if not type_keys:
            return
            
        num_types = len(type_keys)
        # 增大距离和间距
        forward_distance = 300
        spacing = 150
        
        for j, (type_key, type_label) in enumerate(type_keys):
            forward_x = category_pos.x() + direction_x * forward_distance
            forward_y = category_pos.y() + direction_y * forward_distance
            
            if num_types == 1:
                offset = 0
            else:
                offset = (j - (num_types - 1) / 2) * spacing
            
            x = forward_x + perp_x * offset
            y = forward_y + perp_y * offset
            
            type_node = RectNode(type_label, level=2, 
                                data={'type': type_key, 'category': category_node.text})
            type_node.setPos(x, y)
            type_node._original_pos = QPointF(x, y)
            type_node._node_depth = 2
            type_node.node_scale = 1
            self.scene.addItem(type_node)
            self.nodes.append(type_node)
            
            conn = ConnectionCurve(category_node, type_node, level=1)
            conn.update_path()  # 确保路径正确
            conn.setOpacity(1)  # 显示
            type_node.parent_connection = conn
            self.scene.addItem(conn)
            self.connections.append(conn)
            conn.update()
            
            if animated and not self._is_initial_build:
                # 延迟隐藏，然后动画出现
                def do_animate(c=conn, n=type_node, j=j):
                    # 先隐藏
                    c.setOpacity(0)
                    n.node_scale = 0.01
                    c.update()
                    n.update()
                    
                    # 然后动画出现
                    c_anim = QPropertyAnimation(c, b'opacity')
                    c_anim.setDuration(500)
                    c_anim.setStartValue(0.0)
                    c_anim.setEndValue(1.0)
                    c_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                    self._active_animations.append(c_anim)
                    c_anim.finished.connect(lambda: self._cleanup_animation(c_anim))
                    c_anim.start()
                    
                    # 节点动画
                    pos_anim = QPropertyAnimation(n, b'pos')
                    pos_anim.setDuration(600)
                    pos_anim.setStartValue(category_node.pos())
                    pos_anim.setEndValue(QPointF(x, y))
                    pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                    
                    scale_anim = QPropertyAnimation(n, b'node_scale')
                    scale_anim.setDuration(600)
                    scale_anim.setStartValue(0.01)
                    scale_anim.setEndValue(1.0)
                    scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)
                    
                    anim_group = QParallelAnimationGroup(self)
                    anim_group.addAnimation(pos_anim)
                    anim_group.addAnimation(scale_anim)
                    self._active_animations.append(anim_group)
                    anim_group.finished.connect(lambda: self._cleanup_animation(anim_group))
                    anim_group.start()
                
                QTimer.singleShot(j * 50, do_animate)
            
            type_node.node_expanded.connect(
                lambda node=type_node, items=type_items[type_key]: self._expand_type(node, items, animated=True))
            type_node.node_collapsed.connect(
                lambda node=type_node: self._collapse_type(node))
            
            category_node.children_nodes.append(type_node)
            
            # 智能展开: 只展开当前层，不自动展开下一层
            # 移除 self._expand_type(type_node, type_items[type_key], animated=animated)
            
        self._update_connections()
    
    def _expand_type(self, type_node, items, animated=True):
        # 始终使用同步删除
        self._clear_children(type_node, animate=False)
        type_node.is_expanded = True
        
        if not items:
            return
        
        # 使用原始位置
        type_pos = type_node._original_pos if hasattr(type_node, '_original_pos') and type_node._original_pos != QPointF() else type_node.pos()
        
        # 找到父节点并使用父节点的原始位置
        parent_node = None
        for node in self.nodes:
            if hasattr(node, 'children_nodes') and type_node in node.children_nodes:
                parent_node = node
                break
        
        if parent_node:
            parent_pos = parent_node._original_pos if hasattr(parent_node, '_original_pos') and parent_node._original_pos != QPointF() else parent_node.pos()
            dx = type_pos.x() - parent_pos.x()
            dy = type_pos.y() - parent_pos.y()
        else:
            dx, dy = 1, 0
        
        distance = math.sqrt(dx * dx + dy * dy)
        if distance < 1:
            direction_x, direction_y = 1, 0
        else:
            direction_x = dx / distance
            direction_y = dy / distance
        
        perp_x = -direction_y
        perp_y = direction_x
        
        num_items = len(items)
        
        # 根据收藏项数量增大间距和前向距离
        if num_items <= 3:
            forward_distance = 250
            spacing = 180
        elif num_items <= 6:
            forward_distance = 280
            spacing = 150
        elif num_items <= 10:
            forward_distance = 300
            spacing = 130
        else:
            forward_distance = 320
            spacing = 110
        
        for k, item_data in enumerate(items):
            forward_x = type_pos.x() + direction_x * forward_distance
            forward_y = type_pos.y() + direction_y * forward_distance
            
            if num_items == 1:
                offset = 0
            else:
                offset = (k - (num_items - 1) / 2) * spacing
            
            x = forward_x + perp_x * offset
            y = forward_y + perp_y * offset
            
            item_node = ItemNode(item_data['title'], data=item_data, view=self)
            item_node.setPos(x, y)
            item_node._original_pos = QPointF(x, y)
            item_node._node_depth = 3
            item_node.node_scale = 1  # 默认可见
            self.scene.addItem(item_node)
            self.nodes.append(item_node)
            
            # 连接事件
            item_node.node_clicked.connect(self._open_item_url)
            item_node.node_hovered.connect(self._show_cover_preview)
            item_node.node_unhovered.connect(self._hide_cover_preview)
            
            conn = ConnectionCurve(type_node, item_node, level=2)
            conn.setOpacity(1)  # 默认可见
            item_node.parent_connection = conn
            self.scene.addItem(conn)
            self.connections.append(conn)
            conn.update_path()
            conn.update()
            
            if animated and not self._is_initial_build:
                # 延迟隐藏，然后动画出现
                def do_animate(conn=conn, item_node=item_node, x=x, y=y, type_node=type_node):
                    # 先隐藏
                    conn.setOpacity(0)
                    item_node.node_scale = 0.01
                    conn.update()
                    item_node.update()
                    
                    # 然后动画出现
                    c_anim = QPropertyAnimation(conn, b'opacity')
                    c_anim.setDuration(500)
                    c_anim.setStartValue(0.0)
                    c_anim.setEndValue(1.0)
                    c_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                    self._active_animations.append(c_anim)
                    c_anim.finished.connect(lambda: self._cleanup_animation(c_anim))
                    c_anim.start()
                    
                    # 节点动画
                    pos_anim = QPropertyAnimation(item_node, b'pos')
                    pos_anim.setDuration(600)
                    pos_anim.setStartValue(type_node.pos())
                    pos_anim.setEndValue(QPointF(x, y))
                    pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                    
                    scale_anim = QPropertyAnimation(item_node, b'node_scale')
                    scale_anim.setDuration(600)
                    scale_anim.setStartValue(0.01)
                    scale_anim.setEndValue(1.0)
                    scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)
                    
                    anim_group = QParallelAnimationGroup(self)
                    anim_group.addAnimation(pos_anim)
                    anim_group.addAnimation(scale_anim)
                    self._active_animations.append(anim_group)
                    anim_group.finished.connect(lambda: self._cleanup_animation(anim_group))
                    anim_group.start()
                
                QTimer.singleShot(k * 40, do_animate)
            
            type_node.children_nodes.append(item_node)
        
        self._update_connections()
    
    def _open_item_url(self, data):
        """打开收藏项的URL"""
        if data and data.get('url'):
            url = data['url']
            try:
                webbrowser.open(url)
            except Exception as e:
                print(f"[ERROR] 无法打开链接: {e}")
    
    def _show_cover_preview(self, data):
        """显示封面预览"""
        try:
            if data and data.get('cover_path') and os.path.exists(data['cover_path']):
                cover_path = data['cover_path']
                title = data.get('title', '')
                summary = data.get('summary', '')
                
                # 获取鼠标位置并显示预览
                cursor_pos = self.view.mapFromGlobal(self.cursor().pos())
                self.cover_preview.move(cursor_pos.x() + 15, cursor_pos.y() + 15)
                self.cover_preview.show_preview(cover_path, title, summary)
                self.cover_preview.raise_()
        except Exception as e:
            print(f"[ERROR] 显示封面预览失败: {e}")
    
    def _hide_cover_preview(self):
        """隐藏封面预览"""
        try:
            self.cover_preview.hide_preview()
        except Exception as e:
            print(f"[ERROR] 隐藏封面预览失败: {e}")
    
    def _clear_children(self, parent_node, animate=True):
        for child in parent_node.children_nodes[:]:
            # 先递归处理子节点
            self._clear_children(child, animate=animate)
            
            if hasattr(child, 'parent_connection') and child.parent_connection:
                conn = child.parent_connection
                if animate and conn.scene():
                    # 播放连接擦除动画
                    self._animate_connection_undraw(conn)
                else:
                    self.scene.removeItem(conn)
                    if conn in self.connections:
                        self.connections.remove(conn)
                child.parent_connection = None
            
            if animate and child.scene():
                # 播放节点消失动画
                self._animate_node_disappear(child)
            else:
                self.scene.removeItem(child)
                if child in self.nodes:
                    self.nodes.remove(child)
        
        parent_node.children_nodes.clear()
    
    def _collapse_category(self, category_node):
        category_node.is_expanded = False
        self._clear_children(category_node, animate=True)
        self._update_connections()
    
    def _collapse_type(self, type_node):
        type_node.is_expanded = False
        self._clear_children(type_node, animate=True)
        self._update_connections()
    
    def _update_connections(self):
        # 只更新有效连线的路径
        for conn in self.connections:
            try:
                if conn.source.scene() and conn.target.scene():
                    conn.update_path()
            except RuntimeError:
                pass  # 对象可能已被删除
    
    def _update_floating_positions(self):
        """更新节点的飘动位置"""
        import random
        
        for node in self.nodes:
            if hasattr(node, '_node_depth') and node._node_depth > 0:
                # 添加轻微的随机偏移
                original_pos = node._original_pos if hasattr(node, '_original_pos') else node.pos()
                
                # 只在没有悬停且没有被选中时才飘动
                if not node.isUnderMouse() and node.node_scale > 0.5:
                    offset_x = random.uniform(-3, 3)
                    offset_y = random.uniform(-3, 3)
                    
                    target_pos = QPointF(original_pos.x() + offset_x, original_pos.y() + offset_y)
                    
                    # 创建平滑的位移动画
                    pos_anim = QPropertyAnimation(node, b'pos')
                    pos_anim.setDuration(2000)  # 慢速移动
                    pos_anim.setStartValue(node.pos())
                    pos_anim.setEndValue(target_pos)
                    pos_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
                    pos_anim.start()
    
    def _show_summary_with_animation(self, node):
        """带动画显示摘要"""
        if not node.data or not node.data.get('summary'):
            return
        
        # 如果摘要框已存在，先移除
        if node.summary_box:
            self._hide_summary_with_animation(node)
            QTimer.singleShot(250, lambda: self._create_summary_with_animation(node))
        else:
            self._create_summary_with_animation(node)
    
    def _create_summary_with_animation(self, node):
        """创建摘要并显示动画"""
        if not node.data or not node.data.get('summary'):
            return
        
        summary_text = node.data['summary']
        
        # 创建背景框
        node.summary_background = QGraphicsRectItem()
        node.summary_background.setBrush(QBrush(QColor(230, 245, 255)))
        node.summary_background.setPen(QPen(QColor("#3498DB"), 2))
        
        # 创建文本
        node.summary_box = QGraphicsTextItem()
        node.summary_box.setHtml(f"""
            <div style="max-width: {node.summary_max_width}px; padding: 10px;">
                <h4 style="margin: 0 0 8px 0; color: #3498DB;">{node.tr('summary_title')}</h4>
                <p style="margin: 0; color: #333; font-size: 12px; line-height: 1.5;">{summary_text}</p>
            </div>
        """)
        node.summary_box.setTextWidth(node.summary_max_width)
        
        # 获取尺寸
        summary_width = node.summary_box.boundingRect().width()
        summary_height = node.summary_box.boundingRect().height()
        
        # 设置位置
        x = node.width / 2 + 15
        y = -summary_height / 2
        
        node.summary_box.setPos(x, y)
        node.summary_background.setPos(x - 8, y - 8)
        node.summary_background.setRect(0, 0, summary_width + 16, summary_height + 16)
        
        # 设置父项
        node.summary_background.setParentItem(node)
        node.summary_box.setParentItem(node)
        
        # 设置层级
        node.summary_background.setZValue(10)
        node.summary_box.setZValue(11)
        
        # 设置初始缩放为0
        node.summary_background.setScale(0)
        node.summary_box.setScale(0)
        
        # 创建展开动画 - 使用 QVariantAnimation 因为 scale 不是 QGraphicsItem 的 Qt 属性
        anim_group = QParallelAnimationGroup(self)
        
        def create_scale_animation(target_item, start_val, end_val, duration):
            anim = QVariantAnimation(self)
            anim.setDuration(duration)
            anim.setStartValue(start_val)
            anim.setEndValue(end_val)
            anim.setEasingCurve(QEasingCurve.Type.OutBack)
            anim.valueChanged.connect(lambda val, item=target_item: item.setScale(val))
            return anim
        
        bg_anim = create_scale_animation(node.summary_background, 0.0, 1.0, 250)
        text_anim = create_scale_animation(node.summary_box, 0.0, 1.0, 250)
        
        anim_group.addAnimation(bg_anim)
        anim_group.addAnimation(text_anim)
        anim_group.start()
        
        node.summary_visible = True
        node.update()
    
    def _hide_summary_with_animation(self, node):
        """带动画隐藏摘要"""
        if not node.summary_box:
            return
        
        anim_group = QParallelAnimationGroup(self)
        
        def create_scale_animation(target_item, start_val, end_val, duration):
            anim = QVariantAnimation(self)
            anim.setDuration(duration)
            anim.setStartValue(start_val)
            anim.setEndValue(end_val)
            anim.setEasingCurve(QEasingCurve.Type.InBack)
            anim.valueChanged.connect(lambda val, item=target_item: item.setScale(val))
            return anim
        
        if node.summary_background:
            bg_anim = create_scale_animation(node.summary_background, 1.0, 0.0, 200)
            anim_group.addAnimation(bg_anim)
        
        text_anim = create_scale_animation(node.summary_box, 1.0, 0.0, 200)
        anim_group.addAnimation(text_anim)
        
        # 动画结束后移除
        anim_group.finished.connect(lambda: self._remove_summary_items(node))
        anim_group.start()
    
    def _remove_summary_items(self, node):
        """移除摘要相关项"""
        if node.summary_background:
            node.summary_background.setParentItem(None)
            node.summary_background = None
        if node.summary_box:
            node.summary_box.setParentItem(None)
            node.summary_box = None
        node.summary_visible = False
        node.update()
    
    def _show_filter_menu(self):
        """显示筛选菜单"""
        import sqlite3
        categories = []
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT category FROM items WHERE folder_id = ? AND category IS NOT NULL AND category != ''",
                               (self.folder_id,))
                categories = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"[ERROR] 获取分类列表失败: {e}")
        
        menu = QMenu(self)
        all_action = QAction(self.tr("all"), self)
        all_action.triggered.connect(lambda: self._filter_by_category(None))
        menu.addAction(all_action)
        menu.addSeparator()
        for cat in categories:
            action = QAction(cat, self)
            action.triggered.connect(lambda checked, c=cat: self._filter_by_category(c))
            menu.addAction(action)
        menu.exec(self.filter_btn.mapToGlobal(self.filter_btn.rect().bottomLeft()))
    
    def _filter_by_category(self, category):
        """按类别筛选"""
        for node in self.nodes:
            if isinstance(node, ItemNode):
                if category is None:
                    node.setVisible(True)
                else:
                    node.setVisible(node.data.get('category') == category)
    
    def _filter_items(self, text):
        """按搜索文本筛选"""
        text = text.strip().lower()
        for node in self.nodes:
            if isinstance(node, ItemNode):
                if not text:
                    node.setVisible(True)
                else:
                    title = node.data.get('title', '').lower()
                    node.setVisible(text in title)
    
    def toggle_edit_mode(self):
        """切换编辑模式"""
        self.edit_mode = not self.edit_mode
        self.view.edit_mode = self.edit_mode
        
        # 不使用 ItemIsMovable（我们使用自定义拖拽）
        # 但设置 ItemIsSelectable 以便选中
        for node in self.nodes:
            if isinstance(node, ItemNode):
                node.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, self.edit_mode)
                node.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsMovable, False)
        
        # 设置视图属性防止滚动
        if self.edit_mode:
            from PyQt6.QtWidgets import QApplication
            QApplication.instance().setOverrideCursor(QCursor(Qt.CursorShape.CrossCursor))
            # 禁用所有滚动和自动对齐
            self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
            self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            from PyQt6.QtWidgets import QApplication
            QApplication.instance().restoreOverrideCursor()
            # 恢复默认滚动设置
            self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
            self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
            # 恢复默认的拖动模式（用于滚动视图）
            self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            # 关闭可能打开的侧边栏
            self._close_category_sidebar()
            self._close_password_sidebar()
        
        # 更新中心节点的点击行为
        for node in self.nodes:
            if isinstance(node, CenterNode):
                if self.edit_mode:
                    try:
                        node.node_clicked.disconnect()
                    except TypeError:
                        pass
                    node.node_clicked.connect(self._show_category_sidebar)
                else:
                    try:
                        node.node_clicked.disconnect()
                    except TypeError:
                        pass
    
    def edit_item(self, node):
        """编辑收藏项"""
        if node and node.data:
            self.edit_item_requested.emit(node.data)
    
    def delete_item(self, node):
        """删除收藏项"""
        if not node or not node.data:
            return
        item_id = node.data.get('id')
        if item_id is None:
            return
        reply = QMessageBox.question(
            self, self.tr("confirm_delete"),
            self.tr("delete_item_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_item(item_id)
            self._rebuild_mindmap()
    
    def _show_password_sidebar(self, mode, item_data, callback=None):
        """显示密码侧边栏 - 与 main_window.py 保持一致"""
        if not item_data:
            return
        
        item_id = item_data.get('id')
        title = item_data.get('title', '未命名')
        
        self._close_password_sidebar()
        
        # 保存回调函数（用于 input 模式）
        self._pwd_callback = callback
        
        # 遮罩 - 使用 CloseOverlay 确保点击可关闭
        self.pwd_overlay = CloseOverlay(self._close_password_sidebar, self)
        self.pwd_overlay.setGeometry(0, 0, self.width(), self.height())
        self.pwd_overlay.setStyleSheet("background-color: rgba(0,0,0,0.3);")
        self.pwd_overlay.show()
        self.pwd_overlay.raise_()
        
        # 侧边栏
        sidebar = self._create_password_sidebar(mode, item_id, title, callback)
        sidebar.setParent(self)
        sidebar.setFixedWidth(300)
        sidebar.setGeometry(-300, 0, 300, self.height())
        sidebar.raise_()
        sidebar.show()
        
        self.pwd_sidebar = sidebar
        
        # 动画滑入
        anim = QPropertyAnimation(sidebar, b"geometry")
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.setStartValue(sidebar.geometry())
        anim.setEndValue(QRect(0, 0, 300, self.height()))
        anim.start()
        self._pwd_anim = anim
    
    def _close_password_sidebar(self):
        """关闭密码侧边栏"""
        if hasattr(self, '_pwd_closing') and self._pwd_closing:
            return
        
        sidebar = getattr(self, 'pwd_sidebar', None)
        if sidebar:
            self._pwd_closing = True
            anim = QPropertyAnimation(sidebar, b"geometry")
            anim.setDuration(200)
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            anim.setStartValue(sidebar.geometry())
            anim.setEndValue(QRect(-300, 0, 300, self.height()))
            anim.finished.connect(self._cleanup_password_sidebar)
            anim.start()
            self._pwd_anim = anim
            self.pwd_sidebar = None
        else:
            self._cleanup_password_sidebar()
    
    def _cleanup_password_sidebar(self):
        """清理密码侧边栏"""
        sidebar = getattr(self, 'pwd_sidebar', None)
        if sidebar:
            sidebar.close()
            sidebar.deleteLater()
            self.pwd_sidebar = None
        
        overlay = getattr(self, 'pwd_overlay', None)
        if overlay:
            overlay.close()
            overlay.deleteLater()
            self.pwd_overlay = None
        
        self._pwd_closing = False
        self._pwd_callback = None
    
    def _create_password_sidebar(self, mode, item_id, title, callback=None):
        """创建密码侧边栏 - 完全匹配 main_window.py 的样式和逻辑"""
        sidebar = QWidget()
        sidebar.setStyleSheet("background-color: #f5f5f5; border-right: 1px solid #ccc;")
        sidebar.setFixedWidth(300)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 返回按钮
        back_btn = QPushButton(self.tr("back"))
        back_btn.clicked.connect(self._close_password_sidebar)
        layout.addWidget(back_btn)
        
        # 标题
        if mode == 'set':
            title_text = self.tr("set_password")
        elif mode == 'change':
            title_text = self.tr("change_password")
        elif mode == 'remove':
            title_text = self.tr("remove_password")
        elif mode == 'input':
            title_text = self.tr("input_password")
        else:
            title_text = self.tr("password")
        
        title_label = QLabel(title_text)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 错误提示
        self.pwd_error_label = QLabel()
        self.pwd_error_label.setStyleSheet("color: red;")
        self.pwd_error_label.setVisible(False)
        layout.addWidget(self.pwd_error_label)
        
        # 根据模式添加输入框 - 与 main_window.py 完全一致
        self.pwd_inputs = []
        if mode == 'set':
            layout.addWidget(QLabel(self.tr("new_password") + ":"))
            pwd1 = QLineEdit()
            pwd1.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(pwd1)
            layout.addWidget(QLabel(self.tr("confirm_new_password") + ":"))
            pwd2 = QLineEdit()
            pwd2.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(pwd2)
            self.pwd_inputs = [pwd1, pwd2]
        elif mode == 'change':
            layout.addWidget(QLabel(self.tr("old_password") + ":"))
            old_pwd = QLineEdit()
            old_pwd.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(old_pwd)
            layout.addWidget(QLabel(self.tr("new_password") + ":"))
            new_pwd1 = QLineEdit()
            new_pwd1.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(new_pwd1)
            layout.addWidget(QLabel(self.tr("confirm_new_password") + ":"))
            new_pwd2 = QLineEdit()
            new_pwd2.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(new_pwd2)
            self.pwd_inputs = [old_pwd, new_pwd1, new_pwd2]
        elif mode == 'remove':
            layout.addWidget(QLabel(self.tr("enter_old_password") + ":"))
            pwd = QLineEdit()
            pwd.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(pwd)
            self.pwd_inputs = [pwd]
        elif mode == 'input':
            layout.addWidget(QLabel(self.tr("enter_password") + ":"))
            pwd = QLineEdit()
            pwd.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(pwd)
            self.pwd_inputs = [pwd]
        
        layout.addStretch()
        
        # 确认按钮
        confirm_btn = QPushButton(self.tr("confirm"))
        confirm_btn.setObjectName("confirm_btn")
        confirm_btn.clicked.connect(lambda: self._confirm_password_action(mode, item_id, callback))
        layout.addWidget(confirm_btn)
        
        return sidebar
    
    def _confirm_password_action(self, mode, item_id, callback=None):
        """确认密码操作 - 完全匹配 main_window.py 的逻辑"""
        try:
            inputs = [edit.text().strip() for edit in self.pwd_inputs]
            
            if mode == 'set':
                if len(inputs) != 2:
                    return
                if not inputs[0] or not inputs[1]:
                    self._show_pwd_error(self.tr("password_cannot_be_empty"))
                    return
                if inputs[0] != inputs[1]:
                    self._show_pwd_error(self.tr("passwords_do_not_match"))
                    return
                self.db.set_item_password(item_id, inputs[0])
                self._close_password_sidebar()
                self._rebuild_mindmap()
                self.refresh_view_requested.emit()  # 通知主窗口刷新
                QMessageBox.information(self, self.tr("info"), self.tr("password_success"))
            
            elif mode == 'change':
                if len(inputs) != 3:
                    return
                old, new1, new2 = inputs
                # 验证原密码
                if not self.db.verify_item_password(item_id, old):
                    self._show_pwd_error(self.tr("old_password_incorrect"))
                    return
                if not new1 or not new2:
                    self._show_pwd_error(self.tr("password_cannot_be_empty"))
                    return
                if new1 != new2:
                    self._show_pwd_error(self.tr("passwords_do_not_match"))
                    return
                self.db.set_item_password(item_id, new1)
                self._close_password_sidebar()
                self._rebuild_mindmap()
                self.refresh_view_requested.emit()  # 通知主窗口刷新
                QMessageBox.information(self, self.tr("info"), self.tr("password_change_success"))
            
            elif mode == 'remove':
                if len(inputs) != 1:
                    return
                pwd = inputs[0]
                if not self.db.verify_item_password(item_id, pwd):
                    self._show_pwd_error(self.tr("password_incorrect"))
                    return
                self.db.remove_item_password(item_id)
                self._close_password_sidebar()
                self._rebuild_mindmap()
                self.refresh_view_requested.emit()  # 通知主窗口刷新
                QMessageBox.information(self, self.tr("info"), self.tr("password_remove_success"))
            
            elif mode == 'input':
                if len(inputs) != 1:
                    return
                pwd = inputs[0]
                valid = self.db.verify_item_password(item_id, pwd)
                if valid:
                    self._close_password_sidebar()
                    if callback:
                        callback()
                else:
                    self._show_pwd_error(self.tr("password_incorrect"))
        
        except Exception as e:
            QMessageBox.warning(self, self.tr("error"), self.tr("password_operation_failed"))
    
    def _show_pwd_error(self, msg):
        """显示密码错误提示"""
        if hasattr(self, 'pwd_error_label') and self.pwd_error_label:
            self.pwd_error_label.setText(msg)
            self.pwd_error_label.setVisible(True)
    
    def _open_item_url(self, item_data):
        """打开收藏项的URL"""
        try:
            import webbrowser
            url = item_data.get('url', '')
            if url:
                webbrowser.open(url)
        except Exception as e:
            print(f"[ERROR] 打开URL失败: {e}")
    
    def _rebuild_mindmap(self):
        """重新构建思维导图"""
        self.load_data()
    
    def _check_item_drop(self, item_node):
        """检查 ItemNode 是否被拖拽到其他类别区域，返回是否成功"""
        if not item_node or not item_node.data:
            return False
        
        scene_pos = item_node.scenePos()
        item_type = item_node.data.get('item_type')
        current_category = item_node.data.get('category')
        
        # 找到最近的类别节点（level=1 的 RectNode）
        best_category_node = None
        best_distance = float('inf')
        threshold = 200  # 距离阈值
        
        for node in self.nodes:
            if isinstance(node, RectNode) and node.level == 1:
                node_category = node.text
                if node_category == current_category:
                    continue
                
                node_pos = node.scenePos()
                dx = scene_pos.x() - node_pos.x()
                dy = scene_pos.y() - node_pos.y()
                distance = math.sqrt(dx * dx + dy * dy)
                if distance < best_distance and distance < threshold:
                    best_distance = distance
                    best_category_node = node
        
        if best_category_node:
            target_category = best_category_node.text
            item_id = item_node.data.get('id')
            
            if item_id and target_category != current_category:
                # 更新数据库中的类别
                self.db.update_item_category(item_id, target_category)
                # 显示成功提示
                QMessageBox.information(self, self.tr("drag_success"), 
                    self.tr("drag_success_msg").format(target_category))
                # 延迟重建（让提示先显示）
                QTimer.singleShot(100, self._rebuild_mindmap)
                return True
        
        # 没有找到合适的目标
        return False
    
    def _show_category_sidebar(self, data=None):
        """显示分类管理侧边栏（编辑模式下点击中心节点）"""
        if not self.edit_mode:
            return
        
        self._close_category_sidebar()
        QTimer.singleShot(250, self._create_and_show_category_sidebar)
    
    def _create_and_show_category_sidebar(self):
        """创建并显示分类侧边栏"""
        # 创建遮罩 - 使用自定义类处理点击事件
        self.category_overlay = CloseOverlay(self._close_category_sidebar, self)
        self.category_overlay.setGeometry(0, 0, self.width(), self.height())
        self.category_overlay.setStyleSheet("background-color: rgba(0,0,0,0.3);")
        self.category_overlay.show()
        self.category_overlay.raise_()
        
        # 创建侧边栏
        sidebar = self._create_category_sidebar()
        sidebar.setParent(self)
        sidebar.setFixedWidth(280)
        sidebar.setGeometry(self.width(), 0, 280, self.height())
        sidebar.raise_()
        sidebar.show()
        
        self.category_sidebar = sidebar
        
        # 动画滑入
        anim = QPropertyAnimation(sidebar, b"geometry")
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        start_geom = sidebar.geometry()
        end_geom = sidebar.geometry()
        end_geom.moveLeft(self.width() - 280)
        anim.setStartValue(start_geom)
        anim.setEndValue(end_geom)
        anim.start()
        self._sidebar_anim = anim
    
    def _close_category_sidebar(self):
        """关闭分类侧边栏"""
        # 防止重复调用
        if hasattr(self, '_category_closing') and self._category_closing:
            return
        
        sidebar = getattr(self, 'category_sidebar', None)
        overlay = getattr(self, 'category_overlay', None)
        
        if sidebar:
            self._category_closing = True
            anim = QPropertyAnimation(sidebar, b"geometry")
            anim.setDuration(250)
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            anim.setStartValue(sidebar.geometry())
            anim.setEndValue(QRect(self.width(), 0, 280, self.height()))
            anim.finished.connect(self._cleanup_category_sidebar)
            anim.start()
            self._sidebar_anim = anim
            self.category_sidebar = None
        elif overlay:
            self._cleanup_category_sidebar()
    
    def _cleanup_category_sidebar(self):
        """清理分类侧边栏"""
        sidebar = getattr(self, 'category_sidebar', None)
        if sidebar:
            sidebar.close()
            sidebar.deleteLater()
            self.category_sidebar = None
        
        overlay = getattr(self, 'category_overlay', None)
        if overlay:
            overlay.close()
            overlay.deleteLater()
            self.category_overlay = None
        
        self._category_closing = False
    
    def _create_category_sidebar(self):
        """创建分类管理侧边栏"""
        sidebar = QWidget()
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-left: 1px solid #DDDDDD;
            }
            QLabel#sidebar_title {
                padding: 16px;
                font-size: 16px;
                font-weight: bold;
                color: #333;
                border-bottom: 2px solid #3498DB;
            }
            QLabel#category_label {
                padding: 10px 16px;
                font-size: 13px;
                color: #333;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #D0D0D0;
                border-radius: 4px;
                background-color: #F8F9FA;
                font-size: 12px;
                color: #333;
            }
            QPushButton:hover {
                background-color: #E8F4FD;
                border-color: #3498DB;
            }
            QPushButton#add_cat_btn {
                background-color: #3498DB;
                color: white;
                border: none;
                font-weight: bold;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton#add_cat_btn:hover {
                background-color: #2980B9;
            }
            QPushButton#del_cat_btn {
                color: #E74C3C;
                border-color: #E74C3C;
            }
            QPushButton#del_cat_btn:hover {
                background-color: #FDEDEC;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标题
        title = QLabel(self.tr("category_management"))
        title.setObjectName("sidebar_title")
        layout.addWidget(title)
        
        # 分类列表
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 获取所有分类
        import sqlite3
        categories = []
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT DISTINCT category FROM items WHERE folder_id = ? AND category IS NOT NULL AND category != '' ORDER BY category",
                    (self.folder_id,))
                categories = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"[ERROR] 获取分类失败: {e}")
        
        if not categories:
            no_cat = QLabel(self.tr("no_categories"))
            no_cat.setObjectName("category_label")
            no_cat.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_cat.setStyleSheet("padding: 40px; color: #999;")
            content_layout.addWidget(no_cat)
        else:
            for cat in categories:
                cat_row = QHBoxLayout()
                cat_row.setContentsMargins(16, 4, 16, 4)
                
                cat_label = QLabel(cat)
                cat_label.setObjectName("category_label")
                cat_row.addWidget(cat_label)
                
                cat_row.addStretch()
                
                # 重命名按钮
                rename_btn = QPushButton(self.tr("rename_category"))
                rename_btn.setFixedSize(60, 26)
                rename_btn.clicked.connect(lambda checked, c=cat: self._rename_category(c))
                cat_row.addWidget(rename_btn)
                
                # 删除按钮
                del_btn = QPushButton(self.tr("delete_category"))
                del_btn.setObjectName("del_cat_btn")
                del_btn.setFixedSize(50, 26)
                del_btn.clicked.connect(lambda checked, c=cat: self._delete_category(c))
                cat_row.addWidget(del_btn)
                
                content_layout.addLayout(cat_row)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # 添加分类按钮
        add_btn = QPushButton(self.tr("add_category"))
        add_btn.setObjectName("add_cat_btn")
        add_btn.clicked.connect(self._add_category)
        layout.addWidget(add_btn)
        
        return sidebar
    
    def _rename_category(self, old_name):
        """重命名分类"""
        new_name, ok = QInputDialog.getText(self, self.tr("rename_category_dialog_title"), self.tr("rename_category_dialog_label"),
                                             QLineEdit.EchoMode.Normal, old_name)
        if ok and new_name and new_name != old_name:
            import sqlite3
            try:
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE items SET category = ? WHERE folder_id = ? AND category = ?",
                        (new_name, self.folder_id, old_name))
                    conn.commit()
                self._close_category_sidebar()
                self._rebuild_mindmap()
            except Exception as e:
                QMessageBox.warning(self, self.tr("error_title"), f"{self.tr('rename_failed')}: {e}")
    
    def _delete_category(self, category_name):
        """删除分类（将分类下的项目设为未分类）"""
        reply = QMessageBox.question(
            self, self.tr("confirm_delete"),
            self.tr("delete_category_confirm").format(category_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            import sqlite3
            try:
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE items SET category = 'uncategorized' WHERE folder_id = ? AND category = ?",
                        (self.folder_id, category_name))
                    conn.commit()
                # 先关闭侧边栏，再延迟重建（等动画完成）
                self._close_category_sidebar()
                QTimer.singleShot(300, self._rebuild_mindmap)
            except Exception as e:
                QMessageBox.warning(self, self.tr("error_title"), f"{self.tr('delete_failed')}: {e}")
    
    def _add_category(self):
        """添加新分类 - 通过创建一个占位项目来实现"""
        name, ok = QInputDialog.getText(self, self.tr("new_category_dialog_title"), self.tr("new_category_dialog_label"))
        if ok and name:
            import sqlite3
            try:
                # 检查分类是否已存在
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT COUNT(*) FROM items WHERE folder_id = ? AND category = ?",
                        (self.folder_id, name))
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        QMessageBox.warning(self, self.tr("error_title"), self.tr("category_exists").format(name))
                        return
                
                # 创建一个占位项目来代表该分类
                placeholder_title = f"[Category] {name}"
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """INSERT INTO items (folder_id, title, url, category, item_type, summary) 
                           VALUES (?, ?, '', ?, 'link', '')""",
                        (self.folder_id, placeholder_title, name))
                    conn.commit()
                
                # 先关闭侧边栏，再延迟重建（等动画完成）
                self._close_category_sidebar()
                QTimer.singleShot(300, self._rebuild_mindmap)
            except Exception as e:
                QMessageBox.warning(self, self.tr("error_title"), f"{self.tr('add_failed')}: {e}")
    
    def closeEvent(self, event):
        """关闭事件 - 清理资源"""
        # 停止飘动定时器
        if hasattr(self, '_float_timer') and self._float_timer:
            self._float_timer.stop()
            self._float_timer = None
        
        # 关闭所有侧边栏
        self._close_password_sidebar()
        self._close_category_sidebar()
        
        # 清空场景
        self.scene.clear()
        
        event.accept()
