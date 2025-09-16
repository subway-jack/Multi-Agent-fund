import random
import math
import time
from typing import List, Dict, Optional
from src.models.models import Trader, TraderType, Order, OrderType, Stock
from src.core.price_engine import TechnicalIndicators
from src.config.config_manager import config_manager

class AITrader(Trader):
    """AI交易者基类"""
    
    def __init__(self, trader_id: str, trader_type: TraderType, initial_balance: float = 100000):
        super().__init__(trader_id, trader_type, initial_balance)
        
        # 从配置文件获取AI交易员参数
        ai_config = config_manager.get_config().get('ai_trader_config', {})
        
        # 使用配置参数，如果配置不存在则使用默认值
        base_risk = ai_config.get('risk_tolerance', 0.5)
        self.risk_tolerance = random.uniform(max(0.1, base_risk - 0.2), min(0.9, base_risk + 0.2))
        
        self.aggression = random.uniform(0.1, 0.8)  # 激进程度
        self.patience = random.uniform(0.2, 0.9)  # 耐心程度
        self.technical_weight = random.uniform(0.3, 0.9)  # 技术分析权重
        self.last_action_time = 0
        self.decision_interval = ai_config.get('decision_interval', 5)  # 从配置获取决策间隔
        
        # 交易金额限制
        self.min_trade_amount = ai_config.get('min_trade_amount', 1000)
        self.max_trade_amount = ai_config.get('max_trade_amount', 10000)
        self.max_position_size = ai_config.get('max_position_size', 0.3)
        
    def should_make_decision(self, current_time: float) -> bool:
        """判断是否应该做出交易决策"""
        return (current_time - self.last_action_time) >= self.decision_interval
    
    def analyze_market(self, stock: Stock) -> Dict[str, float]:
        """分析市场情况
        
        Returns:
            分析结果字典，包含各种指标
        """
        prices = stock.price_history
        current_price = stock.current_price
        
        analysis = {
            'price_trend': 0.0,  # 价格趋势 (-1到1)
            'volatility': 0.0,   # 波动率
            'rsi': 50.0,         # RSI指标
            'sma_signal': 0.0,   # 移动平均信号
            'bollinger_position': 0.0,  # 布林带位置
        }
        
        if len(prices) < 2:
            return analysis
        
        # 计算价格趋势
        if len(prices) >= 10:
            recent_trend = (prices[-1] - prices[-10]) / prices[-10]
            analysis['price_trend'] = max(-1.0, min(1.0, recent_trend * 10))
        
        # 计算波动率
        if len(prices) >= 5:
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, min(len(prices), 21))]
            analysis['volatility'] = math.sqrt(sum(r**2 for r in returns) / len(returns)) if returns else 0
        
        # 从配置获取技术指标参数
        tech_config = config_manager.get_config().get('technical_indicators', {})
        rsi_period = tech_config.get('rsi_period', 14)
        sma_short = tech_config.get('sma_short_period', 10)
        sma_long = tech_config.get('sma_long_period', 30)
        bb_period = tech_config.get('bollinger_period', 20)
        
        # 技术指标
        if len(prices) >= rsi_period:
            analysis['rsi'] = TechnicalIndicators.rsi(prices, rsi_period)
        
        if len(prices) >= sma_short:
            sma_short_val = TechnicalIndicators.sma(prices, sma_short)
            sma_long_val = TechnicalIndicators.sma(prices, min(sma_long, len(prices)))
            analysis['sma_signal'] = (sma_short_val - sma_long_val) / sma_long_val if sma_long_val > 0 else 0
        
        if len(prices) >= bb_period:
            bb_std = tech_config.get('bollinger_std', 2.0)
            upper, middle, lower = TechnicalIndicators.bollinger_bands(prices, min(bb_period, len(prices)), bb_std)
            if upper > lower:
                analysis['bollinger_position'] = (current_price - lower) / (upper - lower) - 0.5
        
        return analysis
    
    def calculate_position_size(self, stock_price: float, confidence: float) -> int:
        """计算仓位大小
        
        Args:
            stock_price: 股票价格
            confidence: 信心程度 (0到1)
            
        Returns:
            股票数量
        """
        # 基于余额、风险承受能力和信心程度计算仓位
        max_position_value = self.balance * self.max_position_size * confidence
        
        # 限制交易金额在配置范围内
        trade_value = max(self.min_trade_amount, min(max_position_value, self.max_trade_amount))
        base_quantity = int(trade_value / stock_price)
        
        # 添加一些随机性
        randomness = random.uniform(0.8, 1.2)
        quantity = int(base_quantity * randomness)
        
        return max(1, quantity)  # 至少买1股
    
    def make_decision(self, stock: Stock, current_time: float) -> Optional[Order]:
        """做出交易决策（子类需要实现）"""
        raise NotImplementedError

