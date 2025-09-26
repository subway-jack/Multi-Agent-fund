# -*- coding: utf-8 -*-
"""
API工具模块 - 提供通用的API工具函数
"""

import time
import logging
import functools
from typing import Callable, Any, Dict, Optional, Union
from decimal import Decimal, ROUND_DOWN

from .exceptions import (
    APIException, 
    RateLimitException, 
    NetworkException, 
    ServerException,
    ValidationException
)

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, 
                    backoff_factor: float = 2.0, 
                    exceptions: tuple = (NetworkException, ServerException)):
    """
    重试装饰器 - 在指定异常时自动重试
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间 (秒)
        backoff_factor: 退避因子
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    
                    wait_time = delay * (backoff_factor ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {wait_time:.2f}s...")
                    time.sleep(wait_time)
                except Exception as e:
                    # 对于不在重试列表中的异常，直接抛出
                    logger.error(f"Function {func.__name__} failed with non-retryable exception: {e}")
                    raise
            
            # 这行代码理论上不会执行到，但为了类型检查
            raise last_exception
        
        return wrapper
    return decorator


def rate_limit(calls_per_second: float = 10.0):
    """
    速率限制装饰器
    
    Args:
        calls_per_second: 每秒允许的调用次数
    """
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        
        return wrapper
    return decorator


def validate_symbol(symbol: str) -> str:
    """
    验证并标准化交易对符号
    
    Args:
        symbol: 交易对符号
        
    Returns:
        标准化的交易对符号
        
    Raises:
        ValidationException: 符号格式无效
    """
    if not symbol or not isinstance(symbol, str):
        raise ValidationException("Symbol must be a non-empty string")
    
    symbol = symbol.upper().strip()
    
    # 基本格式检查
    if len(symbol) < 6 or len(symbol) > 20:
        raise ValidationException(f"Invalid symbol length: {symbol}")
    
    # 检查是否包含非法字符
    if not symbol.isalnum():
        raise ValidationException(f"Symbol contains invalid characters: {symbol}")
    
    return symbol


def validate_side(side: str) -> str:
    """
    验证订单方向
    
    Args:
        side: 订单方向
        
    Returns:
        标准化的订单方向
        
    Raises:
        ValidationException: 方向无效
    """
    if not side or not isinstance(side, str):
        raise ValidationException("Side must be a non-empty string")
    
    side = side.upper().strip()
    
    if side not in ['BUY', 'SELL']:
        raise ValidationException(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")
    
    return side


def validate_order_type(order_type: str) -> str:
    """
    验证订单类型
    
    Args:
        order_type: 订单类型
        
    Returns:
        标准化的订单类型
        
    Raises:
        ValidationException: 类型无效
    """
    if not order_type or not isinstance(order_type, str):
        raise ValidationException("Order type must be a non-empty string")
    
    order_type = order_type.upper().strip()
    
    valid_types = [
        'LIMIT', 'MARKET', 'STOP_LOSS', 'STOP_LOSS_LIMIT',
        'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT', 'LIMIT_MAKER'
    ]
    
    if order_type not in valid_types:
        raise ValidationException(f"Invalid order type: {order_type}. Must be one of {valid_types}")
    
    return order_type


def validate_time_in_force(time_in_force: str) -> str:
    """
    验证订单有效期
    
    Args:
        time_in_force: 订单有效期
        
    Returns:
        标准化的订单有效期
        
    Raises:
        ValidationException: 有效期无效
    """
    if not time_in_force or not isinstance(time_in_force, str):
        raise ValidationException("Time in force must be a non-empty string")
    
    time_in_force = time_in_force.upper().strip()
    
    if time_in_force not in ['GTC', 'IOC', 'FOK']:
        raise ValidationException(f"Invalid time in force: {time_in_force}. Must be 'GTC', 'IOC', or 'FOK'")
    
    return time_in_force


def validate_quantity(quantity: Union[float, str, Decimal], min_qty: float = 0.0) -> str:
    """
    验证并格式化数量
    
    Args:
        quantity: 数量
        min_qty: 最小数量
        
    Returns:
        格式化的数量字符串
        
    Raises:
        ValidationException: 数量无效
    """
    try:
        if isinstance(quantity, str):
            qty = Decimal(quantity)
        else:
            qty = Decimal(str(quantity))
    except (ValueError, TypeError):
        raise ValidationException(f"Invalid quantity format: {quantity}")
    
    if qty <= 0:
        raise ValidationException(f"Quantity must be positive: {quantity}")
    
    if float(qty) < min_qty:
        raise ValidationException(f"Quantity {quantity} is below minimum {min_qty}")
    
    return str(qty)


def validate_price(price: Union[float, str, Decimal]) -> str:
    """
    验证并格式化价格
    
    Args:
        price: 价格
        
    Returns:
        格式化的价格字符串
        
    Raises:
        ValidationException: 价格无效
    """
    try:
        if isinstance(price, str):
            p = Decimal(price)
        else:
            p = Decimal(str(price))
    except (ValueError, TypeError):
        raise ValidationException(f"Invalid price format: {price}")
    
    if p <= 0:
        raise ValidationException(f"Price must be positive: {price}")
    
    return str(p)


def format_decimal(value: Union[float, str, Decimal], precision: int = 8) -> str:
    """
    格式化小数，去除尾随零
    
    Args:
        value: 要格式化的值
        precision: 精度
        
    Returns:
        格式化的字符串
    """
    try:
        if isinstance(value, str):
            d = Decimal(value)
        else:
            d = Decimal(str(value))
        
        # 量化到指定精度
        quantized = d.quantize(Decimal('0.' + '0' * precision), rounding=ROUND_DOWN)
        
        # 转换为字符串并去除尾随零
        return str(quantized.normalize())
    except (ValueError, TypeError):
        return str(value)


def calculate_notional(quantity: Union[float, str, Decimal], 
                      price: Union[float, str, Decimal]) -> Decimal:
    """
    计算名义价值 (数量 × 价格)
    
    Args:
        quantity: 数量
        price: 价格
        
    Returns:
        名义价值
    """
    try:
        qty = Decimal(str(quantity))
        p = Decimal(str(price))
        return qty * p
    except (ValueError, TypeError):
        raise ValidationException("Invalid quantity or price for notional calculation")


def parse_binance_error(error_response: Dict[str, Any]) -> APIException:
    """
    解析币安API错误响应并返回相应的异常
    
    Args:
        error_response: 错误响应字典
        
    Returns:
        相应的异常实例
    """
    code = error_response.get('code', 0)
    msg = error_response.get('msg', 'Unknown error')
    
    # 根据错误代码返回相应的异常类型
    if code == -1021:  # Timestamp outside of recvWindow
        return ValidationException(f"Timestamp error: {msg}")
    elif code == -1022:  # Invalid signature
        return ValidationException(f"Signature error: {msg}")
    elif code == -2010:  # Account has insufficient balance
        return ValidationException(f"Insufficient balance: {msg}")
    elif code == -2011:  # Unknown order sent
        return ValidationException(f"Unknown order: {msg}")
    elif code == -1003:  # Too many requests
        return RateLimitException(f"Rate limit exceeded: {msg}")
    elif code == -1000:  # Unknown error
        return ServerException(f"Server error: {msg}")
    elif code in [-1001, -1002]:  # Disconnected or Unauthorized
        return NetworkException(f"Connection error: {msg}")
    else:
        return APIException(f"API error {code}: {msg}")


def get_server_time_offset(server_time: int) -> int:
    """
    计算服务器时间偏移
    
    Args:
        server_time: 服务器时间戳 (毫秒)
        
    Returns:
        时间偏移 (毫秒)
    """
    local_time = int(time.time() * 1000)
    return server_time - local_time


def adjust_timestamp(timestamp: Optional[int] = None, offset: int = 0) -> int:
    """
    调整时间戳
    
    Args:
        timestamp: 时间戳 (毫秒)，如果为None则使用当前时间
        offset: 时间偏移 (毫秒)
        
    Returns:
        调整后的时间戳
    """
    if timestamp is None:
        timestamp = int(time.time() * 1000)
    
    return timestamp + offset


class CircuitBreaker:
    """
    熔断器 - 防止连续失败的请求
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """
        初始化熔断器
        
        Args:
            failure_threshold: 失败阈值
            recovery_timeout: 恢复超时时间 (秒)
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        通过熔断器调用函数
        
        Args:
            func: 要调用的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数返回值
            
        Raises:
            APIException: 熔断器开启时
        """
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise APIException("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置"""
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """成功时的处理"""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """失败时的处理"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'