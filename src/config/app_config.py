"""
应用配置管理模块
"""
import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class ServerConfig:
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    log_level: str = "info"

@dataclass
class BinanceConfig:
    """币安配置"""
    base_ws_url: str = "wss://stream.binance.com:9443/ws/"
    reconnect_delay: int = 5
    max_retries: int = 5
    heartbeat_interval: int = 30

@dataclass
class UIConfig:
    """UI配置"""
    window_width: int = 1400
    window_height: int = 800
    chart_max_points: int = 1000
    update_interval: int = 100
    default_symbols: list = None
    
    def __post_init__(self):
        if self.default_symbols is None:
            self.default_symbols = [
                "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT",
                "SOLUSDT", "DOTUSDT", "DOGEUSDT", "AVAXUSDT", "SHIBUSDT"
            ]

@dataclass
class AppConfig:
    """应用程序配置"""
    server: ServerConfig = None
    binance: BinanceConfig = None
    ui: UIConfig = None
    
    def __post_init__(self):
        if self.server is None:
            self.server = ServerConfig()
        if self.binance is None:
            self.binance = BinanceConfig()
        if self.ui is None:
            self.ui = UIConfig()

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_path()
        self.config = AppConfig()
        self.load_config()
        
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 获取项目根目录
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent
        config_dir = project_root / "config"
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / "app_config.json")
        
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config = self._dict_to_config(data)
            else:
                # 如果配置文件不存在，创建默认配置
                self.save_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = AppConfig()  # 使用默认配置
            
    def save_config(self):
        """保存配置"""
        try:
            config_dict = self._config_to_dict(self.config)
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
            
    def _dict_to_config(self, data: Dict[str, Any]) -> AppConfig:
        """字典转配置对象"""
        server_data = data.get('server', {})
        binance_data = data.get('binance', {})
        ui_data = data.get('ui', {})
        
        return AppConfig(
            server=ServerConfig(**server_data),
            binance=BinanceConfig(**binance_data),
            ui=UIConfig(**ui_data)
        )
        
    def _config_to_dict(self, config: AppConfig) -> Dict[str, Any]:
        """配置对象转字典"""
        return {
            'server': asdict(config.server),
            'binance': asdict(config.binance),
            'ui': asdict(config.ui)
        }
        
    def get_server_config(self) -> ServerConfig:
        """获取服务器配置"""
        return self.config.server
        
    def get_binance_config(self) -> BinanceConfig:
        """获取币安配置"""
        return self.config.binance
        
    def get_ui_config(self) -> UIConfig:
        """获取UI配置"""
        return self.config.ui
        
    def update_server_config(self, **kwargs):
        """更新服务器配置"""
        for key, value in kwargs.items():
            if hasattr(self.config.server, key):
                setattr(self.config.server, key, value)
        self.save_config()
        
    def update_binance_config(self, **kwargs):
        """更新币安配置"""
        for key, value in kwargs.items():
            if hasattr(self.config.binance, key):
                setattr(self.config.binance, key, value)
        self.save_config()
        
    def update_ui_config(self, **kwargs):
        """更新UI配置"""
        for key, value in kwargs.items():
            if hasattr(self.config.ui, key):
                setattr(self.config.ui, key, value)
        self.save_config()

# 全局配置管理器实例
config_manager = ConfigManager()