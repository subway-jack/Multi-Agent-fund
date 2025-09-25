# -*- coding: utf-8 -*-
import json
import os
from typing import Dict, Any
from .defaults import (
    MARKET_CONFIG, TRADER_CONFIG, TECHNICAL_CONFIG, 
    TRADING_CONFIG, UI_CONFIG, USER_CONFIG, BINANCE_CONFIG
)

class ConfigManager:
    """配置管理器 - 负责配置的读取、保存和同步"""
    
    def __init__(self, config_file: str = None):
        if config_file is None:
            # 默认配置文件路径
            config_file = os.path.join(os.path.dirname(__file__), "user_config.json")
        self.config_file = config_file
        self.config = {
            'market': MARKET_CONFIG.copy(),
            'trader': TRADER_CONFIG.copy(),
            'technical': TECHNICAL_CONFIG.copy(),
            'trading': TRADING_CONFIG.copy(),
            'ui': UI_CONFIG.copy(),
            'user': USER_CONFIG.copy(),
            'binance': BINANCE_CONFIG.copy()
        }
        self.load_config()
    
    def load_config(self):
        """从文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并用户配置和默认配置
                    self._merge_config(self.config, user_config)
                print(f"✅ 已加载用户配置: {self.config_file}")
            except Exception as e:
                print(f"⚠️ 加载配置文件失败: {e}，使用默认配置")
        else:
            print("📝 使用默认配置")
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            print(f"✅ 配置已保存: {self.config_file}")
            return True
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
            return False
    
    def _merge_config(self, default_config: Dict, user_config: Dict):
        """递归合并配置"""
        for key, value in user_config.items():
            if key in default_config:
                if isinstance(value, dict) and isinstance(default_config[key], dict):
                    self._merge_config(default_config[key], value)
                else:
                    default_config[key] = value
    
    def get_config(self, category: str = None) -> Dict[str, Any]:
        """获取配置
        
        Args:
            category: 配置类别 ('market', 'trader', 'technical', 'trading', 'ui')
                     如果为None，返回所有配置
        """
        if category is None:
            return self.config
        return self.config.get(category, {})
    
    def update_config(self, category: str, key: str, value: Any) -> bool:
        """更新配置项
        
        Args:
            category: 配置类别
            key: 配置键
            value: 新值
        """
        if category in self.config and key in self.config[category]:
            self.config[category][key] = value
            return True
        return False
    
    def update_config_batch(self, updates: Dict[str, Dict[str, Any]]) -> bool:
        """批量更新配置
        
        Args:
            updates: 格式为 {category: {key: value, ...}, ...}
        """
        try:
            for category, config_updates in updates.items():
                if category in self.config:
                    for key, value in config_updates.items():
                        if key in self.config[category]:
                            self.config[category][key] = value
            return True
        except Exception as e:
            print(f"❌ 批量更新配置失败: {e}")
            return False
    
    def reset_to_defaults(self, category: str = None):
        """重置配置为默认值
        
        Args:
            category: 要重置的类别，如果为None则重置所有
        """
        defaults = {
            'market': MARKET_CONFIG.copy(),
            'trader': TRADER_CONFIG.copy(),
            'technical': TECHNICAL_CONFIG.copy(),
            'trading': TRADING_CONFIG.copy(),
            'ui': UI_CONFIG.copy()
        }
        
        if category is None:
            self.config = defaults
        elif category in defaults:
            self.config[category] = defaults[category]
    
    def get_market_config(self) -> Dict[str, Any]:
        """获取市场配置"""
        return self.config['market']
    
    def get_trader_config(self) -> Dict[str, Any]:
        """获取交易员配置"""
        return self.config['trader']
    
    def get_technical_config(self) -> Dict[str, Any]:
        """获取技术指标配置"""
        return self.config['technical']
    
    def get_trading_config(self) -> Dict[str, Any]:
        """获取交易系统配置"""
        return self.config['trading']
    
    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI配置"""
        return self.config['ui']
    
    def validate_config(self) -> Dict[str, list]:
        """验证配置的有效性
        
        Returns:
            包含验证错误的字典
        """
        errors = {
            'market': [],
            'trader': [],
            'technical': [],
            'trading': [],
            'ui': []
        }
        
        # 验证市场配置
        market = self.config['market']
        if market['base_volatility'] < 0 or market['base_volatility'] > 1:
            errors['market'].append('基础波动率必须在0-1之间')
        if market['trend'] < -1 or market['trend'] > 1:
            errors['market'].append('市场趋势必须在-1到1之间')
        
        # 验证交易员配置
        trader = self.config['trader']
        if trader['num_bulls'] < 0 or trader['num_bears'] < 0:
            errors['trader'].append('交易员数量不能为负数')
        if trader['initial_balance'] <= 0:
            errors['trader'].append('初始资金必须大于0')
        
        # 验证技术指标配置
        technical = self.config['technical']
        if technical['rsi_period'] < 1:
            errors['technical'].append('RSI周期必须大于0')
        if technical['sma_short_period'] >= technical['sma_long_period']:
            errors['technical'].append('短期移动平均周期必须小于长期周期')
        
        # 验证交易系统配置
        trading = self.config['trading']
        if trading['commission_rate'] < 0 or trading['commission_rate'] > 1:
            errors['trading'].append('手续费率必须在0-1之间')
        if trading['min_order_size'] <= 0:
            errors['trading'].append('最小订单数量必须大于0')
        
        # 验证UI配置
        ui = self.config['ui']
        if ui['refresh_interval'] <= 0:
            errors['ui'].append('刷新间隔必须大于0')
        
        return errors

# 全局配置管理器实例
config_manager = ConfigManager()