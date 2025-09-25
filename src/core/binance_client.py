# -*- coding: utf-8 -*-
"""
币安API客户端 - 用于获取真实的虚拟货币价格数据
"""

import os
import time
import logging
from typing import Dict, List, Optional, Tuple
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from src.config.config_manager import config_manager

logger = logging.getLogger(__name__)

class BinanceClient:
    """币安API客户端类"""
    
    def __init__(self):
        """初始化币安客户端"""
        self.client = None
        self.config = config_manager.get_config().get('binance', {})
        self.symbols = self.config.get('symbols', [])
        self.price_cache = {}  # 价格缓存
        self.last_update_time = {}  # 最后更新时间
        self.update_interval = self.config.get('price_update_interval', 5)
        self.enabled = self.config.get('enable_real_data', False)
        self.fallback_to_mock = self.config.get('fallback_to_mock', True)
        
        # 初始化客户端
        self._initialize_client()
        
    def _initialize_client(self):
        """初始化币安客户端连接"""
        try:
            # 从环境变量获取API密钥
            api_key = os.getenv('BINANCE_API_KEY', self.config.get('api_key', ''))
            api_secret = os.getenv('BINANCE_API_SECRET', self.config.get('api_secret', ''))
            
            if not api_key or not api_secret:
                logger.warning("币安API密钥未配置，将使用模拟数据")
                self.enabled = False
                return
            
            # 创建客户端
            testnet = self.config.get('testnet', True)
            if testnet:
                self.client = Client(api_key, api_secret, testnet=True)
                logger.info("已连接到币安测试网络")
            else:
                self.client = Client(api_key, api_secret)
                logger.info("已连接到币安主网")
                
            # 测试连接
            self._test_connection()
            
        except Exception as e:
            logger.error(f"初始化币安客户端失败: {e}")
            self.enabled = False
            if not self.fallback_to_mock:
                raise
    
    def _test_connection(self):
        """测试API连接"""
        try:
            if self.client:
                # 获取服务器时间来测试连接
                server_time = self.client.get_server_time()
                logger.info(f"币安API连接成功，服务器时间: {server_time}")
                return True
        except Exception as e:
            logger.error(f"币安API连接测试失败: {e}")
            self.enabled = False
            return False
    
    def get_symbol_price(self, symbol: str) -> Optional[float]:
        """获取单个交易对的价格
        
        Args:
            symbol: 交易对符号，如 'BTCUSDT'
            
        Returns:
            价格，如果获取失败返回None
        """
        if not self.enabled or not self.client:
            return self._get_mock_price(symbol)
        
        try:
            # 检查缓存
            current_time = time.time()
            if (symbol in self.price_cache and 
                symbol in self.last_update_time and
                current_time - self.last_update_time[symbol] < self.update_interval):
                return self.price_cache[symbol]
            
            # 从API获取价格
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            price = float(ticker['price'])
            
            # 更新缓存
            self.price_cache[symbol] = price
            self.last_update_time[symbol] = current_time
            
            logger.debug(f"获取 {symbol} 价格: {price}")
            return price
            
        except (BinanceAPIException, BinanceRequestException) as e:
            logger.error(f"获取 {symbol} 价格失败: {e}")
            if self.fallback_to_mock:
                return self._get_mock_price(symbol)
            return None
        except Exception as e:
            logger.error(f"获取 {symbol} 价格时发生未知错误: {e}")
            if self.fallback_to_mock:
                return self._get_mock_price(symbol)
            return None
    
    def get_all_prices(self) -> Dict[str, float]:
        """获取所有配置的交易对价格
        
        Returns:
            交易对价格字典
        """
        if not self.enabled or not self.client:
            return self._get_all_mock_prices()
        
        try:
            # 批量获取价格
            tickers = self.client.get_all_tickers()
            prices = {}
            
            # 过滤出我们关心的交易对
            for ticker in tickers:
                symbol = ticker['symbol']
                if symbol in self.symbols:
                    price = float(ticker['price'])
                    prices[symbol] = price
                    
                    # 更新缓存
                    self.price_cache[symbol] = price
                    self.last_update_time[symbol] = time.time()
            
            logger.debug(f"批量获取价格成功，共 {len(prices)} 个交易对")
            return prices
            
        except Exception as e:
            logger.error(f"批量获取价格失败: {e}")
            if self.fallback_to_mock:
                return self._get_all_mock_prices()
            return {}
    
    def get_kline_data(self, symbol: str, interval: str = '1m', limit: int = 100) -> List[Dict]:
        """获取K线数据
        
        Args:
            symbol: 交易对符号
            interval: 时间间隔 ('1m', '5m', '1h', '1d' 等)
            limit: 数据条数
            
        Returns:
            K线数据列表
        """
        if not self.enabled or not self.client:
            return self._get_mock_kline_data(symbol, limit)
        
        try:
            klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
            
            # 转换为标准格式
            formatted_klines = []
            for kline in klines:
                formatted_klines.append({
                    'timestamp': int(kline[0]) // 1000,  # 转换为秒
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                })
            
            logger.debug(f"获取 {symbol} K线数据成功，共 {len(formatted_klines)} 条")
            return formatted_klines
            
        except Exception as e:
            logger.error(f"获取 {symbol} K线数据失败: {e}")
            if self.fallback_to_mock:
                return self._get_mock_kline_data(symbol, limit)
            return []
    
    def _get_mock_price(self, symbol: str) -> float:
        """获取模拟价格数据"""
        # 基于符号生成模拟价格
        mock_prices = {
            'BTCUSDT': 45000.0,
            'ETHUSDT': 3000.0,
            'BNBUSDT': 400.0,
            'ADAUSDT': 0.5,
            'SOLUSDT': 100.0,
            'XRPUSDT': 0.6,
            'DOTUSDT': 8.0,
            'DOGEUSDT': 0.08,
            'AVAXUSDT': 35.0,
            'MATICUSDT': 1.2
        }
        
        base_price = mock_prices.get(symbol, 100.0)
        
        # 添加一些随机波动
        import random
        variation = random.uniform(-0.05, 0.05)  # ±5%的波动
        return base_price * (1 + variation)
    
    def _get_all_mock_prices(self) -> Dict[str, float]:
        """获取所有模拟价格"""
        prices = {}
        for symbol in self.symbols:
            prices[symbol] = self._get_mock_price(symbol)
        return prices
    
    def _get_mock_kline_data(self, symbol: str, limit: int) -> List[Dict]:
        """生成模拟K线数据"""
        import random
        
        base_price = self._get_mock_price(symbol)
        klines = []
        current_time = int(time.time())
        
        for i in range(limit):
            timestamp = current_time - (limit - i) * 60  # 每分钟一个数据点
            
            # 生成OHLC数据
            open_price = base_price * (1 + random.uniform(-0.02, 0.02))
            close_price = open_price * (1 + random.uniform(-0.03, 0.03))
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.02))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.02))
            volume = random.uniform(1000, 10000)
            
            klines.append({
                'timestamp': timestamp,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': round(volume, 2)
            })
            
            base_price = close_price  # 下一个周期的基础价格
        
        return klines
    
    def is_enabled(self) -> bool:
        """检查币安API是否启用"""
        return self.enabled
    
    def get_supported_symbols(self) -> List[str]:
        """获取支持的交易对列表"""
        return self.symbols.copy()
    
    def set_enabled(self, enabled: bool):
        """设置是否启用币安API"""
        self.enabled = enabled
        logger.info(f"币安API {'启用' if enabled else '禁用'}")

# 全局实例
binance_client = BinanceClient()