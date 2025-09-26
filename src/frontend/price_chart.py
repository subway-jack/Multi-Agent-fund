"""
价格图表组件
使用PyQtGraph实现实时价格图表
"""
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox
from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QFont
from collections import deque
from datetime import datetime
import numpy as np

class PriceChart(QWidget):
    """价格图表组件"""
    
    symbol_changed = Signal(str)  # 交易对变化信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_symbol = ""
        self.price_data = deque(maxlen=1000)  # 最多保存1000个数据点
        self.time_data = deque(maxlen=1000)
        self.max_points = 1000
        
        self.setup_ui()
        self.setup_chart()
        
        # 更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_chart)
        self.update_timer.start(100)  # 100ms更新一次
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 顶部控制栏
        control_layout = QHBoxLayout()
        
        # 交易对选择
        self.symbol_combo = QComboBox()
        self.symbol_combo.setMinimumWidth(120)
        self.symbol_combo.currentTextChanged.connect(self.on_symbol_changed)
        control_layout.addWidget(QLabel("交易对:"))
        control_layout.addWidget(self.symbol_combo)
        
        # 价格显示
        self.price_label = QLabel("--")
        self.price_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.price_label.setStyleSheet("color: #333; padding: 5px;")
        control_layout.addWidget(QLabel("当前价格:"))
        control_layout.addWidget(self.price_label)
        
        # 涨跌幅显示
        self.change_label = QLabel("--")
        self.change_label.setFont(QFont("Arial", 12))
        control_layout.addWidget(QLabel("涨跌幅:"))
        control_layout.addWidget(self.change_label)
        
        control_layout.addStretch()
        
        # 清除按钮
        self.clear_button = QPushButton("清除数据")
        self.clear_button.clicked.connect(self.clear_data)
        control_layout.addWidget(self.clear_button)
        
        layout.addLayout(control_layout)
        
        # 图表区域
        self.chart_widget = pg.PlotWidget()
        layout.addWidget(self.chart_widget)
        
    def setup_chart(self):
        """设置图表"""
        # 设置图表样式
        self.chart_widget.setBackground('w')  # 白色背景
        self.chart_widget.setLabel('left', '价格 (USDT)', color='black', size='12pt')
        self.chart_widget.setLabel('bottom', '时间', color='black', size='12pt')
        self.chart_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # 创建价格曲线
        self.price_curve = self.chart_widget.plot(
            pen=pg.mkPen(color='#2E86AB', width=2),
            name='价格'
        )
        
        # 设置图例
        self.chart_widget.addLegend()
        
        # 启用缩放和平移
        self.chart_widget.setMouseEnabled(x=True, y=True)
        self.chart_widget.enableAutoRange(axis='y')
        
    def add_popular_symbols(self):
        """添加热门交易对"""
        popular_symbols = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT",
            "SOLUSDT", "DOTUSDT", "DOGEUSDT", "AVAXUSDT", "SHIBUSDT",
            "MATICUSDT", "LTCUSDT", "UNIUSDT", "LINKUSDT", "ATOMUSDT"
        ]
        
        self.symbol_combo.clear()
        self.symbol_combo.addItems(popular_symbols)
        
    def on_symbol_changed(self, symbol: str):
        """交易对变化处理"""
        if symbol and symbol != self.current_symbol:
            self.current_symbol = symbol
            self.clear_data()
            self.chart_widget.setTitle(f"{symbol} 实时价格", color='black', size='14pt')
            self.symbol_changed.emit(symbol)
            
    def update_price(self, price_data: dict):
        """更新价格数据"""
        if not price_data or price_data.get('symbol') != self.current_symbol:
            return
            
        try:
            price = float(price_data.get('price', 0))
            change_percent = price_data.get('change_percent', '0.00%')
            timestamp = datetime.now().timestamp()
            
            # 添加数据点
            self.price_data.append(price)
            self.time_data.append(timestamp)
            
            # 更新价格显示
            self.price_label.setText(f"${price:.4f}")
            
            # 更新涨跌幅显示和颜色
            change_value = float(change_percent.replace('%', ''))
            if change_value > 0:
                self.change_label.setText(f"+{change_percent}")
                self.change_label.setStyleSheet("color: #00C851; font-weight: bold;")
                self.price_label.setStyleSheet("color: #00C851; padding: 5px; font-weight: bold;")
            elif change_value < 0:
                self.change_label.setText(change_percent)
                self.change_label.setStyleSheet("color: #FF4444; font-weight: bold;")
                self.price_label.setStyleSheet("color: #FF4444; padding: 5px; font-weight: bold;")
            else:
                self.change_label.setText(change_percent)
                self.change_label.setStyleSheet("color: #333; font-weight: bold;")
                self.price_label.setStyleSheet("color: #333; padding: 5px; font-weight: bold;")
                
        except (ValueError, TypeError) as e:
            print(f"Error updating price: {e}")
            
    def update_chart(self):
        """更新图表显示"""
        if len(self.price_data) < 2:
            return
            
        try:
            # 转换为numpy数组
            times = np.array(list(self.time_data))
            prices = np.array(list(self.price_data))
            
            # 更新曲线
            self.price_curve.setData(times, prices)
            
            # 自动调整Y轴范围
            if len(prices) > 0:
                min_price = np.min(prices)
                max_price = np.max(prices)
                padding = (max_price - min_price) * 0.1
                self.chart_widget.setYRange(min_price - padding, max_price + padding)
                
        except Exception as e:
            print(f"Error updating chart: {e}")
            
    def clear_data(self):
        """清除数据"""
        self.price_data.clear()
        self.time_data.clear()
        self.price_curve.setData([], [])
        self.price_label.setText("--")
        self.change_label.setText("--")
        self.change_label.setStyleSheet("color: #333;")
        self.price_label.setStyleSheet("color: #333; padding: 5px;")
        
    def set_symbol(self, symbol: str):
        """设置交易对"""
        index = self.symbol_combo.findText(symbol)
        if index >= 0:
            self.symbol_combo.setCurrentIndex(index)
        else:
            self.symbol_combo.addItem(symbol)
            self.symbol_combo.setCurrentText(symbol)