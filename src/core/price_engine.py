import random
import math
import time
import numpy as np
from typing import List, Dict, Tuple
from qbot.models.models import Stock, MarketData
from src.config.config_manager import config_manager
from src.core.binance_client import binance_client

class PriceEngine:
    """价格引擎 - 负责生成和管理股票价格变动"""
    
    def __init__(self, market_data: MarketData):
        self.market_data = market_data
        
        # 从配置文件获取市场参数
        market_config = config_manager.get_config().get('market_settings', {})
        self.volatility = market_config.get('base_volatility', 0.02)  # 基础波动率
        self.trend = 0.0  # 市场趋势 (-1到1)
        self.trend_strength = market_config.get('trend_strength', 0.1)  # 趋势强度
        self.manipulation_factor = 0.0  # 操控因子
        self.last_update_time = time.time()
        self.price_update_interval = market_config.get('price_update_interval', 1.0)  # 价格更新间隔
        
        # 交易影响系统
        self.trade_impacts = {}  # 存储每只股票的交易影响
        self.impact_decay_rate = 0.95  # 影响衰减率
        
        # 市场情绪
        self.market_sentiment = 0.0  # -1 (极度悲观) 到 1 (极度乐观)
        
        # K线数据缓存 - 用于增量更新
        self.kline_cache = {}  # 存储每只股票的历史K线数据
        self.last_kline_update = {}  # 记录每只股票最后更新时间
        self.volume_sensitivity = 0.01  # 成交量敏感度 - 增加交易量对价格的影响
        
        # 币安API集成
        self.binance_client = binance_client
        self.use_real_data = self.binance_client.is_enabled()
        self.crypto_symbols = self.binance_client.get_supported_symbols()
        self.last_binance_update = 0
        self.binance_update_interval = config_manager.get_config().get('binance', {}).get('price_update_interval', 5)
        
        print(f"🔗 价格引擎初始化完成，币安API: {'启用' if self.use_real_data else '禁用'}")
        if self.use_real_data:
            print(f"📊 支持的加密货币: {', '.join(self.crypto_symbols)}")
    
    def is_crypto_symbol(self, symbol: str) -> bool:
        """检查是否为加密货币交易对"""
        return symbol in self.crypto_symbols
    
    def get_real_crypto_price(self, symbol: str) -> float:
        """获取真实的加密货币价格"""
        if not self.use_real_data or not self.is_crypto_symbol(symbol):
            return None
        
        try:
            price = self.binance_client.get_symbol_price(symbol)
            if price is not None:
                print(f"💰 获取 {symbol} 真实价格: ${price:.4f}")
            return price
        except Exception as e:
            print(f"❌ 获取 {symbol} 价格失败: {e}")
            return None
    
    def update_crypto_prices(self):
        """批量更新加密货币价格"""
        if not self.use_real_data:
            return
        
        current_time = time.time()
        if current_time - self.last_binance_update < self.binance_update_interval:
            return
        
        try:
            # 批量获取所有加密货币价格
            prices = self.binance_client.get_all_prices()
            
            for symbol, price in prices.items():
                if symbol in self.market_data.stocks:
                    # 更新现有股票的价格
                    old_price = self.market_data.stocks[symbol].current_price
                    self.market_data.update_price(symbol, price)
                    print(f"📈 更新 {symbol}: ${old_price:.4f} → ${price:.4f}")
                else:
                    # 添加新的加密货币
                    self.add_crypto_stock(symbol, price)
            
            self.last_binance_update = current_time
            print(f"🔄 批量更新了 {len(prices)} 个加密货币价格")
            
        except Exception as e:
            print(f"❌ 批量更新加密货币价格失败: {e}")
    
    def add_crypto_stock(self, symbol: str, price: float):
        """添加新的加密货币到市场数据"""
        try:
            # 创建加密货币名称映射
            crypto_names = {
                'BTCUSDT': '比特币',
                'ETHUSDT': '以太坊',
                'BNBUSDT': '币安币',
                'ADAUSDT': '卡尔达诺',
                'SOLUSDT': 'Solana',
                'XRPUSDT': '瑞波币',
                'DOTUSDT': '波卡',
                'DOGEUSDT': '狗狗币',
                'AVAXUSDT': '雪崩',
                'MATICUSDT': 'Polygon'
            }
            
            name = crypto_names.get(symbol, symbol)
            
            # 生成一些历史价格数据
            price_history = []
            base_price = price
            for i in range(30):
                variation = random.uniform(-0.05, 0.05)
                historical_price = base_price * (1 + variation)
                price_history.append(round(historical_price, 4))
                base_price = historical_price
            
            # 添加到市场数据
            self.market_data.add_stock(symbol, name, price, price_history)
            print(f"➕ 添加新加密货币: {name} ({symbol}) - ${price:.4f}")
            
        except Exception as e:
            print(f"❌ 添加加密货币 {symbol} 失败: {e}")
    
    def add_new_crypto_stock(self, symbol: str, price: float):
        """添加新的加密货币股票到市场数据"""
        if symbol not in self.market_data.stocks:
            # 导入Stock类
            from qbot.models.models import Stock
            
            # 创建新的股票对象
            stock = Stock()
            stock.symbol = symbol
            stock.name = f"Cryptocurrency {symbol}"
            stock.current_price = price
            stock.open_price = price
            stock.high_price = price
            stock.low_price = price
            stock.volume = 0
            stock.price_history = [price]  # 初始化价格历史
            
            self.market_data.add_stock(stock)
            print(f"✅ 添加新的加密货币: {symbol} 价格: ${price:.4f}")

    def generate_price_movement(self, current_price: float, symbol: str = None, time_step: float = 1.0) -> float:
        """生成价格变动
        
        Args:
            current_price: 当前价格
            symbol: 股票代码
            time_step: 时间步长（秒）
            
        Returns:
            新价格
        """
        # 基础随机游走
        random_factor = random.gauss(0, 1) * self.volatility * math.sqrt(time_step)
        
        # 趋势影响
        trend_impact = self.trend * self.trend_strength * 0.001 * time_step
        
        # 庄家操控影响
        manipulation_impact = self.manipulation_factor * 0.005 * time_step
        
        # 交易影响
        trade_impact = 0.0
        if symbol and symbol in self.trade_impacts:
            trade_impact = self.trade_impacts[symbol] * 0.5 * time_step  # 增加交易影响系数从0.01到0.5
        
        # 均值回归因子（防止价格偏离太远）
        mean_reversion = -0.0001 * (current_price - 100) * time_step
        
        # 计算价格变化率
        price_change_rate = random_factor + trend_impact + manipulation_impact + trade_impact + mean_reversion
        
        # 限制单次价格变化幅度，防止价格过于极端
        max_change = 0.2  # 单次最大变化20%
        price_change_rate = max(-max_change, min(max_change, price_change_rate))
        
        # 应用价格变化
        new_price = current_price * (1 + price_change_rate)
        
        # 确保价格不会变成负数或过小，同时设置合理的最低价格
        min_price = max(0.01, current_price * 0.5)  # 最低价格不低于当前价格的50%
        return max(new_price, min_price)
    
    def update_all_prices(self):
        """更新所有股票价格"""
        current_time = time.time()
        time_delta = current_time - self.last_update_time
        
        # 首先更新加密货币价格（如果启用了币安API）
        self.update_crypto_prices()
        
        for symbol, stock in self.market_data.stocks.items():
            # 如果是加密货币且启用了真实数据，尝试获取真实价格
            if self.is_crypto_symbol(symbol) and self.use_real_data:
                real_price = self.get_real_crypto_price(symbol)
                if real_price is not None:
                    # 使用真实价格，但仍然应用一些交易影响
                    trade_impact = 0.0
                    if symbol in self.trade_impacts:
                        trade_impact = self.trade_impacts[symbol] * 0.1  # 减少对真实价格的影响
                    
                    adjusted_price = real_price * (1 + trade_impact)
                    self.market_data.update_price(symbol, adjusted_price)
                    continue
            
            # 对于传统股票或无法获取真实价格的情况，使用模拟价格生成
            new_price = self.generate_price_movement(stock.current_price, symbol, time_delta)
            self.market_data.update_price(symbol, new_price)
        
        # 衰减交易影响
        self.decay_trade_impacts()
        self.last_update_time = current_time
    
    def set_trend(self, trend: float):
        """设置市场趋势 (-1到1)"""
        self.trend = max(-1.0, min(1.0, trend))
        trend_desc = "上涨" if trend > 0 else "下跌" if trend < 0 else "横盘"
        print(f"📈 设置市场趋势: {trend_desc} (强度: {abs(trend):.3f})")
    
    def set_manipulation(self, manipulation: float):
        """设置庄家操控强度 (-1到1)"""
        self.manipulation_factor = max(-1.0, min(1.0, manipulation))
        manip_desc = "拉升" if manipulation > 0 else "打压" if manipulation < 0 else "中性"
        print(f"🎮 设置价格操控: {manip_desc} (强度: {abs(manipulation):.3f})")
    
    def set_volatility(self, volatility: float):
        """设置市场波动率"""
        self.volatility = max(0.001, min(0.1, volatility))
        print(f"📊 设置市场波动率: {volatility:.3f} ({volatility*100:.1f}%)")
    
    def apply_trade_impact(self, symbol: str, quantity: int, trade_type: str):
        """应用交易对价格的影响
        
        Args:
            symbol: 股票代码
            quantity: 交易数量
            trade_type: 交易类型 ('buy' 或 'sell')
        """
        if symbol not in self.market_data.stocks:
            return
        
        # 计算交易影响强度
        stock = self.market_data.stocks[symbol]
        
        # 基于交易量计算影响
        volume_impact = quantity * self.volume_sensitivity
        
        # 买入推高价格，卖出压低价格
        if trade_type == 'buy':
            impact = volume_impact
        else:  # sell
            impact = -volume_impact
        
        # 累加到现有影响中
        if symbol not in self.trade_impacts:
            self.trade_impacts[symbol] = 0.0
        
        self.trade_impacts[symbol] += impact
        
        # 限制影响范围 - 增加影响范围以允许更大的价格变动
        self.trade_impacts[symbol] = max(-1.0, min(1.0, self.trade_impacts[symbol]))
        
        print(f"交易影响: {symbol} {trade_type} {quantity}股, 影响: {impact:.4f}")
    
    def decay_trade_impacts(self):
        """衰减交易影响"""
        for symbol in list(self.trade_impacts.keys()):
            self.trade_impacts[symbol] *= self.impact_decay_rate
            
            # 移除影响很小的项
            if abs(self.trade_impacts[symbol]) < 0.0001:
                del self.trade_impacts[symbol]
    
    def get_trade_impact(self, symbol: str) -> float:
        """获取股票的当前交易影响"""
        return self.trade_impacts.get(symbol, 0.0)
    
    def generate_kline_data(self, symbol: str, period_minutes: int = 100) -> Dict:
        """生成K线数据 - 支持增量更新
        
        Args:
            symbol: 股票代码
            period_minutes: 显示多少个时间周期的数据
            
        Returns:
            K线数据字典，包含多个时间点的数据
        """
        if symbol not in self.market_data.stocks:
            return {}
        
        stock = self.market_data.stocks[symbol]
        current_time = int(time.time())
        current_minute = current_time // 60  # 当前分钟数
        
        # 初始化缓存
        if symbol not in self.kline_cache:
            self._initialize_kline_cache(symbol, period_minutes)
        
        cache = self.kline_cache[symbol]
        last_update_minute = self.last_kline_update.get(symbol, 0)
        
        # 检查是否需要添加新的K线数据点
        if current_minute > last_update_minute:
            self._add_new_kline_point(symbol, current_minute)
            self.last_kline_update[symbol] = current_minute
        
        # 保持数据长度不超过period_minutes
        if len(cache['timestamp']) > period_minutes:
            excess = len(cache['timestamp']) - period_minutes
            for key in cache:
                cache[key] = cache[key][excess:]
        
        return cache.copy()
    
    def _initialize_kline_cache(self, symbol: str, period_minutes: int):
        """初始化K线数据缓存"""
        stock = self.market_data.stocks[symbol]
        current_time = int(time.time())
        current_minute = current_time // 60
        
        timestamps = []
        opens = []
        highs = []
        lows = []
        closes = []
        volumes = []
        
        # 从开盘价开始生成历史数据
        current_price = stock.open_price
        
        for i in range(period_minutes):
            # 生成历史时间戳
            timestamp_minute = current_minute - (period_minutes - i - 1)
            timestamp = timestamp_minute * 60
            timestamps.append(timestamp)
            
            # 生成该周期的OHLC数据
            open_price = current_price
            opens.append(round(open_price, 2))
            
            # 模拟该周期内的价格变动
            period_prices = [open_price]
            for _ in range(10):  # 每分钟10个价格点
                new_price = self.generate_price_movement(period_prices[-1], symbol, 0.1)
                period_prices.append(new_price)
            
            close_price = period_prices[-1]
            high_price = max(period_prices)
            low_price = min(period_prices)
            
            highs.append(round(high_price, 2))
            lows.append(round(low_price, 2))
            closes.append(round(close_price, 2))
            
            # 模拟成交量
            base_volume = 1000
            volume_volatility = abs(close_price - open_price) / open_price if open_price > 0 else 0
            volume = int(base_volume * (1 + volume_volatility * 10) * random.uniform(0.5, 2.0))
            volumes.append(volume)
            
            # 下一个周期的开盘价是当前周期的收盘价
            current_price = close_price
        
        self.kline_cache[symbol] = {
            'timestamp': timestamps,
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes
        }
    
    def _add_new_kline_point(self, symbol: str, current_minute: int):
        """添加新的K线数据点"""
        stock = self.market_data.stocks[symbol]
        cache = self.kline_cache[symbol]
        
        # 新时间戳
        new_timestamp = current_minute * 60
        
        # 获取上一个收盘价作为新的开盘价
        if cache['close']:
            open_price = cache['close'][-1]
        else:
            open_price = stock.open_price
        
        # 生成新的价格数据
        period_prices = [open_price]
        for _ in range(10):  # 每分钟10个价格点
            new_price = self.generate_price_movement(period_prices[-1], symbol, 0.1)
            period_prices.append(new_price)
        
        close_price = stock.current_price  # 使用当前实际价格作为收盘价
        high_price = max(max(period_prices), close_price)
        low_price = min(min(period_prices), close_price)
        
        # 模拟成交量
        base_volume = 1000
        volume_volatility = abs(close_price - open_price) / open_price if open_price > 0 else 0
        volume = int(base_volume * (1 + volume_volatility * 10) * random.uniform(0.5, 2.0))
        
        # 添加新数据点
        cache['timestamp'].append(new_timestamp)
        cache['open'].append(round(open_price, 2))
        cache['high'].append(round(high_price, 2))
        cache['low'].append(round(low_price, 2))
        cache['close'].append(round(close_price, 2))
        cache['volume'].append(volume)
    
    def simulate_market_crash(self, intensity: float = 0.1):
        """模拟市场崩盘
        
        Args:
            intensity: 崩盘强度 (0到1)
        """
        # 增强崩盘效果
        crash_factor = -intensity * random.uniform(0.1, 0.3)
        print(f"💥 市场崩盘！下跌幅度: {abs(crash_factor)*100:.1f}%")
        
        for symbol, stock in self.market_data.stocks.items():
            old_price = stock.current_price
            new_price = max(stock.current_price * (1 + crash_factor), 0.01)
            self.market_data.update_price(symbol, new_price)
            print(f"  {symbol}: {old_price:.2f} → {new_price:.2f} ({((new_price-old_price)/old_price)*100:+.1f}%)")
    
    def simulate_market_surge(self, intensity: float = 0.1):
        """模拟市场暴涨
        
        Args:
            intensity: 暴涨强度 (0到1)
        """
        # 增强暴涨效果
        surge_factor = intensity * random.uniform(0.1, 0.3)
        print(f"🚀 市场暴涨！上涨幅度: {surge_factor*100:.1f}%")
        
        for symbol, stock in self.market_data.stocks.items():
            old_price = stock.current_price
            new_price = stock.current_price * (1 + surge_factor)
            self.market_data.update_price(symbol, new_price)
            print(f"  {symbol}: {old_price:.2f} → {new_price:.2f} ({((new_price-old_price)/old_price)*100:+.1f}%)")
    
    def add_market_noise(self, noise_level: float = 0.01):
        """添加市场噪音
        
        Args:
            noise_level: 噪音水平
        """
        for symbol, stock in self.market_data.stocks.items():
            noise = random.gauss(0, noise_level)
            new_price = stock.current_price * (1 + noise)
            self.market_data.update_price(symbol, max(new_price, 0.01))

class TechnicalIndicators:
    """技术指标计算"""
    
    @staticmethod
    def sma(prices: List[float], period: int) -> float:
        """简单移动平均线"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        return sum(prices[-period:]) / period
    
    @staticmethod
    def ema(prices: List[float], period: int) -> float:
        """指数移动平均线"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> float:
        """相对强弱指数"""
        if len(prices) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50.0
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2) -> Tuple[float, float, float]:
        """布林带
        
        Returns:
            (上轨, 中轨, 下轨)
        """
        if len(prices) < period:
            price = prices[-1] if prices else 0
            return price, price, price
        
        recent_prices = prices[-period:]
        middle = sum(recent_prices) / period
        
        variance = sum((p - middle) ** 2 for p in recent_prices) / period
        std = math.sqrt(variance)
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        
        return upper, middle, lower