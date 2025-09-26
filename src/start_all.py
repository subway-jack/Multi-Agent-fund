#!/usr/bin/env python3
"""
同时启动前后端的脚本
"""
import sys
import time
import subprocess
import threading
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def start_backend():
    """启动后端服务"""
    print("正在启动后端服务...")
    try:
        subprocess.run([
            sys.executable, 
            str(project_root / "src" / "run_backend.py")
        ])
    except KeyboardInterrupt:
        print("后端服务已停止")
    except Exception as e:
        print(f"后端服务启动失败: {e}")

def start_frontend():
    """启动前端应用"""
    print("等待后端服务启动...")
    time.sleep(3)  # 等待后端服务启动
    
    print("正在启动前端应用...")
    try:
        subprocess.run([
            sys.executable, 
            str(project_root / "src" / "run_frontend.py")
        ])
    except KeyboardInterrupt:
        print("前端应用已停止")
    except Exception as e:
        print(f"前端应用启动失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("币安实时价格监控系统")
    print("=" * 60)
    print("正在启动前后端服务...")
    print()
    
    try:
        # 在后台线程启动后端
        backend_thread = threading.Thread(target=start_backend, daemon=True)
        backend_thread.start()
        
        # 启动前端（主线程）
        start_frontend()
        
    except KeyboardInterrupt:
        print("\n正在关闭应用...")
    except Exception as e:
        print(f"启动失败: {e}")
    
    print("应用已关闭")

if __name__ == "__main__":
    main()