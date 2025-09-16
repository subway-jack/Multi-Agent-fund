#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票模拟器应用程序主类
提供统一的应用程序接口和组件管理
"""

import sys
import threading
import time
from typing import Dict, List, Optional
from src.models.models import Stock, MarketData
from src.core.trading_system import TradingEngine
from src.core.banker_interface import BankerInterface
from src.interfaces.visualization import RealTimeVisualizer
from src.core.price_engine import PriceEngine
from src.core.ai_traders import TraderManager
from src.utils.font_loader import font_manager
from src.core.user_trader import UserTrader
from src.config.config_manager import config_manager

class StockSimulatorApp:
    """股票模拟器应用程序主类"""
    
    def __init__(self):
        """初始化应用程序"""
        self._initialized = False
        self._components = {}
        self._stocks = {}
        self._simulation_running = False
        self._simulation_thread = None
        
        # 初始化字体管理器
        font_manager.initialize()
        
        print("📊 股票模拟器应用程序初始化中...")
    
    def initialize(self):
        """初始化所有组件"""
        if self._initialized:
            return
        
        print("🔧 初始化核心组件...")
        
        # 初始化股票数据
        self._init_stocks()
        
        # 初始化市场数据
        self._components['market_data'] = MarketData()
        for stock in self._stocks.values():
            self._components['market_data'].add_stock(stock)
        
        # 初始化AI交易者管理器
        self._components['trader_manager'] = TraderManager()
        self._components['trader_manager'].create_traders(50, 50)
        
        # 初始化价格引擎
        self._components['price_engine'] = PriceEngine(self._components['market_data'])
        
        # 初始化交易引擎（传递价格引擎引用）
        self._components['trading_engine'] = TradingEngine(
            self._components['market_data'], 
            self._components['trader_manager'],
            self._components['price_engine']
        )
        
        # 初始化庄家接口
        self._components['banker'] = BankerInterface(
            self._components['price_engine'],
            self._components['trading_engine'],
            self._components['trader_manager']
        )
        
        # 初始化可视化器
        self._components['visualizer'] = RealTimeVisualizer(
            self._components['trading_engine'],
            self._components['banker']
        )
        
        # 初始化用户交易员（传递价格引擎引用）
        user_config = config_manager.get_config('user')
        self._components['user_trader'] = UserTrader(
            self._components['trading_engine'],
            self._components['price_engine'],
            initial_balance=user_config.get('initial_balance', 100000.0)
        )
        
        self._initialized = True
        print("✅ 所有组件初始化完成")
    
    def _init_stocks(self):
        """初始化股票数据"""
        # 从配置文件中读取股票数据
        market_config = config_manager.get_config('market')
        initial_stocks = market_config.get('initial_stocks', {})
        
        self._stocks = {}
        for symbol, stock_info in initial_stocks.items():
            price = stock_info['price']
            name = stock_info['name']
            price_history = stock_info.get('price_history', None)
            
            # 创建股票对象，传入历史价格数据
            stock = Stock(
                symbol=symbol,
                name=name,
                current_price=price,
                open_price=price,
                high_price=price,
                low_price=price,
                price_history=price_history
            )
            self._stocks[symbol] = stock
        
        print(f"📈 初始化了 {len(self._stocks)} 只股票")
    
    def get_component(self, name: str):
        """获取组件
        
        Args:
            name: 组件名称
            
        Returns:
            组件实例
        """
        if not self._initialized:
            self.initialize()
        
        return self._components.get(name)
    
    def get_stocks(self) -> Dict[str, Stock]:
        """获取股票数据
        
        Returns:
            股票字典
        """
        return self._stocks.copy()
    
    def start_simulation(self):
        """启动模拟"""
        if not self._initialized:
            self.initialize()
        
        if self._simulation_running:
            print("⚠️ 模拟已在运行中")
            return
        
        self._simulation_running = True
        self._simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self._simulation_thread.start()
        print("🚀 模拟已启动")
    
    def stop_simulation(self):
        """停止模拟"""
        if not self._simulation_running:
            print("⚠️ 模拟未在运行")
            return
        
        self._simulation_running = False
        if self._simulation_thread:
            self._simulation_thread.join(timeout=1.0)
        print("⏹️ 模拟已停止")
    
    def _simulation_loop(self):
        """模拟循环"""
        price_update_counter = 0
        while self._simulation_running:
            try:
                # 执行交易（主要价格驱动力）
                self._components['trading_engine'].process_ai_decisions(time.time())
                
                # 减少价格引擎的自动更新频率（每10次循环更新一次，且影响很小）
                price_update_counter += 1
                if price_update_counter >= 10:
                    # 临时降低价格引擎的影响
                    original_volatility = self._components['price_engine'].volatility
                    self._components['price_engine'].volatility *= 0.1  # 大幅降低波动率
                    self._components['price_engine'].update_all_prices()
                    self._components['price_engine'].volatility = original_volatility  # 恢复原始波动率
                    price_update_counter = 0
                
                time.sleep(0.1)  # 100ms更新间隔
                
            except Exception as e:
                print(f"❌ 模拟循环错误: {e}")
                break
    
    def is_simulation_running(self) -> bool:
        """检查模拟是否在运行
        
        Returns:
            bool: 模拟运行状态
        """
        return self._simulation_running
    
    def reset(self):
        """重置应用程序"""
        print("🔄 重置应用程序...")
        
        # 停止模拟
        self.stop_simulation()
        
        # 重置组件
        if self._initialized:
            # 重置庄家参数
            banker = self._components.get('banker')
            if banker:
                banker.reset_all_controls()
            
            # 重新初始化股票价格
            for symbol, stock in self._stocks.items():
                original_price = {
                    'AAPL': 150.0,
                    'TSLA': 800.0,
                    'GOOGL': 2800.0,
                    'MSFT': 300.0,
                    'AMZN': 3200.0
                }.get(symbol, 100.0)
                
                stock.current_price = original_price
                stock.open_price = original_price
                stock.high_price = original_price
                stock.low_price = original_price
            
            # 重置交易者
            trader_manager = self._components.get('trader_manager')
            if trader_manager:
                trader_manager.reset_all_traders()
        
        print("✅ 应用程序重置完成")
    
    def get_status(self) -> Dict:
        """获取应用程序状态
        
        Returns:
            Dict: 状态信息
        """
        if not self._initialized:
            return {'initialized': False, 'simulation_running': False}
        
        trading_engine = self._components.get('trading_engine')
        trader_manager = self._components.get('trader_manager')
        
        status = {
            'initialized': self._initialized,
            'simulation_running': self._simulation_running,
            'stocks_count': len(self._stocks),
            'components_loaded': len(self._components)
        }
        
        if trading_engine:
            stats = trading_engine.get_market_stats()
            status.update({
                'total_trades': stats.get('total_trades', 0),
                'total_volume': stats.get('total_volume', 0),
                'pending_orders': stats.get('pending_orders', 0)
            })
        
        if trader_manager:
            trader_stats = trader_manager.get_trader_stats()
            status.update({
                'total_traders': trader_stats.get('total_traders', 0),
                'active_positions': trader_stats.get('active_positions', 0)
            })
        
        return status
    
    def cleanup(self):
        """清理资源"""
        print("🧹 清理应用程序资源...")
        self.stop_simulation()
        self._components.clear()
        self._stocks.clear()
        self._initialized = False
        print("✅ 资源清理完成")

# 全局应用程序实例
app = StockSimulatorApp()