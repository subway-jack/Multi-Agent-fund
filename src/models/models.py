from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import time
import uuid

class OrderType(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"

class TraderType(Enum):
    BULL = "bull"  # 做多
    BEAR = "bear"  # 做空

@dataclass
class Stock:
    """股票数据模型"""
    symbol: str
    name: str
    current_price: float
    open_price: float
    high_price: float
    low_price: float
    volume: int = 0
    price_history: Optional[List[float]] = None
    
    def __post_init__(self):
        if self.price_history is None:
            # 生成足够的历史价格数据供技术分析使用
            import random
            self.price_history: List[float] = []
            
            # 生成30个历史价格点
            base_price = self.current_price
            for i in range(30):
                # 模拟历史价格波动
                if i == 0:
                    price = base_price * random.uniform(0.95, 1.05)
                else:
                    # 基于前一个价格生成新价格
                    prev_price = self.price_history[-1]
                    change_rate = random.uniform(-0.03, 0.03)  # ±3%的随机波动
                    price = prev_price * (1 + change_rate)
                    price = max(price, base_price * 0.8)  # 不低于基准价格的80%
                    price = min(price, base_price * 1.2)  # 不高于基准价格的120%
                
                self.price_history.append(round(price, 2))
            
            # 最后一个价格设为当前价格
            self.price_history.append(self.current_price)
        else:
            # 使用提供的历史价格数据
            self.price_history = list(self.price_history)  # 创建副本以避免修改原始数据

@dataclass
class Order:
    """订单数据模型"""
    id: str
    trader_id: str
    stock_symbol: str
    order_type: OrderType
    quantity: int
    price: float
    timestamp: float
    status: OrderStatus = OrderStatus.PENDING
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = time.time()

@dataclass
class Position:
    """持仓数据模型"""
    stock_symbol: str
    quantity: int  # 正数表示多头，负数表示空头
    avg_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0

class Trader:
    """交易者基类"""
    def __init__(self, trader_id: str, trader_type: TraderType, initial_balance: float = 100000):
        self.trader_id = trader_id
        self.trader_type = trader_type
        self.balance = initial_balance
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.trade_history: List[Dict] = []
        
    def create_order(self, stock_symbol: str, order_type: OrderType, quantity: int, price: float) -> Order:
        """创建订单"""
        order = Order(
            id="",
            trader_id=self.trader_id,
            stock_symbol=stock_symbol,
            order_type=order_type,
            quantity=quantity,
            price=price,
            timestamp=0
        )
        self.orders.append(order)
        return order
    
    def update_position(self, stock_symbol: str, quantity: int, price: float):
        """更新持仓"""
        if stock_symbol not in self.positions:
            self.positions[stock_symbol] = Position(stock_symbol, 0, 0.0)
        
        position = self.positions[stock_symbol]
        if position.quantity == 0:
            position.quantity = quantity
            position.avg_price = price
        else:
            # 计算新的平均价格
            total_cost = position.quantity * position.avg_price + quantity * price
            position.quantity += quantity
            if position.quantity != 0:
                position.avg_price = total_cost / position.quantity
    
    def calculate_pnl(self, current_prices: Dict[str, float]) -> float:
        """计算总盈亏"""
        total_pnl = 0.0
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                position.unrealized_pnl = (current_price - position.avg_price) * position.quantity
                total_pnl += position.unrealized_pnl + position.realized_pnl
        return total_pnl

class MarketData:
    """市场数据管理"""
    def __init__(self):
        self.stocks: Dict[str, Stock] = {}
        self.order_book: Dict[str, List[Order]] = {}  # 按股票分组的订单簿
        self.trade_records: List[Dict] = []
    
    def add_stock(self, stock: Stock):
        """添加股票"""
        self.stocks[stock.symbol] = stock
        self.order_book[stock.symbol] = []
    
    def update_price(self, symbol: str, new_price: float):
        """更新股票价格"""
        if symbol in self.stocks:
            stock = self.stocks[symbol]
            stock.current_price = new_price
            stock.price_history.append(new_price)
            
            # 更新当日高低价
            stock.high_price = max(stock.high_price, new_price)
            stock.low_price = min(stock.low_price, new_price)
    
    def get_current_prices(self) -> Dict[str, float]:
        """获取当前所有股票价格"""
        return {symbol: stock.current_price for symbol, stock in self.stocks.items()}