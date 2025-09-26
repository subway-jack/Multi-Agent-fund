#!/usr/bin/env python3
"""
后端服务启动脚本
"""
import sys
import os
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.app_config import config_manager

def main():
    """启动FastAPI服务器"""
    print("启动币安实时价格监控后端服务...")
    
    # 获取服务器配置
    server_config = config_manager.get_server_config()
    
    print(f"服务器地址: http://{server_config.host}:{server_config.port}")
    print(f"WebSocket地址: ws://{server_config.host}:{server_config.port}/ws")
    print(f"健康检查: http://{server_config.host}:{server_config.port}/health")
    print("-" * 50)
    
    # 启动服务器
    uvicorn.run(
        "src.backend.fastapi_server:app",
        host=server_config.host,
        port=server_config.port,
        reload=server_config.reload,
        log_level=server_config.log_level,
        access_log=True
    )

if __name__ == "__main__":
    main()