"""
自定义UI组件
"""
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QTextEdit, QScrollArea, QGridLayout,
    QGroupBox, QComboBox, QLineEdit, QCheckBox, QSpacerItem,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QRect
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor
from typing import Dict, List, Optional, Any
import time

from ui.styles import get_icon, get_status_color, THEME

class StatusCard(QFrame):
    """状态卡片组件"""
    
    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setProperty("class", "card")
        
        self.title = title
        self.icon = icon
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # 标题行
        title_layout = QHBoxLayout()
        
        if self.icon:
            icon_label = QLabel(get_icon(self.icon))
            icon_label.setFont(QFont("", 16))
            title_layout.addWidget(icon_label)
        
        title_label = QLabel(self.title)
        title_label.setProperty("class", "subtitle")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 内容区域
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.content_widget)
    
    def add_content(self, widget: QWidget):
        """添加内容"""
        self.content_layout.addWidget(widget)
    
    def clear_content(self):
        """清空内容"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

class NodeStatusWidget(QWidget):
    """节点状态组件"""
    
    def __init__(self, site_name: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.site_name = site_name
        self.icon = icon
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # 站点信息
        site_layout = QHBoxLayout()
        
        if self.icon:
            icon_label = QLabel(get_icon(self.icon))
            icon_label.setFont(QFont("", 20))
            site_layout.addWidget(icon_label)
        
        site_label = QLabel(self.site_name)
        site_label.setFont(QFont("", 14, QFont.Weight.Bold))
        site_layout.addWidget(site_label)
        
        site_layout.addStretch()
        layout.addLayout(site_layout)
        
        # 状态信息
        self.status_label = QLabel("● 未连接")
        self.status_label.setProperty("class", "status-stopped")
        layout.addWidget(self.status_label)
        
        # 延迟信息
        self.latency_label = QLabel("延迟: --")
        self.latency_label.setProperty("class", "description")
        layout.addWidget(self.latency_label)
        
        # 设置固定大小和样式
        self.setFixedSize(160, 120)
        self.setStyleSheet("""
            QWidget {
                border: 1px solid #f0f0f0;
                border-radius: 8px;
                background-color: white;
            }
        """)
        self.setProperty("class", "card")
    
    def update_status(self, is_connected: bool, latency: Optional[float] = None):
        """更新状态"""
        if is_connected:
            self.status_label.setText("● 已连接")
            self.status_label.setStyleSheet(f"color: {get_status_color('running')};")
        else:
            self.status_label.setText("● 未连接")
            self.status_label.setStyleSheet(f"color: {get_status_color('stopped')};")
        
        if latency is not None:
            self.latency_label.setText(f"延迟: {latency:.0f}ms")
        else:
            self.latency_label.setText("延迟: --")

class LogWidget(QTextEdit):
    """日志显示组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(1000)  # 限制最大行数
        
        # 设置字体
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
    
    def add_log(self, message: str, level: str = "INFO"):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        
        # 根据级别设置颜色
        color_map = {
            "DEBUG": "#8c8c8c",
            "INFO": "#262626", 
            "WARNING": THEME["warning_color"],
            "ERROR": THEME["error_color"],
            "SUCCESS": THEME["success_color"]
        }
        
        color = color_map.get(level, "#262626")
        
        # 格式化日志
        formatted_message = f'<span style="color: {color};">[{timestamp}] {message}</span>'
        
        # 添加到文本框
        self.append(formatted_message)
        
        # 滚动到底部
        self.moveCursor(self.textCursor().End)

class MetricsWidget(QWidget):
    """指标显示组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QGridLayout(self)
        layout.setSpacing(16)
        
        # 创建指标项
        self.metrics = {}
        metrics_config = [
            ("uptime", "运行时间", "time", "00:00:00"),
            ("requests", "请求数", "network", "0"),
            ("speed", "当前速度", "speed", "0 KB/s"),
            ("transferred", "传输量", "download", "0 MB")
        ]
        
        for i, (key, title, icon, default_value) in enumerate(metrics_config):
            metric_widget = self.create_metric_item(title, icon, default_value)
            self.metrics[key] = metric_widget
            
            row = i // 2
            col = i % 2
            layout.addWidget(metric_widget, row, col)
    
    def create_metric_item(self, title: str, icon: str, value: str) -> QWidget:
        """创建指标项"""
        widget = QFrame()
        widget.setProperty("class", "card")
        
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        
        # 图标和标题
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(get_icon(icon))
        icon_label.setFont(QFont("", 16))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setProperty("class", "description")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 数值
        value_label = QLabel(value)
        value_label.setFont(QFont("", 18, QFont.Weight.Bold))
        value_label.setProperty("class", "metric-value")
        layout.addWidget(value_label)
        
        # 存储值标签引用
        widget.value_label = value_label
        
        return widget
    
    def update_metric(self, key: str, value: str):
        """更新指标"""
        if key in self.metrics:
            self.metrics[key].value_label.setText(value)

class NodeTableWidget(QTableWidget):
    """节点表格组件"""
    
    node_selected = Signal(str, str, str)  # site_key, ip, domain
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        # 设置列
        headers = ["站点", "IP地址", "域名", "延迟", "成功率", "状态", "操作"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # 设置表格属性
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        
        # 调整列宽
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 站点
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # IP
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # 域名
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 延迟
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 成功率
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # 状态
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # 操作
    
    def add_node_row(self, site_name: str, site_key: str, ip: str, domain: str, 
                     latency: Optional[float], success_rate: float, is_available: bool):
        """添加节点行"""
        row = self.rowCount()
        self.insertRow(row)
        
        # 站点
        site_item = QTableWidgetItem(site_name)
        site_item.setData(Qt.ItemDataRole.UserRole, site_key)
        self.setItem(row, 0, site_item)
        
        # IP地址
        self.setItem(row, 1, QTableWidgetItem(ip))
        
        # 域名
        self.setItem(row, 2, QTableWidgetItem(domain))
        
        # 延迟
        latency_text = f"{latency:.0f}ms" if latency is not None else "--"
        self.setItem(row, 3, QTableWidgetItem(latency_text))
        
        # 成功率
        success_rate_text = f"{success_rate:.1%}"
        self.setItem(row, 4, QTableWidgetItem(success_rate_text))
        
        # 状态
        status_text = "可用" if is_available else "不可用"
        status_item = QTableWidgetItem(status_text)
        if is_available:
            status_item.setForeground(QColor(get_status_color("running")))
        else:
            status_item.setForeground(QColor(get_status_color("stopped")))
        self.setItem(row, 5, status_item)
        
        # 操作按钮
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(4, 4, 4, 4)
        
        test_btn = QPushButton("测试")
        test_btn.clicked.connect(lambda: self.test_node(site_key, ip, domain))
        action_layout.addWidget(test_btn)
        
        remove_btn = QPushButton("删除")
        remove_btn.setProperty("class", "danger")
        remove_btn.clicked.connect(lambda: self.remove_node(site_key, ip, domain))
        action_layout.addWidget(remove_btn)
        
        self.setCellWidget(row, 6, action_widget)
    
    def test_node(self, site_key: str, ip: str, domain: str):
        """测试节点"""
        self.node_selected.emit(site_key, ip, domain)
    
    def remove_node(self, site_key: str, ip: str, domain: str):
        """删除节点"""
        # 找到对应行并删除
        for row in range(self.rowCount()):
            if (self.item(row, 1).text() == ip and 
                self.item(row, 2).text() == domain and
                self.item(row, 0).data(Qt.ItemDataRole.UserRole) == site_key):
                self.removeRow(row)
                break
    
    def clear_nodes(self):
        """清空节点"""
        self.setRowCount(0)
    
    def update_node_status(self, site_key: str, ip: str, domain: str, 
                          latency: Optional[float], success_rate: float, is_available: bool):
        """更新节点状态"""
        for row in range(self.rowCount()):
            if (self.item(row, 1).text() == ip and 
                self.item(row, 2).text() == domain and
                self.item(row, 0).data(Qt.ItemDataRole.UserRole) == site_key):
                
                # 更新延迟
                latency_text = f"{latency:.0f}ms" if latency is not None else "--"
                self.item(row, 3).setText(latency_text)
                
                # 更新成功率
                success_rate_text = f"{success_rate:.1%}"
                self.item(row, 4).setText(success_rate_text)
                
                # 更新状态
                status_text = "可用" if is_available else "不可用"
                status_item = self.item(row, 5)
                status_item.setText(status_text)
                if is_available:
                    status_item.setForeground(QColor(get_status_color("running")))
                else:
                    status_item.setForeground(QColor(get_status_color("stopped")))
                
                break

class AddNodeDialog(QWidget):
    """添加节点对话框"""
    
    node_added = Signal(str, str, str)  # site_key, ip, domain
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加自定义节点")
        self.setFixedSize(400, 200)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # 站点选择
        site_layout = QHBoxLayout()
        site_layout.addWidget(QLabel("站点:"))
        
        self.site_combo = QComboBox()
        from config.settings import SUPPORTED_SITES
        for site_key, site_config in SUPPORTED_SITES.items():
            self.site_combo.addItem(site_config["name"], site_key)
        site_layout.addWidget(self.site_combo)
        
        layout.addLayout(site_layout)
        
        # IP地址输入
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("IP地址:"))
        
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("例如: 140.82.112.3")
        ip_layout.addWidget(self.ip_input)
        
        layout.addLayout(ip_layout)
        
        # 域名输入
        domain_layout = QHBoxLayout()
        domain_layout.addWidget(QLabel("域名:"))
        
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("例如: github.com")
        domain_layout.addWidget(self.domain_input)
        
        layout.addLayout(domain_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(cancel_btn)
        
        add_btn = QPushButton("添加")
        add_btn.setProperty("class", "primary")
        add_btn.clicked.connect(self.add_node)
        button_layout.addWidget(add_btn)
        
        layout.addLayout(button_layout)
    
    def add_node(self):
        """添加节点"""
        site_key = self.site_combo.currentData()
        ip = self.ip_input.text().strip()
        domain = self.domain_input.text().strip()
        
        if not ip or not domain:
            return
        
        self.node_added.emit(site_key, ip, domain)
        self.close()
    
    def clear_inputs(self):
        """清空输入"""
        self.ip_input.clear()
        self.domain_input.clear()

class LoadingWidget(QWidget):
    """加载指示器组件"""
    
    def __init__(self, text: str = "加载中...", parent=None):
        super().__init__(parent)
        self.text = text
        self.angle = 0
        self.setup_ui()
        
        # 创建动画定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 加载图标
        self.loading_label = QLabel("⟳")
        self.loading_label.setFont(QFont("", 24))
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.loading_label)
        
        # 加载文本
        text_label = QLabel(self.text)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setProperty("class", "description")
        layout.addWidget(text_label)
    
    def start_animation(self):
        """开始动画"""
        self.timer.start(100)  # 100ms间隔
    
    def stop_animation(self):
        """停止动画"""
        self.timer.stop()
    
    def update_animation(self):
        """更新动画"""
        self.angle = (self.angle + 30) % 360
        # 这里可以添加旋转效果，但PySide6的QLabel不直接支持旋转
        # 简单地切换不同的旋转符号
        rotation_chars = ["⟳", "⟲", "⟳", "⟲"]
        char_index = (self.angle // 90) % len(rotation_chars)
        self.loading_label.setText(rotation_chars[char_index])

class CertInstallDialog(QWidget):
    """证书安装指导对话框"""
    
    def __init__(self, instructions: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("证书安装指导")
        self.setFixedSize(600, 400)
        self.instructions = instructions
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # 标题
        title_label = QLabel("🔐 CA证书安装指导")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        # 说明
        desc_label = QLabel("为了获得最佳的HTTPS代理体验，请按照以下步骤安装CA证书：")
        desc_label.setProperty("class", "description")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 证书路径
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("证书文件:"))
        
        self.path_label = QLabel(self.instructions["cert_path"])
        self.path_label.setStyleSheet("background-color: #f5f5f5; padding: 4px; border-radius: 4px;")
        path_layout.addWidget(self.path_label)
        
        copy_path_btn = QPushButton("📋 复制路径")
        copy_path_btn.clicked.connect(self.copy_cert_path)
        path_layout.addWidget(copy_path_btn)
        
        layout.addLayout(path_layout)
        
        # 安装步骤
        steps_label = QLabel("安装步骤:")
        steps_label.setProperty("class", "subtitle")
        layout.addWidget(steps_label)
        
        # 步骤列表
        steps_text = QTextEdit()
        steps_text.setReadOnly(True)
        steps_text.setMaximumHeight(200)
        
        steps_content = "\n".join(self.instructions["instructions"])
        steps_text.setPlainText(steps_content)
        layout.addWidget(steps_text)
        
        # 提示信息
        tip_label = QLabel("💡 提示: 安装证书后，重启浏览器以确保生效。如果不安装证书，HTTPS网站可能显示安全警告。")
        tip_label.setProperty("class", "description")
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet("background-color: #e6f7ff; padding: 8px; border-radius: 4px; border-left: 3px solid #1890ff;")
        layout.addWidget(tip_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        open_folder_btn = QPushButton("📁 打开证书文件夹")
        open_folder_btn.clicked.connect(self.open_cert_folder)
        button_layout.addWidget(open_folder_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.setProperty("class", "primary")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def copy_cert_path(self):
        """复制证书路径"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.instructions["cert_path"])
    
    def open_cert_folder(self):
        """打开证书文件夹"""
        import subprocess
        import platform
        from pathlib import Path
        
        cert_folder = Path(self.instructions["cert_path"]).parent
        system = platform.system().lower()
        
        try:
            if system == "windows":
                subprocess.run(f'explorer "{cert_folder}"', shell=True)
            elif system == "darwin":
                subprocess.run(f'open "{cert_folder}"', shell=True)
            elif system == "linux":
                subprocess.run(f'xdg-open "{cert_folder}"', shell=True)
        except Exception as e:
            print(f"无法打开文件夹: {e}")

class SettingsDialog(QWidget):
    """设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(420, 280)
        self.setup_ui()
        self.load_values()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # 标题
        title_label = QLabel(f"{get_icon('settings')} 应用设置")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        # 基础设置区域
        basic_group = QFrame()
        basic_group.setProperty("class", "card")
        basic_layout = QVBoxLayout(basic_group)
        basic_layout.setSpacing(12)
        
        self.auto_start_cb = QCheckBox("开机自启")
        self.minimize_to_tray_cb = QCheckBox("关闭时最小化到托盘")
        self.check_updates_cb = QCheckBox("启动时检查更新")
        
        basic_layout.addWidget(self.auto_start_cb)
        basic_layout.addWidget(self.minimize_to_tray_cb)
        basic_layout.addWidget(self.check_updates_cb)
        layout.addWidget(basic_group)
        
        # 语言与主题（占位）
        appearance_group = QFrame()
        appearance_group.setProperty("class", "card")
        appearance_layout = QVBoxLayout(appearance_group)
        appearance_layout.setSpacing(12)
        
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("语言:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["简体中文", "English"])
        self.lang_combo.setCurrentIndex(0)
        lang_row.addWidget(self.lang_combo)
        lang_row.addStretch()
        appearance_layout.addLayout(lang_row)
        
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("主题:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["默认(浅色)"])
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch()
        appearance_layout.addLayout(theme_row)
        
        layout.addWidget(appearance_group)
        
        # 按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.close)
        save_btn = QPushButton("保存")
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self.save_values)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)
    
    def load_values(self):
        """加载配置值"""
        from config.settings import config
        self.auto_start_cb.setChecked(bool(config.get("auto_start", False)))
        self.minimize_to_tray_cb.setChecked(bool(config.get("minimize_to_tray", True)))
        self.check_updates_cb.setChecked(bool(config.get("check_updates", True)))
    
    def save_values(self):
        """保存配置值"""
        from config.settings import config
        config.set("auto_start", self.auto_start_cb.isChecked())
        config.set("minimize_to_tray", self.minimize_to_tray_cb.isChecked())
        config.set("check_updates", self.check_updates_cb.isChecked())
        self.close()