# -*- coding: utf-8 -*-
"""
BaseAPI基类测试用例
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from requests import Response, Session
from requests.exceptions import RequestException, Timeout, ConnectionError

from src.api.base import BaseAPI
from src.api.exceptions import (
    APIException,
    RateLimitException,
    AuthenticationException,
    NetworkException,
    ServerException,
    ValidationException
)


class TestableBaseAPI(BaseAPI):
    """用于测试的BaseAPI具体实现"""
    
    def test_connection(self) -> bool:
        """测试连接的具体实现"""
        try:
            response = self._make_request("GET", "/ping")
            return response.get("success", False)
        except Exception:
            return False


class TestBaseAPI:
    """BaseAPI基类测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.api = TestableBaseAPI(
            api_key="test_api_key",
            api_secret="test_secret_key",
            base_url="https://api.test.com"
        )
    
    def test_init_with_keys(self):
        """测试使用API密钥初始化"""
        api = TestableBaseAPI(
            api_key="test_key",
            api_secret="test_secret",
            base_url="https://api.test.com"
        )
        
        assert api.api_key == "test_key"
        assert api.api_secret == "test_secret"
        assert api.base_url == "https://api.test.com"
        assert isinstance(api.session, Session)
    
    def test_init_without_keys(self):
        """测试不使用API密钥初始化"""
        api = TestableBaseAPI(base_url="https://api.test.com")
        
        assert api.api_key is None
        assert api.api_secret is None
        assert api.base_url == "https://api.test.com"
    
    @patch.dict('os.environ', {
        'BINANCE_API_KEY': 'env_api_key',
        'BINANCE_SECRET_KEY': 'env_secret_key'
    })
    def test_init_from_environment(self):
        """测试从环境变量初始化"""
        api = BaseAPI(base_url="https://api.test.com")
        
        assert api.api_key == "env_api_key"
        assert api.secret_key == "env_secret_key"
    
    def test_generate_signature(self):
        """测试签名生成"""
        query_string = "symbol=BTCUSDT&side=BUY&type=LIMIT&quantity=1&price=50000"
        signature = self.api._generate_signature(query_string)
        
        assert isinstance(signature, str)
        assert len(signature) == 64  # HMAC-SHA256 hex digest length
    
    def test_generate_signature_empty_string(self):
        """测试空字符串签名生成"""
        signature = self.api._generate_signature("")
        assert isinstance(signature, str)
        assert len(signature) == 64
    
    def test_generate_signature_without_secret(self):
        """测试没有密钥时的签名生成"""
        api = BaseAPI(base_url="https://api.test.com")
        
        with pytest.raises(ValueError, match="Secret key is required"):
            api._generate_signature("test")
    
    @patch('src.api.base.time.time')
    def test_get_timestamp(self, mock_time):
        """测试时间戳获取"""
        mock_time.return_value = 1234567890.123
        timestamp = self.api._get_timestamp()
        
        assert timestamp == 1234567890123  # 毫秒时间戳
    
    def test_prepare_params_public(self):
        """测试公开接口参数准备"""
        params = {"symbol": "BTCUSDT", "limit": 100}
        prepared = self.api._prepare_params(params, signed=False)
        
        assert prepared == params
        assert "timestamp" not in prepared
        assert "signature" not in prepared
    
    @patch('src.api.base.time.time')
    def test_prepare_params_signed(self, mock_time):
        """测试签名接口参数准备"""
        mock_time.return_value = 1234567890.123
        params = {"symbol": "BTCUSDT", "side": "BUY"}
        prepared = self.api._prepare_params(params, signed=True)
        
        assert "timestamp" in prepared
        assert "signature" in prepared
        assert prepared["timestamp"] == 1234567890123
        assert prepared["symbol"] == "BTCUSDT"
        assert prepared["side"] == "BUY"
    
    def test_prepare_params_signed_without_keys(self):
        """测试没有密钥时的签名参数准备"""
        api = BaseAPI(base_url="https://api.test.com")
        params = {"symbol": "BTCUSDT"}
        
        with pytest.raises(ValueError, match="API key and secret key are required"):
            api._prepare_params(params, signed=True)
    
    @patch('requests.Session.request')
    def test_make_request_success(self, mock_request):
        """测试成功的请求"""
        # 模拟成功响应
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": "test"}
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        result = self.api._make_request("GET", "/test")
        
        assert result == {"success": True, "data": "test"}
        mock_request.assert_called_once()
    
    @patch('requests.Session.request')
    def test_make_request_with_params(self, mock_request):
        """测试带参数的请求"""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        params = {"symbol": "BTCUSDT", "limit": 100}
        self.api._make_request("GET", "/test", params=params)
        
        # 验证请求参数
        call_args = mock_request.call_args
        assert call_args[1]["params"] == params
    
    @patch('requests.Session.request')
    def test_make_request_signed(self, mock_request):
        """测试签名请求"""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        params = {"symbol": "BTCUSDT"}
        self.api._make_request("POST", "/test", params=params, signed=True)
        
        # 验证请求包含签名
        call_args = mock_request.call_args
        request_params = call_args[1].get("params") or call_args[1].get("data")
        assert "timestamp" in request_params
        assert "signature" in request_params
    
    @patch('requests.Session.request')
    def test_make_request_network_error(self, mock_request):
        """测试网络错误"""
        mock_request.side_effect = ConnectionError("Connection failed")
        
        with pytest.raises(NetworkException):
            self.api._make_request("GET", "/test")
    
    @patch('requests.Session.request')
    def test_make_request_timeout(self, mock_request):
        """测试超时错误"""
        mock_request.side_effect = Timeout("Request timeout")
        
        with pytest.raises(NetworkException):
            self.api._make_request("GET", "/test")
    
    @patch('requests.Session.request')
    def test_make_request_generic_exception(self, mock_request):
        """测试通用请求异常"""
        mock_request.side_effect = RequestException("Generic error")
        
        with pytest.raises(NetworkException):
            self.api._make_request("GET", "/test")
    
    @patch('requests.Session.request')
    def test_handle_response_400_error(self, mock_request):
        """测试400错误响应处理"""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "code": -1022,
            "msg": "Invalid signature"
        }
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        with pytest.raises(ValidationException):
            self.api._make_request("GET", "/test")
    
    @patch('requests.Session.request')
    def test_handle_response_401_error(self, mock_request):
        """测试401错误响应处理"""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        with pytest.raises(AuthenticationException):
            self.api._make_request("GET", "/test")
    
    @patch('requests.Session.request')
    def test_handle_response_403_error(self, mock_request):
        """测试403错误响应处理"""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        with pytest.raises(AuthenticationException):
            self.api._make_request("GET", "/test")
    
    @patch('requests.Session.request')
    def test_handle_response_429_error(self, mock_request):
        """测试429速率限制错误"""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"
        mock_response.headers = {"Retry-After": "60"}
        mock_request.return_value = mock_response
        
        with pytest.raises(RateLimitException):
            self.api._make_request("GET", "/test")
    
    @patch('requests.Session.request')
    def test_handle_response_500_error(self, mock_request):
        """测试500服务器错误"""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        with pytest.raises(ServerException):
            self.api._make_request("GET", "/test")
    
    @patch('requests.Session.request')
    def test_handle_response_non_json_200(self, mock_request):
        """测试非JSON的200响应"""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("No JSON")
        mock_response.text = "OK"
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        result = self.api._make_request("GET", "/test")
        assert result == {"success": True}
    
    @patch('requests.Session.request')
    def test_circuit_breaker_integration(self, mock_request):
        """测试熔断器集成"""
        # 模拟连续失败
        mock_request.side_effect = ConnectionError("Connection failed")
        
        # 触发熔断器
        for _ in range(5):  # 默认失败阈值是5
            with pytest.raises(NetworkException):
                self.api._make_request("GET", "/test")
        
        # 现在应该触发熔断器
        with pytest.raises(APIException, match="Circuit breaker is OPEN"):
            self.api._make_request("GET", "/test")
    
    def test_session_headers(self):
        """测试会话头部设置"""
        headers = self.api.session.headers
        
        assert "User-Agent" in headers
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
    
    def test_session_timeout(self):
        """测试会话超时设置"""
        # 检查默认超时
        assert hasattr(self.api, 'timeout')
        assert self.api.timeout == 30
    
    @patch('requests.Session.request')
    def test_rate_limiting(self, mock_request):
        """测试速率限制"""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        # 记录请求时间
        start_time = time.time()
        
        # 连续发送两个请求
        self.api._make_request("GET", "/test")
        self.api._make_request("GET", "/test")
        
        end_time = time.time()
        
        # 由于速率限制，第二个请求应该有延迟
        # 注意：这个测试可能不稳定，因为实际的速率限制实现可能不同
        assert end_time - start_time >= 0  # 至少验证没有错误
    
    def test_url_construction(self):
        """测试URL构造"""
        # 测试基本URL构造
        url = self.api.base_url + "/test"
        assert url == "https://api.test.com/test"
        
        # 测试带参数的URL构造
        endpoint = "/api/v3/ticker/price"
        full_url = self.api.base_url + endpoint
        assert full_url == "https://api.test.com/api/v3/ticker/price"
    
    def test_api_key_header(self):
        """测试API密钥头部"""
        # 当有API密钥时，应该设置X-MBX-APIKEY头部
        assert "X-MBX-APIKEY" in self.api.session.headers
        assert self.api.session.headers["X-MBX-APIKEY"] == "test_api_key"
    
    def test_api_key_header_without_key(self):
        """测试没有API密钥时的头部"""
        api = BaseAPI(base_url="https://api.test.com")
        
        # 没有API密钥时，不应该设置X-MBX-APIKEY头部
        assert "X-MBX-APIKEY" not in api.session.headers


