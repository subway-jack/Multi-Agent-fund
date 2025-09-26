# -*- coding: utf-8 -*-
"""
API基础类模块
"""

import time
import hmac
import hashlib
import logging
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from abc import ABC, abstractmethod
from urllib.parse import urlencode

from .exceptions import (
    APIException, 
    RateLimitException, 
    AuthenticationException,
    NetworkException,
    ServerException,
    ValidationException
)
from .utils import CircuitBreaker, parse_binance_error, retry_on_failure

logger = logging.getLogger(__name__)


class BaseAPI(ABC):
    """API基础类"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, 
                 base_url: str = None, timeout: int = 10):
        """
        初始化API客户端
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            base_url: API基础URL
            timeout: 请求超时时间
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.timeout = timeout
        # 初始化熔断器
        self.circuit_breaker = CircuitBreaker()
        
        self.session = requests.Session()
        
        # 设置默认请求头
        self.session.headers.update({
            'User-Agent': 'AI-Fund-Trading-Bot/1.0',
            'Content-Type': 'application/json'
        })
        
        # 速率限制
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 最小请求间隔(秒)
    
    def _wait_for_rate_limit(self):
        """等待速率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _generate_signature(self, params: Dict[str, Any], timestamp: int = None) -> str:
        """
        生成API签名
        
        Args:
            params: 请求参数
            timestamp: 时间戳
            
        Returns:
            签名字符串
        """
        if not self.api_secret:
            raise AuthenticationException("API secret is required for signed requests")
        
        if timestamp:
            params['timestamp'] = timestamp
        
        query_string = urlencode(sorted(params.items()))
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff_factor=2.0)
    def _make_request(self, method: str, endpoint: str, params: Dict[str, Any] = None, 
                     signed: bool = False, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            params: 请求参数
            signed: 是否需要签名
            timeout: 超时时间
            
        Returns:
            响应数据
        """
        def _request():
            if params is None:
                params_copy = {}
            else:
                params_copy = params.copy()
            
            # 添加时间戳
            if signed:
                params_copy['timestamp'] = int(time.time() * 1000)
                params_copy['signature'] = self._generate_signature(params_copy)
            
            # 构建URL
            url = f"{self.base_url}{endpoint}"
            
            # 设置请求头
            headers = {}
            if self.api_key:
                headers['X-MBX-APIKEY'] = self.api_key
            
            # 发送请求
            try:
                if method.upper() == 'GET':
                    response = self.session.get(
                        url, 
                        params=params_copy, 
                        headers=headers, 
                        timeout=timeout or self.timeout
                    )
                elif method.upper() == 'POST':
                    response = self.session.post(
                        url, 
                        data=params_copy, 
                        headers=headers, 
                        timeout=timeout or self.timeout
                    )
                elif method.upper() == 'DELETE':
                    response = self.session.delete(
                        url, 
                        params=params_copy, 
                        headers=headers, 
                        timeout=timeout or self.timeout
                    )
                else:
                    raise ValidationException(f"Unsupported HTTP method: {method}")
                
                return self._handle_response(response)
                
            except requests.exceptions.Timeout:
                raise NetworkException("Request timeout")
            except requests.exceptions.ConnectionError:
                raise NetworkException("Connection error")
            except requests.exceptions.RequestException as e:
                raise NetworkException(f"Request failed: {str(e)}")
        
        # 使用熔断器执行请求
        return self.circuit_breaker.call(_request)
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        处理HTTP响应
        
        Args:
            response: HTTP响应对象
            
        Returns:
            解析后的响应数据
            
        Raises:
            各种API异常
        """
        try:
            data = response.json()
        except ValueError:
            # 如果响应不是JSON格式
            if response.status_code == 200:
                return {'success': True}
            else:
                raise APIException(f"Invalid response format: {response.text}")
        
        # 检查HTTP状态码
        if response.status_code == 200:
            return data
        elif response.status_code == 400:
            # 客户端错误，解析具体错误
            raise parse_binance_error(data)
        elif response.status_code == 401:
            raise AuthenticationException("Invalid API key or signature")
        elif response.status_code == 403:
            raise AuthenticationException("Access denied")
        elif response.status_code == 418:
            # IP被封禁
            raise RateLimitException("IP banned")
        elif response.status_code == 429:
            raise RateLimitException("Rate limit exceeded")
        elif response.status_code >= 500:
            raise ServerException(f"Server error: {response.status_code}")
        else:
            raise APIException(f"HTTP {response.status_code}: {data}")
    
    @abstractmethod
    def test_connection(self) -> bool:
        """测试API连接"""
        pass
    
    def close(self):
        """关闭会话"""
        if self.session:
            self.session.close()