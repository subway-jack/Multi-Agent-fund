import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import time
from datetime import datetime, timedelta
import threading
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.app import app
from src.config.config_manager import config_manager

# 页面配置
st.set_page_config(
    page_title="📈 股票模拟交易系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .profit {
        color: #00ff00;
        font-weight: bold;
    }
    .loss {
        color: #ff0000;
        font-weight: bold;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# 初始化应用
if 'app_initialized' not in st.session_state:
    app.initialize()
    st.session_state.app_initialized = True
    st.session_state.selected_stock = 'AAPL'
    st.session_state.simulation_running = False

# 获取应用组件
stocks = app.get_stocks()
market_data = app.get_component('market_data')
user_trader = app.get_component('user_trader')
banker = app.get_component('banker')
price_engine = app.get_component('price_engine')

def get_stock_data(symbol):
    """获取股票数据"""
    stock = stocks[symbol]
    current_price = stock.current_price
    
    # 计算涨跌额和涨跌幅
    price_change = current_price - stock.open_price
    price_change_percent = (price_change / stock.open_price) * 100 if stock.open_price > 0 else 0
    
    # 生成K线数据
    kline_data = price_engine.generate_kline_data(symbol, period_minutes=100)
    
    return {
        'symbol': symbol,
        'name': stock.name,
        'current_price': current_price,
        'change': price_change,
        'change_percent': price_change_percent,
        'volume': stock.volume,
        'kline_data': kline_data
    }

def create_kline_chart(stock_data):
    """创建K线图"""
    kline_data = stock_data['kline_data']
    
    # 现在kline_data已经包含数组格式的数据
    timestamps = kline_data['timestamp']
    opens = kline_data['open']
    highs = kline_data['high']
    lows = kline_data['low']
    closes = kline_data['close']
    volumes = kline_data['volume']
    
    # 转换时间戳为可读格式
    from datetime import datetime
    formatted_timestamps = [datetime.fromtimestamp(ts).strftime('%H:%M') for ts in timestamps]
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(f"{stock_data['name']} ({stock_data['symbol']}) K线图", "成交量"),
        row_width=[0.7, 0.3]
    )
    
    # K线图
    fig.add_trace(
        go.Candlestick(
            x=formatted_timestamps,
            open=opens,
            high=highs,
            low=lows,
            close=closes,
            name="K线"
        ),
        row=1, col=1
    )
    
    # 成交量
    colors = ['red' if close < open else 'green' for close, open in zip(closes, opens)]
    
    fig.add_trace(
        go.Bar(
            x=formatted_timestamps,
            y=volumes,
            name="成交量",
            marker_color=colors
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title=f"{stock_data['name']} 实时行情",
        yaxis_title="价格 ($)",
        yaxis2_title="成交量",
        xaxis_rangeslider_visible=False,
        height=600,
        showlegend=False
    )
    
    return fig

def display_account_info():
    """显示账户信息"""
    account_info = user_trader.get_account_info()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 账户余额",
            value=f"${account_info.get('balance', 0):,.2f}"
        )
    
    with col2:
        st.metric(
            label="📊 总资产",
            value=f"${account_info.get('total_assets', 0):,.2f}"
        )
    
    with col3:
        pnl = account_info.get('total_profit_loss', 0)
        st.metric(
            label="💹 盈亏",
            value=f"${pnl:,.2f}",
            delta=f"{account_info.get('total_profit_loss_pct', 0):.2f}%"
        )
    
    with col4:
        st.metric(
            label="📈 持仓数量",
            value=len(account_info.get('positions', []))
        )

def display_positions():
    """显示持仓信息"""
    account_info = user_trader.get_account_info()
    positions = account_info.get('positions', [])
    
    if positions:
        st.subheader("📋 当前持仓")
        
        position_data = []
        for pos in positions:
            symbol = pos['symbol']
            stock = stocks[symbol]
            current_value = pos['quantity'] * pos['current_price']
            cost_basis = pos['quantity'] * pos['avg_cost']
            pnl = pos['profit_loss']
            pnl_percent = pos['profit_loss_pct']
            
            position_data.append({
                '股票代码': symbol,
                '股票名称': stock.name,
                '持仓数量': pos['quantity'],
                '平均成本': f"${pos['avg_cost']:.2f}",
                '当前价格': f"${pos['current_price']:.2f}",
                '当前市值': f"${pos['market_value']:.2f}",
                '盈亏': f"${pnl:.2f}",
                '盈亏率': f"{pnl_percent:.2f}%"
            })
        
        df = pd.DataFrame(position_data)
        st.dataframe(df, width='stretch')
    else:
        st.info("暂无持仓")

# 侧边栏导航
st.sidebar.title("🎯 导航菜单")
page = st.sidebar.selectbox(
    "选择页面",
    ["🏠 首页概览", "📈 股票详情", "💼 交易中心", "🏦 庄家操作", "📊 市场数据", "🤖 交易员收益", "⚙️ 系统配置"]
)

# 股票选择
st.sidebar.subheader("📊 股票选择")
selected_stock = st.sidebar.selectbox(
    "选择股票",
    list(stocks.keys()),
    format_func=lambda x: f"{x} - {stocks[x].name}"
)
st.session_state.selected_stock = selected_stock

# 模拟控制
st.sidebar.subheader("🎮 模拟控制")
if st.sidebar.button("▶️ 开始模拟" if not st.session_state.simulation_running else "⏸️ 停止模拟"):
    if not st.session_state.simulation_running:
        app.start_simulation()
        st.session_state.simulation_running = True
        st.sidebar.success("模拟已开始")
    else:
        app.stop_simulation()
        st.session_state.simulation_running = False
        st.sidebar.info("模拟已停止")

if st.sidebar.button("🔄 重置系统"):
    app.reset()
    st.sidebar.success("系统已重置")

# 主页面内容
if page == "🏠 首页概览":
    st.markdown('<h1 class="main-header">📈 股票模拟交易系统</h1>', unsafe_allow_html=True)
    
    # 账户信息
    st.subheader("💰 账户概览")
    display_account_info()
    
    # 配置验证信息
    st.subheader("🔍 配置验证")
    config_verification = []
    market_config = config_manager.get_config('market')
    initial_stocks_config = market_config.get('initial_stocks', {})
    
    for symbol, stock in stocks.items():
        config_price = initial_stocks_config.get(symbol, {}).get('price', 'N/A')
        config_verification.append({
            '股票代码': symbol,
            '股票名称': stock.name,
            '配置价格': f"${config_price:.2f}" if config_price != 'N/A' else 'N/A',
            '开盘价格': f"${stock.open_price:.2f}",
            '当前价格': f"${stock.current_price:.2f}",
            '价格匹配': '✅' if abs(float(config_price) - stock.open_price) < 0.01 else '❌' if config_price != 'N/A' else '❓'
        })
    
    df_config = pd.DataFrame(config_verification)
    st.dataframe(df_config, width='stretch')
    
    # 市场概览
    st.subheader("📊 市场概览")
    
    market_overview = []
    for symbol, stock in stocks.items():
        # 计算涨跌额和涨跌幅
        price_change = stock.current_price - stock.open_price
        price_change_percent = (price_change / stock.open_price) * 100 if stock.open_price > 0 else 0
        
        market_overview.append({
            '股票代码': symbol,
            '股票名称': stock.name,
            '当前价格': f"${stock.current_price:.2f}",
            '涨跌额': f"${price_change:.2f}",
            '涨跌幅': f"{price_change_percent:.2f}%",
            '成交量': f"{stock.volume:,}"
        })
    
    df_market = pd.DataFrame(market_overview)
    st.dataframe(df_market, width='stretch')
    
    # 持仓信息
    display_positions()

