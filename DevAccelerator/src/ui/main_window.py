"""
主窗口界面
"""
import asyncio
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QTabWidget, QFrame, QScrollArea,
    QSystemTrayIcon, QMenu, QApplication, QMessageBox, QSplitter,
    QTextEdit, QGroupBox, QCheckBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QObject
from PySide6.QtGui import QIcon, QFont, QPixmap, QPainter, QAction

from config.settings import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, APP_NAME
from core.accelerator import accelerator, AcceleratorStatus
from ui.styles import ANT_DESIGN_STYLE, get_icon, get_status_color, THEME
from ui.widgets import (
    StatusCard, NodeStatusWidget, LogWidget, MetricsWidget, 
    NodeTableWidget, AddNodeDialog, LoadingWidget, CertInstallDialog
)
from utils.logger import setup_logger

logger = setup_logger("main_window")

class AcceleratorWorker(QObject):
    """加速器工作线程"""
    
    status_changed = Signal(str)
    nodes_updated = Signal(dict)
    stats_updated = Signal(dict)
    log_message = Signal(str, str)
    
    def __init__(self):
        super().__init__()
        self.running = False
    
    def start_monitoring(self):
        """开始监控"""
        self.running = True
        self.monitor_loop()
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
    
    def monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 更新状态
                status = accelerator.get_status()
                self.status_changed.emit(status.value)
                
                # 更新节点信息
                nodes_info = accelerator.get_nodes_info()
                self.nodes_updated.emit(nodes_info)
                
                # 更新统计信息
                stats = accelerator.get_stats()
                self.stats_updated.emit(stats)
                
                # 等待1秒
                QThread.msleep(1000)
                
            except Exception as e:
                self.log_message.emit(f"监控线程出错: {e}", "ERROR")
                break

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v1.0.0")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # 应用样式
        self.setStyleSheet(ANT_DESIGN_STYLE)
        
        # 初始化组件
        self.node_widgets = {}
        self.add_node_dialog = None
        self.setup_ui()
        self.setup_system_tray()
        
        # 设置工作线程
        self.worker_thread = QThread()
        self.worker = AcceleratorWorker()
        self.worker.moveToThread(self.worker_thread)
        
        # 连接信号
        self.worker.status_changed.connect(self.update_status)
        self.worker.nodes_updated.connect(self.update_nodes_display)
        self.worker.stats_updated.connect(self.update_stats_display)
        self.worker.log_message.connect(self.add_log_message)
        
        # 启动工作线程
        self.worker_thread.started.connect(self.worker.start_monitoring)
        self.worker_thread.start()
        
        # 连接加速器状态回调
        accelerator.add_status_callback(self.on_accelerator_status_changed)
        
        # 初始化状态
        self.update_ui_state()
    
    def setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # 顶部控制栏
        self.setup_control_bar(main_layout)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧面板
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧面板
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割比例
        splitter.setSizes([400, 600])
        
        # 状态栏
        self.setup_status_bar()
    
    def setup_control_bar(self, parent_layout):
        """设置控制栏"""
        control_frame = QFrame()
        control_frame.setProperty("class", "card")
        control_layout = QHBoxLayout(control_frame)
        
        # 状态显示
        self.status_label = QLabel("● 已停止")
        self.status_label.setFont(QFont("", 14, QFont.Weight.Bold))
        self.status_label.setProperty("class", "status-stopped")
        control_layout.addWidget(self.status_label)
        
        control_layout.addStretch()
        
        # 控制按钮
        self.start_button = QPushButton(f"{get_icon('play')} 启动加速")
        self.start_button.setProperty("class", "primary")
        self.start_button.clicked.connect(self.toggle_accelerator)
        control_layout.addWidget(self.start_button)
        
        self.refresh_button = QPushButton(f"{get_icon('refresh')} 刷新节点")
        self.refresh_button.clicked.connect(self.refresh_nodes)
        control_layout.addWidget(self.refresh_button)
        
        self.settings_button = QPushButton(f"{get_icon('settings')} 设置")
        self.settings_button.clicked.connect(self.show_settings)
        control_layout.addWidget(self.settings_button)
        
        parent_layout.addWidget(control_frame)
    
    def create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(16)
        
        # 站点状态卡片
        sites_card = StatusCard("站点状态", "network")
        self.setup_sites_status(sites_card)
        left_layout.addWidget(sites_card)
        
        # 指标卡片
        metrics_card = StatusCard("实时指标", "chart")
        self.metrics_widget = MetricsWidget()
        metrics_card.add_content(self.metrics_widget)
        left_layout.addWidget(metrics_card)
        
        # 系统代理配置
        proxy_card = StatusCard("代理配置", "settings")
        self.setup_proxy_config(proxy_card)
        left_layout.addWidget(proxy_card)
        
        left_layout.addStretch()
        return left_widget
    
    def setup_sites_status(self, parent_card):
        """设置站点状态"""
        from config.settings import SUPPORTED_SITES
        
        # 创建网格布局
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(12)
        
        # 为每个支持的站点创建状态卡片
        row, col = 0, 0
        for site_key, site_config in SUPPORTED_SITES.items():
            node_widget = NodeStatusWidget(
                site_config["name"], 
                site_config.get("icon", "network")
            )
            self.node_widgets[site_key] = node_widget
            
            grid_layout.addWidget(node_widget, row, col)
            
            col += 1
            if col >= 2:  # 每行2个
                col = 0
                row += 1
        
        parent_card.add_content(grid_widget)
    
    def setup_proxy_config(self, parent_card):
        """设置代理配置"""
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)
        
        # HTTP代理
        http_layout = QHBoxLayout()
        http_layout.addWidget(QLabel("HTTP代理:"))
        self.http_proxy_label = QLabel("127.0.0.1:8080")
        self.http_proxy_label.setProperty("class", "description")
        http_layout.addWidget(self.http_proxy_label)
        http_layout.addStretch()
        config_layout.addLayout(http_layout)
        
        # HTTPS代理
        https_layout = QHBoxLayout()
        https_layout.addWidget(QLabel("HTTPS代理:"))
        self.https_proxy_label = QLabel("127.0.0.1:8443")
        self.https_proxy_label.setProperty("class", "description")
        https_layout.addWidget(self.https_proxy_label)
        https_layout.addStretch()
        config_layout.addLayout(https_layout)
        
        # DNS服务器
        dns_layout = QHBoxLayout()
        dns_layout.addWidget(QLabel("DNS服务器:"))
        self.dns_server_label = QLabel("127.0.0.1:5353")
        self.dns_server_label.setProperty("class", "description")
        dns_layout.addWidget(self.dns_server_label)
        dns_layout.addStretch()
        config_layout.addLayout(dns_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        copy_button = QPushButton(f"{get_icon('copy')} 复制配置")
        copy_button.clicked.connect(self.copy_proxy_config)
        button_layout.addWidget(copy_button)
        
        cert_button = QPushButton(f"{get_icon('key')} 证书安装")
        cert_button.clicked.connect(self.show_cert_install_dialog)
        button_layout.addWidget(cert_button)
        
        config_layout.addLayout(button_layout)
        
        parent_card.add_content(config_widget)
    
    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        right_layout.addWidget(self.tab_widget)
        
        # 节点管理标签页
        self.setup_nodes_tab()
        
        # 日志标签页
        self.setup_logs_tab()
        
        return right_widget
    
    def setup_nodes_tab(self):
        """设置节点管理标签页"""
        nodes_widget = QWidget()
        nodes_layout = QVBoxLayout(nodes_widget)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        add_node_btn = QPushButton(f"{get_icon('add')} 添加节点")
        add_node_btn.clicked.connect(self.show_add_node_dialog)
        toolbar_layout.addWidget(add_node_btn)
        
        test_all_btn = QPushButton(f"{get_icon('refresh')} 测试所有")
        test_all_btn.clicked.connect(self.test_all_nodes)
        toolbar_layout.addWidget(test_all_btn)
        
        toolbar_layout.addStretch()
        
        refresh_github_btn = QPushButton(f"{get_icon('github')} 刷新GitHub")
        refresh_github_btn.clicked.connect(self.refresh_github_nodes)
        toolbar_layout.addWidget(refresh_github_btn)
        
        nodes_layout.addLayout(toolbar_layout)
        
        # 节点表格
        self.nodes_table = NodeTableWidget()
        self.nodes_table.node_selected.connect(self.test_single_node)
        nodes_layout.addWidget(self.nodes_table)
        
        self.tab_widget.addTab(nodes_widget, f"{get_icon('network')} 节点管理")
    
    def setup_logs_tab(self):
        """设置日志标签页"""
        logs_widget = QWidget()
        logs_layout = QVBoxLayout(logs_widget)
        
        # 日志工具栏
        log_toolbar = QHBoxLayout()
        
        clear_logs_btn = QPushButton(f"{get_icon('remove')} 清空日志")
        clear_logs_btn.clicked.connect(self.clear_logs)
        log_toolbar.addWidget(clear_logs_btn)
        
        log_toolbar.addStretch()
        
        # 日志级别选择
        log_level_label = QLabel("级别:")
        log_toolbar.addWidget(log_level_label)
        
        from PySide6.QtWidgets import QComboBox
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["全部", "INFO", "WARNING", "ERROR"])
        log_toolbar.addWidget(self.log_level_combo)
        
        logs_layout.addLayout(log_toolbar)
        
        # 日志显示
        self.log_widget = LogWidget()
        logs_layout.addWidget(self.log_widget)
        
        self.tab_widget.addTab(logs_widget, f"{get_icon('log')} 运行日志")
    
    def setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = self.statusBar()
        
        # 连接状态
        self.connection_status = QLabel("未连接")
        self.status_bar.addWidget(self.connection_status)
        
        self.status_bar.addPermanentWidget(QLabel(f"版本: v1.0.0"))
    
    def setup_system_tray(self):
        """设置系统托盘"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        start_action = QAction("启动加速", self)
        start_action.triggered.connect(self.start_accelerator)
        tray_menu.addAction(start_action)
        
        stop_action = QAction("停止加速", self)
        stop_action.triggered.connect(self.stop_accelerator)
        tray_menu.addAction(stop_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
    
    def tray_icon_activated(self, reason):
        """托盘图标激活"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isHidden():
                self.show()
            else:
                self.hide()
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self.quit_application()
    
    def quit_application(self):
        """退出应用程序"""
        # 停止工作线程
        self.worker.stop_monitoring()
        self.worker_thread.quit()
        self.worker_thread.wait()
        
        # 停止加速器
        if accelerator.is_running():
            asyncio.run(accelerator.stop())
        
        QApplication.quit()
    
    def toggle_accelerator(self):
        """切换加速器状态"""
        if accelerator.is_running():
            self.stop_accelerator()
        else:
            self.start_accelerator()
    
    def start_accelerator(self):
        """启动加速器"""
        self.add_log_message("正在启动加速器...", "INFO")
        self.start_button.setEnabled(False)
        
        # 在后台线程中启动
        def start_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(accelerator.start())
            if success:
                self.add_log_message("加速器启动成功", "SUCCESS")
            else:
                self.add_log_message("加速器启动失败", "ERROR")
            self.start_button.setEnabled(True)
        
        import threading
        threading.Thread(target=start_async, daemon=True).start()
    
    def stop_accelerator(self):
        """停止加速器"""
        self.add_log_message("正在停止加速器...", "INFO")
        self.start_button.setEnabled(False)
        
        # 在后台线程中停止
        def stop_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(accelerator.stop())
            self.add_log_message("加速器已停止", "INFO")
            self.start_button.setEnabled(True)
        
        import threading
        threading.Thread(target=stop_async, daemon=True).start()
    
    def refresh_nodes(self):
        """刷新节点"""
        self.add_log_message("正在刷新节点...", "INFO")
        
        def refresh_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(accelerator.test_nodes())
            self.add_log_message("节点刷新完成", "SUCCESS")
        
        import threading
        threading.Thread(target=refresh_async, daemon=True).start()
    
    def refresh_github_nodes(self):
        """刷新GitHub节点"""
        self.add_log_message("正在刷新GitHub节点...", "INFO")
        
        def refresh_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(accelerator.refresh_github_nodes())
            self.add_log_message("GitHub节点刷新完成", "SUCCESS")
        
        import threading
        threading.Thread(target=refresh_async, daemon=True).start()
    
    def test_all_nodes(self):
        """测试所有节点"""
        self.add_log_message("正在测试所有节点...", "INFO")
        
        def test_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(accelerator.test_nodes())
            total_tested = sum(len(site_results) for site_results in results.values())
            self.add_log_message(f"节点测试完成，共测试 {total_tested} 个节点", "SUCCESS")
        
        import threading
        threading.Thread(target=test_async, daemon=True).start()
    
    def test_single_node(self, site_key: str, ip: str, domain: str):
        """测试单个节点"""
        self.add_log_message(f"正在测试节点 {ip} ({domain})...", "INFO")
        # 这里可以添加单个节点测试的逻辑
    
    def show_add_node_dialog(self):
        """显示添加节点对话框"""
        if not self.add_node_dialog:
            self.add_node_dialog = AddNodeDialog(self)
            self.add_node_dialog.node_added.connect(self.add_custom_node)
        
        self.add_node_dialog.clear_inputs()
        self.add_node_dialog.show()
    
    def add_custom_node(self, site_key: str, ip: str, domain: str):
        """添加自定义节点"""
        success = accelerator.add_custom_node(site_key, ip, domain)
        if success:
            self.add_log_message(f"已添加自定义节点: {ip} ({domain})", "SUCCESS")
        else:
            self.add_log_message(f"添加自定义节点失败: {ip} ({domain})", "ERROR")
    
    def copy_proxy_config(self):
        """复制代理配置"""
        config_text = f"""HTTP代理: http://127.0.0.1:8080
HTTPS代理: http://127.0.0.1:8443  
DNS服务器: 127.0.0.1:5353

注意: DNS端口为5353，需要在系统网络设置中手动配置。"""
        
        clipboard = QApplication.clipboard()
        clipboard.setText(config_text)
        
        self.add_log_message("代理配置已复制到剪贴板", "SUCCESS")
    
    def show_cert_install_dialog(self):
        """显示证书安装对话框"""
        try:
            from core.cert_manager import CertificateManager
            cert_manager = CertificateManager()
            
            # 确保证书存在
            if not cert_manager.ensure_ca_certificate():
                QMessageBox.warning(self, "错误", "无法生成CA证书")
                return
            
            # 获取安装说明
            instructions = cert_manager.get_cert_install_instructions()
            
            # 显示对话框
            dialog = CertInstallDialog(instructions, self)
            dialog.show()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"显示证书安装对话框失败: {e}")
    
    def clear_logs(self):
        """清空日志"""
        self.log_widget.clear()
    
    def show_settings(self):
        """显示设置"""
        # 这里可以添加设置对话框
        QMessageBox.information(self, "设置", "设置功能开发中...")
    
    def on_accelerator_status_changed(self, status: AcceleratorStatus):
        """加速器状态变化回调"""
        self.update_ui_state()
    
    def update_status(self, status_str: str):
        """更新状态显示"""
        status_map = {
            "running": ("● 运行中", "running"),
            "stopped": ("● 已停止", "stopped"),
            "starting": ("● 启动中", "starting"),
            "stopping": ("● 停止中", "stopping"),
            "error": ("● 错误", "error")
        }
        
        text, status_class = status_map.get(status_str, ("● 未知", "stopped"))
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {get_status_color(status_class)};")
        
        # 更新连接状态
        if status_str == "running":
            self.connection_status.setText("已连接")
        else:
            self.connection_status.setText("未连接")
    
    def update_nodes_display(self, nodes_info: dict):
        """更新节点显示"""
        current_nodes = nodes_info.get("current_nodes", {})
        all_nodes = nodes_info.get("all_nodes", {})
        
        # 更新站点状态卡片
        for site_key, node in current_nodes.items():
            if site_key in self.node_widgets:
                if node and node.is_available:
                    self.node_widgets[site_key].update_status(True, node.latency)
                else:
                    self.node_widgets[site_key].update_status(False)
        
        # 更新节点表格
        self.nodes_table.clear_nodes()
        for site_key, nodes in all_nodes.items():
            from config.settings import SUPPORTED_SITES
            site_name = SUPPORTED_SITES.get(site_key, {}).get("name", site_key)
            
            for node in nodes:
                self.nodes_table.add_node_row(
                    site_name, site_key, node.ip, node.domain,
                    node.latency, node.success_rate, node.is_available
                )
    
    def update_stats_display(self, stats: dict):
        """更新统计显示"""
        # 格式化运行时间
        uptime = stats.get("uptime")
        if uptime:
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            seconds = int(uptime % 60)
            uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            uptime_str = "00:00:00"
        
        # 格式化传输量
        bytes_transferred = stats.get("bytes_transferred", 0)
        if bytes_transferred > 1024 * 1024:
            transferred_str = f"{bytes_transferred / (1024 * 1024):.1f} MB"
        elif bytes_transferred > 1024:
            transferred_str = f"{bytes_transferred / 1024:.1f} KB"
        else:
            transferred_str = f"{bytes_transferred} B"
        
        # 更新指标
        self.metrics_widget.update_metric("uptime", uptime_str)
        self.metrics_widget.update_metric("requests", str(stats.get("requests_count", 0)))
        self.metrics_widget.update_metric("speed", "0 KB/s")  # 需要实现速度计算
        self.metrics_widget.update_metric("transferred", transferred_str)
    
    def add_log_message(self, message: str, level: str = "INFO"):
        """添加日志消息"""
        self.log_widget.add_log(message, level)
    
    def update_ui_state(self):
        """更新UI状态"""
        is_running = accelerator.is_running()
        status = accelerator.get_status()
        
        # 更新按钮状态
        if status == AcceleratorStatus.STARTING:
            self.start_button.setText(f"{get_icon('refresh')} 启动中...")
            self.start_button.setEnabled(False)
        elif status == AcceleratorStatus.STOPPING:
            self.start_button.setText(f"{get_icon('refresh')} 停止中...")
            self.start_button.setEnabled(False)
        elif is_running:
            self.start_button.setText(f"{get_icon('stop')} 停止加速")
            self.start_button.setEnabled(True)
        else:
            self.start_button.setText(f"{get_icon('play')} 启动加速")
            self.start_button.setEnabled(True)
        
        # 更新其他控件状态
        self.refresh_button.setEnabled(is_running)
        
        # 更新托盘图标状态
        if hasattr(self, 'tray_icon'):
            if is_running:
                self.tray_icon.setToolTip(f"{APP_NAME} - 运行中")
            else:
                self.tray_icon.setToolTip(f"{APP_NAME} - 已停止")