# -*- coding: utf-8 -*-
"""
币安API测试用例
"""

import pytest
import os
import time
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from src.api import BinanceAPI
from src.api.exceptions import (
    APIException,
    RateLimitException,
    AuthenticationException,
    NetworkException,
    ServerException,
    ValidationException
)


class TestBinanceAPI:
    """币安API测试类"""
    
    @pytest.fixture
    def api_client(self):
        """创建测试用的API客户端"""
        return BinanceAPI(
            api_key="test_api_key",
            api_secret="test_api_secret",
            testnet=True
        )
    
    @pytest.fixture
    def api_client_no_auth(self):
        """创建无认证的API客户端"""
        return BinanceAPI(testnet=True)
    
    def test_init_with_credentials(self):
        """测试使用凭据初始化"""
        api = BinanceAPI(
            api_key="test_key",
            api_secret="test_secret",
            testnet=True
        )
        
        assert api.api_key == "test_key"
        assert api.api_secret == "test_secret"
        assert api.testnet is True
        assert "testnet" in api.base_url
    
    def test_init_from_env(self):
        """测试从环境变量初始化"""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'env_key',
            'BINANCE_API_SECRET': 'env_secret'
        }):
            api = BinanceAPI()
            assert api.api_key == "env_key"
            assert api.api_secret == "env_secret"
    
    def test_init_mainnet(self):
        """测试主网初始化"""
        api = BinanceAPI(testnet=False)
        assert "testnet" not in api.base_url
        assert "api.binance.com" in api.base_url
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, api_client):
        """测试连接成功"""
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = {}
            
            result = api_client.test_connection()
            
            assert result is True
            mock_request.assert_called_once_with('GET', '/api/v3/ping')
    
    @pytest.mark.asyncio
    async def test_test_connection_failure(self, api_client):
        """测试连接失败"""
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.side_effect = NetworkException("Connection failed")
            
            result = api_client.test_connection()
            
            assert result is False
    
    def test_get_server_time(self, api_client):
        """测试获取服务器时间"""
        expected_time = int(time.time() * 1000)
        
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = {'serverTime': expected_time}
            
            result = api_client.get_server_time()
            
            assert result == expected_time
            mock_request.assert_called_once_with('GET', '/api/v3/time')
    
    def test_get_exchange_info(self, api_client):
        """测试获取交易所信息"""
        expected_info = {
            'timezone': 'UTC',
            'serverTime': 1234567890,
            'symbols': []
        }
        
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = expected_info
            
            result = api_client.get_exchange_info()
            
            assert result == expected_info
            mock_request.assert_called_once_with('GET', '/api/v3/exchangeInfo')
    
    def test_get_exchange_info_with_symbol(self, api_client):
        """测试获取特定交易对信息"""
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = {'symbols': []}
            
            api_client.get_exchange_info('BTCUSDT')
            
            mock_request.assert_called_once_with(
                'GET', 
                '/api/v3/exchangeInfo',
                {'symbol': 'BTCUSDT'}
            )
    
    def test_get_system_status(self, api_client):
        """测试获取系统状态"""
        expected_status = {
            'status': 0,
            'msg': 'normal'
        }
        
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = expected_status
            
            result = api_client.get_system_status()
            
            assert result == expected_status
            mock_request.assert_called_once_with('GET', '/sapi/v1/system/status')


