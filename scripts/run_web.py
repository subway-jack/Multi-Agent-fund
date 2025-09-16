#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票模拟器 - Web界面启动脚本
使用Streamlit提供现代化的Web UI体验
"""

import os
import sys
import subprocess

def main():
    """启动Streamlit Web界面"""
    print("🌐 启动股票模拟器 Web 界面...")
    print("📊 功能说明:")
    print("   • 现代化的Web界面")
    print("   • 实时数据可视化")
    print("   • 庄家操控面板")
    print("   • 交互式图表分析")
    print("\n🚀 正在启动Streamlit服务器...")
    
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    streamlit_app = os.path.join(project_root, "src", "interfaces", "streamlit_app.py")
    
    try:
        # 启动streamlit应用
        subprocess.run(["streamlit", "run", streamlit_app], cwd=project_root)
    except KeyboardInterrupt:
        print("\n👋 Web界面已关闭")
    except FileNotFoundError:
        print("❌ 未找到streamlit命令，请先安装: pip install streamlit")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()