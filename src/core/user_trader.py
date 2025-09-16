import time
from typing import Dict, List, Optional, Tuple
from src.models.models import Stock, Order, OrderType
from src.core.price_engine import PriceEngine
from src.core.trading_system import TradingEngine

class UserTrader:
    """用户交易员类 - 提供真实的股票交易体验"""
    
    def __init__(self, trading_engine: TradingEngine, price_engine: PriceEngine = None, initial_balance: float = 100000.0):
        self.trading_engine = trading_engine
        self.price_engine = price_engine
        self.initial_balance = initial_balance
        self.balance = initial_balance  # 可用资金
        self.positions: Dict[str, int] = {}  # 持仓 {股票代码: 数量}
        self.avg_cost: Dict[str, float] = {}  # 平均成本 {股票代码: 平均价格}
        self.transaction_history: List[Dict] = []  # 交易历史
        self.commission_rate = 0.0003  # 佣金费率 0.03%
        self.min_commission = 5.0  # 最低佣金 5元
        self.stamp_tax_rate = 0.001  # 印花税 0.1% (仅卖出时收取)
        
    def get_account_info(self) -> Dict:
        """获取账户信息"""
        total_market_value = 0
        position_details = []
        
        for symbol, quantity in self.positions.items():
            if quantity > 0:
                stock = self.trading_engine.market_data.stocks.get(symbol)
                if stock:
                    market_value = quantity * stock.current_price
                    total_market_value += market_value
                    
                    avg_cost = self.avg_cost.get(symbol, 0)
                    profit_loss = (stock.current_price - avg_cost) * quantity
                    profit_loss_pct = (stock.current_price - avg_cost) / avg_cost * 100 if avg_cost > 0 else 0
                    
                    position_details.append({
                        'symbol': symbol,
                        'quantity': quantity,
                        'avg_cost': avg_cost,
                        'current_price': stock.current_price,
                        'market_value': market_value,
                        'profit_loss': profit_loss,
                        'profit_loss_pct': profit_loss_pct
                    })
        
        total_assets = self.balance + total_market_value
        total_profit_loss = total_assets - self.initial_balance
        total_profit_loss_pct = total_profit_loss / self.initial_balance * 100
        
        return {
            'balance': self.balance,
            'market_value': total_market_value,
            'total_assets': total_assets,
            'total_profit_loss': total_profit_loss,
            'total_profit_loss_pct': total_profit_loss_pct,
            'positions': position_details
        }
    
    def get_trading_price(self, symbol: str, order_type: OrderType) -> Tuple[float, str]:
        """获取真实的交易价格
        
        Returns:
            Tuple[float, str]: (价格, 价格类型说明)
        """
        stock = self.trading_engine.market_data.stocks.get(symbol)
        if not stock:
            return 0.0, "股票不存在"
        
        # 模拟买卖价差 (bid-ask spread)
        spread_pct = 0.001  # 0.1% 的价差
        
        if order_type == OrderType.BUY:
            # 买入价格 = 当前价格 + 价差的一半
            price = stock.current_price * (1 + spread_pct / 2)
            return price, "买入价(卖一价)"
        else:
            # 卖出价格 = 当前价格 - 价差的一半
            price = stock.current_price * (1 - spread_pct / 2)
            return price, "卖出价(买一价)"
    
    def calculate_fees(self, amount: float, order_type: OrderType) -> Dict[str, float]:
        """计算交易费用
        
        Args:
            amount: 交易金额
            order_type: 订单类型
            
        Returns:
            Dict: 费用明细
        """
        # 佣金计算
        commission = max(amount * self.commission_rate, self.min_commission)
        
        # 印花税 (仅卖出时收取)
        stamp_tax = amount * self.stamp_tax_rate if order_type == OrderType.SELL else 0
        
        # 过户费 (上海股票收取，这里简化为所有股票都收取)
        transfer_fee = amount * 0.00002  # 0.002%
        
        total_fees = commission + stamp_tax + transfer_fee
        
        return {
            'commission': commission,
            'stamp_tax': stamp_tax,
            'transfer_fee': transfer_fee,
            'total_fees': total_fees
        }
    
    def place_order(self, symbol: str, order_type: OrderType, quantity: int) -> Dict:
        """下单交易
        
        Args:
            symbol: 股票代码
            order_type: 订单类型
            quantity: 数量
            
        Returns:
            Dict: 交易结果
        """
        if symbol not in self.trading_engine.market_data.stocks:
            return {'success': False, 'message': f'股票 {symbol} 不存在'}
        
        if quantity <= 0:
            return {'success': False, 'message': '交易数量必须大于0'}
        
        # 获取交易价格
        price, price_desc = self.get_trading_price(symbol, order_type)
        amount = quantity * price
        
        # 计算费用
        fees = self.calculate_fees(amount, order_type)
        
        if order_type == OrderType.BUY:
            # 买入检查
            total_cost = amount + fees['total_fees']
            if self.balance < total_cost:
                return {
                    'success': False, 
                    'message': f'资金不足，需要 {total_cost:.2f} 元，当前余额 {self.balance:.2f} 元'
                }
            
            # 执行买入
            self.balance -= total_cost
            
            if symbol not in self.positions:
                self.positions[symbol] = 0
                self.avg_cost[symbol] = 0
            
            # 更新平均成本
            old_quantity = self.positions[symbol]
            old_cost = self.avg_cost[symbol] * old_quantity
            new_cost = price * quantity
            
            self.positions[symbol] += quantity
            self.avg_cost[symbol] = (old_cost + new_cost) / self.positions[symbol]
            
        else:
            # 卖出检查
            current_position = self.positions.get(symbol, 0)
            if current_position < quantity:
                return {
                    'success': False, 
                    'message': f'持仓不足，当前持有 {current_position} 股，尝试卖出 {quantity} 股'
                }
            
            # 执行卖出
            revenue = amount - fees['total_fees']
            self.balance += revenue
            self.positions[symbol] -= quantity
            
            # 如果全部卖出，清除平均成本记录
            if self.positions[symbol] == 0:
                self.avg_cost[symbol] = 0
        
        # 应用交易对价格的影响
        if self.price_engine:
            trade_type = 'buy' if order_type == OrderType.BUY else 'sell'
            self.price_engine.apply_trade_impact(symbol, quantity, trade_type)
        
        # 记录交易历史
        transaction = {
            'timestamp': time.time(),
            'symbol': symbol,
            'order_type': order_type.value,
            'quantity': quantity,
            'price': price,
            'amount': amount,
            'fees': fees,
            'balance_after': self.balance
        }
        self.transaction_history.append(transaction)
        
        return {
            'success': True,
            'message': f'交易成功: {order_type.value} {symbol} {quantity}股 @ {price:.2f}元',
            'transaction': transaction
        }
    
    def buy_stock(self, symbol: str, quantity: int) -> Dict:
        """买入股票"""
        return self.place_order(symbol, OrderType.BUY, quantity)
    
    def sell_stock(self, symbol: str, quantity: int) -> Dict:
        """卖出股票"""
        return self.place_order(symbol, OrderType.SELL, quantity)
    
    def get_available_stocks(self) -> List[Dict]:
        """获取可交易的股票列表"""
        stocks = []
        for symbol, stock in self.trading_engine.market_data.stocks.items():
            buy_price, _ = self.get_trading_price(symbol, OrderType.BUY)
            sell_price, _ = self.get_trading_price(symbol, OrderType.SELL)
            
            stocks.append({
                'symbol': symbol,
                'name': stock.name,
                'current_price': stock.current_price,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'change_pct': ((stock.current_price - stock.open_price) / stock.open_price * 100) if stock.open_price > 0 else 0
            })
        
        return stocks
    
    def reset_account(self, new_balance: float = None):
        """重置账户"""
        if new_balance is not None:
            self.initial_balance = new_balance
        
        self.balance = self.initial_balance
        self.positions.clear()
        self.avg_cost.clear()
        self.transaction_history.clear()
        
        print(f"✅ 账户已重置，初始资金: {self.initial_balance:.2f} 元")