class TestBinanceMarketAPI:
    """币安市场数据API测试类"""
    
    @pytest.fixture
    def api_client(self):
        """创建测试用的API客户端"""
        return BinanceAPI(testnet=True)
    
    def test_get_order_book(self, api_client):
        """测试获取订单簿"""
        expected_data = {
            'lastUpdateId': 123456,
            'bids': [['50000.00', '1.00']],
            'asks': [['50001.00', '1.00']]
        }
        
        with patch.object(api_client.market, 'get_order_book') as mock_method:
            mock_method.return_value = expected_data
            
            result = api_client.market.get_order_book('BTCUSDT')
            
            assert result == expected_data
            mock_method.assert_called_once_with('BTCUSDT', limit=100)
    
    def test_get_recent_trades(self, api_client):
        """测试获取最近交易"""
        expected_trades = [
            {
                'id': 123456,
                'price': '50000.00',
                'qty': '1.00',
                'time': 1234567890,
                'isBuyerMaker': True
            }
        ]
        
        with patch.object(api_client.market, 'get_recent_trades') as mock_method:
            mock_method.return_value = expected_trades
            
            result = api_client.market.get_recent_trades('BTCUSDT')
            
            assert result == expected_trades
            mock_method.assert_called_once_with('BTCUSDT', limit=500)
    
    def test_get_kline_data(self, api_client):
        """测试获取K线数据"""
        expected_klines = [
            [
                1234567890,  # 开盘时间
                '50000.00',  # 开盘价
                '51000.00',  # 最高价
                '49000.00',  # 最低价
                '50500.00',  # 收盘价
                '100.00',    # 成交量
                1234567950,  # 收盘时间
                '5050000.00',  # 成交额
                1000,        # 成交笔数
                '50.00',     # 主动买入成交量
                '2525000.00',  # 主动买入成交额
                '0'          # 忽略
            ]
        ]
        
        with patch.object(api_client.market, 'get_kline_data') as mock_method:
            mock_method.return_value = expected_klines
            
            result = api_client.market.get_kline_data('BTCUSDT', '1h')
            
            assert result == expected_klines
            mock_method.assert_called_once_with('BTCUSDT', '1h', limit=500)
    
    def test_get_24hr_ticker(self, api_client):
        """测试获取24小时价格变动统计"""
        expected_ticker = {
            'symbol': 'BTCUSDT',
            'priceChange': '1000.00',
            'priceChangePercent': '2.00',
            'weightedAvgPrice': '50250.00',
            'prevClosePrice': '50000.00',
            'lastPrice': '51000.00',
            'lastQty': '1.00',
            'bidPrice': '50999.00',
            'askPrice': '51001.00',
            'openPrice': '50000.00',
            'highPrice': '52000.00',
            'lowPrice': '49000.00',
            'volume': '10000.00',
            'quoteVolume': '502500000.00',
            'openTime': 1234567890,
            'closeTime': 1234654290,
            'firstId': 123456,
            'lastId': 234567,
            'count': 111111
        }
        
        with patch.object(api_client.market, 'get_24hr_ticker') as mock_method:
            mock_method.return_value = expected_ticker
            
            result = api_client.market.get_24hr_ticker('BTCUSDT')
            
            assert result == expected_ticker
            mock_method.assert_called_once_with('BTCUSDT')
    
    def test_get_symbol_price(self, api_client):
        """测试获取最新价格"""
        expected_price = {
            'symbol': 'BTCUSDT',
            'price': '51000.00'
        }
        
        with patch.object(api_client.market, 'get_symbol_price') as mock_method:
            mock_method.return_value = expected_price
            
            result = api_client.market.get_symbol_price('BTCUSDT')
            
            assert result == expected_price
            mock_method.assert_called_once_with('BTCUSDT')