elif page == "📈 股票详情":
    stock_data = get_stock_data(selected_stock)
    
    st.title(f"📈 {stock_data['name']} ({stock_data['symbol']})")
    
    # 股票基本信息
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="当前价格",
            value=f"${stock_data['current_price']:.2f}",
            delta=f"{stock_data['change']:.2f}"
        )
    
    with col2:
        st.metric(
            label="涨跌幅",
            value=f"{stock_data['change_percent']:.2f}%"
        )
    
    with col3:
        st.metric(
            label="成交量",
            value=f"{stock_data['volume']:,}"
        )
    
    with col4:
        # 显示技术指标
        kline_data = stock_data['kline_data']
        # 现在kline_data['close']是数组，可以计算真正的SMA
        closes = kline_data['close']
        sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else np.mean(closes)
        st.metric(
            label="SMA(20)",
            value=f"${sma_20:.2f}"
        )
    
    # K线图
    fig = create_kline_chart(stock_data)
    st.plotly_chart(fig, width='stretch')
    
    # 快速交易
    st.subheader("⚡ 快速交易")
    col1, col2 = st.columns(2)
    
    with col1:
        quantity = st.number_input("交易数量", min_value=1, value=100, step=1)
        if st.button("🟢 买入", width='stretch'):
            try:
                result = user_trader.buy_stock(selected_stock, quantity)
                if result['success']:
                    st.success(f"成功买入 {quantity} 股 {selected_stock}")
                else:
                    st.error(f"买入失败: {result['message']}")
            except Exception as e:
                st.error(f"交易错误: {str(e)}")
    
    with col2:
        if st.button("🔴 卖出", width='stretch'):
            try:
                result = user_trader.sell_stock(selected_stock, quantity)
                if result['success']:
                    st.success(f"成功卖出 {quantity} 股 {selected_stock}")
                else:
                    st.error(f"卖出失败: {result['message']}")
            except Exception as e:
                st.error(f"交易错误: {str(e)}")

elif page == "💼 交易中心":
    st.title("💼 交易中心")
    
    # 账户信息
    display_account_info()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 下单交易")
        
        trade_symbol = st.selectbox(
            "选择股票",
            list(stocks.keys()),
            format_func=lambda x: f"{x} - {stocks[x].name}"
        )
        
        trade_type = st.radio("交易类型", ["买入", "卖出"])
        trade_quantity = st.number_input("交易数量", min_value=1, value=100, step=1)
        
        # 显示预估信息
        stock = stocks[trade_symbol]
        estimated_cost = stock.current_price * trade_quantity
        st.info(f"预估{trade_type}金额: ${estimated_cost:.2f}")
        
        if st.button(f"确认{trade_type}", width='stretch'):
            try:
                if trade_type == "买入":
                    result = user_trader.buy_stock(trade_symbol, trade_quantity)
                else:
                    result = user_trader.sell_stock(trade_symbol, trade_quantity)
                
                if result['success']:
                    st.success(f"交易成功！{trade_type} {trade_quantity} 股 {trade_symbol}")
                    st.rerun()
                else:
                    st.error(f"交易失败: {result['message']}")
            except Exception as e:
                st.error(f"交易错误: {str(e)}")
    
    with col2:
        st.subheader("📋 持仓管理")
        display_positions()

