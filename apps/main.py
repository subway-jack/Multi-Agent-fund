#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票模拟器主程序
作者: AI Assistant
功能: 模拟股票交易市场，包含庄家操控和AI交易者
"""

import time
import threading
import sys
import os
from typing import Dict, List

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 导入自定义模块
from src.models.models import Stock, MarketData
from src.core.price_engine import PriceEngine
from src.core.ai_traders import TraderManager
from src.core.trading_system import TradingEngine
from src.core.banker_interface import BankerInterface
from src.interfaces.visualization import RealTimeVisualizer
from src.config.config_manager import config_manager

class StockSimulator:
    """股票模拟器主类"""
    
    def __init__(self):
        # 初始化核心组件
        self.market_data = MarketData()
        self.price_engine = PriceEngine(self.market_data)
        self.trader_manager = TraderManager()
        self.trading_engine = TradingEngine(self.market_data, self.trader_manager)
        self.banker_interface = BankerInterface(self.price_engine, self.trading_engine, self.trader_manager)
        self.visualizer = RealTimeVisualizer(self.trading_engine, self.banker_interface)
        
        # 运行状态
        self.is_running = False
        self.simulation_thread = None
        
    def initialize_market(self):
        """初始化市场"""
        print("🚀 正在初始化股票模拟器...")
        
        # 从配置文件中读取股票数据
        market_config = config_manager.get_config('market')
        initial_stocks = market_config.get('initial_stocks', {})
        
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
            self.market_data.add_stock(stock)
        
        # 创建AI交易者
        print("👥 创建AI交易者...")
        self.trader_manager.create_traders(num_bulls=50, num_bears=50)
        
        print("✅ 市场初始化完成!")
        print(f"📊 股票数量: {len(self.market_data.stocks)}")
        print(f"👥 交易者数量: {len(self.trader_manager.traders)}")
        
    def start_simulation(self):
        """启动模拟"""
        if self.is_running:
            print("⚠️  模拟器已在运行中")
            return
        
        self.is_running = True
        self.simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.simulation_thread.start()
        print("🎮 股票模拟器已启动!")
    
    def stop_simulation(self):
        """停止模拟"""
        self.is_running = False
        if self.simulation_thread:
            self.simulation_thread.join(timeout=1)
        print("⏹️  股票模拟器已停止")
    
    def _simulation_loop(self):
        """模拟循环"""
        while self.is_running:
            try:
                current_time = time.time()
                
                # 更新价格
                self.price_engine.update_all_prices()
                
                # 处理AI交易者决策
                self.trading_engine.process_ai_decisions(current_time)
                
                # 清理过期订单
                self.trading_engine.cleanup_old_orders()
                
                # 休眠
                time.sleep(0.1)  # 100ms更新一次
                
            except Exception as e:
                print(f"❌ 模拟循环错误: {e}")
                time.sleep(1)
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
🎮 股票模拟器 - 庄家控制台

📊 基本命令:
  status          - 显示市场状态
  report          - 生成市场报告
  traders         - 显示交易者统计
  help            - 显示此帮助信息
  quit/exit       - 退出程序

🎯 庄家操控命令:
  trend <值>      - 设置市场趋势 (-1到1)
  manipulate <股票> <强度> - 操控股票价格 (-1到1)
  volatility <值> - 设置波动率 (0.001到0.1)
  crash <强度>    - 触发市场崩盘 (0到1)
  surge <强度>    - 触发市场暴涨 (0到1)
  noise <强度>    - 增加市场噪音 (0到1)
  reset           - 重置所有控制参数

💰 庄家交易命令:
  buy <股票> <数量> [价格偏移]   - 庄家买入
  sell <股票> <数量> [价格偏移]  - 庄家卖出

📈 可视化命令:
  chart           - 启动实时图表
  snapshot        - 保存图表快照

示例:
  trend 0.5       - 设置上涨趋势
  manipulate AAPL 0.3 - 拉升苹果股价
  buy TSLA 1000   - 庄家买入1000股特斯拉
  volatility 0.05 - 设置5%波动率
"""
        print(help_text)
    
    def process_command(self, command: str):
        """处理用户命令"""
        parts = command.strip().split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        
        try:
            if cmd in ['quit', 'exit']:
                return False
            
            elif cmd == 'help':
                self.show_help()
            
            elif cmd == 'status':
                self.banker_interface.print_market_status()
            
            elif cmd == 'report':
                report = self.visualizer.generate_report()
                print(report)
            
            elif cmd == 'traders':
                stats = self.trader_manager.get_trader_stats()
                analysis = self.banker_interface.analyze_trader_behavior()
                print(f"\n👥 交易者统计:")
                print(f"  总数: {stats['total_traders']}")
                print(f"  做多: {stats['bull_traders']} (盈利率: {analysis['bull_traders']['avg_return']:.2%})")
                print(f"  做空: {stats['bear_traders']} (盈利率: {analysis['bear_traders']['avg_return']:.2%})")
                print(f"  活跃持仓: {stats['active_positions']}")
            
            elif cmd == 'trend' and len(parts) >= 2:
                trend = float(parts[1])
                self.banker_interface.set_market_trend(trend)
            
            elif cmd == 'manipulate' and len(parts) >= 3:
                symbol = parts[1].upper()
                strength = float(parts[2])
                self.banker_interface.manipulate_price(symbol, strength)
            
            elif cmd == 'volatility' and len(parts) >= 2:
                volatility = float(parts[1])
                self.banker_interface.set_volatility(volatility)
            
            elif cmd == 'crash' and len(parts) >= 2:
                intensity = float(parts[1])
                self.banker_interface.trigger_market_event('crash', intensity)
            
            elif cmd == 'surge' and len(parts) >= 2:
                intensity = float(parts[1])
                self.banker_interface.trigger_market_event('surge', intensity)
            
            elif cmd == 'noise' and len(parts) >= 2:
                intensity = float(parts[1])
                self.banker_interface.trigger_market_event('volatility', intensity)
            
            elif cmd == 'reset':
                self.banker_interface.reset_market_controls()
            
            elif cmd == 'buy' and len(parts) >= 3:
                symbol = parts[1].upper()
                quantity = int(parts[2])
                price_offset = float(parts[3]) if len(parts) > 3 else 0.0
                from models import OrderType
                self.banker_interface.create_large_order(symbol, OrderType.BUY, quantity, price_offset)
            
            elif cmd == 'sell' and len(parts) >= 3:
                symbol = parts[1].upper()
                quantity = int(parts[2])
                price_offset = float(parts[3]) if len(parts) > 3 else 0.0
                from models import OrderType
                self.banker_interface.create_large_order(symbol, OrderType.SELL, quantity, price_offset)
            
            elif cmd == 'chart':
                print("📊 启动实时图表...")
                self.visualizer.start_real_time_display()
            
            elif cmd == 'snapshot':
                self.visualizer.save_snapshot()
            
            else:
                print(f"❌ 未知命令: {command}")
                print("💡 输入 'help' 查看可用命令")
        
        except (ValueError, IndexError) as e:
            print(f"❌ 命令格式错误: {e}")
            print("💡 输入 'help' 查看命令格式")
        except Exception as e:
            print(f"❌ 执行命令时出错: {e}")
        
        return True
    
    def run_interactive_mode(self):
        """运行交互模式"""
        print("\n" + "="*60)
        print("🎮 欢迎使用股票模拟器 - 庄家版")
        print("="*60)
        print("💡 输入 'help' 查看可用命令")
        print("💡 输入 'quit' 或 'exit' 退出程序")
        print("="*60)
        
        # 初始化并启动模拟
        self.initialize_market()
        self.start_simulation()
        
        # 显示初始状态
        time.sleep(1)  # 等待模拟器启动
        self.banker_interface.print_market_status()
        
        # 交互循环
        try:
            while True:
                try:
                    command = input("\n🎮 庄家控制台 > ").strip()
                    if not self.process_command(command):
                        break
                except KeyboardInterrupt:
                    print("\n\n👋 检测到 Ctrl+C，正在退出...")
                    break
                except EOFError:
                    print("\n\n👋 检测到 EOF，正在退出...")
                    break
        
        finally:
            self.stop_simulation()
            print("\n🎯 感谢使用股票模拟器！")

def main():
    """主函数"""
    try:
        simulator = StockSimulator()
        simulator.run_interactive_mode()
    except Exception as e:
        print(f"❌ 程序运行错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()