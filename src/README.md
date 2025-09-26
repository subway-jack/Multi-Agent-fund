# 币安实时价格监控系统

基于 PySide6 + PyQtGraph + FastAPI + WebSocket 构建的实时加密货币价格监控系统。

## 功能特性

- 🚀 **实时价格监控**: 通过币安WebSocket API获取实时价格数据
- 📊 **动态图表显示**: 使用PyQtGraph实现高性能实时价格图表
- 🔄 **多交易对支持**: 同时监控多个加密货币交易对
- 🌐 **前后端分离**: FastAPI后端 + PySide6前端架构
- 🔌 **WebSocket通信**: 前后端通过WebSocket实现实时数据传输
- 🔧 **自动重连机制**: 网络断开时自动重连
- ⚙️ **配置管理**: 灵活的配置文件管理
- 📱 **现代化UI**: 基于PySide6的现代化用户界面

## 项目结构

```
src/
├── backend/                 # 后端服务
│   ├── __init__.py
│   ├── binance_websocket.py # 币安WebSocket客户端
│   └── fastapi_server.py    # FastAPI服务器
├── frontend/                # 前端应用
│   ├── __init__.py
│   ├── app.py              # 应用程序入口
│   ├── main_window.py      # 主窗口界面
│   ├── price_chart.py      # 价格图表组件
│   └── websocket_client.py # WebSocket客户端
├── config/                 # 配置管理
│   └── app_config.py       # 应用配置
├── run_backend.py          # 后端启动脚本
├── run_frontend.py         # 前端启动脚本
├── start_all.py           # 同时启动前后端
└── README.md              # 项目说明
```

## 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖包：
- `fastapi==0.115.6` - Web框架
- `uvicorn[standard]==0.34.0` - ASGI服务器
- `PySide6==6.8.1` - GUI框架
- `pyqtgraph==0.13.7` - 图表库
- `websockets==15.0.1` - WebSocket支持
- `python-binance==1.0.19` - 币安API

## 使用方法

### 方式一：同时启动前后端

```bash
cd src
python start_all.py
```

### 方式二：分别启动

1. 启动后端服务：
```bash
cd src
python run_backend.py
```

2. 启动前端应用：
```bash
cd src
python run_frontend.py
```

## API接口

### WebSocket接口

- **连接地址**: `ws://localhost:8000/ws`

### 消息格式

#### 订阅交易对
```json
{
    "type": "subscribe",
    "symbols": ["BTCUSDT", "ETHUSDT"]
}
```

#### 取消订阅
```json
{
    "type": "unsubscribe",
    "symbols": ["BTCUSDT"]
}
```

#### 价格更新推送
```json
{
    "type": "price_update",
    "data": {
        "symbol": "BTCUSDT",
        "price": 45000.50,
        "change": 1.25,
        "change_percent": "2.85%",
        "volume": 1234567.89,
        "high": 46000.00,
        "low": 44000.00,
        "timestamp": "2024-01-01T12:00:00"
    }
}
```

### REST接口

- `GET /` - 根路径信息
- `GET /health` - 健康检查
- `GET /symbols` - 获取热门交易对列表

## 配置说明

配置文件位置：`config/app_config.json`

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "reload": true,
    "log_level": "info"
  },
  "binance": {
    "base_ws_url": "wss://stream.binance.com:9443/ws/",
    "reconnect_delay": 5,
    "max_retries": 5,
    "heartbeat_interval": 30
  },
  "ui": {
    "window_width": 1400,
    "window_height": 800,
    "chart_max_points": 1000,
    "update_interval": 100,
    "default_symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
  }
}
```

## 技术架构

### 后端架构
- **FastAPI**: 提供WebSocket和REST API服务
- **币安WebSocket**: 连接币安实时数据流
- **异步处理**: 使用asyncio处理并发连接
- **自动重连**: 网络异常时自动重连机制

### 前端架构
- **PySide6**: 跨平台GUI框架
- **PyQtGraph**: 高性能实时图表显示
- **WebSocket客户端**: 与后端实时通信
- **信号槽机制**: Qt信号槽实现组件通信

### 数据流程
1. 币安WebSocket → 后端服务器
2. 后端服务器 → 前端WebSocket客户端
3. 前端客户端 → PyQtGraph图表组件
4. 图表组件 → 用户界面显示

## 开发说明

### 添加新的交易对
在 `src/config/app_config.py` 中的 `UIConfig.default_symbols` 列表中添加新的交易对。

### 自定义图表样式
修改 `src/frontend/price_chart.py` 中的 `setup_chart()` 方法。

### 修改服务器配置
编辑 `config/app_config.json` 文件或使用配置管理器API。

## 注意事项

1. **网络连接**: 需要稳定的网络连接访问币安API
2. **资源使用**: 监控多个交易对会增加内存和CPU使用
3. **数据限制**: 图表默认显示最近1000个数据点
4. **API限制**: 遵守币安API使用限制

## 故障排除

### 常见问题

1. **连接失败**
   - 检查网络连接
   - 确认后端服务已启动
   - 检查防火墙设置

2. **图表不更新**
   - 检查WebSocket连接状态
   - 确认已订阅交易对
   - 查看控制台错误信息

3. **性能问题**
   - 减少监控的交易对数量
   - 调整图表更新频率
   - 清理历史数据

## 许可证

本项目采用 MIT 许可证。