elif page == "🏦 庄家操作":
    st.title("🏦 庄家操作中心")
    
    st.warning("⚠️ 庄家操作会影响市场价格，请谨慎使用！")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 趋势控制")
        
        trend_strength = st.slider("趋势强度", -1.0, 1.0, 0.0, 0.1)
        
        if st.button("设置上涨趋势", width='stretch'):
            banker.set_market_trend(0.5)
            st.success("已设置上涨趋势")
        
        if st.button("设置下跌趋势", width='stretch'):
            banker.set_market_trend(-0.5)
            st.success("已设置下跌趋势")
        
        if st.button("清除趋势", width='stretch'):
            banker.set_market_trend(0.0)
            st.success("已清除趋势")
    
    with col2:
        st.subheader("💥 市场事件")
        
        if st.button("📉 触发市场崩盘", width='stretch'):
            banker.trigger_market_crash()
            st.error("市场崩盘已触发！")
        
        if st.button("📈 触发市场暴涨", width='stretch'):
            banker.trigger_market_boom()
            st.success("市场暴涨已触发！")
        
        if st.button("🔄 重置市场", width='stretch'):
            banker.reset_market_controls()
            st.info("市场已重置")
    
    st.subheader("⚙️ 高级控制")
    
    col3, col4 = st.columns(2)
    
    with col3:
        volatility = st.slider("波动率", 0.0, 2.0, 1.0, 0.1)
        if st.button("设置波动率"):
            banker.set_volatility(volatility)
            st.success(f"波动率已设置为 {volatility}")
    
    with col4:
        manipulation = st.slider("操控强度", -1.0, 1.0, 0.0, 0.1)
        if st.button("设置操控"):
            banker.set_manipulation(manipulation)
            st.success(f"操控强度已设置为 {manipulation}")

elif page == "📊 市场数据":
    st.title("📊 市场数据分析")
    
    # 市场总览图表
    st.subheader("📈 市场价格走势")
    
    # 创建价格对比图
    price_data = []
    for symbol, stock in stocks.items():
        kline_data = price_engine.generate_kline_data(symbol, period_minutes=50)
        if kline_data and kline_data['timestamp']:  # 确保有数据
            # 展开时间序列数据
            for i, timestamp in enumerate(kline_data['timestamp']):
                price_data.append({
                    'timestamp': datetime.fromtimestamp(timestamp).strftime('%H:%M'),
                    'symbol': symbol,
                    'price': kline_data['close'][i]
                })
    
    df_prices = pd.DataFrame(price_data)
    
    fig_prices = px.line(
        df_prices, 
        x='timestamp', 
        y='price', 
        color='symbol',
        title="股票价格走势对比",
        labels={'price': '价格 ($)', 'timestamp': '时间'}
    )
    
    st.plotly_chart(fig_prices, width='stretch')
    
    # 成交量分析
    st.subheader("📊 成交量分析")
    
    volume_data = []
    for symbol, stock in stocks.items():
        volume_data.append({
            '股票代码': symbol,
            '股票名称': stock.name,
            '成交量': stock.volume
        })
    
    df_volume = pd.DataFrame(volume_data)
    
    fig_volume = px.bar(
        df_volume,
        x='股票代码',
        y='成交量',
        title="各股票成交量对比",
        color='成交量',
        color_continuous_scale='viridis'
    )
    
    st.plotly_chart(fig_volume, width='stretch')
    
    # 市场统计
    st.subheader("📋 市场统计")
    
    total_market_cap = sum(stock.current_price * 1000000 for stock in stocks.values())  # 假设每只股票1M股
    avg_price = sum(stock.current_price for stock in stocks.values()) / len(stocks)
    total_volume = sum(stock.volume for stock in stocks.values())
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("总市值", f"${total_market_cap/1e9:.2f}B")
    
    with col2:
        st.metric("平均股价", f"${avg_price:.2f}")
    
    with col3:
        st.metric("总成交量", f"{total_volume:,}")