class BullTrader(AITrader):
    """做多交易者"""
    
    def __init__(self, trader_id: str, initial_balance: float = 100000):
        super().__init__(trader_id, TraderType.BULL, initial_balance)
        self.buy_threshold = random.uniform(0.3, 0.7)  # 买入阈值
        self.sell_threshold = random.uniform(0.1, 0.4)  # 卖出阈值
        self.profit_target = random.uniform(0.05, 0.2)  # 止盈目标
        self.stop_loss = random.uniform(0.03, 0.1)  # 止损点
        
    def make_decision(self, stock: Stock, current_time: float) -> Optional[Order]:
        """做多交易者的决策逻辑"""
        # if not self.should_make_decision(current_time):
        #     return None
            
        self.last_action_time = current_time
        analysis = self.analyze_market(stock)
                    
        # 计算买入信号强度
        buy_signals = [
            analysis['price_trend'] > 0,  # 上升趋势
            analysis['rsi'] < 30,  # RSI超卖
            analysis['sma_signal'] > 0,  # 短期均线上穿长期均线
            analysis['bollinger_position'] < -0.3,  # 价格接近布林带下轨
        ]
        
        # 计算卖出信号强度
        sell_signals = [
            analysis['price_trend'] < -0.2,  # 下降趋势
            analysis['rsi'] > 70,  # RSI超买
            analysis['sma_signal'] < -0.1,  # 短期均线下穿长期均线
            analysis['bollinger_position'] > 0.3,  # 价格接近布林带上轨
        ]
        
        buy_strength = sum(buy_signals) / len(buy_signals)
        sell_strength = sum(sell_signals) / len(sell_signals)
        
        # 信号强度计算完成
        
        # 检查当前持仓
        current_position = self.positions.get(stock.symbol, None)
        
        # 决策逻辑
        if current_position is None or current_position.quantity <= 0:
            # 没有持仓或持空仓，考虑买入
            if buy_strength >= self.buy_threshold:
                confidence = buy_strength * self.technical_weight + (1 - self.technical_weight) * random.uniform(0.3, 0.8)
                quantity = self.calculate_position_size(stock.current_price, confidence)
                
                if quantity > 0:  # 确保数量大于0
                    # 价格策略：稍微低于当前价格买入
                    price_offset = random.uniform(-0.002, 0.001)
                    order_price = stock.current_price * (1 + price_offset)
                    
                    return self.create_order(stock.symbol, OrderType.BUY, quantity, order_price)
                else:
                    return None
        
        else:
            # 有多头持仓，考虑卖出
            # 检查止盈止损
            price_change = (stock.current_price - current_position.avg_price) / current_position.avg_price
            
            should_sell = False
            
            # 止盈
            if price_change >= self.profit_target:
                should_sell = True
            
            # 止损
            elif price_change <= -self.stop_loss:
                should_sell = True
            
            # 技术信号卖出
            elif sell_strength >= self.sell_threshold:
                should_sell = True
            
            if should_sell:
                # 卖出部分或全部持仓
                sell_ratio = random.uniform(0.3, 1.0) if price_change > 0 else 1.0  # 盈利时可能部分卖出
                quantity = max(1, int(current_position.quantity * sell_ratio))
                
                # 价格策略：稍微高于当前价格卖出
                price_offset = random.uniform(-0.001, 0.002)
                order_price = stock.current_price * (1 + price_offset)
                
                return self.create_order(stock.symbol, OrderType.SELL, quantity, order_price)
        
        return None

