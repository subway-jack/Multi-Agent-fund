# -*- coding: utf-8 -*-
"""
币安API主客户端
"""

import os
import logging
from typing import Dict, List, Optional, Any

from ..base import BaseAPI
from ..exceptions import APIException, AuthenticationException
from .spot import SpotAPI
from .market import MarketDataAPI
from .account import AccountAPI

logger = logging.getLogger(__name__)


class BinanceAPI(BaseAPI):
    """
    币安API主客户端
    
    基于币安官方API文档实现: https://developers.binance.com/docs/binance-spot-api-docs
    """
    
    # 币安API端点
    MAINNET_BASE_URL = "https://api.binance.com"
    TESTNET_BASE_URL = "https://testnet.binance.vision"
    
    # 备用端点 (更好的性能但稳定性较低)
    BACKUP_ENDPOINTS = [
        "https://api1.binance.com",
        "https://api2.binance.com", 
        "https://api3.binance.com",
        "https://api4.binance.com"
    ]
    
    def __init__(self, api_key: str = None, api_secret: str = None, 
                 testnet: bool = False, timeout: int = 10):
        """
        初始化币安API客户端
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            testnet: 是否使用测试网络
            timeout: 请求超时时间
        """
        # 从环境变量获取密钥
        if not api_key:
            api_key = os.getenv('BINANCE_API_KEY')
        if not api_secret:
            api_secret = os.getenv('BINANCE_API_SECRET')
        
        # 选择基础URL
        base_url = self.TESTNET_BASE_URL if testnet else self.MAINNET_BASE_URL
        
        super().__init__(api_key, api_secret, base_url, timeout)
        
        self.testnet = testnet
        
        # 初始化子模块
        self.spot = SpotAPI(self)
        self.market = MarketDataAPI(self)
        self.account = AccountAPI(self)
        
        # 设置币安特定的请求头
        if self.api_key:
            self.session.headers.update({
                'X-MBX-APIKEY': self.api_key
            })
        
        logger.info(f"币安API客户端初始化完成 (testnet={testnet})")
    
    def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            连接是否成功
        """
        try:
            response = self._make_request('GET', '/api/v3/ping')
            return response == {}
        except Exception as e:
            logger.error(f"API连接测试失败: {e}")
            return False
    
    def get_server_time(self) -> Dict[str, Any]:
        """
        获取服务器时间
        
        Returns:
            服务器时间信息
        """
        return self._make_request('GET', '/api/v3/time')
    
    def get_exchange_info(self, symbol: str = None) -> Dict[str, Any]:
        """
        获取交易所信息
        
        Args:
            symbol: 可选，指定交易对
            
        Returns:
            交易所信息
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._make_request('GET', '/api/v3/exchangeInfo', params)
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        Returns:
            系统状态信息
        """
        return self._make_request('GET', '/sapi/v1/system/status')
    
    def get_account_status(self) -> Dict[str, Any]:
        """
        获取账户状态 (需要API密钥)
        
        Returns:
            账户状态信息
        """
        if not self.api_key:
            raise AuthenticationException("API key required for account status")
        
        return self._make_request('GET', '/sapi/v1/account/status', signed=True)
    
    def get_api_trading_status(self) -> Dict[str, Any]:
        """
        获取API交易状态 (需要API密钥)
        
        Returns:
            API交易状态信息
        """
        if not self.api_key:
            raise AuthenticationException("API key required for trading status")
        
        return self._make_request('GET', '/sapi/v1/account/apiTradingStatus', signed=True)
    
    def switch_to_backup_endpoint(self, endpoint_index: int = 0) -> bool:
        """
        切换到备用端点
        
        Args:
            endpoint_index: 备用端点索引 (0-3)
            
        Returns:
            切换是否成功
        """
        if 0 <= endpoint_index < len(self.BACKUP_ENDPOINTS):
            old_url = self.base_url
            self.base_url = self.BACKUP_ENDPOINTS[endpoint_index]
            
            # 测试新端点
            if self.test_connection():
                logger.info(f"已切换到备用端点: {self.base_url}")
                return True
            else:
                # 切换失败，恢复原端点
                self.base_url = old_url
                logger.warning(f"备用端点连接失败，恢复到: {self.base_url}")
                return False
        
        return False
    
    def get_rate_limits(self) -> List[Dict[str, Any]]:
        """
        获取当前的速率限制信息
        
        Returns:
            速率限制信息列表
        """
        exchange_info = self.get_exchange_info()
        return exchange_info.get('rateLimits', [])
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
    
    def __repr__(self):
        return f"BinanceAPI(testnet={self.testnet}, base_url='{self.base_url}')"