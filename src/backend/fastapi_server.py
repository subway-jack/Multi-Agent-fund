"""
FastAPI服务器
提供WebSocket接口给前端，转发币安实时价格数据
"""
import asyncio
import json
import logging
from typing import Dict, List, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .binance_websocket import BinanceWebSocketClient

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscribed_symbols: Set[str] = set()
        
    async def connect(self, websocket: WebSocket):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
        
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            
    async def broadcast(self, message: str):
        """广播消息给所有连接的客户端"""
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection)

# 全局变量
manager = ConnectionManager()
binance_client = BinanceWebSocketClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting FastAPI server...")
    yield
    logger.info("Shutting down FastAPI server...")
    await binance_client.close_all_connections()

# 创建FastAPI应用
app = FastAPI(
    title="Binance Real-time Price API",
    description="实时获取币安交易对价格数据",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def price_callback(data: dict):
    """价格数据回调函数"""
    message = json.dumps({
        "type": "price_update",
        "data": data
    })
    await manager.broadcast(message)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点"""
    await manager.connect(websocket)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await handle_client_message(message, websocket)
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": "Invalid JSON format"}),
                    websocket
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

async def handle_client_message(message: dict, websocket: WebSocket):
    """处理客户端消息"""
    message_type = message.get("type")
    
    if message_type == "subscribe":
        symbols = message.get("symbols", [])
        await subscribe_symbols(symbols, websocket)
        
    elif message_type == "unsubscribe":
        symbols = message.get("symbols", [])
        await unsubscribe_symbols(symbols, websocket)
        
    elif message_type == "get_subscribed":
        await manager.send_personal_message(
            json.dumps({
                "type": "subscribed_symbols",
                "symbols": list(manager.subscribed_symbols)
            }),
            websocket
        )
    else:
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": f"Unknown message type: {message_type}"}),
            websocket
        )

async def subscribe_symbols(symbols: List[str], websocket: WebSocket):
    """订阅交易对"""
    try:
        new_symbols = []
        for symbol in symbols:
            symbol = symbol.upper()
            if symbol not in manager.subscribed_symbols:
                new_symbols.append(symbol)
                manager.subscribed_symbols.add(symbol)
        
        if new_symbols:
            # 连接到币安WebSocket
            await binance_client.connect_multiple_tickers(new_symbols, price_callback)
            
        await manager.send_personal_message(
            json.dumps({
                "type": "subscribe_success",
                "symbols": symbols,
                "total_subscribed": len(manager.subscribed_symbols)
            }),
            websocket
        )
        
        logger.info(f"Subscribed to symbols: {symbols}")
        
    except Exception as e:
        logger.error(f"Error subscribing to symbols: {e}")
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": f"Failed to subscribe: {str(e)}"}),
            websocket
        )

async def unsubscribe_symbols(symbols: List[str], websocket: WebSocket):
    """取消订阅交易对"""
    try:
        for symbol in symbols:
            symbol = symbol.upper()
            manager.subscribed_symbols.discard(symbol)
            
        await manager.send_personal_message(
            json.dumps({
                "type": "unsubscribe_success",
                "symbols": symbols,
                "total_subscribed": len(manager.subscribed_symbols)
            }),
            websocket
        )
        
        logger.info(f"Unsubscribed from symbols: {symbols}")
        
    except Exception as e:
        logger.error(f"Error unsubscribing from symbols: {e}")
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": f"Failed to unsubscribe: {str(e)}"}),
            websocket
        )

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Binance Real-time Price API",
        "version": "1.0.0",
        "endpoints": {
            "websocket": "/ws",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "subscribed_symbols": len(manager.subscribed_symbols),
        "symbols": list(manager.subscribed_symbols)
    }

@app.get("/symbols")
async def get_popular_symbols():
    """获取热门交易对列表"""
    popular_symbols = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT",
        "SOLUSDT", "DOTUSDT", "DOGEUSDT", "AVAXUSDT", "SHIBUSDT",
        "MATICUSDT", "LTCUSDT", "UNIUSDT", "LINKUSDT", "ATOMUSDT"
    ]
    return {"symbols": popular_symbols}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )