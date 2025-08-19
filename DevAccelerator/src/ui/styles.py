"""
界面样式定义
"""
from config.settings import THEME

# Ant Design风格的样式表
ANT_DESIGN_STYLE = f"""
/* 全局样式 */
QWidget {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    font-size: 14px;
    color: {THEME['text_color']};
}}

/* 主窗口 */
QMainWindow {{
    background-color: {THEME['background_color']};
}}

/* 按钮样式 */
QPushButton {{
    background-color: white;
    border: 1px solid {THEME['border_color']};
    border-radius: 6px;
    padding: 6px 15px;
    font-weight: 400;
    min-height: 22px;
}}

QPushButton:hover {{
    border-color: {THEME['primary_color']};
    color: {THEME['primary_color']};
}}

QPushButton:pressed {{
    background-color: {THEME['primary_color']};
    border-color: {THEME['primary_color']};
    color: white;
}}

QPushButton:disabled {{
    background-color: #f5f5f5;
    border-color: {THEME['border_color']};
    color: rgba(0, 0, 0, 0.25);
}}

/* 主要按钮 */
QPushButton.primary {{
    background-color: {THEME['primary_color']};
    border-color: {THEME['primary_color']};
    color: white;
}}

QPushButton.primary:hover {{
    background-color: #40a9ff;
    border-color: #40a9ff;
}}

QPushButton.primary:pressed {{
    background-color: #096dd9;
    border-color: #096dd9;
}}

/* 危险按钮 */
QPushButton.danger {{
    background-color: {THEME['error_color']};
    border-color: {THEME['error_color']};
    color: white;
}}

QPushButton.danger:hover {{
    background-color: #ff4d4f;
    border-color: #ff4d4f;
}}

/* 成功按钮 */
QPushButton.success {{
    background-color: {THEME['success_color']};
    border-color: {THEME['success_color']};
    color: white;
}}

QPushButton.success:hover {{
    background-color: #73d13d;
    border-color: #73d13d;
}}

/* 卡片样式 */
QFrame.card {{
    background-color: white;
    border: 1px solid #f0f0f0;
    border-radius: 8px;
    padding: 16px;
}}

QFrame.card:hover {{
    border-color: {THEME['border_color']};
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
}}

/* 标签样式 */
QLabel.title {{
    font-size: 20px;
    font-weight: 600;
    color: {THEME['text_color']};
    margin-bottom: 16px;
}}

QLabel.subtitle {{
    font-size: 16px;
    font-weight: 500;
    color: {THEME['text_color']};
    margin-bottom: 12px;
}}

QLabel.description {{
    color: rgba(0, 0, 0, 0.65);
    font-size: 14px;
}}

/* 状态标签 */
QLabel.status-running {{
    background-color: {THEME['success_color']};
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
}}

QLabel.status-stopped {{
    background-color: #d9d9d9;
    color: {THEME['text_color']};
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
}}

QLabel.status-error {{
    background-color: {THEME['error_color']};
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
}}

/* 表格样式 */
QTableWidget {{
    background-color: white;
    border: 1px solid #f0f0f0;
    border-radius: 6px;
    gridline-color: #f0f0f0;
    selection-background-color: #e6f7ff;
}}

QTableWidget::item {{
    padding: 8px;
    border-bottom: 1px solid #f0f0f0;
}}

QTableWidget::item:selected {{
    background-color: #e6f7ff;
    color: {THEME['text_color']};
}}

QHeaderView::section {{
    background-color: #fafafa;
    border: none;
    border-bottom: 1px solid #f0f0f0;
    border-right: 1px solid #f0f0f0;
    padding: 8px;
    font-weight: 500;
}}

/* 输入框样式 */
QLineEdit {{
    background-color: white;
    border: 1px solid {THEME['border_color']};
    border-radius: 6px;
    padding: 6px 11px;
    font-size: 14px;
}}

QLineEdit:focus {{
    border-color: {THEME['primary_color']};
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}}

QLineEdit:disabled {{
    background-color: #f5f5f5;
    color: rgba(0, 0, 0, 0.25);
}}

/* 下拉框样式 */
QComboBox {{
    background-color: white;
    border: 1px solid {THEME['border_color']};
    border-radius: 6px;
    padding: 6px 11px;
    font-size: 14px;
    min-width: 100px;
}}

QComboBox:focus {{
    border-color: {THEME['primary_color']};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #999;
    margin-right: 5px;
}}

QComboBox QAbstractItemView {{
    background-color: white;
    border: 1px solid {THEME['border_color']};
    border-radius: 6px;
    selection-background-color: #e6f7ff;
}}

/* 滚动条样式 */
QScrollBar:vertical {{
    background-color: #f0f0f0;
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background-color: #d9d9d9;
    border-radius: 4px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: #bfbfbf;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* 分割线 */
QFrame.divider {{
    background-color: #f0f0f0;
    max-height: 1px;
    margin: 16px 0;
}}

/* 工具栏 */
QToolBar {{
    background-color: white;
    border: none;
    border-bottom: 1px solid #f0f0f0;
    padding: 8px;
}}

QToolBar QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 8px;
    margin: 2px;
}}

QToolBar QToolButton:hover {{
    background-color: #f5f5f5;
    border-color: {THEME['border_color']};
}}

QToolBar QToolButton:pressed {{
    background-color: #e6f7ff;
    border-color: {THEME['primary_color']};
}}

/* 状态栏 */
QStatusBar {{
    background-color: white;
    border-top: 1px solid #f0f0f0;
    padding: 4px 8px;
}}

/* 菜单样式 */
QMenuBar {{
    background-color: white;
    border-bottom: 1px solid #f0f0f0;
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 8px 16px;
}}

QMenuBar::item:selected {{
    background-color: #e6f7ff;
    border-radius: 4px;
}}

QMenu {{
    background-color: white;
    border: 1px solid {THEME['border_color']};
    border-radius: 6px;
    padding: 4px 0;
}}

QMenu::item {{
    padding: 8px 16px;
    margin: 2px 4px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: #e6f7ff;
}}

/* 进度条样式 */
QProgressBar {{
    background-color: #f0f0f0;
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {THEME['primary_color']};
    border-radius: 4px;
}}

/* 选项卡样式 */
QTabWidget::pane {{
    background-color: white;
    border: 1px solid #f0f0f0;
    border-radius: 6px;
    top: -1px;
}}

QTabBar::tab {{
    background-color: #fafafa;
    border: 1px solid #f0f0f0;
    border-bottom: none;
    padding: 8px 16px;
    margin-right: 2px;
}}

QTabBar::tab:first {{
    border-top-left-radius: 6px;
}}

QTabBar::tab:last {{
    border-top-right-radius: 6px;
    margin-right: 0;
}}

QTabBar::tab:selected {{
    background-color: white;
    border-bottom: 2px solid {THEME['primary_color']};
}}

QTabBar::tab:hover {{
    background-color: #e6f7ff;
}}

/* 复选框样式 */
QCheckBox {{
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {THEME['border_color']};
    border-radius: 4px;
    background-color: white;
}}

QCheckBox::indicator:checked {{
    background-color: {THEME['primary_color']};
    border-color: {THEME['primary_color']};
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xMC42IDEuNEw0LjMgNy43TDEuNCA0LjgiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
}}

QCheckBox::indicator:hover {{
    border-color: {THEME['primary_color']};
}}

/* 单选框样式 */
QRadioButton {{
    spacing: 8px;
}}

QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {THEME['border_color']};
    border-radius: 8px;
    background-color: white;
}}

QRadioButton::indicator:checked {{
    background-color: {THEME['primary_color']};
    border-color: {THEME['primary_color']};
}}

QRadioButton::indicator:checked::after {{
    content: '';
    width: 6px;
    height: 6px;
    border-radius: 3px;
    background-color: white;
    margin: 4px;
}}

/* 文本编辑器样式 */
QTextEdit {{
    background-color: white;
    border: 1px solid {THEME['border_color']};
    border-radius: 6px;
    padding: 8px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 12px;
}}

QTextEdit:focus {{
    border-color: {THEME['primary_color']};
}}

/* 分组框样式 */
QGroupBox {{
    background-color: white;
    border: 1px solid #f0f0f0;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 500;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: white;
    color: {THEME['text_color']};
}}

/* 提示框样式 */
QToolTip {{
    background-color: rgba(0, 0, 0, 0.85);
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 12px;
}}
"""

