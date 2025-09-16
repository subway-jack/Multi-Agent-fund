import time
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from src.models.models import Order, OrderType, OrderStatus, MarketData, Trader
from src.core.ai_traders import TraderManager

class OrderBook:
    """订单簿"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.buy_orders: List[Order] = []  # 买单，按价格降序排列
        self.sell_orders: List[Order] = []  # 卖单，按价格升序排列
        self.trade_history: List[Dict] = []
    
    def add_order(self, order: Order):
        """添加订单到订单簿"""
        if order.order_type == OrderType.BUY:
            self.buy_orders.append(order)
            # 按价格降序排列（最高价在前）
            self.buy_orders.sort(key=lambda x: x.price, reverse=True)
        else:
            self.sell_orders.append(order)
            # 按价格升序排列（最低价在前）
            self.sell_orders.sort(key=lambda x: x.price)
    
    def remove_order(self, order_id: str):
        """移除订单"""
        self.buy_orders = [o for o in self.buy_orders if o.id != order_id]
        self.sell_orders = [o for o in self.sell_orders if o.id != order_id]
    
    def get_best_bid(self) -> Optional[float]:
        """获取最佳买价"""
        return self.buy_orders[0].price if self.buy_orders else None
    
    def get_best_ask(self) -> Optional[float]:
        """获取最佳卖价"""
        return self.sell_orders[0].price if self.sell_orders else None
    
    def get_spread(self) -> Optional[float]:
        """获取买卖价差"""
        bid = self.get_best_bid()
        ask = self.get_best_ask()
        if bid and ask:
            return ask - bid
        return None
    
    def get_depth(self, levels: int = 5) -> Dict:
        """获取订单簿深度"""
        return {
            'bids': [(o.price, o.quantity) for o in self.buy_orders[:levels]],
            'asks': [(o.price, o.quantity) for o in self.sell_orders[:levels]]
        }

class TradingEngine:
    """交易引擎"""
    
    def __init__(self, market_data: MarketData, trader_manager: TraderManager, price_engine=None):
        self.market_data = market_data
        self.trader_manager = trader_manager
        self.price_engine = price_engine  # 价格引擎引用
        self.order_books: Dict[str, OrderBook] = {}
        self.pending_orders: List[Order] = []
        self.executed_trades: List[Dict] = []
        
        # 为每个股票创建订单簿
        for symbol in market_data.stocks.keys():
            self.order_books[symbol] = OrderBook(symbol)
    
    def submit_order(self, order: Order) -> bool:
        """提交订单"""
        if order.stock_symbol not in self.order_books:
            return False
        
        # 验证订单
        if not self._validate_order(order):
            order.status = OrderStatus.CANCELLED
            return False
        
        # 添加到订单簿
        self.order_books[order.stock_symbol].add_order(order)
        self.pending_orders.append(order)
        
        # 尝试匹配订单
        self._match_orders(order.stock_symbol)
        
        return True
    
    def _validate_order(self, order: Order) -> bool:
        """验证订单有效性"""
        # 检查基本参数
        if order.quantity <= 0 or order.price <= 0:
            return False
        
        # 检查交易者是否存在
        if order.trader_id not in self.trader_manager.traders:
            return False
        
        trader = self.trader_manager.traders[order.trader_id]
        
        # 检查买单资金是否充足
        if order.order_type == OrderType.BUY:
            required_funds = order.quantity * order.price
            if trader.balance < required_funds:
                return False
        
        # 检查卖单是否有足够持仓
        elif order.order_type == OrderType.SELL:
            position = trader.positions.get(order.stock_symbol)
            if not position or position.quantity < order.quantity:
                # 允许卖空（负持仓）
                pass
        
        return True
    
    def _match_orders(self, symbol: str):
        """匹配订单"""
        order_book = self.order_books[symbol]
        
        while order_book.buy_orders and order_book.sell_orders:
            best_buy = order_book.buy_orders[0]
            best_sell = order_book.sell_orders[0]
            
            # 检查价格是否匹配
            if best_buy.price >= best_sell.price:
                # 执行交易
                trade_price = (best_buy.price + best_sell.price) / 2  # 使用中间价
                trade_quantity = min(best_buy.quantity, best_sell.quantity)
                
                self._execute_trade(best_buy, best_sell, trade_price, trade_quantity)
                
                # 更新订单数量
                best_buy.quantity -= trade_quantity
                best_sell.quantity -= trade_quantity
                
                # 移除已完全成交的订单
                if best_buy.quantity == 0:
                    best_buy.status = OrderStatus.FILLED
                    order_book.buy_orders.pop(0)
                    self.pending_orders = [o for o in self.pending_orders if o.id != best_buy.id]
                
                if best_sell.quantity == 0:
                    best_sell.status = OrderStatus.FILLED
                    order_book.sell_orders.pop(0)
                    self.pending_orders = [o for o in self.pending_orders if o.id != best_sell.id]
            else:
                break
    
    def _execute_trade(self, buy_order: Order, sell_order: Order, price: float, quantity: int):
        """执行交易"""
        timestamp = time.time()
        
        # 记录交易
        trade = {
            'timestamp': timestamp,
            'symbol': buy_order.stock_symbol,
            'price': price,
            'quantity': quantity,
            'buy_trader': buy_order.trader_id,
            'sell_trader': sell_order.trader_id,
            'buy_order_id': buy_order.id,
            'sell_order_id': sell_order.id
        }
        
        self.executed_trades.append(trade)
        self.order_books[buy_order.stock_symbol].trade_history.append(trade)
        
        # 更新交易者持仓和余额
        buy_trader = self.trader_manager.traders[buy_order.trader_id]
        sell_trader = self.trader_manager.traders[sell_order.trader_id]
        
        # 买方：增加持仓，减少余额
        buy_trader.update_position(buy_order.stock_symbol, quantity, price)
        buy_trader.balance -= price * quantity
        
        # 卖方：减少持仓，增加余额
        sell_trader.update_position(sell_order.stock_symbol, -quantity, price)
        sell_trader.balance += price * quantity
        
        # 更新股票价格和成交量 - 价格完全基于实际成交价格
        self.market_data.update_price(buy_order.stock_symbol, price)
        
        if buy_order.stock_symbol in self.market_data.stocks:
            self.market_data.stocks[buy_order.stock_symbol].volume += quantity
            
        print(f"交易执行: {buy_order.stock_symbol} 价格:{price:.2f} 数量:{quantity} 买方:{buy_order.trader_id} 卖方:{sell_order.trader_id}")
        
        # 记录交易历史
        buy_trader.trade_history.append({
            'timestamp': timestamp,
            'symbol': buy_order.stock_symbol,
            'type': 'buy',
            'quantity': quantity,
            'price': price,
            'total': price * quantity
        })
        
        sell_trader.trade_history.append({
            'timestamp': timestamp,
            'symbol': buy_order.stock_symbol,
            'type': 'sell',
            'quantity': quantity,
            'price': price,
            'total': price * quantity
        })
    
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        for order in self.pending_orders:
            if order.id == order_id:
                order.status = OrderStatus.CANCELLED
                
                # 从订单簿中移除
                if order.stock_symbol in self.order_books:
                    self.order_books[order.stock_symbol].remove_order(order_id)
                
                # 从待处理订单中移除
                self.pending_orders = [o for o in self.pending_orders if o.id != order_id]
                return True
        
        return False
    
    def get_market_summary(self) -> Dict:
        """获取市场摘要"""
        summary = {
            'total_trades': len(self.executed_trades),
            'total_volume': sum(trade['quantity'] for trade in self.executed_trades),
            'total_value': sum(trade['price'] * trade['quantity'] for trade in self.executed_trades),
            'pending_orders': len(self.pending_orders),
            'symbols': {}
        }
        
        for symbol, order_book in self.order_books.items():
            stock = self.market_data.stocks[symbol]
            summary['symbols'][symbol] = {
                'current_price': stock.current_price,
                'best_bid': order_book.get_best_bid(),
                'best_ask': order_book.get_best_ask(),
                'spread': order_book.get_spread(),
                'trades_count': len(order_book.trade_history),
                'volume': stock.volume
            }
        
        return summary
    
    def get_trader_performance(self) -> Dict[str, Dict]:
        """获取交易者表现"""
        performance = {}
        current_prices = self.market_data.get_current_prices()
        
        for trader_id, trader in self.trader_manager.traders.items():
            total_pnl = trader.calculate_pnl(current_prices)
            
            performance[trader_id] = {
                'type': trader.trader_type.value,
                'balance': trader.balance,
                'total_pnl': total_pnl,
                'total_value': trader.balance + total_pnl,
                'positions_count': len([p for p in trader.positions.values() if p.quantity != 0]),
                'trades_count': len(trader.trade_history),
                'return_rate': total_pnl / 100000 if trader.balance > 0 else 0  # 假设初始资金10万
            }
        
        return performance
    
    def process_ai_decisions(self, current_time: float):
        """处理AI交易者的决策"""
        # 获取所有交易者对所有股票的决策
        orders = self.trader_manager.get_all_decisions(self.market_data.stocks, current_time)
        for order in orders:
            self.submit_order(order)
    
    def cleanup_old_orders(self, max_age_seconds: float = 300):
        """清理过期订单"""
        current_time = time.time()
        expired_orders = [
            order for order in self.pending_orders 
            if (current_time - order.timestamp) > max_age_seconds
        ]
        
        for order in expired_orders:
            self.cancel_order(order.id)