class TestBinanceSpotAPI:
    """币安现货交易API测试类"""
    
    @pytest.fixture
    def api_client(self):
        """创建测试用的API客户端"""
        return BinanceAPI(
            api_key="test_api_key",
            api_secret="test_api_secret",
            testnet=True
        )
    
    def test_create_order_market_buy(self, api_client):
        """测试创建市价买单"""
        expected_order = {
            'symbol': 'BTCUSDT',
            'orderId': 123456,
            'orderListId': -1,
            'clientOrderId': 'test_order_id',
            'transactTime': 1234567890,
            'price': '0.00000000',
            'origQty': '0.00100000',
            'executedQty': '0.00100000',
            'cummulativeQuoteQty': '51.00000000',
            'status': 'FILLED',
            'timeInForce': 'GTC',
            'type': 'MARKET',
            'side': 'BUY'
        }
        
        with patch.object(api_client.spot, 'create_order') as mock_method:
            mock_method.return_value = expected_order
            
            result = api_client.spot.buy_market('BTCUSDT', quote_order_qty=51.0)
            
            assert result == expected_order
            mock_method.assert_called_once_with(
                symbol='BTCUSDT',
                side='BUY',
                order_type='MARKET',
                quantity=None,
                quote_order_qty=51.0
            )
    
    def test_create_order_limit_sell(self, api_client):
        """测试创建限价卖单"""
        expected_order = {
            'symbol': 'BTCUSDT',
            'orderId': 123457,
            'orderListId': -1,
            'clientOrderId': 'test_order_id_2',
            'transactTime': 1234567890,
            'price': '52000.00000000',
            'origQty': '0.00100000',
            'executedQty': '0.00000000',
            'cummulativeQuoteQty': '0.00000000',
            'status': 'NEW',
            'timeInForce': 'GTC',
            'type': 'LIMIT',
            'side': 'SELL'
        }
        
        with patch.object(api_client.spot, 'create_order') as mock_method:
            mock_method.return_value = expected_order
            
            result = api_client.spot.sell_limit('BTCUSDT', 0.001, 52000.0)
            
            assert result == expected_order
            mock_method.assert_called_once_with(
                symbol='BTCUSDT',
                side='SELL',
                order_type='LIMIT',
                quantity=0.001,
                price=52000.0,
                time_in_force='GTC'
            )
    
    def test_get_order(self, api_client):
        """测试查询订单"""
        expected_order = {
            'symbol': 'BTCUSDT',
            'orderId': 123456,
            'orderListId': -1,
            'clientOrderId': 'test_order_id',
            'price': '52000.00000000',
            'origQty': '0.00100000',
            'executedQty': '0.00000000',
            'cummulativeQuoteQty': '0.00000000',
            'status': 'NEW',
            'timeInForce': 'GTC',
            'type': 'LIMIT',
            'side': 'SELL',
            'stopPrice': '0.00000000',
            'icebergQty': '0.00000000',
            'time': 1234567890,
            'updateTime': 1234567890,
            'isWorking': True,
            'origQuoteOrderQty': '0.00000000'
        }
        
        with patch.object(api_client.spot, 'get_order') as mock_method:
            mock_method.return_value = expected_order
            
            result = api_client.spot.get_order('BTCUSDT', order_id=123456)
            
            assert result == expected_order
            mock_method.assert_called_once_with('BTCUSDT', order_id=123456)
    
    def test_cancel_order(self, api_client):
        """测试取消订单"""
        expected_result = {
            'symbol': 'BTCUSDT',
            'origClientOrderId': 'test_order_id',
            'orderId': 123456,
            'orderListId': -1,
            'clientOrderId': 'cancel_test_order_id',
            'price': '52000.00000000',
            'origQty': '0.00100000',
            'executedQty': '0.00000000',
            'cummulativeQuoteQty': '0.00000000',
            'status': 'CANCELED',
            'timeInForce': 'GTC',
            'type': 'LIMIT',
            'side': 'SELL'
        }
        
        with patch.object(api_client.spot, 'cancel_order') as mock_method:
            mock_method.return_value = expected_result
            
            result = api_client.spot.cancel_order('BTCUSDT', order_id=123456)
            
            assert result == expected_result
            mock_method.assert_called_once_with('BTCUSDT', order_id=123456)
    
    def test_get_open_orders(self, api_client):
        """测试获取当前挂单"""
        expected_orders = [
            {
                'symbol': 'BTCUSDT',
                'orderId': 123456,
                'orderListId': -1,
                'clientOrderId': 'test_order_id',
                'price': '52000.00000000',
                'origQty': '0.00100000',
                'executedQty': '0.00000000',
                'cummulativeQuoteQty': '0.00000000',
                'status': 'NEW',
                'timeInForce': 'GTC',
                'type': 'LIMIT',
                'side': 'SELL',
                'stopPrice': '0.00000000',
                'icebergQty': '0.00000000',
                'time': 1234567890,
                'updateTime': 1234567890,
                'isWorking': True,
                'origQuoteOrderQty': '0.00000000'
            }
        ]
        
        with patch.object(api_client.spot, 'get_open_orders') as mock_method:
            mock_method.return_value = expected_orders
            
            result = api_client.spot.get_open_orders('BTCUSDT')
            
            assert result == expected_orders
            mock_method.assert_called_once_with('BTCUSDT')


