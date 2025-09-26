"""
前端应用程序入口
PySide6 GUI应用程序
"""
import sys
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from .main_window import MainWindow

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class CryptoPriceApp:
    """加密货币价格监控应用"""
    
    def __init__(self):
        self.app = None
        self.main_window = None
        
    def run(self):
        """运行应用程序"""
        # 创建QApplication实例
        self.app = QApplication(sys.argv)
        
        # 设置应用程序属性
        self.app.setApplicationName("币安实时价格监控")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("CryptoMonitor")
        
        # 设置高DPI支持
        self.app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        self.app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # 创建主窗口
        self.main_window = MainWindow()
        self.main_window.show()
        
        # 运行应用程序
        return self.app.exec()

def main():
    """主函数"""
    app = CryptoPriceApp()
    sys.exit(app.run())

if __name__ == "__main__":
    main()