# 图标样式（使用Unicode符号）
ICONS = {
    "play": "▶",
    "stop": "⏹",
    "refresh": "🔄",
    "settings": "⚙",
    "info": "ℹ",
    "warning": "⚠",
    "error": "❌",
    "success": "✅",
    "github": "🐱",
    "gitlab": "🦊",
    "npm": "📦",
    "docker": "🐳",
    "python": "🐍",
    "network": "🌐",
    "speed": "⚡",
    "time": "⏰",
    "chart": "📊",
    "log": "📝",
    "folder": "📁",
    "file": "📄",
    "download": "⬇",
    "upload": "⬆",
    "link": "🔗",
    "shield": "🛡",
    "key": "🔑",
    "eye": "👁",
    "eye_off": "🙈",
    "add": "➕",
    "remove": "➖",
    "edit": "✏",
    "save": "💾",
    "copy": "📋",
    "paste": "📄"
}

def get_icon(name: str) -> str:
    """获取图标"""
    return ICONS.get(name, "")

def get_status_color(status: str) -> str:
    """获取状态颜色"""
    status_colors = {
        "running": THEME["success_color"],
        "stopped": "#d9d9d9", 
        "error": THEME["error_color"],
        "warning": THEME["warning_color"],
        "starting": THEME["primary_color"],
        "stopping": THEME["warning_color"]
    }
    return status_colors.get(status.lower(), THEME["text_color"])