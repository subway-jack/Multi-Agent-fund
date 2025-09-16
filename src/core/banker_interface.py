import time
from typing import Dict, List, Optional
from src.models.models import Stock, Order, OrderType
from src.core.price_engine import PriceEngine
from src.core.trading_system import TradingEngine
from src.core.ai_traders import TraderManager

class BankerInterface:
    """庄家操作界面"""
    
    def __init__(self, price_engine: PriceEngine, trading_engine: TradingEngine, trader_manager: TraderManager):
        self.price_engine = price_engine
        self.trading_engine = trading_engine
        self.trader_manager = trader_manager
        self.manipulation_history: List[Dict] = []
        self.banker_balance = 10000000  # 庄家资金1000万
        self.banker_positions: Dict[str, int] = {}  # 庄家持仓
        
    def set_market_trend(self, trend: float, duration_minutes: int = 5):
        """设置市场趋势
        
        Args:
            trend: 趋势强度 (-1到1，负数下跌，正数上涨)
            duration_minutes: 持续时间（分钟）
        """
        self.price_engine.set_trend(trend)
        
        action = {
            'timestamp': time.time(),
            'action': 'set_trend',
            'parameters': {'trend': trend, 'duration': duration_minutes},
            'description': f"设置市场趋势: {'上涨' if trend > 0 else '下跌' if trend < 0 else '横盘'} (强度: {abs(trend):.2f})"
        }
        self.manipulation_history.append(action)
        
        print(f"✅ 庄家操作: {action['description']}")
    
    def trigger_market_crash(self, intensity: float = 0.8):
        """触发市场崩盘
        
        Args:
            intensity: 崩盘强度 (0到1)
        """
        self.trigger_market_event('crash', intensity)
    
    def trigger_market_boom(self, intensity: float = 0.8):
        """触发市场暴涨
        
        Args:
            intensity: 暴涨强度 (0到1)
        """
        self.trigger_market_event('surge', intensity)
    
    def increase_volatility(self, intensity: float = 0.5):
        """增加市场波动性
        
        Args:
            intensity: 波动强度 (0到1)
        """
        self.trigger_market_event('volatility', intensity)
    
    def place_large_order(self, symbol: str, order_type: str, amount: int, value: float):
        """下大单影响市场
        
        Args:
            symbol: 股票代码
            order_type: 订单类型 ('buy' 或 'sell')
            amount: 数量
            value: 价格偏移百分比
        """
        # 转换订单类型
        if order_type.lower() == 'buy':
            order_enum = OrderType.BUY
        elif order_type.lower() == 'sell':
            order_enum = OrderType.SELL
        else:
            print(f"❌ 无效的订单类型: {order_type}")
            return
        
        # 调用现有的create_large_order方法
        self.create_large_order(symbol, order_enum, amount, value / 100.0)
    
    def manipulate_price(self, symbol: str, manipulation_strength: float, duration_minutes: int = 3):
        """直接操控股票价格
        
        Args:
            symbol: 股票代码
            manipulation_strength: 操控强度 (-1到1)
            duration_minutes: 持续时间（分钟）
        """
        if symbol not in self.trading_engine.market_data.stocks:
            print(f"❌ 股票 {symbol} 不存在")
            return
        
        self.price_engine.set_manipulation(manipulation_strength)
        
        action = {
            'timestamp': time.time(),
            'action': 'manipulate_price',
            'parameters': {'symbol': symbol, 'strength': manipulation_strength, 'duration': duration_minutes},
            'description': f"操控 {symbol} 价格: {'拉升' if manipulation_strength > 0 else '打压' if manipulation_strength < 0 else '稳定'} (强度: {abs(manipulation_strength):.2f})"
        }
        self.manipulation_history.append(action)
        
        print(f"✅ 庄家操作: {action['description']}")
    
    def create_large_order(self, symbol: str, order_type: OrderType, quantity: int, price_offset: float = 0.0):
        """创建大单影响市场
        
        Args:
            symbol: 股票代码
            order_type: 订单类型
            quantity: 数量
            price_offset: 价格偏移（相对于当前价格的百分比）
        """
        if symbol not in self.trading_engine.market_data.stocks:
            print(f"❌ 股票 {symbol} 不存在")
            return
        
        stock = self.trading_engine.market_data.stocks[symbol]
        order_price = stock.current_price * (1 + price_offset)
        
        # 检查庄家资金
        if order_type == OrderType.BUY:
            required_funds = quantity * order_price
            if self.banker_balance < required_funds:
                print(f"❌ 庄家资金不足，需要 {required_funds:.2f}，当前余额 {self.banker_balance:.2f}")
                return
        
        # 创建庄家订单
        order = Order(
            id="",
            trader_id="banker",
            stock_symbol=symbol,
            order_type=order_type,
            quantity=quantity,
            price=order_price,
            timestamp=0
        )
        
        # 直接执行庄家订单（不通过撮合系统）
        self._execute_banker_order(order)
        
        action = {
            'timestamp': time.time(),
            'action': 'large_order',
            'parameters': {'symbol': symbol, 'type': order_type.value, 'quantity': quantity, 'price': order_price},
            'description': f"庄家{order_type.value} {symbol}: {quantity}股 @ {order_price:.2f}"
        }
        self.manipulation_history.append(action)
        
        print(f"✅ 庄家操作: {action['description']}")
    
    def _execute_banker_order(self, order: Order):
        """执行庄家订单"""
        symbol = order.stock_symbol
        
        if order.order_type == OrderType.BUY:
            # 庄家买入
            cost = order.quantity * order.price
            self.banker_balance -= cost
            
            if symbol not in self.banker_positions:
                self.banker_positions[symbol] = 0
            self.banker_positions[symbol] += order.quantity
            
            # 影响市场价格（买入推高价格）
            price_impact = min(0.02, order.quantity / 10000)  # 最大2%的价格影响
            new_price = order.price * (1 + price_impact)
            self.trading_engine.market_data.update_price(symbol, new_price)
            
        else:
            # 庄家卖出
            revenue = order.quantity * order.price
            self.banker_balance += revenue
            
            if symbol not in self.banker_positions:
                self.banker_positions[symbol] = 0
            self.banker_positions[symbol] -= order.quantity
            
            # 影响市场价格（卖出压低价格）
            price_impact = min(0.02, order.quantity / 10000)
            new_price = order.price * (1 - price_impact)
            self.trading_engine.market_data.update_price(symbol, new_price)
    
    def trigger_market_event(self, event_type: str, intensity: float = 0.5):
        """触发市场事件
        
        Args:
            event_type: 事件类型 ('crash', 'surge', 'volatility')
            intensity: 事件强度 (0到1)
        """
        if event_type == 'crash':
            self.price_engine.simulate_market_crash(intensity)
            description = f"触发市场崩盘 (强度: {intensity:.2f})"
        elif event_type == 'surge':
            self.price_engine.simulate_market_surge(intensity)
            description = f"触发市场暴涨 (强度: {intensity:.2f})"
        elif event_type == 'volatility':
            self.price_engine.add_market_noise(intensity * 0.05)
            description = f"增加市场波动 (强度: {intensity:.2f})"
        else:
            print(f"❌ 未知事件类型: {event_type}")
            return
        
        action = {
            'timestamp': time.time(),
            'action': 'market_event',
            'parameters': {'event_type': event_type, 'intensity': intensity},
            'description': description
        }
        self.manipulation_history.append(action)
        
        print(f"✅ 庄家操作: {description}")
    
    def set_volatility(self, volatility: float):
        """设置市场波动率
        
        Args:
            volatility: 波动率 (0.001到0.1)
        """
        self.price_engine.set_volatility(volatility)
        
        action = {
            'timestamp': time.time(),
            'action': 'set_volatility',
            'parameters': {'volatility': volatility},
            'description': f"设置市场波动率: {volatility:.3f}"
        }
        self.manipulation_history.append(action)
        
        print(f"✅ 庄家操作: {action['description']}")
    
    def get_market_control_panel(self) -> Dict:
        """获取市场控制面板信息"""
        market_summary = self.trading_engine.get_market_summary()
        trader_stats = self.trader_manager.get_trader_stats()
        
        return {
            'banker_status': {
                'balance': self.banker_balance,
                'positions': self.banker_positions,
                'total_manipulations': len(self.manipulation_history)
            },
            'market_status': {
                'total_trades': market_summary['total_trades'],
                'total_volume': market_summary['total_volume'],
                'pending_orders': market_summary['pending_orders'],
                'current_trend': self.price_engine.trend,
                'current_volatility': self.price_engine.volatility,
                'manipulation_factor': self.price_engine.manipulation_factor
            },
            'trader_status': trader_stats,
            'stock_prices': {symbol: data['current_price'] for symbol, data in market_summary['symbols'].items()}
        }
    
    def get_manipulation_history(self, limit: int = 10) -> List[Dict]:
        """获取操控历史"""
        return self.manipulation_history[-limit:]
    
    def reset_market_controls(self):
        """重置市场控制参数"""
        self.price_engine.set_trend(0.0)
        self.price_engine.set_manipulation(0.0)
        self.price_engine.set_volatility(0.02)
        
        action = {
            'timestamp': time.time(),
            'action': 'reset_controls',
            'parameters': {},
            'description': "重置所有市场控制参数"
        }
        self.manipulation_history.append(action)
        
        print(f"✅ 庄家操作: {action['description']}")
    
    def reset_all_controls(self):
        """重置所有庄家控制参数"""
        # 重置市场控制参数
        self.reset_market_controls()
        
        # 重置庄家持仓
        self.banker_positions.clear()
        
        # 清空操作历史
        self.manipulation_history.clear()
        
        print("🔄 已重置所有庄家控制参数")
    
    def analyze_trader_behavior(self) -> Dict:
        """分析交易者行为"""
        performance = self.trading_engine.get_trader_performance()
        
        bull_performance = [p for p in performance.values() if p['type'] == 'bull']
        bear_performance = [p for p in performance.values() if p['type'] == 'bear']
        
        analysis = {
            'bull_traders': {
                'count': len(bull_performance),
                'avg_return': sum(p['return_rate'] for p in bull_performance) / len(bull_performance) if bull_performance else 0,
                'profitable_count': len([p for p in bull_performance if p['total_pnl'] > 0]),
                'total_trades': sum(p['trades_count'] for p in bull_performance)
            },
            'bear_traders': {
                'count': len(bear_performance),
                'avg_return': sum(p['return_rate'] for p in bear_performance) / len(bear_performance) if bear_performance else 0,
                'profitable_count': len([p for p in bear_performance if p['total_pnl'] > 0]),
                'total_trades': sum(p['trades_count'] for p in bear_performance)
            },
            'market_sentiment': {
                'bull_profit_rate': len([p for p in bull_performance if p['total_pnl'] > 0]) / len(bull_performance) if bull_performance else 0,
                'bear_profit_rate': len([p for p in bear_performance if p['total_pnl'] > 0]) / len(bear_performance) if bear_performance else 0
            }
        }
        
        return analysis
    
    def print_market_status(self):
        """打印市场状态"""
        control_panel = self.get_market_control_panel()
        
        print("\n" + "="*60)
        print("📊 股票模拟器 - 庄家控制面板")
        print("="*60)
        
        # 庄家状态
        banker = control_panel['banker_status']
        print(f"💰 庄家资金: {banker['balance']:,.2f}")
        print(f"📈 庄家持仓: {len(banker['positions'])} 只股票")
        print(f"🎮 操控次数: {banker['total_manipulations']}")
        
        # 市场状态
        market = control_panel['market_status']
        print(f"\n📊 市场概况:")
        print(f"  总交易数: {market['total_trades']}")
        print(f"  总成交量: {market['total_volume']:,}")
        print(f"  待处理订单: {market['pending_orders']}")
        print(f"  当前趋势: {market['current_trend']:+.3f}")
        print(f"  波动率: {market['current_volatility']:.3f}")
        print(f"  操控因子: {market['manipulation_factor']:+.3f}")
        
        # 交易者状态
        traders = control_panel['trader_status']
        print(f"\n👥 交易者状态:")
        print(f"  做多交易者: {traders['bull_traders']}")
        print(f"  做空交易者: {traders['bear_traders']}")
        print(f"  活跃持仓: {traders['active_positions']}")
        
        # 股票价格
        print(f"\n💹 股票价格:")
        for symbol, price in control_panel['stock_prices'].items():
            print(f"  {symbol}: {price:.2f}")
        
        print("="*60)