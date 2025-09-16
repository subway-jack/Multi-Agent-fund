#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票模拟器 - GUI桌面应用启动脚本
使用pygame提供原生桌面应用体验
"""

import os
import sys

def main():
    """启动GUI桌面应用"""
    print("🖥️  启动股票模拟器 GUI 桌面应用...")
    print("📊 功能说明:")
    print("   • 原生桌面应用界面")
    print("   • 鼠标和键盘操作")
    print("   • 实时数据显示")
    print("   • 庄家控制面板")
    print("\n🚀 正在初始化GUI界面...")
    
    # 获取项目根目录并添加到Python路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    try:
        # 导入并启动GUI应用
        from src.interfaces.gui_interface import StockSimulatorGUI
        from src.core.app import app
        
        # 创建并运行GUI
        gui = StockSimulatorGUI()
        print("✅ GUI界面已启动!")
        print("💡 提示: 点击'开始模拟'按钮开始AI交易")
        gui.run()
        
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        print("请运行: pip install pygame")
    except Exception as e:
        import traceback
        print(f"❌ 启动失败: {e}")
        print("详细错误信息:")
        traceback.print_exc()
    finally:
        # 清理应用程序资源
        try:
            from src.core.app import app
            app.cleanup()
        except:
            pass

if __name__ == "__main__":
    main()