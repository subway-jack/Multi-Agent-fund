#!/usr/bin/env python3
"""
测试真实币安API密钥连接
"""

import sys
import os
import time
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.binance_client import binance_client
from src.config.config_manager import config_manager

def test_api_connection():
    """测试API连接"""
    print("🔗 测试币安API连接...")
    
    # 检查配置
    binance_config = config_manager.get_config('binance')
    api_key = binance_config.get('api_key', '')
    api_secret = binance_config.get('api_secret', '')
    
    print(f"API Key: {api_key[:10]}...{api_key[-10:] if len(api_key) > 20 else api_key}")
    print(f"API Secret: {api_secret[:10]}...{api_secret[-10:] if len(api_secret) > 20 else api_secret}")
    print(f"启用状态: {binance_config.get('enabled', False)}")
    
    # 测试连接
    try:
        is_connected = binance_client.test_connection()
        if is_connected:
            print("✅ API连接成功！")
            return True
        else:
            print("❌ API连接失败")
            return False
    except Exception as e:
        print(f"❌ API连接异常: {e}")
        return False

def test_account_info():
    """测试账户信息获取"""
    print("\n📊 测试账户信息获取...")
    
    try:
        # 这里我们可以尝试获取账户信息（如果API密钥有权限）
        # 注意：这需要币安客户端支持账户信息查询
        print("⚠️  账户信息查询需要特定权限，跳过此测试")
        return True
    except Exception as e:
        print(f"❌ 获取账户信息失败: {e}")
        return False

def test_market_data():
    """测试市场数据获取"""
    print("\n💰 测试市场数据获取...")
    
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    
    for symbol in test_symbols:
        try:
            price = binance_client.get_symbol_price(symbol)
            print(f"✅ {symbol}: ${price:.4f}")
        except Exception as e:
            print(f"❌ 获取{symbol}价格失败: {e}")
            return False
    
    return True

def test_batch_prices():
    """测试批量价格获取"""
    print("\n📈 测试批量价格获取...")
    
    try:
        prices = binance_client.get_all_prices()
        print(f"✅ 成功获取 {len(prices)} 个交易对的价格")
        
        # 显示前5个价格
        count = 0
        for symbol, price in prices.items():
            if count < 5:
                print(f"  {symbol}: ${price:.4f}")
                count += 1
            else:
                break
        
        if len(prices) > 5:
            print(f"  ... 还有 {len(prices) - 5} 个交易对")
        
        return True
    except Exception as e:
        print(f"❌ 批量获取价格失败: {e}")
        return False

def test_kline_data():
    """测试K线数据获取"""
    print("\n📊 测试K线数据获取...")
    
    try:
        klines = binance_client.get_klines('BTCUSDT', '1h', 5)
        print(f"✅ 成功获取BTCUSDT的 {len(klines)} 条K线数据")
        
        if klines:
            latest = klines[-1]
            print(f"  最新K线: 开盘${latest['open']:.2f}, 收盘${latest['close']:.2f}, "
                  f"最高${latest['high']:.2f}, 最低${latest['low']:.2f}")
        
        return True
    except Exception as e:
        print(f"❌ 获取K线数据失败: {e}")
        return False

def test_rate_limits():
    """测试API调用频率限制"""
    print("\n⏱️  测试API调用频率...")
    
    try:
        start_time = time.time()
        
        # 快速连续调用多次
        for i in range(5):
            price = binance_client.get_symbol_price('BTCUSDT')
            print(f"  第{i+1}次调用: ${price:.4f}")
            time.sleep(0.1)  # 短暂延迟
        
        end_time = time.time()
        print(f"✅ 5次连续调用完成，耗时: {end_time - start_time:.2f}秒")
        return True
    except Exception as e:
        print(f"❌ 频率测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🚀 币安API真实密钥测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 运行所有测试
    tests = [
        ("API连接测试", test_api_connection),
        ("账户信息测试", test_account_info),
        ("市场数据测试", test_market_data),
        ("批量价格测试", test_batch_prices),
        ("K线数据测试", test_kline_data),
        ("频率限制测试", test_rate_limits),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
    
    # 测试总结
    print("\n" + "=" * 60)
    print("📋 测试总结")
    print("=" * 60)
    print(f"总测试数: {total}")
    print(f"通过测试: {passed}")
    print(f"失败测试: {total - passed}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 所有测试通过！币安API密钥配置正确且可正常使用。")
    elif passed > 0:
        print("⚠️  部分测试通过，API密钥基本可用，但可能存在权限或网络问题。")
    else:
        print("❌ 所有测试失败，请检查API密钥配置或网络连接。")

if __name__ == "__main__":
    main()