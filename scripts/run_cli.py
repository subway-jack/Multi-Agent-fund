#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票模拟器 - 命令行界面启动脚本
提供传统的终端交互体验
"""

import os
import sys

def main():
    """启动命令行界面"""
    print("💻 启动股票模拟器 命令行界面...")
    print("📊 功能说明:")
    print("   • 传统终端交互界面")
    print("   • 文本菜单操作")
    print("   • 实时数据显示")
    print("   • 庄家控制命令")
    print("\n🚀 正在初始化命令行界面...")
    
    # 获取项目根目录并添加到Python路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    try:
        # 导入并运行主程序
        from apps.main import main as run_main
        run_main()
    except KeyboardInterrupt:
        print("\n👋 命令行界面已关闭")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("请检查依赖是否正确安装")

if __name__ == "__main__":
    main()