elif page == "🤖 交易员收益":
    st.title("🤖 交易员收益分析")
    
    # 获取交易员表现数据
    trading_engine = app.get_component('trading_engine')
    performance_data = trading_engine.get_trader_performance()
    
    if not performance_data:
        st.warning("暂无交易员数据，请先启动模拟交易。")
    else:
        # 总体统计
        st.subheader("📊 总体统计")
        
        bull_traders = [p for p in performance_data.values() if p['type'] == 'bull']
        bear_traders = [p for p in performance_data.values() if p['type'] == 'bear']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("做多交易员", len(bull_traders))
        
        with col2:
            st.metric("做空交易员", len(bear_traders))
        
        with col3:
            profitable_bulls = len([p for p in bull_traders if p['total_pnl'] > 0])
            bull_profit_rate = (profitable_bulls / len(bull_traders) * 100) if bull_traders else 0
            st.metric("做多盈利率", f"{bull_profit_rate:.1f}%")
        
        with col4:
            profitable_bears = len([p for p in bear_traders if p['total_pnl'] > 0])
            bear_profit_rate = (profitable_bears / len(bear_traders) * 100) if bear_traders else 0
            st.metric("做空盈利率", f"{bear_profit_rate:.1f}%")
        
        # 收益分布图表
        st.subheader("📈 收益分布")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 做多交易员收益分布
            if bull_traders:
                bull_pnl = [p['total_pnl'] for p in bull_traders]
                fig_bull = px.histogram(
                    x=bull_pnl,
                    nbins=20,
                    title="做多交易员收益分布",
                    labels={'x': '收益 ($)', 'y': '交易员数量'},
                    color_discrete_sequence=['#2ecc71']
                )
                fig_bull.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="盈亏平衡线")
                st.plotly_chart(fig_bull, use_container_width=True)
            else:
                st.info("暂无做多交易员数据")
        
        with col2:
            # 做空交易员收益分布
            if bear_traders:
                bear_pnl = [p['total_pnl'] for p in bear_traders]
                fig_bear = px.histogram(
                    x=bear_pnl,
                    nbins=20,
                    title="做空交易员收益分布",
                    labels={'x': '收益 ($)', 'y': '交易员数量'},
                    color_discrete_sequence=['#e74c3c']
                )
                fig_bear.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="盈亏平衡线")
                st.plotly_chart(fig_bear, use_container_width=True)
            else:
                st.info("暂无做空交易员数据")
        
        # 详细交易员列表
        st.subheader("📋 交易员详情")
        
        # 筛选选项
        col1, col2, col3 = st.columns(3)
        
        with col1:
            trader_type_filter = st.selectbox(
                "交易员类型",
                ["全部", "做多", "做空"]
            )
        
        with col2:
            sort_by = st.selectbox(
                "排序方式",
                ["收益率", "总收益", "交易次数", "持仓数量"]
            )
        
        with col3:
            show_count = st.selectbox(
                "显示数量",
                [10, 20, 50, 100]
            )
        
        # 过滤和排序数据
        filtered_data = []
        for trader_id, data in performance_data.items():
            if trader_type_filter == "全部" or \
               (trader_type_filter == "做多" and data['type'] == 'bull') or \
               (trader_type_filter == "做空" and data['type'] == 'bear'):
                filtered_data.append({
                    '交易员ID': trader_id,
                    '类型': '做多' if data['type'] == 'bull' else '做空',
                    '总资产': f"${data['total_value']:,.2f}",
                    '可用资金': f"${data['balance']:,.2f}",
                    '总收益': f"${data['total_pnl']:,.2f}",
                    '收益率': f"{data['return_rate']*100:.2f}%",
                    '持仓数量': data['positions_count'],
                    '交易次数': data['trades_count']
                })
        
        # 排序
        sort_key_map = {
            "收益率": lambda x: float(x['收益率'].replace('%', '')),
            "总收益": lambda x: float(x['总收益'].replace('$', '').replace(',', '')),
            "交易次数": lambda x: x['交易次数'],
            "持仓数量": lambda x: x['持仓数量']
        }
        
        if sort_by in sort_key_map:
            filtered_data.sort(key=sort_key_map[sort_by], reverse=True)
        
        # 限制显示数量
        filtered_data = filtered_data[:show_count]
        
        if filtered_data:
            df_traders = pd.DataFrame(filtered_data)
            
            # 添加颜色样式
            def highlight_profit_loss(val):
                if isinstance(val, str) and ('$' in val or '%' in val):
                    if val.startswith('$'):
                        num_val = float(val.replace('$', '').replace(',', ''))
                    else:
                        num_val = float(val.replace('%', ''))
                    
                    if num_val > 0:
                        return 'color: #00ff00; font-weight: bold'
                    elif num_val < 0:
                        return 'color: #ff0000; font-weight: bold'
                return ''
            
            styled_df = df_traders.style.applymap(highlight_profit_loss, subset=['总收益', '收益率'])
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.info("没有符合条件的交易员数据")
        
        # 用户交易员收益
        st.subheader("👤 用户交易员收益")
        
        user_account = user_trader.get_account_info()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总资产", f"${user_account['total_assets']:,.2f}")
        
        with col2:
            st.metric("可用资金", f"${user_account['balance']:,.2f}")
        
        with col3:
            profit_loss = user_account['total_profit_loss']
            delta_color = "normal" if profit_loss >= 0 else "inverse"
            st.metric("总盈亏", f"${profit_loss:,.2f}", delta_color=delta_color)
        
        with col4:
            profit_loss_pct = user_account['total_profit_loss_pct']
            delta_color = "normal" if profit_loss_pct >= 0 else "inverse"
            st.metric("收益率", f"{profit_loss_pct:.2f}%", delta_color=delta_color)

