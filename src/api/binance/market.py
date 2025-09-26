# -*- coding: utf-8 -*-
"""
币安市场数据API
"""

import logging
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger(__name__)


class MarketDataAPI:
    """币安市场数据API"""
    
    def __init__(self, client):
        """
        初始化市场数据API
        
        Args:
            client: BinanceAPI客户端实例
        """
        self.client = client
    
    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        获取订单簿深度信息
        
        Args:
            symbol: 交易对符号，如 'BTCUSDT'
            limit: 返回的深度数量 (5, 10, 20, 50, 100, 500, 1000, 5000)
            
        Returns:
            订单簿数据
        """
        params = {
            'symbol': symbol.upper(),
            'limit': limit
        }
        
        return self.client._make_request('GET', '/api/v3/depth', params)
    
    def get_recent_trades(self, symbol: str, limit: int = 500) -> List[Dict[str, Any]]:
        """
        获取最近成交记录
        
        Args:
            symbol: 交易对符号
            limit: 返回的记录数量 (最大1000)
            
        Returns:
            成交记录列表
        """
        params = {
            'symbol': symbol.upper(),
            'limit': min(limit, 1000)
        }
        
        return self.client._make_request('GET', '/api/v3/trades', params)
    
    def get_historical_trades(self, symbol: str, limit: int = 500, 
                            from_id: int = None) -> List[Dict[str, Any]]:
        """
        获取历史成交记录 (需要API密钥)
        
        Args:
            symbol: 交易对符号
            limit: 返回的记录数量 (最大1000)
            from_id: 从指定交易ID开始获取
            
        Returns:
            历史成交记录列表
        """
        params = {
            'symbol': symbol.upper(),
            'limit': min(limit, 1000)
        }
        
        if from_id:
            params['fromId'] = from_id
        
        return self.client._make_request('GET', '/api/v3/historicalTrades', params)
    
    def get_agg_trades(self, symbol: str, limit: int = 500, 
                      start_time: int = None, end_time: int = None,
                      from_id: int = None) -> List[Dict[str, Any]]:
        """
        获取聚合成交记录
        
        Args:
            symbol: 交易对符号
            limit: 返回的记录数量 (最大1000)
            start_time: 开始时间戳 (毫秒)
            end_time: 结束时间戳 (毫秒)
            from_id: 从指定聚合交易ID开始获取
            
        Returns:
            聚合成交记录列表
        """
        params = {
            'symbol': symbol.upper(),
            'limit': min(limit, 1000)
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        if from_id:
            params['fromId'] = from_id
        
        return self.client._make_request('GET', '/api/v3/aggTrades', params)
    
    def get_klines(self, symbol: str, interval: str, limit: int = 500,
                  start_time: int = None, end_time: int = None) -> List[List]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对符号
            interval: K线间隔 ('1s', '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M')
            limit: 返回的数量 (最大1000)
            start_time: 开始时间戳 (毫秒)
            end_time: 结束时间戳 (毫秒)
            
        Returns:
            K线数据列表，每个元素包含: [开盘时间, 开盘价, 最高价, 最低价, 收盘价, 成交量, 收盘时间, 成交额, 成交笔数, 主动买入成交量, 主动买入成交额, 忽略]
        """
        params = {
            'symbol': symbol.upper(),
            'interval': interval,
            'limit': min(limit, 1000)
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        return self.client._make_request('GET', '/api/v3/klines', params)
    
    def get_avg_price(self, symbol: str) -> Dict[str, Any]:
        """
        获取当前平均价格
        
        Args:
            symbol: 交易对符号
            
        Returns:
            平均价格信息
        """
        params = {'symbol': symbol.upper()}
        return self.client._make_request('GET', '/api/v3/avgPrice', params)
    
    def get_ticker_24hr(self, symbol: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        获取24小时价格变动统计
        
        Args:
            symbol: 可选，交易对符号。如果不提供，返回所有交易对的统计
            
        Returns:
            24小时统计数据
        """
        params = {}
        if symbol:
            params['symbol'] = symbol.upper()
        
        return self.client._make_request('GET', '/api/v3/ticker/24hr', params)
    
    def get_ticker_price(self, symbol: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        获取最新价格
        
        Args:
            symbol: 可选，交易对符号。如果不提供，返回所有交易对的价格
            
        Returns:
            价格信息
        """
        params = {}
        if symbol:
            params['symbol'] = symbol.upper()
        
        return self.client._make_request('GET', '/api/v3/ticker/price', params)
    
    def get_ticker_book(self, symbol: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        获取最优挂单价格
        
        Args:
            symbol: 可选，交易对符号。如果不提供，返回所有交易对的最优挂单
            
        Returns:
            最优挂单价格信息
        """
        params = {}
        if symbol:
            params['symbol'] = symbol.upper()
        
        return self.client._make_request('GET', '/api/v3/ticker/bookTicker', params)
    
    def get_rolling_window_stats(self, symbol: str = None, window_size: str = '1d') -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        获取滚动窗口价格变动统计
        
        Args:
            symbol: 可选，交易对符号
            window_size: 窗口大小 ('1m', '2m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '2d', '3d', '7d', '30d')
            
        Returns:
            滚动窗口统计数据
        """
        params = {'windowSize': window_size}
        if symbol:
            params['symbol'] = symbol.upper()
        
        return self.client._make_request('GET', '/api/v3/ticker', params)
    
    def get_price_change_stats(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """
        批量获取价格变动统计
        
        Args:
            symbols: 交易对符号列表
            
        Returns:
            价格变动统计列表
        """
        if symbols:
            # 批量查询特定交易对
            results = []
            for symbol in symbols:
                try:
                    result = self.get_ticker_24hr(symbol)
                    results.append(result)
                except Exception as e:
                    logger.warning(f"获取 {symbol} 统计数据失败: {e}")
            return results
        else:
            # 获取所有交易对统计
            return self.get_ticker_24hr()
    
    def get_market_summary(self, symbols: List[str] = None) -> Dict[str, Any]:
        """
        获取市场概览
        
        Args:
            symbols: 可选，指定交易对列表
            
        Returns:
            市场概览数据
        """
        if symbols:
            # 获取指定交易对的数据
            tickers = []
            for symbol in symbols:
                try:
                    ticker = self.get_ticker_24hr(symbol)
                    tickers.append(ticker)
                except Exception as e:
                    logger.warning(f"获取 {symbol} 数据失败: {e}")
        else:
            # 获取所有交易对数据
            tickers = self.get_ticker_24hr()
        
        if not isinstance(tickers, list):
            tickers = [tickers]
        
        # 计算市场统计
        total_volume = sum(float(t.get('volume', 0)) for t in tickers)
        total_quote_volume = sum(float(t.get('quoteVolume', 0)) for t in tickers)
        gainers = [t for t in tickers if float(t.get('priceChangePercent', 0)) > 0]
        losers = [t for t in tickers if float(t.get('priceChangePercent', 0)) < 0]
        
        return {
            'total_pairs': len(tickers),
            'total_volume': total_volume,
            'total_quote_volume': total_quote_volume,
            'gainers_count': len(gainers),
            'losers_count': len(losers),
            'top_gainers': sorted(gainers, key=lambda x: float(x.get('priceChangePercent', 0)), reverse=True)[:10],
            'top_losers': sorted(losers, key=lambda x: float(x.get('priceChangePercent', 0)))[:10],
            'highest_volume': sorted(tickers, key=lambda x: float(x.get('volume', 0)), reverse=True)[:10]
        }