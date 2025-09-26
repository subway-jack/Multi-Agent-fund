# -*- coding: utf-8 -*-
"""
币安现货交易API
"""

import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal

from ..exceptions import ValidationException, AuthenticationException

logger = logging.getLogger(__name__)


class SpotAPI:
    """币安现货交易API"""
    
    def __init__(self, client):
        """
        初始化现货交易API
        
        Args:
            client: BinanceAPI客户端实例
        """
        self.client = client
    
    def _require_auth(self):
        """检查是否有API密钥"""
        if not self.client.api_key or not self.client.api_secret:
            raise AuthenticationException("API key and secret required for trading operations")
    
    def create_order(self, symbol: str, side: str, order_type: str, 
                    quantity: float = None, quote_order_qty: float = None,
                    price: float = None, time_in_force: str = 'GTC',
                    stop_price: float = None, iceberg_qty: float = None,
                    new_order_resp_type: str = 'ACK') -> Dict[str, Any]:
        """
        创建新订单
        
        Args:
            symbol: 交易对符号
            side: 订单方向 ('BUY' 或 'SELL')
            order_type: 订单类型 ('LIMIT', 'MARKET', 'STOP_LOSS', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT', 'LIMIT_MAKER')
            quantity: 订单数量
            quote_order_qty: 报价资产数量 (仅适用于MARKET订单)
            price: 订单价格 (LIMIT订单必需)
            time_in_force: 订单有效期 ('GTC', 'IOC', 'FOK')
            stop_price: 止损价格 (STOP_LOSS和TAKE_PROFIT订单必需)
            iceberg_qty: 冰山订单数量
            new_order_resp_type: 响应类型 ('ACK', 'RESULT', 'FULL')
            
        Returns:
            订单创建结果
        """
        self._require_auth()
        
        params = {
            'symbol': symbol.upper(),
            'side': side.upper(),
            'type': order_type.upper(),
            'newOrderRespType': new_order_resp_type
        }
        
        # 验证必需参数
        if order_type.upper() in ['LIMIT', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT', 'LIMIT_MAKER']:
            if not price:
                raise ValidationException("Price is required for LIMIT orders")
            params['price'] = str(price)
            params['timeInForce'] = time_in_force
        
        if order_type.upper() in ['STOP_LOSS', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT']:
            if not stop_price:
                raise ValidationException("Stop price is required for STOP orders")
            params['stopPrice'] = str(stop_price)
        
        if quantity:
            params['quantity'] = str(quantity)
        elif quote_order_qty and order_type.upper() == 'MARKET':
            params['quoteOrderQty'] = str(quote_order_qty)
        else:
            raise ValidationException("Either quantity or quoteOrderQty is required")
        
        if iceberg_qty:
            params['icebergQty'] = str(iceberg_qty)
        
        return self.client._make_request('POST', '/api/v3/order', params, signed=True)
    
    def create_test_order(self, symbol: str, side: str, order_type: str, 
                         quantity: float = None, price: float = None,
                         time_in_force: str = 'GTC') -> Dict[str, Any]:
        """
        创建测试订单 (不会实际执行)
        
        Args:
            symbol: 交易对符号
            side: 订单方向
            order_type: 订单类型
            quantity: 订单数量
            price: 订单价格
            time_in_force: 订单有效期
            
        Returns:
            测试结果
        """
        self._require_auth()
        
        params = {
            'symbol': symbol.upper(),
            'side': side.upper(),
            'type': order_type.upper()
        }
        
        if quantity:
            params['quantity'] = str(quantity)
        if price:
            params['price'] = str(price)
        if order_type.upper() == 'LIMIT':
            params['timeInForce'] = time_in_force
        
        return self.client._make_request('POST', '/api/v3/order/test', params, signed=True)
    
    def get_order(self, symbol: str, order_id: int = None, 
                 orig_client_order_id: str = None) -> Dict[str, Any]:
        """
        查询订单状态
        
        Args:
            symbol: 交易对符号
            order_id: 订单ID
            orig_client_order_id: 客户端订单ID
            
        Returns:
            订单信息
        """
        self._require_auth()
        
        params = {'symbol': symbol.upper()}
        
        if order_id:
            params['orderId'] = order_id
        elif orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        else:
            raise ValidationException("Either orderId or origClientOrderId is required")
        
        return self.client._make_request('GET', '/api/v3/order', params, signed=True)
    
    def cancel_order(self, symbol: str, order_id: int = None,
                    orig_client_order_id: str = None,
                    new_client_order_id: str = None) -> Dict[str, Any]:
        """
        取消订单
        
        Args:
            symbol: 交易对符号
            order_id: 订单ID
            orig_client_order_id: 客户端订单ID
            new_client_order_id: 新的客户端订单ID
            
        Returns:
            取消结果
        """
        self._require_auth()
        
        params = {'symbol': symbol.upper()}
        
        if order_id:
            params['orderId'] = order_id
        elif orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        else:
            raise ValidationException("Either orderId or origClientOrderId is required")
        
        if new_client_order_id:
            params['newClientOrderId'] = new_client_order_id
        
        return self.client._make_request('DELETE', '/api/v3/order', params, signed=True)
    
    def cancel_all_orders(self, symbol: str) -> List[Dict[str, Any]]:
        """
        取消指定交易对的所有挂单
        
        Args:
            symbol: 交易对符号
            
        Returns:
            取消结果列表
        """
        self._require_auth()
        
        params = {'symbol': symbol.upper()}
        return self.client._make_request('DELETE', '/api/v3/openOrders', params, signed=True)
    
    def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """
        获取当前挂单
        
        Args:
            symbol: 可选，交易对符号。如果不提供，返回所有交易对的挂单
            
        Returns:
            挂单列表
        """
        self._require_auth()
        
        params = {}
        if symbol:
            params['symbol'] = symbol.upper()
        
        return self.client._make_request('GET', '/api/v3/openOrders', params, signed=True)
    
    def get_all_orders(self, symbol: str, order_id: int = None,
                      start_time: int = None, end_time: int = None,
                      limit: int = 500) -> List[Dict[str, Any]]:
        """
        获取所有订单 (包括历史订单)
        
        Args:
            symbol: 交易对符号
            order_id: 起始订单ID
            start_time: 开始时间戳 (毫秒)
            end_time: 结束时间戳 (毫秒)
            limit: 返回数量 (最大1000)
            
        Returns:
            订单列表
        """
        self._require_auth()
        
        params = {
            'symbol': symbol.upper(),
            'limit': min(limit, 1000)
        }
        
        if order_id:
            params['orderId'] = order_id
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        return self.client._make_request('GET', '/api/v3/allOrders', params, signed=True)
    
    def get_my_trades(self, symbol: str, order_id: int = None,
                     start_time: int = None, end_time: int = None,
                     from_id: int = None, limit: int = 500) -> List[Dict[str, Any]]:
        """
        获取账户交易历史
        
        Args:
            symbol: 交易对符号
            order_id: 订单ID
            start_time: 开始时间戳 (毫秒)
            end_time: 结束时间戳 (毫秒)
            from_id: 起始交易ID
            limit: 返回数量 (最大1000)
            
        Returns:
            交易历史列表
        """
        self._require_auth()
        
        params = {
            'symbol': symbol.upper(),
            'limit': min(limit, 1000)
        }
        
        if order_id:
            params['orderId'] = order_id
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        if from_id:
            params['fromId'] = from_id
        
        return self.client._make_request('GET', '/api/v3/myTrades', params, signed=True)
    
    def get_order_count_usage(self) -> List[Dict[str, Any]]:
        """
        获取当前订单数量使用情况
        
        Returns:
            订单数量使用情况
        """
        self._require_auth()
        
        return self.client._make_request('GET', '/api/v3/rateLimit/order', signed=True)
    
    # 便捷方法
    def buy_market(self, symbol: str, quantity: float = None, 
                  quote_order_qty: float = None) -> Dict[str, Any]:
        """
        市价买入
        
        Args:
            symbol: 交易对符号
            quantity: 买入数量
            quote_order_qty: 使用报价资产的数量
            
        Returns:
            订单结果
        """
        return self.create_order(
            symbol=symbol,
            side='BUY',
            order_type='MARKET',
            quantity=quantity,
            quote_order_qty=quote_order_qty
        )
    
    def sell_market(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """
        市价卖出
        
        Args:
            symbol: 交易对符号
            quantity: 卖出数量
            
        Returns:
            订单结果
        """
        return self.create_order(
            symbol=symbol,
            side='SELL',
            order_type='MARKET',
            quantity=quantity
        )
    
    def buy_limit(self, symbol: str, quantity: float, price: float,
                 time_in_force: str = 'GTC') -> Dict[str, Any]:
        """
        限价买入
        
        Args:
            symbol: 交易对符号
            quantity: 买入数量
            price: 买入价格
            time_in_force: 订单有效期
            
        Returns:
            订单结果
        """
        return self.create_order(
            symbol=symbol,
            side='BUY',
            order_type='LIMIT',
            quantity=quantity,
            price=price,
            time_in_force=time_in_force
        )
    
    def sell_limit(self, symbol: str, quantity: float, price: float,
                  time_in_force: str = 'GTC') -> Dict[str, Any]:
        """
        限价卖出
        
        Args:
            symbol: 交易对符号
            quantity: 卖出数量
            price: 卖出价格
            time_in_force: 订单有效期
            
        Returns:
            订单结果
        """
        return self.create_order(
            symbol=symbol,
            side='SELL',
            order_type='LIMIT',
            quantity=quantity,
            price=price,
            time_in_force=time_in_force
        )