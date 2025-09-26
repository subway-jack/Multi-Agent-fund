# -*- coding: utf-8 -*-
"""
API工具模块测试用例
"""

import pytest
import time
from decimal import Decimal
from unittest.mock import Mock, patch

from src.api.utils import (
    retry_on_failure,
    rate_limit,
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_time_in_force,
    validate_quantity,
    validate_price,
    format_decimal,
    calculate_notional,
    parse_binance_error,
    get_server_time_offset,
    adjust_timestamp,
    CircuitBreaker
)
from src.api.exceptions import (
    APIException,
    RateLimitException,
    AuthenticationException,
    NetworkException,
    ServerException,
    ValidationException
)


class TestRetryDecorator:
    """重试装饰器测试类"""
    
    def test_retry_success_first_attempt(self):
        """测试第一次尝试就成功"""
        call_count = 0
        
        @retry_on_failure(max_retries=3)
        def test_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = test_function()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_success_after_failures(self):
        """测试失败后重试成功"""
        call_count = 0
        
        @retry_on_failure(max_retries=3, delay=0.01)
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkException("Network error")
            return "success"
        
        result = test_function()
        assert result == "success"
        assert call_count == 3
    
    def test_retry_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        call_count = 0
        
        @retry_on_failure(max_retries=2, delay=0.01)
        def test_function():
            nonlocal call_count
            call_count += 1
            raise NetworkException("Network error")
        
        with pytest.raises(NetworkException):
            test_function()
        
        assert call_count == 3  # 初始调用 + 2次重试
    
    def test_retry_non_retryable_exception(self):
        """测试不可重试的异常"""
        call_count = 0
        
        @retry_on_failure(max_retries=3, exceptions=(NetworkException,))
        def test_function():
            nonlocal call_count
            call_count += 1
            raise ValidationException("Validation error")
        
        with pytest.raises(ValidationException):
            test_function()
        
        assert call_count == 1  # 不应该重试


class TestRateLimitDecorator:
    """速率限制装饰器测试类"""
    
    def test_rate_limit_basic(self):
        """测试基本速率限制"""
        call_times = []
        
        @rate_limit(calls_per_second=10.0)  # 每秒10次调用
        def test_function():
            call_times.append(time.time())
            return "success"
        
        # 连续调用两次
        test_function()
        test_function()
        
        # 检查时间间隔
        if len(call_times) >= 2:
            time_diff = call_times[1] - call_times[0]
            assert time_diff >= 0.1  # 至少间隔0.1秒
    
    def test_rate_limit_no_delay_needed(self):
        """测试不需要延迟的情况"""
        @rate_limit(calls_per_second=1.0)
        def test_function():
            return "success"
        
        start_time = time.time()
        result = test_function()
        end_time = time.time()
        
        assert result == "success"
        assert (end_time - start_time) < 0.01  # 第一次调用应该很快


