#!/usr/bin/env python3
"""
前端应用启动脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.frontend.app import main

if __name__ == "__main__":
    print("启动币安实时价格监控前端应用...")
    print("请确保后端服务已经启动 (运行 python src/run_backend.py)")
    print("-" * 50)
    main()