class TestBinanceAccountAPI:
    """币安账户API测试类"""
    
    @pytest.fixture
    def api_client(self):
        """创建测试用的API客户端"""
        return BinanceAPI(
            api_key="test_api_key",
            api_secret="test_api_secret",
            testnet=True
        )
    
    def test_get_account_info(self, api_client):
        """测试获取账户信息"""
        expected_account = {
            'makerCommission': 15,
            'takerCommission': 15,
            'buyerCommission': 0,
            'sellerCommission': 0,
            'canTrade': True,
            'canWithdraw': True,
            'canDeposit': True,
            'updateTime': 1234567890,
            'accountType': 'SPOT',
            'balances': [
                {
                    'asset': 'BTC',
                    'free': '0.00100000',
                    'locked': '0.00000000'
                },
                {
                    'asset': 'USDT',
                    'free': '1000.00000000',
                    'locked': '0.00000000'
                }
            ],
            'permissions': ['SPOT']
        }
        
        with patch.object(api_client.account, 'get_account_info') as mock_method:
            mock_method.return_value = expected_account
            
            result = api_client.account.get_account_info()
            
            assert result == expected_account
            mock_method.assert_called_once()
    
    def test_get_balance(self, api_client):
        """测试获取余额"""
        expected_balances = [
            {
                'asset': 'BTC',
                'free': '0.00100000',
                'locked': '0.00000000'
            },
            {
                'asset': 'USDT',
                'free': '1000.00000000',
                'locked': '0.00000000'
            }
        ]
        
        with patch.object(api_client.account, 'get_balance') as mock_method:
            mock_method.return_value = expected_balances
            
            result = api_client.account.get_balance()
            
            assert result == expected_balances
            mock_method.assert_called_once_with(None)
    
    def test_get_balance_by_asset(self, api_client):
        """测试获取特定资产余额"""
        expected_balance = {
            'asset': 'BTC',
            'free': '0.00100000',
            'locked': '0.00000000'
        }
        
        with patch.object(api_client.account, 'get_balance_by_asset') as mock_method:
            mock_method.return_value = expected_balance
            
            result = api_client.account.get_balance_by_asset('BTC')
            
            assert result == expected_balance
            mock_method.assert_called_once_with('BTC')
    
    def test_has_sufficient_balance(self, api_client):
        """测试检查余额是否充足"""
        with patch.object(api_client.account, 'has_sufficient_balance') as mock_method:
            mock_method.return_value = True
            
            result = api_client.account.has_sufficient_balance('USDT', 100.0)
            
            assert result is True
            mock_method.assert_called_once_with('USDT', 100.0)


class TestExceptionHandling:
    """异常处理测试类"""
    
    @pytest.fixture
    def api_client(self):
        """创建测试用的API客户端"""
        return BinanceAPI(testnet=True)
    
    def test_authentication_exception(self, api_client):
        """测试认证异常"""
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.side_effect = AuthenticationException("Invalid API key")
            
            with pytest.raises(AuthenticationException):
                api_client.account.get_account_info()
    
    def test_rate_limit_exception(self, api_client):
        """测试速率限制异常"""
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.side_effect = RateLimitException("Rate limit exceeded")
            
            with pytest.raises(RateLimitException):
                api_client.market.get_symbol_price('BTCUSDT')
    
    def test_validation_exception(self, api_client):
        """测试验证异常"""
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.side_effect = ValidationException("Invalid symbol")
            
            with pytest.raises(ValidationException):
                api_client.market.get_symbol_price('INVALID')
    
    def test_network_exception(self, api_client):
        """测试网络异常"""
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.side_effect = NetworkException("Connection timeout")
            
            with pytest.raises(NetworkException):
                api_client.test_connection()
    
    def test_server_exception(self, api_client):
        """测试服务器异常"""
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.side_effect = ServerException("Internal server error")
            
            with pytest.raises(ServerException):
                api_client.get_server_time()


@pytest.mark.integration
class TestBinanceAPIIntegration:
    """币安API集成测试类 (需要网络连接)"""
    
    @pytest.fixture
    def api_client(self):
        """创建测试网API客户端"""
        return BinanceAPI(testnet=True)
    
    @pytest.mark.network
    def test_ping_connection(self, api_client):
        """测试连接 (集成测试)"""
        result = api_client.test_connection()
        assert isinstance(result, bool)
    
    @pytest.mark.network
    def test_get_server_time_integration(self, api_client):
        """测试获取服务器时间 (集成测试)"""
        server_time = api_client.get_server_time()
        assert isinstance(server_time, int)
        assert server_time > 0
    
    @pytest.mark.network
    def test_get_exchange_info_integration(self, api_client):
        """测试获取交易所信息 (集成测试)"""
        exchange_info = api_client.get_exchange_info()
        assert 'timezone' in exchange_info
        assert 'serverTime' in exchange_info
        assert 'symbols' in exchange_info
    
    @pytest.mark.network
    def test_get_symbol_price_integration(self, api_client):
        """测试获取价格 (集成测试)"""
        price_data = api_client.market.get_symbol_price('BTCUSDT')
        assert 'symbol' in price_data
        assert 'price' in price_data
        assert price_data['symbol'] == 'BTCUSDT'
        assert float(price_data['price']) > 0
    
    @pytest.mark.network
    def test_get_order_book_integration(self, api_client):
        """测试获取订单簿 (集成测试)"""
        order_book = api_client.market.get_order_book('BTCUSDT', limit=10)
        assert 'lastUpdateId' in order_book
        assert 'bids' in order_book
        assert 'asks' in order_book
        assert len(order_book['bids']) <= 10
        assert len(order_book['asks']) <= 10