class BearTrader(AITrader):
    """做空交易者"""
    
    def __init__(self, trader_id: str, initial_balance: float = 100000):
        super().__init__(trader_id, TraderType.BEAR, initial_balance)
        self.sell_threshold = random.uniform(0.3, 0.7)  # 卖空阈值
        self.cover_threshold = random.uniform(0.1, 0.4)  # 平仓阈值
        self.profit_target = random.uniform(0.05, 0.2)  # 止盈目标
        self.stop_loss = random.uniform(0.03, 0.1)  # 止损点
        
    def make_decision(self, stock: Stock, current_time: float) -> Optional[Order]:
        """做空交易者的决策逻辑"""
        # if not self.should_make_decision(current_time):
        #     return None
            
        self.last_action_time = current_time
        analysis = self.analyze_market(stock)
                
        # 计算卖空信号强度
        sell_signals = [
            analysis['price_trend'] < 0,  # 下降趋势
            analysis['rsi'] > 70,  # RSI超买
            analysis['sma_signal'] < 0,  # 短期均线下穿长期均线
            analysis['bollinger_position'] > 0.3,  # 价格接近布林带上轨
        ]
        
        # 计算平仓信号强度
        cover_signals = [
            analysis['price_trend'] > 0.2,  # 上升趋势
            analysis['rsi'] < 30,  # RSI超卖
            analysis['sma_signal'] > 0.1,  # 短期均线上穿长期均线
            analysis['bollinger_position'] < -0.3,  # 价格接近布林带下轨
        ]
        
        sell_strength = sum(sell_signals) / len(sell_signals)
        cover_strength = sum(cover_signals) / len(cover_signals)
        
        # 检查当前持仓
        current_position = self.positions.get(stock.symbol, None)
        
        # 决策逻辑
        if current_position is None or current_position.quantity >= 0:
            # 没有持仓或持多仓，考虑卖空
            if sell_strength >= self.sell_threshold:
                confidence = sell_strength * self.technical_weight + (1 - self.technical_weight) * random.uniform(0.3, 0.8)
                quantity = self.calculate_position_size(stock.current_price, confidence)
                
                # 价格策略：稍微高于当前价格卖出
                price_offset = random.uniform(-0.001, 0.002)
                order_price = stock.current_price * (1 + price_offset)
                
                return self.create_order(stock.symbol, OrderType.SELL, quantity, order_price)
        
        else:
            # 有空头持仓，考虑平仓
            # 检查止盈止损（注意空头的盈亏计算相反）
            price_change = (current_position.avg_price - stock.current_price) / current_position.avg_price
            
            should_cover = False
            
            # 止盈
            if price_change >= self.profit_target:
                should_cover = True
            
            # 止损
            elif price_change <= -self.stop_loss:
                should_cover = True
            
            # 技术信号平仓
            elif cover_strength >= self.cover_threshold:
                should_cover = True
            
            if should_cover:
                # 买入平仓（注意空头持仓quantity是负数）
                cover_ratio = random.uniform(0.3, 1.0) if price_change > 0 else 1.0
                quantity = max(1, int(abs(current_position.quantity) * cover_ratio))
                
                # 价格策略：稍微低于当前价格买入
                price_offset = random.uniform(-0.002, 0.001)
                order_price = stock.current_price * (1 + price_offset)
                
                return self.create_order(stock.symbol, OrderType.BUY, quantity, order_price)
        
        return None

class TraderManager:
    """交易者管理器"""
    
    def __init__(self):
        self.traders: Dict[str, AITrader] = {}
    
    def create_traders(self, num_bulls: int = 50, num_bears: int = 50):
        """创建指定数量的交易者"""
        # 创建做多交易者
        for i in range(num_bulls):
            trader_id = f"bull_{i+1:03d}"
            trader = BullTrader(trader_id)
            self.traders[trader_id] = trader
        
        # 创建做空交易者
        for i in range(num_bears):
            trader_id = f"bear_{i+1:03d}"
            trader = BearTrader(trader_id)
            self.traders[trader_id] = trader
    
    def get_all_decisions(self, stocks: Dict[str, Stock], current_time: float) -> List[Order]:
        """获取所有交易者对所有股票的决策"""
        orders = []
        current_round_decisions = {symbol: 0 for symbol in stocks.keys()}
        
        # 初始化累积决策统计
        if not hasattr(self, '_total_decisions'):
            self._total_decisions = {symbol: 0 for symbol in stocks.keys()}
        
        # 调试：打印股票列表
        if not hasattr(self, '_stocks_debug_printed'):
            print(f"🔍 传入的股票列表: {list(stocks.keys())}")
            self._stocks_debug_printed = True
        
        for trader in self.traders.values():
            # 每个交易者可以对所有股票做决策
            for stock in stocks.values():
                order = trader.make_decision(stock, current_time)
                if order:
                    orders.append(order)
                    current_round_decisions[stock.symbol] += 1
                    self._total_decisions[stock.symbol] += 1
        
        # 每10秒打印一次决策统计
        if hasattr(self, '_last_debug_time'):
            if current_time - self._last_debug_time >= 10:
                current_total = sum(current_round_decisions.values())
                cumulative_total = sum(self._total_decisions.values())
                print(f"📊 AI决策统计: 本轮={current_total}, 累积={cumulative_total}, 详细={dict(self._total_decisions)}")
                self._last_debug_time = current_time
        else:
            self._last_debug_time = current_time
            
        return orders
    
    def get_trader_stats(self) -> Dict[str, Dict]:
        """获取交易者统计信息"""
        stats = {
            'total_traders': len(self.traders),
            'bull_traders': len([t for t in self.traders.values() if t.trader_type == TraderType.BULL]),
            'bear_traders': len([t for t in self.traders.values() if t.trader_type == TraderType.BEAR]),
            'total_balance': sum(t.balance for t in self.traders.values()),
            'active_positions': sum(1 for t in self.traders.values() if t.positions),
        }
        return stats
    
    def reset_all_traders(self):
        """重置所有交易者状态"""
        for trader in self.traders.values():
            trader.balance = trader.initial_balance
            trader.positions.clear()
            trader.last_action_time = 0
        print(f"✅ 已重置 {len(self.traders)} 个交易者")