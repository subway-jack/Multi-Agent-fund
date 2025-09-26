# -*- coding: utf-8 -*-
"""
API异常类测试用例
"""

import pytest
from src.api.exceptions import (
    APIException,
    RateLimitException,
    AuthenticationException,
    NetworkException,
    ServerException,
    ValidationException
)


class TestAPIException:
    """API异常基类测试"""
    
    def test_api_exception_basic(self):
        """测试基本API异常"""
        error = APIException("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.code is None
        assert error.details is None
    
    def test_api_exception_with_code(self):
        """测试带错误码的API异常"""
        error = APIException("Test error", code=-1000)
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.code == -1000
        assert error.details is None
    
    def test_api_exception_with_details(self):
        """测试带详细信息的API异常"""
        details = {"symbol": "BTCUSDT", "side": "BUY"}
        error = APIException("Test error", code=-1000, details=details)
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.code == -1000
        assert error.details == details
    
    def test_api_exception_inheritance(self):
        """测试API异常继承关系"""
        error = APIException("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, APIException)


class TestRateLimitException:
    """速率限制异常测试"""
    
    def test_rate_limit_exception_basic(self):
        """测试基本速率限制异常"""
        error = RateLimitException("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"
        assert error.message == "Rate limit exceeded"
        assert isinstance(error, APIException)
    
    def test_rate_limit_exception_with_retry_after(self):
        """测试带重试时间的速率限制异常"""
        details = {"retry_after": 60}
        error = RateLimitException("Rate limit exceeded", details=details)
        assert error.details["retry_after"] == 60
    
    def test_rate_limit_exception_inheritance(self):
        """测试速率限制异常继承关系"""
        error = RateLimitException("Rate limit exceeded")
        assert isinstance(error, Exception)
        assert isinstance(error, APIException)
        assert isinstance(error, RateLimitException)


class TestAuthenticationException:
    """认证异常测试"""
    
    def test_authentication_exception_basic(self):
        """测试基本认证异常"""
        error = AuthenticationException("Invalid API key")
        assert str(error) == "Invalid API key"
        assert error.message == "Invalid API key"
        assert isinstance(error, APIException)
    
    def test_authentication_exception_with_code(self):
        """测试带错误码的认证异常"""
        error = AuthenticationException("Invalid signature", code=-1022)
        assert error.code == -1022
        assert error.message == "Invalid signature"
    
    def test_authentication_exception_inheritance(self):
        """测试认证异常继承关系"""
        error = AuthenticationException("Invalid API key")
        assert isinstance(error, Exception)
        assert isinstance(error, APIException)
        assert isinstance(error, AuthenticationException)


class TestNetworkException:
    """网络异常测试"""
    
    def test_network_exception_basic(self):
        """测试基本网络异常"""
        error = NetworkException("Connection timeout")
        assert str(error) == "Connection timeout"
        assert error.message == "Connection timeout"
        assert isinstance(error, APIException)
    
    def test_network_exception_with_details(self):
        """测试带详细信息的网络异常"""
        details = {"timeout": 30, "url": "https://api.binance.com"}
        error = NetworkException("Connection timeout", details=details)
        assert error.details["timeout"] == 30
        assert error.details["url"] == "https://api.binance.com"
    
    def test_network_exception_inheritance(self):
        """测试网络异常继承关系"""
        error = NetworkException("Connection timeout")
        assert isinstance(error, Exception)
        assert isinstance(error, APIException)
        assert isinstance(error, NetworkException)


class TestServerException:
    """服务器异常测试"""
    
    def test_server_exception_basic(self):
        """测试基本服务器异常"""
        error = ServerException("Internal server error")
        assert str(error) == "Internal server error"
        assert error.message == "Internal server error"
        assert isinstance(error, APIException)
    
    def test_server_exception_with_code(self):
        """测试带错误码的服务器异常"""
        error = ServerException("Service unavailable", code=503)
        assert error.code == 503
        assert error.message == "Service unavailable"
    
    def test_server_exception_inheritance(self):
        """测试服务器异常继承关系"""
        error = ServerException("Internal server error")
        assert isinstance(error, Exception)
        assert isinstance(error, APIException)
        assert isinstance(error, ServerException)


class TestValidationException:
    """验证异常测试"""
    
    def test_validation_exception_basic(self):
        """测试基本验证异常"""
        error = ValidationException("Invalid parameter")
        assert str(error) == "Invalid parameter"
        assert error.message == "Invalid parameter"
        assert isinstance(error, APIException)
    
    def test_validation_exception_with_field(self):
        """测试带字段信息的验证异常"""
        details = {"field": "symbol", "value": "INVALID"}
        error = ValidationException("Invalid symbol", details=details)
        assert error.details["field"] == "symbol"
        assert error.details["value"] == "INVALID"
    
    def test_validation_exception_inheritance(self):
        """测试验证异常继承关系"""
        error = ValidationException("Invalid parameter")
        assert isinstance(error, Exception)
        assert isinstance(error, APIException)
        assert isinstance(error, ValidationException)


class TestExceptionChaining:
    """异常链测试"""
    
    def test_exception_chaining(self):
        """测试异常链"""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise APIException("API error occurred") from e
        except APIException as api_error:
            assert str(api_error) == "API error occurred"
            assert isinstance(api_error.__cause__, ValueError)
            assert str(api_error.__cause__) == "Original error"
    
    def test_nested_exception_handling(self):
        """测试嵌套异常处理"""
        def inner_function():
            raise NetworkException("Network connection failed")
        
        def outer_function():
            try:
                inner_function()
            except NetworkException as e:
                raise AuthenticationException("Authentication failed due to network") from e
        
        with pytest.raises(AuthenticationException) as exc_info:
            outer_function()
        
        assert "Authentication failed" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, NetworkException)


class TestExceptionComparison:
    """异常比较测试"""
    
    def test_exception_equality(self):
        """测试异常相等性"""
        error1 = APIException("Test error", code=-1000)
        error2 = APIException("Test error", code=-1000)
        error3 = APIException("Different error", code=-1000)
        error4 = APIException("Test error", code=-2000)
        
        # 注意：异常对象通常不相等，除非重写了__eq__方法
        assert error1 is not error2
        assert str(error1) == str(error2)
        assert error1.code == error2.code
        assert str(error1) != str(error3)
        assert error1.code != error4.code
    
    def test_exception_type_checking(self):
        """测试异常类型检查"""
        errors = [
            APIException("API error"),
            RateLimitException("Rate limit"),
            AuthenticationException("Auth error"),
            NetworkException("Network error"),
            ServerException("Server error"),
            ValidationException("Validation error")
        ]
        
        # 所有异常都应该是APIException的实例
        for error in errors:
            assert isinstance(error, APIException)
        
        # 检查特定类型
        assert isinstance(errors[1], RateLimitException)
        assert isinstance(errors[2], AuthenticationException)
        assert isinstance(errors[3], NetworkException)
        assert isinstance(errors[4], ServerException)
        assert isinstance(errors[5], ValidationException)
        
        # 检查类型不匹配
        assert not isinstance(errors[1], AuthenticationException)
        assert not isinstance(errors[2], RateLimitException)


class TestExceptionSerialization:
    """异常序列化测试"""
    
    def test_exception_str_representation(self):
        """测试异常字符串表示"""
        error = APIException("Test error", code=-1000, details={"key": "value"})
        str_repr = str(error)
        assert "Test error" in str_repr
    
    def test_exception_repr_representation(self):
        """测试异常repr表示"""
        error = APIException("Test error", code=-1000)
        repr_str = repr(error)
        assert "APIException" in repr_str
        assert "Test error" in repr_str
    
    def test_exception_attributes_access(self):
        """测试异常属性访问"""
        details = {"symbol": "BTCUSDT", "side": "BUY"}
        error = ValidationException("Invalid order", code=-2010, details=details)
        
        assert hasattr(error, 'message')
        assert hasattr(error, 'code')
        assert hasattr(error, 'details')
        
        assert error.message == "Invalid order"
        assert error.code == -2010
        assert error.details == details
        assert error.details["symbol"] == "BTCUSDT"


class TestExceptionHandlingPatterns:
    """异常处理模式测试"""
    
    def test_catch_specific_exception(self):
        """测试捕获特定异常"""
        def raise_rate_limit():
            raise RateLimitException("Too many requests")
        
        with pytest.raises(RateLimitException):
            raise_rate_limit()
        
        # 也应该能被APIException捕获
        try:
            raise_rate_limit()
        except APIException as e:
            assert isinstance(e, RateLimitException)
    
    def test_catch_multiple_exceptions(self):
        """测试捕获多种异常"""
        def raise_various_errors(error_type):
            if error_type == "rate":
                raise RateLimitException("Rate limit")
            elif error_type == "auth":
                raise AuthenticationException("Auth error")
            elif error_type == "network":
                raise NetworkException("Network error")
            else:
                raise APIException("Generic error")
        
        # 测试捕获多种特定异常
        for error_type in ["rate", "auth", "network"]:
            with pytest.raises((RateLimitException, AuthenticationException, NetworkException)):
                raise_various_errors(error_type)
        
        # 测试捕获基类异常
        for error_type in ["rate", "auth", "network", "generic"]:
            with pytest.raises(APIException):
                raise_various_errors(error_type)
    
    def test_exception_context_manager(self):
        """测试异常上下文管理器"""
        class ErrorContext:
            def __init__(self):
                self.errors = []
            
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type and issubclass(exc_type, APIException):
                    self.errors.append(exc_val)
                    return True  # 抑制异常
                return False
        
        with ErrorContext() as ctx:
            raise RateLimitException("Rate limit exceeded")
        
        assert len(ctx.errors) == 1
        assert isinstance(ctx.errors[0], RateLimitException)