class TestValidationFunctions:
    """验证函数测试类"""
    
    def test_validate_symbol_valid(self):
        """测试有效的交易对符号"""
        assert validate_symbol('BTCUSDT') == 'BTCUSDT'
        assert validate_symbol('btcusdt') == 'BTCUSDT'
        assert validate_symbol(' ETHBTC ') == 'ETHBTC'
    
    def test_validate_symbol_invalid(self):
        """测试无效的交易对符号"""
        with pytest.raises(ValidationException):
            validate_symbol('')
        
        with pytest.raises(ValidationException):
            validate_symbol(None)
        
        with pytest.raises(ValidationException):
            validate_symbol('BTC')  # 太短
        
        with pytest.raises(ValidationException):
            validate_symbol('BTC-USDT')  # 包含非法字符
    
    def test_validate_side_valid(self):
        """测试有效的订单方向"""
        assert validate_side('BUY') == 'BUY'
        assert validate_side('buy') == 'BUY'
        assert validate_side('SELL') == 'SELL'
        assert validate_side('sell') == 'SELL'
    
    def test_validate_side_invalid(self):
        """测试无效的订单方向"""
        with pytest.raises(ValidationException):
            validate_side('')
        
        with pytest.raises(ValidationException):
            validate_side('INVALID')
        
        with pytest.raises(ValidationException):
            validate_side(None)
    
    def test_validate_order_type_valid(self):
        """测试有效的订单类型"""
        valid_types = ['LIMIT', 'MARKET', 'STOP_LOSS', 'STOP_LOSS_LIMIT', 
                      'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT', 'LIMIT_MAKER']
        
        for order_type in valid_types:
            assert validate_order_type(order_type) == order_type
            assert validate_order_type(order_type.lower()) == order_type
    
    def test_validate_order_type_invalid(self):
        """测试无效的订单类型"""
        with pytest.raises(ValidationException):
            validate_order_type('INVALID')
        
        with pytest.raises(ValidationException):
            validate_order_type('')
        
        with pytest.raises(ValidationException):
            validate_order_type(None)
    
    def test_validate_time_in_force_valid(self):
        """测试有效的订单有效期"""
        valid_tifs = ['GTC', 'IOC', 'FOK']
        
        for tif in valid_tifs:
            assert validate_time_in_force(tif) == tif
            assert validate_time_in_force(tif.lower()) == tif
    
    def test_validate_time_in_force_invalid(self):
        """测试无效的订单有效期"""
        with pytest.raises(ValidationException):
            validate_time_in_force('INVALID')
        
        with pytest.raises(ValidationException):
            validate_time_in_force('')
        
        with pytest.raises(ValidationException):
            validate_time_in_force(None)
    
    def test_validate_quantity_valid(self):
        """测试有效的数量"""
        assert validate_quantity(1.0) == '1'
        assert validate_quantity('1.5') == '1.5'
        assert validate_quantity(Decimal('2.5')) == '2.5'
        assert validate_quantity(0.001, min_qty=0.0001) == '0.001'
    
    def test_validate_quantity_invalid(self):
        """测试无效的数量"""
        with pytest.raises(ValidationException):
            validate_quantity(0)
        
        with pytest.raises(ValidationException):
            validate_quantity(-1)
        
        with pytest.raises(ValidationException):
            validate_quantity('invalid')
        
        with pytest.raises(ValidationException):
            validate_quantity(0.001, min_qty=0.01)  # 低于最小值
    
    def test_validate_price_valid(self):
        """测试有效的价格"""
        assert validate_price(50000.0) == '50000'
        assert validate_price('50000.5') == '50000.5'
        assert validate_price(Decimal('50000.25')) == '50000.25'
    
    def test_validate_price_invalid(self):
        """测试无效的价格"""
        with pytest.raises(ValidationException):
            validate_price(0)
        
        with pytest.raises(ValidationException):
            validate_price(-1)
        
        with pytest.raises(ValidationException):
            validate_price('invalid')


class TestUtilityFunctions:
    """工具函数测试类"""
    
    def test_format_decimal(self):
        """测试小数格式化"""
        assert format_decimal(1.0) == '1'
        assert format_decimal('1.50000000') == '1.5'
        assert format_decimal(Decimal('1.23456789'), precision=4) == '1.2345'
        assert format_decimal('invalid') == 'invalid'  # 无效输入返回原值
    
    def test_calculate_notional(self):
        """测试名义价值计算"""
        result = calculate_notional(1.5, 50000)
        assert result == Decimal('75000')
        
        result = calculate_notional('0.001', '50000.5')
        assert result == Decimal('50.0005')
    
    def test_calculate_notional_invalid(self):
        """测试无效的名义价值计算"""
        with pytest.raises(ValidationException):
            calculate_notional('invalid', 50000)
        
        with pytest.raises(ValidationException):
            calculate_notional(1.0, 'invalid')
    
    def test_parse_binance_error(self):
        """测试币安错误解析"""
        # 测试时间戳错误
        error = parse_binance_error({'code': -1021, 'msg': 'Timestamp outside of recvWindow'})
        assert isinstance(error, ValidationException)
        
        # 测试签名错误
        error = parse_binance_error({'code': -1022, 'msg': 'Invalid signature'})
        assert isinstance(error, ValidationException)
        
        # 测试余额不足
        error = parse_binance_error({'code': -2010, 'msg': 'Account has insufficient balance'})
        assert isinstance(error, ValidationException)
        
        # 测试速率限制
        error = parse_binance_error({'code': -1003, 'msg': 'Too many requests'})
        assert isinstance(error, RateLimitException)
        
        # 测试服务器错误
        error = parse_binance_error({'code': -1000, 'msg': 'Unknown error'})
        assert isinstance(error, ServerException)
        
        # 测试网络错误
        error = parse_binance_error({'code': -1001, 'msg': 'Disconnected'})
        assert isinstance(error, NetworkException)
        
        # 测试未知错误
        error = parse_binance_error({'code': -9999, 'msg': 'Unknown error code'})
        assert isinstance(error, APIException)
    
    def test_get_server_time_offset(self):
        """测试服务器时间偏移计算"""
        current_time = int(time.time() * 1000)
        server_time = current_time + 1000  # 服务器时间快1秒
        
        offset = get_server_time_offset(server_time)
        assert abs(offset - 1000) < 100  # 允许一些误差
    
    def test_adjust_timestamp(self):
        """测试时间戳调整"""
        # 测试使用当前时间
        adjusted = adjust_timestamp(offset=1000)
        current = int(time.time() * 1000)
        assert abs(adjusted - current - 1000) < 100
        
        # 测试使用指定时间戳
        timestamp = 1234567890000
        adjusted = adjust_timestamp(timestamp, offset=1000)
        assert adjusted == 1234567891000


