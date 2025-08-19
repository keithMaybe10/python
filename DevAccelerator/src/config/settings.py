"""
应用配置文件
"""
import os
import json
from pathlib import Path

# 应用基本信息
APP_NAME = "DevAccelerator"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "开发者网站访问加速器"

# 路径配置
BASE_DIR = Path(__file__).parent.parent.parent
CONFIG_DIR = BASE_DIR / "config"
CACHE_DIR = BASE_DIR / "cache"
CERTS_DIR = BASE_DIR / "certs"
LOGS_DIR = BASE_DIR / "logs"

# 创建必要目录
for dir_path in [CONFIG_DIR, CACHE_DIR, CERTS_DIR, LOGS_DIR]:
    dir_path.mkdir(exist_ok=True)

# 网络配置
DNS_PORT = 53
PROXY_PORT = 8080
HTTPS_PROXY_PORT = 8443

# 支持的站点配置
SUPPORTED_SITES = {
    "github.com": {
        "name": "GitHub",
        "domains": ["github.com", "api.github.com", "raw.githubusercontent.com", 
                   "codeload.github.com", "github.githubassets.com"],
        "test_url": "https://github.com",
        "icon": "github"
    },
    "gitlab.com": {
        "name": "GitLab", 
        "domains": ["gitlab.com", "assets.gitlab-static.net"],
        "test_url": "https://gitlab.com",
        "icon": "gitlab"
    },
    "npmjs.com": {
        "name": "npm",
        "domains": ["registry.npmjs.org", "npmjs.com"],
        "test_url": "https://registry.npmjs.org",
        "icon": "npm"
    },
    "docker.com": {
        "name": "Docker Hub",
        "domains": ["registry-1.docker.io", "index.docker.io", "docker.com"],
        "test_url": "https://index.docker.io",
        "icon": "docker"
    },
    "pypi.org": {
        "name": "PyPI",
        "domains": ["pypi.org", "files.pythonhosted.org"],
        "test_url": "https://pypi.org",
        "icon": "python"
    }
}

# DNS服务器配置
DNS_SERVERS = [
    "8.8.8.8",      # Google DNS
    "1.1.1.1",      # Cloudflare DNS
    "208.67.222.222" # OpenDNS
]

# 代理配置
PROXY_TIMEOUT = 30
MAX_CONCURRENT_REQUESTS = 100
RETRY_ATTEMPTS = 3
RETRY_DELAY = 1

# 监控配置
MONITOR_INTERVAL = 60  # 秒
SPEED_TEST_INTERVAL = 300  # 秒
HEALTH_CHECK_INTERVAL = 30  # 秒

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# 界面配置
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600

# 主题配置
THEME = {
    "primary_color": "#1890ff",
    "success_color": "#52c41a", 
    "warning_color": "#faad14",
    "error_color": "#f5222d",
    "background_color": "#f0f2f5",
    "text_color": "#262626",
    "border_color": "#d9d9d9"
}

class Config:
    """配置管理类"""
    
    def __init__(self):
        self.config_file = CONFIG_DIR / "config.json"
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.user_config = json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                self.user_config = {}
        else:
            self.user_config = {}
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key, default=None):
        """获取配置值"""
        return self.user_config.get(key, default)
    
    def set(self, key, value):
        """设置配置值"""
        self.user_config[key] = value
        self.save_config()

# 全局配置实例
config = Config()