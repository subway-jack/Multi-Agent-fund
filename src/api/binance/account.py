# -*- coding: utf-8 -*-
"""
币安账户信息API
"""

import logging
from typing import Dict, List, Optional, Any

from ..exceptions import AuthenticationException

logger = logging.getLogger(__name__)


class AccountAPI:
    """币安账户信息API"""
    
    def __init__(self, client):
        """
        初始化账户API
        
        Args:
            client: BinanceAPI客户端实例
        """
        self.client = client
    
    def _require_auth(self):
        """检查是否有API密钥"""
        if not self.client.api_key or not self.client.api_secret:
            raise AuthenticationException("API key and secret required for account operations")
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        获取账户信息
        
        Returns:
            账户信息，包括余额、权限等
        """
        self._require_auth()
        
        return self.client._make_request('GET', '/api/v3/account', signed=True)
    
    def get_account_status(self) -> Dict[str, Any]:
        """
        获取账户状态
        
        Returns:
            账户状态信息
        """
        self._require_auth()
        
        return self.client._make_request('GET', '/sapi/v1/account/status', signed=True)
    
    def get_api_trading_status(self) -> Dict[str, Any]:
        """
        获取API交易状态
        
        Returns:
            API交易状态
        """
        self._require_auth()
        
        return self.client._make_request('GET', '/sapi/v1/account/apiTradingStatus', signed=True)
    
    def get_dust_log(self, start_time: int = None, end_time: int = None) -> Dict[str, Any]:
        """
        获取小额资产转换BNB历史
        
        Args:
            start_time: 开始时间戳 (毫秒)
            end_time: 结束时间戳 (毫秒)
            
        Returns:
            小额资产转换历史
        """
        self._require_auth()
        
        params = {}
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        return self.client._make_request('GET', '/sapi/v1/asset/dribblet', params, signed=True)
    
    def dust_transfer(self, assets: List[str]) -> Dict[str, Any]:
        """
        小额资产转换BNB
        
        Args:
            assets: 要转换的资产列表
            
        Returns:
            转换结果
        """
        self._require_auth()
        
        params = {
            'asset': ','.join(assets)
        }
        
        return self.client._make_request('POST', '/sapi/v1/asset/dust', params, signed=True)
    
    def get_asset_dividend_record(self, asset: str = None, start_time: int = None,
                                 end_time: int = None, limit: int = 20) -> Dict[str, Any]:
        """
        获取资产分红记录
        
        Args:
            asset: 资产名称
            start_time: 开始时间戳 (毫秒)
            end_time: 结束时间戳 (毫秒)
            limit: 返回数量 (最大500)
            
        Returns:
            分红记录
        """
        self._require_auth()
        
        params = {
            'limit': min(limit, 500)
        }
        
        if asset:
            params['asset'] = asset
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        return self.client._make_request('GET', '/sapi/v1/asset/assetDividend', params, signed=True)
    
    def get_asset_detail(self, asset: str = None) -> Dict[str, Any]:
        """
        获取资产详情
        
        Args:
            asset: 可选，资产名称。如果不提供，返回所有资产详情
            
        Returns:
            资产详情
        """
        self._require_auth()
        
        params = {}
        if asset:
            params['asset'] = asset
        
        return self.client._make_request('GET', '/sapi/v1/asset/assetDetail', params, signed=True)
    
    def get_trade_fee(self, symbol: str = None) -> List[Dict[str, Any]]:
        """
        获取交易手续费率
        
        Args:
            symbol: 可选，交易对符号。如果不提供，返回所有交易对的手续费率
            
        Returns:
            手续费率信息
        """
        self._require_auth()
        
        params = {}
        if symbol:
            params['symbol'] = symbol.upper()
        
        return self.client._make_request('GET', '/sapi/v1/asset/tradeFee', params, signed=True)
    
    def universal_transfer(self, transfer_type: str, asset: str, amount: float,
                          from_symbol: str = None, to_symbol: str = None) -> Dict[str, Any]:
        """
        万能划转
        
        Args:
            transfer_type: 划转类型 (如 'MAIN_UMFUTURE', 'MAIN_CMFUTURE', 'MAIN_MARGIN' 等)
            asset: 资产名称
            amount: 划转数量
            from_symbol: 源交易对符号 (某些划转类型需要)
            to_symbol: 目标交易对符号 (某些划转类型需要)
            
        Returns:
            划转结果
        """
        self._require_auth()
        
        params = {
            'type': transfer_type,
            'asset': asset,
            'amount': str(amount)
        }
        
        if from_symbol:
            params['fromSymbol'] = from_symbol
        if to_symbol:
            params['toSymbol'] = to_symbol
        
        return self.client._make_request('POST', '/sapi/v1/asset/transfer', params, signed=True)
    
    def get_universal_transfer_history(self, transfer_type: str, start_time: int = None,
                                     end_time: int = None, current: int = 1,
                                     size: int = 10, from_symbol: str = None,
                                     to_symbol: str = None) -> Dict[str, Any]:
        """
        查询万能划转历史
        
        Args:
            transfer_type: 划转类型
            start_time: 开始时间戳 (毫秒)
            end_time: 结束时间戳 (毫秒)
            current: 当前页数
            size: 每页数量 (最大100)
            from_symbol: 源交易对符号
            to_symbol: 目标交易对符号
            
        Returns:
            划转历史
        """
        self._require_auth()
        
        params = {
            'type': transfer_type,
            'current': current,
            'size': min(size, 100)
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        if from_symbol:
            params['fromSymbol'] = from_symbol
        if to_symbol:
            params['toSymbol'] = to_symbol
        
        return self.client._make_request('GET', '/sapi/v1/asset/transfer', params, signed=True)
    
    def get_funding_wallet(self, asset: str = None, need_btc_valuation: str = 'true') -> List[Dict[str, Any]]:
        """
        查询资金钱包
        
        Args:
            asset: 可选，资产名称
            need_btc_valuation: 是否需要BTC估值
            
        Returns:
            资金钱包信息
        """
        self._require_auth()
        
        params = {
            'needBtcValuation': need_btc_valuation
        }
        
        if asset:
            params['asset'] = asset
        
        return self.client._make_request('POST', '/sapi/v1/asset/get-funding-asset', params, signed=True)
    
    def get_user_asset(self, asset: str = None, need_btc_valuation: bool = True) -> List[Dict[str, Any]]:
        """
        获取用户资产
        
        Args:
            asset: 可选，资产名称
            need_btc_valuation: 是否需要BTC估值
            
        Returns:
            用户资产信息
        """
        self._require_auth()
        
        params = {
            'needBtcValuation': str(need_btc_valuation).lower()
        }
        
        if asset:
            params['asset'] = asset
        
        return self.client._make_request('POST', '/sapi/v3/asset/getUserAsset', params, signed=True)
    
    def convert_bnb_burn_status(self) -> Dict[str, Any]:
        """
        获取BNB抵扣开关状态
        
        Returns:
            BNB抵扣状态
        """
        self._require_auth()
        
        return self.client._make_request('GET', '/sapi/v1/bnbBurn', signed=True)
    
    def toggle_bnb_burn(self, spot_bnb_burn: bool = None, interest_bnb_burn: bool = None) -> Dict[str, Any]:
        """
        切换BNB抵扣开关
        
        Args:
            spot_bnb_burn: 现货交易和保证金利息的BNB抵扣开关
            interest_bnb_burn: 保证金数据和保证金借贷的BNB抵扣开关
            
        Returns:
            切换结果
        """
        self._require_auth()
        
        params = {}
        if spot_bnb_burn is not None:
            params['spotBNBBurn'] = str(spot_bnb_burn).lower()
        if interest_bnb_burn is not None:
            params['interestBNBBurn'] = str(interest_bnb_burn).lower()
        
        return self.client._make_request('POST', '/sapi/v1/bnbBurn', params, signed=True)
    
    def get_balance(self, asset: str = None) -> List[Dict[str, Any]]:
        """
        获取账户余额 (便捷方法)
        
        Args:
            asset: 可选，特定资产名称
            
        Returns:
            余额信息
        """
        account_info = self.get_account_info()
        balances = account_info.get('balances', [])
        
        if asset:
            asset = asset.upper()
            balances = [b for b in balances if b['asset'] == asset]
        
        # 只返回有余额的资产
        return [b for b in balances if float(b['free']) > 0 or float(b['locked']) > 0]
    
    def get_balance_by_asset(self, asset: str) -> Dict[str, Any]:
        """
        获取特定资产余额
        
        Args:
            asset: 资产名称
            
        Returns:
            资产余额信息，如果没有找到返回None
        """
        balances = self.get_balance(asset)
        return balances[0] if balances else None
    
    def has_sufficient_balance(self, asset: str, required_amount: float) -> bool:
        """
        检查是否有足够余额
        
        Args:
            asset: 资产名称
            required_amount: 需要的数量
            
        Returns:
            是否有足够余额
        """
        balance = self.get_balance_by_asset(asset)
        if not balance:
            return False
        
        available = float(balance['free'])
        return available >= required_amount