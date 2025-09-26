"""
前端WebSocket客户端
用于连接FastAPI后端服务
"""
import json
import logging
from typing import Callable, Optional, List
from PySide6.QtCore import QObject, Signal, QThread, QTimer
from PySide6.QtWebSockets import QWebSocket
from PySide6.QtNetwork import QNetworkRequest
from PySide6.QtCore import QUrl

logger = logging.getLogger(__name__)

class WebSocketClient(QObject):
    """WebSocket客户端"""
    
    # 信号定义
    connected = Signal()
    disconnected = Signal()
    price_updated = Signal(dict)  # 价格更新信号
    error_occurred = Signal(str)  # 错误信号
    connection_status_changed = Signal(bool)  # 连接状态变化
    
    def __init__(self, server_url: str = "ws://localhost:8000/ws"):
        super().__init__()
        self.server_url = server_url
        self.websocket = QWebSocket()
        self.is_connected = False
        self.subscribed_symbols = set()
        
        # 连接信号
        self.websocket.connected.connect(self._on_connected)
        self.websocket.disconnected.connect(self._on_disconnected)
        self.websocket.textMessageReceived.connect(self._on_message_received)
        self.websocket.errorOccurred.connect(self._on_error)
        
        # 重连定时器
        self.reconnect_timer = QTimer()
        self.reconnect_timer.timeout.connect(self._attempt_reconnect)
        self.reconnect_timer.setSingleShot(True)
        
        # 心跳定时器
        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self._send_heartbeat)
        
    def connect_to_server(self):
        """连接到服务器"""
        if self.is_connected:
            logger.warning("Already connected to server")
            return
            
        logger.info(f"Connecting to {self.server_url}")
        request = QNetworkRequest(QUrl(self.server_url))
        self.websocket.open(request)
        
    def disconnect_from_server(self):
        """断开服务器连接"""
        if self.is_connected:
            self.websocket.close()
        self.heartbeat_timer.stop()
        self.reconnect_timer.stop()
        
    def _on_connected(self):
        """连接成功回调"""
        self.is_connected = True
        logger.info("Connected to server")
        self.connected.emit()
        self.connection_status_changed.emit(True)
        
        # 启动心跳
        self.heartbeat_timer.start(30000)  # 30秒心跳
        
    def _on_disconnected(self):
        """断开连接回调"""
        self.is_connected = False
        logger.info("Disconnected from server")
        self.disconnected.emit()
        self.connection_status_changed.emit(False)
        
        # 停止心跳
        self.heartbeat_timer.stop()
        
        # 启动重连
        self._start_reconnect()
        
    def _on_message_received(self, message: str):
        """接收消息回调"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "price_update":
                self.price_updated.emit(data.get("data", {}))
                
            elif message_type == "subscribe_success":
                symbols = data.get("symbols", [])
                for symbol in symbols:
                    self.subscribed_symbols.add(symbol)
                logger.info(f"Successfully subscribed to: {symbols}")
                
            elif message_type == "unsubscribe_success":
                symbols = data.get("symbols", [])
                for symbol in symbols:
                    self.subscribed_symbols.discard(symbol)
                logger.info(f"Successfully unsubscribed from: {symbols}")
                
            elif message_type == "error":
                error_msg = data.get("message", "Unknown error")
                logger.error(f"Server error: {error_msg}")
                self.error_occurred.emit(error_msg)
                
            elif message_type == "subscribed_symbols":
                symbols = data.get("symbols", [])
                self.subscribed_symbols = set(symbols)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
            self.error_occurred.emit(f"Failed to parse server message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            self.error_occurred.emit(f"Error handling message: {e}")
            
    def _on_error(self, error):
        """错误回调"""
        error_msg = f"WebSocket error: {error}"
        logger.error(error_msg)
        self.error_occurred.emit(error_msg)
        
    def _send_heartbeat(self):
        """发送心跳"""
        if self.is_connected:
            self._send_message({"type": "heartbeat"})
            
    def _start_reconnect(self):
        """开始重连"""
        if not self.reconnect_timer.isActive():
            self.reconnect_timer.start(5000)  # 5秒后重连
            
    def _attempt_reconnect(self):
        """尝试重连"""
        if not self.is_connected:
            logger.info("Attempting to reconnect...")
            self.connect_to_server()
            
    def _send_message(self, message: dict):
        """发送消息"""
        if self.is_connected:
            try:
                json_message = json.dumps(message)
                self.websocket.sendTextMessage(json_message)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                self.error_occurred.emit(f"Failed to send message: {e}")
        else:
            logger.warning("Cannot send message: not connected")
            
    def subscribe_symbols(self, symbols: List[str]):
        """订阅交易对"""
        message = {
            "type": "subscribe",
            "symbols": symbols
        }
        self._send_message(message)
        
    def unsubscribe_symbols(self, symbols: List[str]):
        """取消订阅交易对"""
        message = {
            "type": "unsubscribe",
            "symbols": symbols
        }
        self._send_message(message)
        
    def get_subscribed_symbols(self):
        """获取已订阅的交易对"""
        message = {"type": "get_subscribed"}
        self._send_message(message)
        
    def is_symbol_subscribed(self, symbol: str) -> bool:
        """检查交易对是否已订阅"""
        return symbol.upper() in self.subscribed_symbols