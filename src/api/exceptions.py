# -*- coding: utf-8 -*-
"""
API异常处理模块
"""


class APIException(Exception):
    """API基础异常类"""
    
    def __init__(self, message: str, error_code: str = None, status_code: int = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class RateLimitException(APIException):
    """API频率限制异常"""
    
    def __init__(self, message: str = "API rate limit exceeded", retry_after: int = None):
        super().__init__(message, "RATE_LIMIT", 429)
        self.retry_after = retry_after


class AuthenticationException(APIException):
    """API认证异常"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_FAILED", 401)


class NetworkException(APIException):
    """网络连接异常"""
    
    def __init__(self, message: str = "Network connection failed"):
        super().__init__(message, "NETWORK_ERROR", 0)


class ServerException(APIException):
    """服务器异常"""
    
    def __init__(self, message: str = "Server error", status_code: int = 500):
        super().__init__(message, "SERVER_ERROR", status_code)


class ValidationException(APIException):
    """参数验证异常"""
    
    def __init__(self, message: str = "Invalid parameters"):
        super().__init__(message, "VALIDATION_ERROR", 400)