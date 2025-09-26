"""
币安WebSocket连接模块
用于获取实时价格数据
"""
import asyncio
import json
import logging
from typing import Dict, List, Callable, Optional
import websockets
from datetime import datetime

logger = logging.getLogger(__name__)

class BinanceWebSocketClient:
    """币安WebSocket客户端"""
    
    def __init__(self):
        self.base_url = "wss://stream.binance.com:9443/ws/"
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self.running = False
        
    async def connect_symbol_ticker(self, symbol: str, callback: Callable):
        """连接单个交易对的价格流"""
        stream_name = f"{symbol.lower()}@ticker"
        
        if stream_name not in self.callbacks:
            self.callbacks[stream_name] = []
        self.callbacks[stream_name].append(callback)
        
        if stream_name not in self.connections:
            await self._create_connection(stream_name)
    
    async def connect_multiple_tickers(self, symbols: List[str], callback: Callable):
        """连接多个交易对的价格流"""
        streams = [f"{symbol.lower()}@ticker" for symbol in symbols]
        stream_name = "/".join(streams)
        
        if stream_name not in self.callbacks:
            self.callbacks[stream_name] = []
        self.callbacks[stream_name].append(callback)
        
        if stream_name not in self.connections:
            await self._create_connection(stream_name)
    
    async def _create_connection(self, stream_name: str):
        """创建WebSocket连接"""
        try:
            url = f"{self.base_url}{stream_name}"
            logger.info(f"Connecting to {url}")
            
            websocket = await websockets.connect(url)
            self.connections[stream_name] = websocket
            
            # 启动消息监听任务
            asyncio.create_task(self._listen_messages(stream_name, websocket))
            
        except Exception as e:
            logger.error(f"Failed to connect to {stream_name}: {e}")
            raise
    
    async def _listen_messages(self, stream_name: str, websocket):
        """监听WebSocket消息"""
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(stream_name, data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"Connection closed for {stream_name}")
            # 尝试重连
            await self._reconnect(stream_name)
        except Exception as e:
            logger.error(f"Error in message listener for {stream_name}: {e}")
    
    async def _handle_message(self, stream_name: str, data: dict):
        """处理接收到的消息"""
        if stream_name in self.callbacks:
            # 格式化数据
            formatted_data = self._format_ticker_data(data)
            
            # 调用所有回调函数
            for callback in self.callbacks[stream_name]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(formatted_data)
                    else:
                        callback(formatted_data)
                except Exception as e:
                    logger.error(f"Error in callback: {e}")
    
    def _format_ticker_data(self, data: dict) -> dict:
        """格式化ticker数据"""
        if 's' in data:  # 单个ticker数据
            return {
                'symbol': data['s'],
                'price': float(data['c']),
                'change': float(data['P']),
                'change_percent': f"{float(data['P']):.2f}%",
                'volume': float(data['v']),
                'high': float(data['h']),
                'low': float(data['l']),
                'timestamp': datetime.now().isoformat()
            }
        return data
    
    async def _reconnect(self, stream_name: str):
        """重连机制"""
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to reconnect {stream_name} (attempt {attempt + 1})")
                await asyncio.sleep(retry_delay)
                await self._create_connection(stream_name)
                logger.info(f"Successfully reconnected {stream_name}")
                return
            except Exception as e:
                logger.error(f"Reconnection attempt {attempt + 1} failed: {e}")
                retry_delay *= 2  # 指数退避
        
        logger.error(f"Failed to reconnect {stream_name} after {max_retries} attempts")
    
    async def close_connection(self, stream_name: str):
        """关闭指定连接"""
        if stream_name in self.connections:
            await self.connections[stream_name].close()
            del self.connections[stream_name]
            if stream_name in self.callbacks:
                del self.callbacks[stream_name]
    
    async def close_all_connections(self):
        """关闭所有连接"""
        for stream_name in list(self.connections.keys()):
            await self.close_connection(stream_name)
        self.running = False
    
    def is_connected(self, stream_name: str) -> bool:
        """检查连接状态"""
        return stream_name in self.connections and not self.connections[stream_name].closed