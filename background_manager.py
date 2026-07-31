import os
import json
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt, QRect

class BackgroundManager:
    """
    背景管理器 - 管理应用背景的渲染和设置
    
    支持：
    1. 大背景设置（主题色蒙层、背景图片、透明度、模糊度）
    2. 卡片区域背景设置（独立的背景色、背景图片、透明度、模糊度）
    """
    
    # 背景图片策略
    BACKGROUND_STRATEGIES = {
        "stretch": "拉伸",
        "tile": "平铺",
        "center": "居中",
        "fill": "填充",
        "fit": "适应"
    }
    
    def __init__(self):
        # 大背景设置
        self._main_theme_opacity = 0.6  # 大背景主题色透明度（0-1），默认60%
        self._main_bg_image_path = ""    # 大背景图片路径
        self._main_bg_image_opacity = 0.5  # 大背景图片透明度（0-1）
        self._main_bg_strategy = "stretch"  # 大背景策略
        self._main_bg_blur_radius = 0    # 大背景模糊度（已移除，保留兼容性）
        
        # 卡片区域背景设置
        self._card_bg_enabled = True     # 是否启用卡片背景
        self._card_theme_opacity = 0.4   # 卡片区域主题色透明度（0-1），默认40%
        self._card_bg_image_path = ""    # 卡片区域背景图片路径
        self._card_bg_image_opacity = 0.5  # 卡片区域背景图片透明度（0-1）
        self._card_bg_strategy = "stretch"  # 卡片区域背景策略
        
        # 缓存的背景图片
        self._main_bg_pixmap = None
        self._card_bg_pixmap = None
        
    def load_config(self, config):
        """从配置文件加载背景设置"""
        if config is None:
            return
        
        # 大背景设置
        self._main_theme_opacity = config.get("main_theme_opacity", 0.6)
        self._main_bg_image_path = config.get("main_bg_image_path", "")
        self._main_bg_image_opacity = config.get("main_bg_image_opacity", 0.5)
        self._main_bg_strategy = config.get("main_bg_strategy", "stretch")
        
        # 卡片区域背景设置
        self._card_bg_enabled = config.get("card_bg_enabled", True)
        self._card_theme_opacity = config.get("card_theme_opacity", 0.4)
        self._card_bg_image_path = config.get("card_bg_image_path", "")
        self._card_bg_image_opacity = config.get("card_bg_image_opacity", 0.5)
        self._card_bg_strategy = config.get("card_bg_strategy", "stretch")
        
        # 加载背景图片
        if self._main_bg_image_path and os.path.exists(self._main_bg_image_path):
            self._main_bg_pixmap = QPixmap(self._main_bg_image_path)
        if self._card_bg_image_path and os.path.exists(self._card_bg_image_path):
            self._card_bg_pixmap = QPixmap(self._card_bg_image_path)
    
    def save_config(self):
        """保存背景设置到字典"""
        return {
            # 大背景设置
            "main_theme_opacity": self._main_theme_opacity,
            "main_bg_image_path": self._main_bg_image_path,
            "main_bg_image_opacity": self._main_bg_image_opacity,
            "main_bg_strategy": self._main_bg_strategy,
            # 卡片区域背景设置
            "card_bg_enabled": self._card_bg_enabled,
            "card_theme_opacity": self._card_theme_opacity,
            "card_bg_image_path": self._card_bg_image_path,
            "card_bg_image_opacity": self._card_bg_image_opacity,
            "card_bg_strategy": self._card_bg_strategy
        }
    
    # ---------- 大背景属性访问器 ----------
    @property
    def main_theme_opacity(self):
        return self._main_theme_opacity
    
    @main_theme_opacity.setter
    def main_theme_opacity(self, value):
        self._main_theme_opacity = max(0.0, min(1.0, value))
    
    @property
    def main_bg_image_path(self):
        return self._main_bg_image_path
    
    @main_bg_image_path.setter
    def main_bg_image_path(self, path):
        self._main_bg_image_path = path
        if path and os.path.exists(path):
            self._main_bg_pixmap = QPixmap(path)
        else:
            self._main_bg_pixmap = None
    
    @property
    def main_bg_image_opacity(self):
        return self._main_bg_image_opacity
    
    @main_bg_image_opacity.setter
    def main_bg_image_opacity(self, value):
        self._main_bg_image_opacity = max(0.0, min(1.0, value))
    
    @property
    def main_bg_strategy(self):
        return self._main_bg_strategy
    
    @main_bg_strategy.setter
    def main_bg_strategy(self, value):
        if value in self.BACKGROUND_STRATEGIES:
            self._main_bg_strategy = value
    
    # ---------- 卡片区域背景属性访问器 ----------
    @property
    def card_bg_enabled(self):
        return self._card_bg_enabled
    
    @card_bg_enabled.setter
    def card_bg_enabled(self, value):
        self._card_bg_enabled = bool(value)
    
    @property
    def card_theme_opacity(self):
        return self._card_theme_opacity
    
    @card_theme_opacity.setter
    def card_theme_opacity(self, value):
        self._card_theme_opacity = max(0.0, min(1.0, value))
    
    @property
    def card_bg_image_path(self):
        return self._card_bg_image_path
    
    @card_bg_image_path.setter
    def card_bg_image_path(self, path):
        self._card_bg_image_path = path
        if path and os.path.exists(path):
            self._card_bg_pixmap = QPixmap(path)
        else:
            self._card_bg_pixmap = None
    
    @property
    def card_bg_image_opacity(self):
        return self._card_bg_image_opacity
    
    @card_bg_image_opacity.setter
    def card_bg_image_opacity(self, value):
        self._card_bg_image_opacity = max(0.0, min(1.0, value))
    
    @property
    def card_bg_strategy(self):
        return self._card_bg_strategy
    
    @card_bg_strategy.setter
    def card_bg_strategy(self, value):
        if value in self.BACKGROUND_STRATEGIES:
            self._card_bg_strategy = value
    
    # ---------- 渲染方法 ----------
    def render_main_background(self, painter, rect, theme_color, dark_mode):
        """
        渲染大背景
        
        Args:
            painter: QPainter对象
            rect: 绘制区域
            theme_color: 主题色QColor对象
            dark_mode: 是否深色模式
        """
        # 1. 绘制基础背景（深色/浅色）
        if dark_mode:
            base_color = QColor(30, 30, 30)
        else:
            base_color = QColor(245, 245, 245)
        
        painter.fillRect(rect, base_color)
        
        # 2. 绘制背景图片（如果有）
        has_image = self._main_bg_pixmap and not self._main_bg_pixmap.isNull()
        if has_image:
            self._draw_background_image(painter, rect, self._main_bg_pixmap, 
                                       self._main_bg_image_opacity, self._main_bg_strategy)
        
        # 3. 绘制主题色蒙层（有背景图片时不覆盖）
        if self._main_theme_opacity > 0 and not has_image:
            overlay_color = QColor(theme_color)
            overlay_color.setAlpha(int(self._main_theme_opacity * 255))
            painter.fillRect(rect, overlay_color)
    
    def render_card_background(self, painter, rect, theme_color, dark_mode):
        """
        渲染卡片区域背景
        
        Args:
            painter: QPainter对象
            rect: 绘制区域
            theme_color: 主题色QColor对象
            dark_mode: 是否深色模式
        """
        # 卡片背景总是启用
        
        # 1. 绘制基础背景（深色/浅色）
        if dark_mode:
            base_color = QColor(40, 40, 40)
        else:
            base_color = QColor(255, 255, 255)
        
        painter.fillRect(rect, base_color)
        
        # 2. 绘制背景图片（如果有）
        has_image = self._card_bg_pixmap and not self._card_bg_pixmap.isNull()
        if has_image:
            self._draw_background_image(painter, rect, self._card_bg_pixmap,
                                       self._card_bg_image_opacity, self._card_bg_strategy)
        
        # 3. 绘制主题色蒙层（有背景图片时不覆盖）
        if self._card_theme_opacity > 0 and not has_image:
            overlay_color = QColor(theme_color)
            overlay_color.setAlpha(int(self._card_theme_opacity * 255))
            painter.fillRect(rect, overlay_color)
    
    def _draw_background_image(self, painter, rect, pixmap, opacity, strategy):
        """根据策略绘制背景图片"""
        if pixmap.isNull():
            return
            
        # 先根据策略获取要绘制的图片
        if strategy == "stretch":
            scaled_pixmap = pixmap.scaled(
                rect.size(), Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            draw_rect = rect
            draw_pixmap = scaled_pixmap
            
        elif strategy == "tile":
            draw_rect = rect
            draw_pixmap = pixmap
            
        elif strategy == "center":
            draw_rect = QRect(
                (rect.width() - pixmap.width()) // 2,
                (rect.height() - pixmap.height()) // 2,
                pixmap.width(),
                pixmap.height()
            )
            draw_pixmap = pixmap
            
        elif strategy == "fill":
            scaled_pixmap = pixmap.scaled(
                rect.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (scaled_pixmap.width() - rect.width()) // 2
            y = (scaled_pixmap.height() - rect.height()) // 2
            draw_rect = QRect(x, y, rect.width(), rect.height())
            draw_pixmap = scaled_pixmap
            
        elif strategy == "fit":
            scaled_pixmap = pixmap.scaled(
                rect.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            draw_rect = QRect(
                (rect.width() - scaled_pixmap.width()) // 2,
                (rect.height() - scaled_pixmap.height()) // 2,
                scaled_pixmap.width(),
                scaled_pixmap.height()
            )
            draw_pixmap = scaled_pixmap
            
        else:
            draw_rect = rect
            draw_pixmap = pixmap
        
        # 绘制最终图片
        painter.setOpacity(opacity)
        
        if strategy == "tile":
            # 平铺绘制
            pixmap_size = draw_pixmap.size()
            x = 0
            while x < rect.width():
                y = 0
                while y < rect.height():
                    painter.drawPixmap(x, y, pixmap_size.width(), pixmap_size.height(), draw_pixmap)
                    y += pixmap_size.height()
                x += pixmap_size.width()
        else:
            painter.drawPixmap(draw_rect, draw_pixmap)
        
        painter.setOpacity(1.0)

# 创建全局背景管理器实例
background_manager = BackgroundManager()