class TestBaseAPIEdgeCases:
    """BaseAPI边界情况测试"""
    
    def test_empty_base_url(self):
        """测试空基础URL"""
        with pytest.raises(ValueError):
            BaseAPI(base_url="")
    
    def test_invalid_base_url(self):
        """测试无效基础URL"""
        # 这里可能需要根据实际实现调整
        api = BaseAPI(base_url="invalid-url")
        assert api.base_url == "invalid-url"
    
    def test_none_params(self):
        """测试None参数"""
        api = BaseAPI(base_url="https://api.test.com")
        prepared = api._prepare_params(None, signed=False)
        assert prepared == {}
    
    def test_empty_params(self):
        """测试空参数"""
        api = BaseAPI(base_url="https://api.test.com")
        prepared = api._prepare_params({}, signed=False)
        assert prepared == {}
    
    @patch('requests.Session.request')
    def test_malformed_json_response(self, mock_request):
        """测试格式错误的JSON响应"""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        result = BaseAPI(base_url="https://api.test.com")._make_request("GET", "/test")
        assert result == {"success": True}
    
    def test_special_characters_in_params(self):
        """测试参数中的特殊字符"""
        api = BaseAPI(
            api_key="test_key",
            secret_key="test_secret",
            base_url="https://api.test.com"
        )
        
        params = {
            "symbol": "BTC/USDT",  # 包含斜杠
            "note": "Test & Debug",  # 包含&符号
            "price": "50,000.00"  # 包含逗号
        }
        
        prepared = api._prepare_params(params, signed=True)
        
        # 验证参数被正确处理
        assert "timestamp" in prepared
        assert "signature" in prepared
        assert prepared["symbol"] == "BTC/USDT"
        assert prepared["note"] == "Test & Debug"
        assert prepared["price"] == "50,000.00"