elif page == "⚙️ 系统配置":
    st.title("⚙️ 系统配置")
    
    st.info("💡 在这里可以调整系统的各种参数，修改后会自动保存并在下次启动时生效。")
    
    # 获取当前配置
    current_config = config_manager.get_config()
    
    # 创建标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 市场设置", "🤖 AI交易员", "📈 技术指标", "💱 交易系统", "🎨 界面设置"])
    
    with tab1:
        st.subheader("📊 市场基础设置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 股票配置
            st.write("**股票配置**")
            
            # 显示当前股票列表
            stock_config = current_config.get('market_settings', {}).get('stocks', {})
            
            for symbol, info in stock_config.items():
                st.write(f"**{symbol} - {info['name']}**")
                new_price = st.number_input(
                    f"{symbol} 初始价格",
                    min_value=1.0,
                    value=float(info['initial_price']),
                    step=1.0,
                    key=f"stock_price_{symbol}"
                )
                
                if new_price != info['initial_price']:
                    config_manager.update_config(f'market.initial_stocks.{symbol}.price', new_price)
        
        with col2:
            # 市场参数
            st.write("**市场参数**")
            
            market_settings = current_config.get('market_settings', {})
            
            volatility = st.slider(
                "基础波动率",
                min_value=0.01,
                max_value=0.1,
                value=market_settings.get('base_volatility', 0.02),
                step=0.001,
                key="base_volatility"
            )
            
            trend_strength = st.slider(
                "趋势强度",
                min_value=0.0,
                max_value=1.0,
                value=market_settings.get('trend_strength', 0.1),
                step=0.01,
                key="trend_strength"
            )
            
            update_interval = st.number_input(
                "价格更新间隔(秒)",
                min_value=0.1,
                max_value=10.0,
                value=market_settings.get('price_update_interval', 1.0),
                step=0.1,
                key="price_update_interval"
            )
            
            # 保存市场设置
            if st.button("保存市场设置", key="save_market"):
                config_manager.update_config('market.base_volatility', volatility)
                config_manager.update_config('market.trend', trend_strength)
                config_manager.update_config('market.impact_decay_rate', update_interval)
                st.success("市场设置已保存！")
    
    with tab2:
        st.subheader("🤖 AI交易员配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**决策参数**")
            
            ai_config = current_config.get('ai_trader_config', {})
            
            decision_interval = st.number_input(
                "决策间隔(秒)",
                min_value=1,
                max_value=60,
                value=ai_config.get('decision_interval', 5),
                step=1,
                key="ai_decision_interval"
            )
            
            risk_tolerance = st.slider(
                "风险承受度",
                min_value=0.1,
                max_value=2.0,
                value=ai_config.get('risk_tolerance', 0.5),
                step=0.1,
                key="ai_risk_tolerance"
            )
            
            max_position_size = st.number_input(
                "最大持仓比例",
                min_value=0.1,
                max_value=1.0,
                value=ai_config.get('max_position_size', 0.3),
                step=0.05,
                key="ai_max_position"
            )
        
        with col2:
            st.write("**交易参数**")
            
            min_trade_amount = st.number_input(
                "最小交易金额",
                min_value=100,
                max_value=10000,
                value=ai_config.get('min_trade_amount', 1000),
                step=100,
                key="ai_min_trade"
            )
            
            max_trade_amount = st.number_input(
                "最大交易金额",
                min_value=1000,
                max_value=100000,
                value=ai_config.get('max_trade_amount', 10000),
                step=1000,
                key="ai_max_trade"
            )
            
            # 保存AI设置
            if st.button("保存AI设置", key="save_ai"):
                config_manager.update_config('trader.decision_interval_min', decision_interval)
                config_manager.update_config('trader.risk_tolerance_min', risk_tolerance)
                config_manager.update_config('trader.initial_balance', max_position_size)
                config_manager.update_config('trader.num_bulls', min_trade_amount)
                config_manager.update_config('trader.num_bears', max_trade_amount)
                st.success("AI交易员设置已保存！")
    
    with tab3:
        st.subheader("📈 技术指标配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**移动平均线**")
            
            tech_config = current_config.get('technical_indicators', {})
            
            sma_short = st.number_input(
                "短期SMA周期",
                min_value=5,
                max_value=50,
                value=tech_config.get('sma_short_period', 10),
                step=1,
                key="sma_short"
            )
            
            sma_long = st.number_input(
                "长期SMA周期",
                min_value=10,
                max_value=200,
                value=tech_config.get('sma_long_period', 30),
                step=1,
                key="sma_long"
            )
            
            ema_period = st.number_input(
                "EMA周期",
                min_value=5,
                max_value=100,
                value=tech_config.get('ema_period', 12),
                step=1,
                key="ema_period"
            )
        
        with col2:
            st.write("**其他指标**")
            
            rsi_period = st.number_input(
                "RSI周期",
                min_value=5,
                max_value=50,
                value=tech_config.get('rsi_period', 14),
                step=1,
                key="rsi_period"
            )
            
            bb_period = st.number_input(
                "布林带周期",
                min_value=10,
                max_value=50,
                value=tech_config.get('bollinger_period', 20),
                step=1,
                key="bb_period"
            )
            
            bb_std = st.number_input(
                "布林带标准差倍数",
                min_value=1.0,
                max_value=3.0,
                value=tech_config.get('bollinger_std', 2.0),
                step=0.1,
                key="bb_std"
            )
            
            # 保存技术指标设置
            if st.button("保存技术指标设置", key="save_tech"):
                config_manager.update_config('technical.sma_short_period', sma_short)
                config_manager.update_config('technical.sma_long_period', sma_long)
                config_manager.update_config('technical.price_history_length', ema_period)
                config_manager.update_config('technical.rsi_period', rsi_period)
                config_manager.update_config('technical.bollinger_period', bb_period)
                config_manager.update_config('technical.bollinger_std_dev', bb_std)
                st.success("技术指标设置已保存！")
    
    with tab4:
        st.subheader("💱 交易系统配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**交易费用**")
            
            trading_config = current_config.get('trading_system', {})
            
            commission_rate = st.number_input(
                "佣金费率(%)",
                min_value=0.0,
                max_value=1.0,
                value=trading_config.get('commission_rate', 0.001) * 100,
                step=0.001,
                key="commission_rate"
            ) / 100
            
            min_commission = st.number_input(
                "最低佣金",
                min_value=0.0,
                max_value=10.0,
                value=trading_config.get('min_commission', 5.0),
                step=0.1,
                key="min_commission"
            )
            
            slippage = st.number_input(
                "滑点(%)",
                min_value=0.0,
                max_value=0.5,
                value=trading_config.get('slippage', 0.001) * 100,
                step=0.001,
                key="slippage"
            ) / 100
        
        with col2:
            st.write("**风险控制**")
            
            max_daily_loss = st.number_input(
                "单日最大亏损(%)",
                min_value=1.0,
                max_value=50.0,
                value=trading_config.get('max_daily_loss_pct', 10.0),
                step=1.0,
                key="max_daily_loss"
            )
            
            position_limit = st.number_input(
                "单只股票持仓限制(%)",
                min_value=10.0,
                max_value=100.0,
                value=trading_config.get('max_position_pct', 30.0),
                step=5.0,
                key="position_limit"
            )
            
            # 保存交易系统设置
            if st.button("保存交易系统设置", key="save_trading"):
                config_manager.update_config('trading.commission_rate', commission_rate)
                config_manager.update_config('trading.min_order_size', min_commission)
                config_manager.update_config('trading.max_order_size', slippage)
                config_manager.update_config('trading.price_precision', max_daily_loss)
                config_manager.update_config('trading.order_timeout', position_limit)
                st.success("交易系统设置已保存！")
    
    with tab5:
        st.subheader("🎨 界面设置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**显示设置**")
            
            ui_config = current_config.get('ui_settings', {})
            
            refresh_interval = st.number_input(
                "界面刷新间隔(秒)",
                min_value=0.5,
                max_value=10.0,
                value=ui_config.get('refresh_interval', 1.0),
                step=0.1,
                key="refresh_interval"
            )
            
            chart_points = st.number_input(
                "图表显示点数",
                min_value=50,
                max_value=500,
                value=ui_config.get('chart_data_points', 100),
                step=10,
                key="chart_points"
            )
            
            decimal_places = st.number_input(
                "价格显示小数位",
                min_value=2,
                max_value=6,
                value=ui_config.get('price_decimal_places', 2),
                step=1,
                key="decimal_places"
            )
        
        with col2:
            st.write("**主题设置**")
            
            theme_color = st.selectbox(
                "主题颜色",
                ["蓝色", "绿色", "紫色", "橙色"],
                index=["蓝色", "绿色", "紫色", "橙色"].index(ui_config.get('theme_color', '蓝色')),
                key="theme_color"
            )
            
            show_animations = st.checkbox(
                "显示动画效果",
                value=ui_config.get('show_animations', True),
                key="show_animations"
            )
            
            # 保存界面设置
            if st.button("保存界面设置", key="save_ui"):
                config_manager.update_config('ui.refresh_interval', refresh_interval)
                config_manager.update_config('ui.chart_period_minutes', chart_points)
                config_manager.update_config('ui.max_log_entries', decimal_places)
                config_manager.update_config('ui.default_trade_quantity', theme_color)
                st.success("界面设置已保存！")
    
    # 配置管理操作
    st.markdown("---")
    st.subheader("🔧 配置管理")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 保存所有配置", key="save_all"):
            config_manager.save_config()
            st.success("所有配置已保存到文件！")
    
    with col2:
        if st.button("🔄 重置为默认", key="reset_config"):
            config_manager.reset_to_defaults()
            st.success("配置已重置为默认值！")
            st.rerun()
    
    with col3:
        if st.button("📋 显示当前配置", key="show_config"):
            st.json(current_config)

# 自动刷新
if st.session_state.simulation_running:
    time.sleep(1)
    st.rerun()

# 页脚
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>📈 股票模拟交易系统 | 由 Streamlit 强力驱动</div>",
    unsafe_allow_html=True
)