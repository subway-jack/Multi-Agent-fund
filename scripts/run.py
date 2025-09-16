#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票模拟器 - 通用启动脚本
让用户选择启动哪种界面模式
"""

import os
import sys
import subprocess

def show_menu():
    """显示启动菜单"""
    print("\n" + "="*60)
    print("🎮 股票模拟器 - 启动菜单")
    print("="*60)
    print("请选择启动模式:")
    print("")
    print("1. 🌐 Web界面    - 现代化Web UI (推荐)")
    print("2. 🖥️  GUI界面    - 桌面应用界面")
    print("3. 💻 命令行界面  - 传统终端交互")
    print("4. ❌ 退出")
    print("")
    print("="*60)

def run_web():
    """启动Web界面"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    web_script = os.path.join(script_dir, "run_web.py")
    subprocess.run([sys.executable, web_script])

def run_gui():
    """启动GUI界面"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gui_script = os.path.join(script_dir, "run_gui.py")
    subprocess.run([sys.executable, gui_script])

def run_cli():
    """启动命令行界面"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cli_script = os.path.join(script_dir, "run_cli.py")
    subprocess.run([sys.executable, cli_script])

def main():
    """主函数"""
    while True:
        show_menu()
        
        try:
            choice = input("请输入选择 (1-4): ").strip()
            
            if choice == "1":
                print("\n🌐 启动Web界面...")
                run_web()
            elif choice == "2":
                print("\n🖥️ 启动GUI界面...")
                run_gui()
            elif choice == "3":
                print("\n💻 启动命令行界面...")
                run_cli()
            elif choice == "4":
                print("\n👋 再见!")
                break
            else:
                print("\n❌ 无效选择，请输入 1-4")
                
        except KeyboardInterrupt:
            print("\n\n👋 检测到 Ctrl+C，退出程序")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")

if __name__ == "__main__":
    main()