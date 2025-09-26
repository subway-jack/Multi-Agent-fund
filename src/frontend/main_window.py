"""
主窗口界面
整合所有组件的主界面
"""
import sys
import logging
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QSplitter, QTextEdit, QLabel, QPushButton, 
                               QStatusBar, QMenuBar, QMessageBox, QGroupBox,
                               QListWidget, QListWidgetItem, QCheckBox)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QIcon, QFont

from .websocket_client import WebSocketClient
from .price_chart import PriceChart

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.websocket_client = None
        self.setup_ui()
        self.setup_websocket()
        self.setup_connections()
        
        # 状态更新定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # 每秒更新状态
        
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("币安实时价格监控系统")
        self.setGeometry(100, 100, 1400, 800)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 连接状态标签
        self.connection_label = QLabel("未连接")
        self.connection_label.setStyleSheet("color: red; font-weight: bold;")
        self.status_bar.addPermanentWidget(self.connection_label)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧面板
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧图表区域
        self.price_chart = PriceChart()
        splitter.addWidget(self.price_chart)
        
        # 设置分割器比例
        splitter.setSizes([300, 1100])
        
        # 初始化图表
        self.price_chart.add_popular_symbols()
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 连接菜单
        connection_menu = menubar.addMenu('连接')
        
        connect_action = QAction('连接服务器', self)
        connect_action.triggered.connect(self.connect_to_server)
        connection_menu.addAction(connect_action)
        
        disconnect_action = QAction('断开连接', self)
        disconnect_action.triggered.connect(self.disconnect_from_server)
        connection_menu.addAction(disconnect_action)
        
        connection_menu.addSeparator()
        
        exit_action = QAction('退出', self)
        exit_action.triggered.connect(self.close)
        connection_menu.addAction(exit_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_left_panel(self):
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 连接控制组
        connection_group = QGroupBox("连接控制")
        connection_layout = QVBoxLayout(connection_group)
        
        self.connect_button = QPushButton("连接服务器")
        self.connect_button.clicked.connect(self.connect_to_server)
        connection_layout.addWidget(self.connect_button)
        
        self.disconnect_button = QPushButton("断开连接")
        self.disconnect_button.clicked.connect(self.disconnect_from_server)
        self.disconnect_button.setEnabled(False)
        connection_layout.addWidget(self.disconnect_button)
        
        layout.addWidget(connection_group)
        
        # 交易对管理组
        symbols_group = QGroupBox("交易对管理")
        symbols_layout = QVBoxLayout(symbols_group)
        
        # 已订阅交易对列表
        symbols_layout.addWidget(QLabel("已订阅交易对:"))
        self.subscribed_list = QListWidget()
        self.subscribed_list.itemClicked.connect(self.on_symbol_selected)
        symbols_layout.addWidget(self.subscribed_list)
        
        # 订阅控制
        subscribe_layout = QHBoxLayout()
        self.subscribe_button = QPushButton("订阅选中")
        self.subscribe_button.clicked.connect(self.subscribe_selected_symbol)
        self.subscribe_button.setEnabled(False)
        subscribe_layout.addWidget(self.subscribe_button)
        
        self.unsubscribe_button = QPushButton("取消订阅")
        self.unsubscribe_button.clicked.connect(self.unsubscribe_selected_symbol)
        self.unsubscribe_button.setEnabled(False)
        subscribe_layout.addWidget(self.unsubscribe_button)
        
        symbols_layout.addLayout(subscribe_layout)
        
        layout.addWidget(symbols_group)
        
        # 日志区域
        log_group = QGroupBox("系统日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)
        
        # 清除日志按钮
        clear_log_button = QPushButton("清除日志")
        clear_log_button.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_button)
        
        layout.addWidget(log_group)
        
        layout.addStretch()
        
        return panel
        
    def setup_websocket(self):
        """设置WebSocket客户端"""
        self.websocket_client = WebSocketClient()
        
    def setup_connections(self):
        """设置信号连接"""
        if self.websocket_client:
            self.websocket_client.connected.connect(self.on_connected)
            self.websocket_client.disconnected.connect(self.on_disconnected)
            self.websocket_client.price_updated.connect(self.on_price_updated)
            self.websocket_client.error_occurred.connect(self.on_error)
            self.websocket_client.connection_status_changed.connect(self.on_connection_status_changed)
            
        # 图表信号
        self.price_chart.symbol_changed.connect(self.on_chart_symbol_changed)
        
    def connect_to_server(self):
        """连接到服务器"""
        if self.websocket_client:
            self.websocket_client.connect_to_server()
            self.log_message("正在连接到服务器...")
            
    def disconnect_from_server(self):
        """断开服务器连接"""
        if self.websocket_client:
            self.websocket_client.disconnect_from_server()
            self.log_message("断开服务器连接")
            
    def on_connected(self):
        """连接成功处理"""
        self.log_message("✓ 已连接到服务器")
        self.connect_button.setEnabled(False)
        self.disconnect_button.setEnabled(True)
        self.subscribe_button.setEnabled(True)
        
        # 自动订阅当前选中的交易对
        current_symbol = self.price_chart.current_symbol
        if current_symbol:
            self.websocket_client.subscribe_symbols([current_symbol])
            
    def on_disconnected(self):
        """断开连接处理"""
        self.log_message("✗ 已断开服务器连接")
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.subscribe_button.setEnabled(False)
        self.unsubscribe_button.setEnabled(False)
        
    def on_price_updated(self, price_data: dict):
        """价格更新处理"""
        self.price_chart.update_price(price_data)
        
        # 更新订阅列表中的价格
        symbol = price_data.get('symbol', '')
        price = price_data.get('price', 0)
        change_percent = price_data.get('change_percent', '0.00%')
        
        for i in range(self.subscribed_list.count()):
            item = self.subscribed_list.item(i)
            if item.text().startswith(symbol):
                item.setText(f"{symbol} - ${price:.4f} ({change_percent})")
                
                # 设置颜色
                change_value = float(change_percent.replace('%', ''))
                if change_value > 0:
                    item.setBackground(Qt.green)
                elif change_value < 0:
                    item.setBackground(Qt.red)
                else:
                    item.setBackground(Qt.white)
                break
                
    def on_error(self, error_message: str):
        """错误处理"""
        self.log_message(f"✗ 错误: {error_message}")
        
    def on_connection_status_changed(self, connected: bool):
        """连接状态变化处理"""
        if connected:
            self.connection_label.setText("已连接")
            self.connection_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.connection_label.setText("未连接")
            self.connection_label.setStyleSheet("color: red; font-weight: bold;")
            
    def on_chart_symbol_changed(self, symbol: str):
        """图表交易对变化处理"""
        if self.websocket_client and self.websocket_client.is_connected:
            # 订阅新的交易对
            self.websocket_client.subscribe_symbols([symbol])
            self.log_message(f"订阅交易对: {symbol}")
            
    def on_symbol_selected(self, item: QListWidgetItem):
        """交易对选中处理"""
        symbol = item.text().split(' - ')[0]  # 提取交易对名称
        self.price_chart.set_symbol(symbol)
        self.unsubscribe_button.setEnabled(True)
        
    def subscribe_selected_symbol(self):
        """订阅选中的交易对"""
        current_symbol = self.price_chart.current_symbol
        if current_symbol and self.websocket_client and self.websocket_client.is_connected:
            if not self.websocket_client.is_symbol_subscribed(current_symbol):
                self.websocket_client.subscribe_symbols([current_symbol])
                
                # 添加到订阅列表
                item = QListWidgetItem(f"{current_symbol} - 加载中...")
                self.subscribed_list.addItem(item)
                
                self.log_message(f"订阅交易对: {current_symbol}")
            else:
                self.log_message(f"交易对 {current_symbol} 已经订阅")
                
    def unsubscribe_selected_symbol(self):
        """取消订阅选中的交易对"""
        current_item = self.subscribed_list.currentItem()
        if current_item:
            symbol = current_item.text().split(' - ')[0]
            if self.websocket_client:
                self.websocket_client.unsubscribe_symbols([symbol])
                
            # 从列表中移除
            row = self.subscribed_list.row(current_item)
            self.subscribed_list.takeItem(row)
            
            self.log_message(f"取消订阅交易对: {symbol}")
            self.unsubscribe_button.setEnabled(False)
            
    def log_message(self, message: str):
        """添加日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def clear_log(self):
        """清除日志"""
        self.log_text.clear()
        
    def update_status(self):
        """更新状态栏"""
        if self.websocket_client:
            subscribed_count = len(self.websocket_client.subscribed_symbols)
            self.status_bar.showMessage(f"已订阅 {subscribed_count} 个交易对")
            
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "币安实时价格监控系统 v1.0\n\n"
            "基于 PySide6 + PyQtGraph + FastAPI 构建\n"
            "实时获取币安交易所价格数据\n\n"
            "功能特性:\n"
            "• 实时价格图表显示\n"
            "• 多交易对同时监控\n"
            "• WebSocket 长连接\n"
            "• 自动重连机制"
        )
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.websocket_client:
            self.websocket_client.disconnect_from_server()
        event.accept()