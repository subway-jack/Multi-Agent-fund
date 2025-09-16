import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle
import numpy as np
import time
from typing import Dict, List, Tuple
from collections import deque
from src.models.models import Stock
from src.core.trading_system import TradingEngine
from src.core.banker_interface import BankerInterface

class RealTimeVisualizer:
    """实时可视化器"""
    
    def __init__(self, trading_engine: TradingEngine, banker_interface: BankerInterface):
        self.trading_engine = trading_engine
        self.banker_interface = banker_interface
        
        # 数据存储
        self.price_history = {}
        self.volume_history = {}
        self.trade_history = deque(maxlen=100)
        self.pnl_history = {'bull': deque(maxlen=100), 'bear': deque(maxlen=100)}
        
        # 图表设置
        plt.style.use('dark_background')
        self.fig = None
        self.axes = {}
        
    def setup_dashboard(self):
        """设置仪表板"""
        self.fig = plt.figure(figsize=(16, 12))
        self.fig.suptitle('股票模拟器 - 实时监控面板', fontsize=16, color='white')
        
        # 创建子图
        gs = self.fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 价格走势图
        self.axes['price'] = self.fig.add_subplot(gs[0, :])
        self.axes['price'].set_title('股票价格走势', color='white')
        self.axes['price'].set_ylabel('价格', color='white')
        
        # 成交量图
        self.axes['volume'] = self.fig.add_subplot(gs[1, 0])
        self.axes['volume'].set_title('成交量', color='white')
        self.axes['volume'].set_ylabel('成交量', color='white')
        
        # 订单簿深度图
        self.axes['depth'] = self.fig.add_subplot(gs[1, 1])
        self.axes['depth'].set_title('订单簿深度', color='white')
        self.axes['depth'].set_ylabel('价格', color='white')
        
        # 盈亏分布图
        self.axes['pnl'] = self.fig.add_subplot(gs[1, 2])
        self.axes['pnl'].set_title('盈亏分布', color='white')
        self.axes['pnl'].set_ylabel('盈亏', color='white')
        
        # 交易者表现图
        self.axes['performance'] = self.fig.add_subplot(gs[2, 0])
        self.axes['performance'].set_title('交易者表现', color='white')
        self.axes['performance'].set_ylabel('收益率', color='white')
        
        # 市场情绪图
        self.axes['sentiment'] = self.fig.add_subplot(gs[2, 1])
        self.axes['sentiment'].set_title('市场情绪', color='white')
        
        # 庄家操控历史
        self.axes['manipulation'] = self.fig.add_subplot(gs[2, 2])
        self.axes['manipulation'].set_title('庄家操控历史', color='white')
        
        # 设置图表样式
        for ax in self.axes.values():
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')
    
    def update_price_chart(self):
        """更新价格走势图"""
        ax = self.axes['price']
        ax.clear()
        ax.set_title('股票价格走势', color='white')
        ax.set_ylabel('价格', color='white')
        
        for symbol, stock in self.trading_engine.market_data.stocks.items():
            if len(stock.price_history) > 1:
                times = list(range(len(stock.price_history)))
                ax.plot(times, stock.price_history, label=symbol, linewidth=2)
        
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def update_volume_chart(self):
        """更新成交量图"""
        ax = self.axes['volume']
        ax.clear()
        ax.set_title('成交量', color='white')
        ax.set_ylabel('成交量', color='white')
        
        symbols = list(self.trading_engine.market_data.stocks.keys())
        volumes = [stock.volume for stock in self.trading_engine.market_data.stocks.values()]
        
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57']
        bars = ax.bar(symbols, volumes, color=colors[:len(symbols)])
        
        # 添加数值标签
        for bar, volume in zip(bars, volumes):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                   f'{volume:,}', ha='center', va='bottom', color='white')
        
        ax.grid(True, alpha=0.3)
    
    def update_depth_chart(self, symbol: str = None):
        """更新订单簿深度图"""
        ax = self.axes['depth']
        ax.clear()
        ax.set_title('订单簿深度', color='white')
        ax.set_ylabel('价格', color='white')
        ax.set_xlabel('数量', color='white')
        
        if not symbol:
            symbol = list(self.trading_engine.order_books.keys())[0] if self.trading_engine.order_books else None
        
        if symbol and symbol in self.trading_engine.order_books:
            order_book = self.trading_engine.order_books[symbol]
            depth = order_book.get_depth(10)
            
            # 买单（绿色）
            if depth['bids']:
                bid_prices = [bid[0] for bid in depth['bids']]
                bid_quantities = [bid[1] for bid in depth['bids']]
                ax.barh(bid_prices, bid_quantities, color='#2ecc71', alpha=0.7, label='买单')
            
            # 卖单（红色）
            if depth['asks']:
                ask_prices = [ask[0] for ask in depth['asks']]
                ask_quantities = [-ask[1] for ask in depth['asks']]  # 负数显示在左侧
                ax.barh(ask_prices, ask_quantities, color='#e74c3c', alpha=0.7, label='卖单')
            
            ax.legend()
            ax.axvline(x=0, color='white', linestyle='--', alpha=0.5)
        
        ax.grid(True, alpha=0.3)
    
    def update_pnl_chart(self):
        """更新盈亏分布图"""
        ax = self.axes['pnl']
        ax.clear()
        ax.set_title('盈亏分布', color='white')
        ax.set_ylabel('交易者数量', color='white')
        ax.set_xlabel('盈亏', color='white')
        
        performance = self.trading_engine.get_trader_performance()
        
        bull_pnl = [p['total_pnl'] for p in performance.values() if p['type'] == 'bull']
        bear_pnl = [p['total_pnl'] for p in performance.values() if p['type'] == 'bear']
        
        if bull_pnl or bear_pnl:
            bins = np.linspace(-50000, 50000, 20)
            
            if bull_pnl:
                ax.hist(bull_pnl, bins=bins, alpha=0.7, color='#2ecc71', label='做多交易者')
            
            if bear_pnl:
                ax.hist(bear_pnl, bins=bins, alpha=0.7, color='#e74c3c', label='做空交易者')
            
            ax.axvline(x=0, color='white', linestyle='--', alpha=0.5)
            ax.legend()
        
        ax.grid(True, alpha=0.3)
    
    def update_performance_chart(self):
        """更新交易者表现图"""
        ax = self.axes['performance']
        ax.clear()
        ax.set_title('交易者表现', color='white')
        ax.set_ylabel('平均收益率', color='white')
        
        analysis = self.banker_interface.analyze_trader_behavior()
        
        categories = ['做多交易者', '做空交易者']
        returns = [analysis['bull_traders']['avg_return'], analysis['bear_traders']['avg_return']]
        colors = ['#2ecc71', '#e74c3c']
        
        bars = ax.bar(categories, returns, color=colors)
        
        # 添加数值标签
        for bar, ret in zip(bars, returns):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + (height*0.01 if height > 0 else height*0.01),
                   f'{ret:.2%}', ha='center', va='bottom' if height > 0 else 'top', color='white')
        
        ax.axhline(y=0, color='white', linestyle='--', alpha=0.5)
        ax.grid(True, alpha=0.3)
    
    def update_sentiment_chart(self):
        """更新市场情绪图"""
        ax = self.axes['sentiment']
        ax.clear()
        ax.set_title('市场情绪', color='white')
        
        analysis = self.banker_interface.analyze_trader_behavior()
        sentiment = analysis['market_sentiment']
        
        # 创建饼图
        labels = ['做多盈利', '做多亏损', '做空盈利', '做空亏损']
        bull_profitable = analysis['bull_traders']['profitable_count']
        bull_losing = analysis['bull_traders']['count'] - bull_profitable
        bear_profitable = analysis['bear_traders']['profitable_count']
        bear_losing = analysis['bear_traders']['count'] - bear_profitable
        
        sizes = [bull_profitable, bull_losing, bear_profitable, bear_losing]
        colors = ['#2ecc71', '#ff6b6b', '#3498db', '#e67e22']
        
        if sum(sizes) > 0:
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                            startangle=90, textprops={'color': 'white'})
        
    def update_manipulation_chart(self):
        """更新庄家操控历史图"""
        ax = self.axes['manipulation']
        ax.clear()
        ax.set_title('庄家操控历史', color='white')
        ax.set_ylabel('操控强度', color='white')
        
        history = self.banker_interface.get_manipulation_history(20)
        
        if history:
            times = list(range(len(history)))
            actions = []
            
            for h in history:
                if h['action'] == 'set_trend':
                    actions.append(h['parameters'].get('trend', 0))
                elif h['action'] == 'manipulate_price':
                    actions.append(h['parameters'].get('strength', 0))
                else:
                    actions.append(0)
            
            colors = ['#2ecc71' if a > 0 else '#e74c3c' if a < 0 else '#95a5a6' for a in actions]
            ax.bar(times, actions, color=colors)
            
            ax.axhline(y=0, color='white', linestyle='--', alpha=0.5)
        
        ax.grid(True, alpha=0.3)
    
    def update_all_charts(self):
        """更新所有图表"""
        self.update_price_chart()
        self.update_volume_chart()
        self.update_depth_chart()
        self.update_pnl_chart()
        self.update_performance_chart()
        self.update_sentiment_chart()
        self.update_manipulation_chart()
        
        plt.tight_layout()
    
    def start_real_time_display(self, update_interval: int = 2000):
        """启动实时显示
        
        Args:
            update_interval: 更新间隔（毫秒）
        """
        if not self.fig:
            self.setup_dashboard()
        
        def animate(frame):
            self.update_all_charts()
            return []
        
        ani = animation.FuncAnimation(self.fig, animate, interval=update_interval, blit=False)
        plt.show()
        return ani
    
    def save_snapshot(self, filename: str = None):
        """保存当前图表快照"""
        if not filename:
            timestamp = int(time.time())
            filename = f"market_snapshot_{timestamp}.png"
        
        if self.fig:
            self.update_all_charts()
            self.fig.savefig(filename, dpi=300, bbox_inches='tight', 
                           facecolor='black', edgecolor='none')
            print(f"📸 市场快照已保存: {filename}")
    
    def generate_report(self) -> str:
        """生成市场报告"""
        market_summary = self.trading_engine.get_market_summary()
        trader_analysis = self.banker_interface.analyze_trader_behavior()
        control_panel = self.banker_interface.get_market_control_panel()
        
        report = f"""
📊 股票模拟器市场报告
{'='*50}

📈 市场概况:
  总交易数: {market_summary['total_trades']:,}
  总成交量: {market_summary['total_volume']:,}
  总成交额: {market_summary['total_value']:,.2f}
  待处理订单: {market_summary['pending_orders']}

👥 交易者表现:
  做多交易者: {trader_analysis['bull_traders']['count']}
    - 平均收益率: {trader_analysis['bull_traders']['avg_return']:.2%}
    - 盈利人数: {trader_analysis['bull_traders']['profitable_count']}
    - 总交易数: {trader_analysis['bull_traders']['total_trades']}
  
  做空交易者: {trader_analysis['bear_traders']['count']}
    - 平均收益率: {trader_analysis['bear_traders']['avg_return']:.2%}
    - 盈利人数: {trader_analysis['bear_traders']['profitable_count']}
    - 总交易数: {trader_analysis['bear_traders']['total_trades']}

💰 庄家状态:
  资金余额: {control_panel['banker_status']['balance']:,.2f}
  持仓数量: {len(control_panel['banker_status']['positions'])}
  操控次数: {control_panel['banker_status']['total_manipulations']}

📊 市场参数:
  当前趋势: {control_panel['market_status']['current_trend']:+.3f}
  波动率: {control_panel['market_status']['current_volatility']:.3f}
  操控因子: {control_panel['market_status']['manipulation_factor']:+.3f}

💹 股票价格:
"""
        
        for symbol, price in control_panel['stock_prices'].items():
            stock = self.trading_engine.market_data.stocks[symbol]
            change = ((price - stock.open_price) / stock.open_price) * 100
            report += f"  {symbol}: {price:.2f} ({change:+.2f}%)\n"
        
        report += f"\n📅 报告时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report