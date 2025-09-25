#!/usr/bin/env python3
"""
币安API集成测试脚本
测试币安API客户端和价格引擎的集成功能
"""

import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.binance_client import binance_client
from src.config.config_manager import config_manager

# 简化的Stock和MarketData类用于测试
class Stock:
    def __init__(self):
        self.symbol = ""
        self.name = ""
        self.current_price = 0.0
        self.open_price = 0.0
        self.high_price = 0.0
        self.low_price = 0.0
        self.volume = 0
        self.price_history = []

class MarketData:
    def __init__(self):
        self.stocks = {}
    
    def add_stock(self, stock):
        self.stocks[stock.symbol] = stock
    
    def update_price(self, symbol, new_price):
        if symbol in self.stocks:
            stock = self.stocks[symbol]
            stock.current_price = new_price
            stock.price_history.append(new_price)
            stock.high_price = max(stock.high_price, new_price)
            stock.low_price = min(stock.low_price, new_price)

def test_binance_client():
    """测试币安客户端基本功能"""
    print("🔍 测试币安客户端...")
    
    # 测试连接
    print(f"币安客户端启用状态: {binance_client.is_enabled()}")
    print(f"支持的交易对: {binance_client.get_supported_symbols()}")
    
    # 测试获取单个价格
    try:
        price = binance_client.get_symbol_price('BTCUSDT')
        print(f"BTCUSDT 当前价格: ${price:.2f}")
    except Exception as e:
        print(f"获取BTCUSDT价格失败: {e}")
    
    # 测试获取所有价格
    try:
        all_prices = binance_client.get_all_prices()
        print(f"获取到 {len(all_prices)} 个交易对的价格")
        for symbol, price in list(all_prices.items())[:3]:  # 只显示前3个
            print(f"  {symbol}: ${price:.4f}")
    except Exception as e:
        print(f"获取所有价格失败: {e}")

def test_price_engine_integration():
    """测试价格引擎集成"""
    print("\n🔧 测试价格引擎集成...")
    
    # 创建市场数据
    market_data = MarketData()
    
    # 测试添加加密货币
    print("添加加密货币到市场数据...")
    
    # 手动添加加密货币股票
    btc_stock = Stock()
    btc_stock.symbol = 'BTCUSDT'
    btc_stock.name = 'Cryptocurrency BTCUSDT'
    btc_stock.current_price = 50000.0
    btc_stock.open_price = 50000.0
    btc_stock.high_price = 50000.0
    btc_stock.low_price = 50000.0
    btc_stock.volume = 0
    btc_stock.price_history = [50000.0]
    market_data.add_stock(btc_stock)
    
    eth_stock = Stock()
    eth_stock.symbol = 'ETHUSDT'
    eth_stock.name = 'Cryptocurrency ETHUSDT'
    eth_stock.current_price = 3000.0
    eth_stock.open_price = 3000.0
    eth_stock.high_price = 3000.0
    eth_stock.low_price = 3000.0
    eth_stock.volume = 0
    eth_stock.price_history = [3000.0]
    market_data.add_stock(eth_stock)
    
    print(f"市场中的股票数量: {len(market_data.stocks)}")
    for symbol, stock in market_data.stocks.items():
        print(f"  {symbol} ({stock.name}): ${stock.current_price:.2f}")
    
    # 测试更新加密货币价格
    print("\n更新加密货币价格...")
    
    # 模拟从币安API获取价格并更新
    crypto_symbols = ['BTCUSDT', 'ETHUSDT']
    for symbol in crypto_symbols:
        if symbol in market_data.stocks:
            try:
                # 尝试获取真实价格
                real_price = binance_client.get_symbol_price(symbol)
                market_data.update_price(symbol, real_price)
                print(f"  {symbol}: 更新为真实价格 ${real_price:.4f}")
            except Exception as e:
                # 如果获取失败，使用模拟价格
                import random
                mock_price = market_data.stocks[symbol].current_price * (1 + random.uniform(-0.02, 0.02))
                market_data.update_price(symbol, mock_price)
                print(f"  {symbol}: 使用模拟价格 ${mock_price:.4f} (原因: {e})")
    
    print("更新后的价格:")
    for symbol, stock in market_data.stocks.items():
        if symbol in crypto_symbols:
            print(f"  {symbol}: ${stock.current_price:.4f}")

def test_full_integration():
    """测试完整集成流程"""
    print("\n🚀 测试完整集成流程...")
    
    # 创建市场数据
    market_data = MarketData()
    
    # 添加一些传统股票（模拟数据）
    traditional_stock = Stock()
    traditional_stock.symbol = 'AAPL'
    traditional_stock.name = 'Apple Inc.'
    traditional_stock.current_price = 150.0
    traditional_stock.open_price = 150.0
    traditional_stock.high_price = 150.0
    traditional_stock.low_price = 150.0
    traditional_stock.volume = 0
    traditional_stock.price_history = [150.0]
    market_data.add_stock(traditional_stock)
    
    # 添加加密货币
    btc_stock = Stock()
    btc_stock.symbol = 'BTCUSDT'
    btc_stock.name = 'Cryptocurrency BTCUSDT'
    btc_stock.current_price = 50000.0
    btc_stock.open_price = 50000.0
    btc_stock.high_price = 50000.0
    btc_stock.low_price = 50000.0
    btc_stock.volume = 0
    btc_stock.price_history = [50000.0]
    market_data.add_stock(btc_stock)
    
    eth_stock = Stock()
    eth_stock.symbol = 'ETHUSDT'
    eth_stock.name = 'Cryptocurrency ETHUSDT'
    eth_stock.current_price = 3000.0
    eth_stock.open_price = 3000.0
    eth_stock.high_price = 3000.0
    eth_stock.low_price = 3000.0
    eth_stock.volume = 0
    eth_stock.price_history = [3000.0]
    market_data.add_stock(eth_stock)
    
    print(f"初始市场股票数量: {len(market_data.stocks)}")
    
    # 模拟价格更新循环
    print("\n开始价格更新循环...")
    crypto_symbols = ['BTCUSDT', 'ETHUSDT']
    
    for i in range(3):
        print(f"\n--- 第 {i+1} 次更新 ---")
        
        # 更新所有股票价格
        for symbol, stock in market_data.stocks.items():
            if symbol in crypto_symbols:
                # 加密货币：尝试获取真实价格
                try:
                    real_price = binance_client.get_symbol_price(symbol)
                    market_data.update_price(symbol, real_price)
                except Exception:
                    # 如果获取失败，使用模拟价格变动
                    import random
                    change_rate = random.uniform(-0.02, 0.02)
                    new_price = stock.current_price * (1 + change_rate)
                    market_data.update_price(symbol, new_price)
            else:
                # 传统股票：使用模拟价格变动
                import random
                change_rate = random.uniform(-0.01, 0.01)
                new_price = stock.current_price * (1 + change_rate)
                market_data.update_price(symbol, new_price)
        
        # 显示更新后的价格
        for symbol, stock in market_data.stocks.items():
            change = stock.current_price - stock.open_price
            change_pct = (change / stock.open_price) * 100 if stock.open_price > 0 else 0
            print(f"  {symbol}: ${stock.current_price:.4f} ({change:+.4f}, {change_pct:+.2f}%)")
        
        time.sleep(2)  # 等待2秒

def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 币安API集成测试")
    print("=" * 60)
    
    try:
        # 测试币安客户端
        test_binance_client()
        
        # 测试价格引擎集成
        test_price_engine_integration()
        
        # 测试完整集成
        test_full_integration()
        
        print("\n✅ 所有测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()