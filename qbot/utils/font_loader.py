# -*- coding: utf-8 -*-
import pygame
import os
from typing import Dict, Optional
from src.config import settings as S

class FontManager:
    """统一的字体管理器类"""
    
    def __init__(self):
        self._fonts = {}
        self._font_paths = [
            '/System/Library/Fonts/PingFang.ttc',  # macOS
            '/System/Library/Fonts/Hiragino Sans GB.ttc',  # macOS
            'C:/Windows/Fonts/msyh.ttc',  # Windows
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',  # Linux
        ]
        self._system_fonts = S.EXTRA_FONT_CANDIDATES
        self._initialized = False
    
    def initialize(self):
        """初始化字体管理器"""
        if self._initialized:
            return
        
        pygame.font.init()
        self._load_fonts()
        self._initialized = True
    
    def _load_fonts(self):
        """加载字体"""
        # 尝试加载文件字体
        font_loaded = False
        for font_path in self._font_paths:
            if os.path.exists(font_path):
                try:
                    self._fonts = {
                        'small': pygame.font.Font(font_path, S.FONT_SIZE_SMALL),
                        'normal': pygame.font.Font(font_path, S.FONT_SIZE_BIG),
                        'title': pygame.font.Font(font_path, 36),
                        'large': pygame.font.Font(font_path, 48)
                    }
                    font_loaded = True
                    print(f"✅ 成功加载字体文件: {font_path}")
                    break
                except Exception as e:
                    print(f"⚠️ 字体文件加载失败 {font_path}: {e}")
                    continue
        
        # 如果文件字体加载失败，尝试系统字体
        if not font_loaded:
            for font_name in self._system_fonts:
                try:
                    self._fonts = {
                        'small': pygame.font.SysFont(font_name, S.FONT_SIZE_SMALL),
                        'normal': pygame.font.SysFont(font_name, S.FONT_SIZE_BIG),
                        'title': pygame.font.SysFont(font_name, 36),
                        'large': pygame.font.SysFont(font_name, 48)
                    }
                    font_loaded = True
                    print(f"✅ 成功加载系统字体: {font_name}")
                    break
                except Exception as e:
                    print(f"⚠️ 系统字体加载失败 {font_name}: {e}")
                    continue
        
        # 最后使用默认字体
        if not font_loaded:
            self._fonts = {
                'small': pygame.font.Font(None, S.FONT_SIZE_SMALL),
                'normal': pygame.font.Font(None, S.FONT_SIZE_BIG),
                'title': pygame.font.Font(None, 36),
                'large': pygame.font.Font(None, 48)
            }
            print("⚠️ 使用默认字体，中文显示可能不正常")
    
    def get_font(self, size: str = 'normal') -> pygame.font.Font:
        """获取指定大小的字体
        
        Args:
            size: 字体大小 ('small', 'normal', 'title', 'large')
            
        Returns:
            pygame.font.Font: 字体对象
        """
        if not self._initialized:
            self.initialize()
        
        return self._fonts.get(size, self._fonts['normal'])
    
    def get_custom_font(self, size: int) -> pygame.font.Font:
        """获取自定义大小的字体
        
        Args:
            size: 字体大小
            
        Returns:
            pygame.font.Font: 字体对象
        """
        if not self._initialized:
            self.initialize()
        
        # 尝试使用已加载的字体路径创建自定义大小字体
        for font_path in self._font_paths:
            if os.path.exists(font_path):
                try:
                    return pygame.font.Font(font_path, size)
                except:
                    continue
        
        # 尝试系统字体
        for font_name in self._system_fonts:
            try:
                return pygame.font.SysFont(font_name, size)
            except:
                continue
        
        # 默认字体
        return pygame.font.Font(None, size)
    
    def render_text(self, text: str, size: str = 'normal', color=(0, 0, 0), antialias=True) -> pygame.Surface:
        """渲染文本
        
        Args:
            text: 要渲染的文本
            size: 字体大小
            color: 文本颜色
            antialias: 是否抗锯齿
            
        Returns:
            pygame.Surface: 渲染后的文本表面
        """
        font = self.get_font(size)
        return font.render(text, antialias, color)

# 全局字体管理器实例
font_manager = FontManager()

# 向后兼容的函数
def load_fonts():
    """向后兼容的字体加载函数"""
    font_manager.initialize()
    return {
        'small': font_manager.get_font('small'),
        'normal': font_manager.get_font('normal'),
        'title': font_manager.get_font('title')
    }