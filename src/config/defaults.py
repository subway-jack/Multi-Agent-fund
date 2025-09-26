# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 字体大小设置
FONT_SIZE_SMALL = 16
FONT_SIZE_BIG = 24

# 市场基础设置
MARKET_CONFIG = {
    'initial_stocks': {
        'AAPL': {
            'name': '苹果公司', 
            'price': 150.0,
            'price_history': [145.2, 147.8, 149.1, 146.5, 148.9, 151.2, 149.7, 152.3, 150.8, 148.4, 149.9, 151.7, 153.2, 150.6, 149.3, 151.8, 148.7, 150.4, 152.9, 149.8, 151.5, 148.2, 150.7, 152.1, 149.4, 151.9, 148.6, 150.3, 149.7, 150.0]
        },
        'TSLA': {
            'name': '特斯拉', 
            'price': 800.0,
            'price_history': [785.4, 792.1, 798.7, 803.2, 795.8, 801.4, 789.6, 806.3, 812.7, 798.9, 804.5, 791.2, 807.8, 815.3, 802.6, 796.4, 809.1, 793.7, 805.9, 811.4, 797.8, 803.2, 788.5, 812.6, 806.7, 794.3, 808.9, 801.5, 795.2, 800.0]
        },
        'GOOGL': {
            'name': '谷歌', 
            'price': 2800.0,
            'price_history': [2745.6, 2768.9, 2791.2, 2823.7, 2756.4, 2812.8, 2734.5, 2845.3, 2867.1, 2789.6, 2821.4, 2743.8, 2856.7, 2892.3, 2778.9, 2834.6, 2751.2, 2819.7, 2863.4, 2795.8, 2827.3, 2742.9, 2851.6, 2888.7, 2776.4, 2823.9, 2748.5, 2814.2, 2785.7, 2800.0]
        },
        'MSFT': {
            'name': '微软', 
            'price': 300.0,
            'price_history': [294.7, 297.3, 301.8, 295.6, 299.2, 303.4, 291.9, 305.7, 308.1, 296.8, 302.5, 289.3, 307.9, 311.6, 298.4, 304.2, 292.7, 306.8, 309.3, 297.1, 303.6, 290.8, 308.4, 312.9, 299.7, 305.1, 293.4, 307.2, 301.5, 300.0]
        },
        'AMZN': {
            'name': '亚马逊', 
            'price': 3200.0,
            'price_history': [3142.8, 3178.4, 3205.7, 3167.3, 3189.6, 3234.2, 3156.9, 3251.4, 3278.6, 3193.7, 3217.8, 3145.2, 3263.9, 3295.1, 3174.6, 3228.3, 3158.7, 3241.5, 3267.8, 3186.4, 3212.9, 3149.6, 3256.7, 3289.3, 3171.8, 3225.4, 3152.3, 3248.9, 3195.7, 3200.0]
        }
    },
    'base_volatility': 0.02,  # 基础波动率
    'trend': 0.0,  # 市场趋势
    'manipulation_factor': 0.0,  # 操控因子
    'impact_decay_rate': 0.95,  # 影响衰减率
    'volume_sensitivity': 0.001  # 成交量敏感度
}

# AI交易员配置
TRADER_CONFIG = {
    'num_bulls': 50,  # 做多交易员数量
    'num_bears': 50,  # 做空交易员数量
    'initial_balance': 100000,  # 初始资金
    'decision_interval_min': 1,  # 最小决策间隔(秒)
    'decision_interval_max': 5,  # 最大决策间隔(秒)
    'risk_tolerance_min': 0.1,  # 最小风险承受能力
    'risk_tolerance_max': 0.9,  # 最大风险承受能力
    'aggression_min': 0.1,  # 最小激进程度
    'aggression_max': 0.8,  # 最大激进程度
    'patience_min': 0.2,  # 最小耐心程度
    'patience_max': 0.9,  # 最大耐心程度
    'technical_weight_min': 0.3,  # 最小技术分析权重
    'technical_weight_max': 0.9,  # 最大技术分析权重
    'buy_threshold_min': 0.3,  # 最小买入阈值
    'buy_threshold_max': 0.7,  # 最大买入阈值
    'sell_threshold_min': 0.3,  # 最小卖出阈值
    'sell_threshold_max': 0.7,  # 最大卖出阈值
    'profit_target_min': 0.05,  # 最小止盈目标
    'profit_target_max': 0.2,  # 最大止盈目标
    'stop_loss_min': 0.03,  # 最小止损
    'stop_loss_max': 0.1  # 最大止损
}

# 技术分析配置
TECHNICAL_CONFIG = {
    'rsi_period': 14,  # RSI周期
    'sma_short_period': 5,  # 短期移动平均周期
    'sma_long_period': 20,  # 长期移动平均周期
    'bollinger_period': 20,  # 布林带周期
    'bollinger_std_dev': 2,  # 布林带标准差倍数
    'price_history_length': 30  # 价格历史长度
}

# 币安API配置
BINANCE_CONFIG = {
    'api_key': os.getenv('BINANCE_API_KEY', ''),  # 币安API密钥
    'api_secret': os.getenv('BINANCE_API_SECRET', ''),  # 币安API密钥
    'testnet': False,  # 是否使用测试网络（改为False使用真实网络）
    'base_url': 'https://api.binance.com',  # API基础URL
    'testnet_url': 'https://testnet.binance.vision',  # 测试网络URL
    'timeout': 10,  # 请求超时时间(秒)
    'symbols': [  # 支持的交易对
        'BTCUSDT',  # 比特币/USDT
        'ETHUSDT',  # 以太坊/USDT
        'BNBUSDT',  # 币安币/USDT
        'ADAUSDT',  # 卡尔达诺/USDT
        'SOLUSDT',  # Solana/USDT
        'XRPUSDT',  # 瑞波币/USDT
        'DOTUSDT',  # 波卡/USDT
        'DOGEUSDT', # 狗狗币/USDT
        'AVAXUSDT', # 雪崩/USDT
        'MATICUSDT' # Polygon/USDT
    ],
    'price_update_interval': 5,  # 价格更新间隔(秒)
    'enable_real_data': True,  # 启用真实数据（改为True）
    'fallback_to_mock': True  # 当API失败时是否回退到模拟数据
}

# 交易系统配置
TRADING_CONFIG = {
    'commission_rate': 0.001,  # 手续费率
    'min_order_size': 1,  # 最小订单数量
    'max_order_size': 10000,  # 最大订单数量
    'price_precision': 2,  # 价格精度(小数位)
    'order_timeout': 300  # 订单超时时间(秒)
}

# UI界面配置
UI_CONFIG = {
    'refresh_interval': 1,  # 界面刷新间隔(秒)
    'chart_period_minutes': 100,  # 图表显示周期(分钟)
    'max_log_entries': 1000,  # 最大日志条目数
    'default_trade_quantity': 100  # 默认交易数量
}

# 用户交易员配置
USER_CONFIG = {
    'initial_balance': 100000.0,  # 用户初始资金
    'commission_rate': 0.0003,  # 用户佣金费率
    'min_commission': 5.0,  # 最低佣金
    'stamp_tax_rate': 0.001  # 印花税率
}