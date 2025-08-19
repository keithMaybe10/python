"""
应用程序入口
"""
import sys
import os
import asyncio
import signal
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon

import qasync

from ui.main_window import MainWindow
from config.settings import APP_NAME
from utils.logger import setup_logger

logger = setup_logger("main")

class DevAcceleratorApp:
    """开发者加速器应用程序"""
    
    def __init__(self):
        self.app = None
        self.main_window = None
        self.event_loop = None
    
    def create_app(self):
        """创建应用程序"""
        # 创建QApplication
        self.app = QApplication(sys.argv)
        self.app.setApplicationName(APP_NAME)
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("DevAccelerator")
        
        # 设置应用图标（如果有的话）
        # self.app.setWindowIcon(QIcon("assets/icon.png"))
        
        # 创建异步事件循环
        self.event_loop = qasync.QEventLoop(self.app)
        asyncio.set_event_loop(self.event_loop)
        
        # 设置信号处理
        self.setup_signal_handlers()
        
        return self.app
    
    def setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(sig, frame):
            logger.info(f"接收到信号 {sig}，正在退出...")
            self.quit_application()
        
        # 设置SIGINT和SIGTERM处理器
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def create_main_window(self):
        """创建主窗口"""
        self.main_window = MainWindow()
        return self.main_window
    
    def run(self):
        """运行应用程序"""
        try:
            logger.info(f"正在启动 {APP_NAME}...")
            
            # 创建应用程序
            app = self.create_app()
            
            # 检查系统要求
            if not self.check_system_requirements():
                return 1
            
            # 创建主窗口
            main_window = self.create_main_window()
            main_window.show()
            
            logger.info(f"{APP_NAME} 启动成功")
            
            # 运行事件循环
            with self.event_loop:
                return self.event_loop.run_forever()
                
        except KeyboardInterrupt:
            logger.info("用户中断，正在退出...")
            return 0
        except Exception as e:
            logger.error(f"应用程序运行出错: {e}")
            return 1
        finally:
            self.cleanup()
    
    def check_system_requirements(self) -> bool:
        """检查系统要求"""
        try:
            # 检查Python版本
            if sys.version_info < (3, 8):
                QMessageBox.critical(
                    None, 
                    "系统要求不满足",
                    "需要Python 3.8或更高版本"
                )
                return False
            
            # 检查是否有管理员权限（Windows）
            if os.name == 'nt':
                try:
                    import ctypes
                    if not ctypes.windll.shell32.IsUserAnAdmin():
                        QMessageBox.warning(
                            None,
                            "权限提示", 
                            "建议以管理员权限运行以获得最佳体验"
                        )
                except Exception:
                    pass
            
            # 检查网络连接
            try:
                import socket
                socket.create_connection(("8.8.8.8", 53), timeout=3)
            except OSError:
                QMessageBox.warning(
                    None,
                    "网络连接",
                    "网络连接异常，某些功能可能无法正常使用"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"系统要求检查失败: {e}")
            return True  # 检查失败时仍然允许启动
    
    def quit_application(self):
        """退出应用程序"""
        try:
            if self.main_window:
                self.main_window.quit_application()
            
            if self.event_loop and self.event_loop.is_running():
                self.event_loop.stop()
            
            if self.app:
                self.app.quit()
                
        except Exception as e:
            logger.error(f"退出应用程序时出错: {e}")
    
    def cleanup(self):
        """清理资源"""
        try:
            logger.info("正在清理资源...")
            
            # 这里可以添加其他清理逻辑
            
            logger.info("资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源时出错: {e}")

def main():
    """主函数"""
    try:
        # 创建并运行应用程序
        app = DevAcceleratorApp()
        exit_code = app.run()
        
        logger.info(f"{APP_NAME} 已退出，退出码: {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())