class TestCircuitBreaker:
    """熔断器测试类"""
    
    def test_circuit_breaker_closed_state(self):
        """测试熔断器关闭状态"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        
        def success_function():
            return "success"
        
        result = cb.call(success_function)
        assert result == "success"
        assert cb.state == 'CLOSED'
        assert cb.failure_count == 0
    
    def test_circuit_breaker_open_state(self):
        """测试熔断器开启状态"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        def failing_function():
            raise Exception("Test error")
        
        # 触发足够的失败次数
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_function)
        
        assert cb.state == 'OPEN'
        assert cb.failure_count == 2
        
        # 现在应该直接抛出熔断器异常
        with pytest.raises(APIException, match="Circuit breaker is OPEN"):
            cb.call(failing_function)
    
    def test_circuit_breaker_half_open_state(self):
        """测试熔断器半开状态"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        
        def failing_function():
            raise Exception("Test error")
        
        def success_function():
            return "success"
        
        # 触发熔断器开启
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_function)
        
        assert cb.state == 'OPEN'
        
        # 等待恢复超时
        time.sleep(0.2)
        
        # 下一次调用应该进入半开状态，如果成功则重置
        result = cb.call(success_function)
        assert result == "success"
        assert cb.state == 'CLOSED'
        assert cb.failure_count == 0
    
    def test_circuit_breaker_recovery_failure(self):
        """测试熔断器恢复失败"""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        
        def failing_function():
            raise Exception("Test error")
        
        # 触发熔断器开启
        with pytest.raises(Exception):
            cb.call(failing_function)
        
        assert cb.state == 'OPEN'
        
        # 等待恢复超时
        time.sleep(0.2)
        
        # 尝试恢复但失败
        with pytest.raises(Exception):
            cb.call(failing_function)
        
        # 应该重新进入开启状态
        assert cb.state == 'OPEN'


class TestIntegrationScenarios:
    """集成场景测试类"""
    
    def test_retry_with_circuit_breaker(self):
        """测试重试机制与熔断器的集成"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        call_count = 0
        
        @retry_on_failure(max_retries=2, delay=0.01)
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkException("Network error")
            return "success"
        
        # 使用熔断器调用重试函数
        result = cb.call(test_function)
        assert result == "success"
        assert call_count == 3
        assert cb.state == 'CLOSED'
    
    def test_validation_with_error_parsing(self):
        """测试验证与错误解析的集成"""
        # 测试符号验证后的错误解析
        try:
            symbol = validate_symbol('BTCUSDT')
            assert symbol == 'BTCUSDT'
            
            # 模拟API错误响应
            error_response = {'code': -2010, 'msg': 'Account has insufficient balance'}
            error = parse_binance_error(error_response)
            raise error
            
        except ValidationException as e:
            assert "insufficient balance" in str(e).lower()
    
    def test_rate_limit_with_retry(self):
        """测试速率限制与重试的集成"""
        call_times = []
        
        @rate_limit(calls_per_second=5.0)  # 每秒5次调用
        @retry_on_failure(max_retries=1, delay=0.01)
        def test_function():
            call_times.append(time.time())
            if len(call_times) == 1:
                raise NetworkException("First call fails")
            return "success"
        
        result = test_function()
        assert result == "success"
        assert len(call_times) == 2
        
        # 检查速率限制是否生效
        if len(call_times) >= 2:
            time_diff = call_times[1] - call_times[0]
            assert time_diff >= 0.2  # 至少间隔0.2秒