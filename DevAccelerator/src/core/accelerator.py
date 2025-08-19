"""
加速器核心模块
"""
import asyncio
import time
from typing import Dict, Optional, Callable

from core.status import AcceleratorStatus
from config.settings import config
from utils.logger import setup_logger

logger = setup_logger("accelerator")

# 条件导入核心模块
try:
    from core.cert_manager import CertificateManager
    from core.dns_server import DNSServerManager
    from core.proxy_server import ProxyServerManager
    from core.node_manager import NodeManager
    CORE_MODULES_AVAILABLE = True
except ImportError as e:
    CORE_MODULES_AVAILABLE = False
    logger.warning(f"核心模块不完全可用: {e}")

class DevAccelerator:
    """开发者加速器核心类"""
    
    def __init__(self):
        self.status = AcceleratorStatus.STOPPED
        self.status_callbacks: list[Callable] = []
        
        # 初始化组件
        self.cert_manager = CertificateManager()
        self.dns_server = DNSServerManager()
        self.proxy_server = ProxyServerManager(self.cert_manager)
        self.node_manager = NodeManager()
        
        # 统计信息
        self.start_time: Optional[float] = None
        self.stats = {
            "requests_count": 0,
            "bytes_transferred": 0,
            "active_connections": 0,
            "errors_count": 0
        }
        
        # 加载配置
        self.load_config()
    
    def add_status_callback(self, callback: Callable):
        """添加状态变化回调"""
        self.status_callbacks.append(callback)
    
    def remove_status_callback(self, callback: Callable):
        """移除状态变化回调"""
        if callback in self.status_callbacks:
            self.status_callbacks.remove(callback)
    
    def _notify_status_change(self):
        """通知状态变化"""
        for callback in self.status_callbacks:
            try:
                callback(self.status)
            except Exception as e:
                logger.error(f"状态回调执行失败: {e}")
    
    def _set_status(self, status: AcceleratorStatus):
        """设置状态"""
        if self.status != status:
            old_status = self.status
            self.status = status
            logger.info(f"加速器状态变化: {old_status.value} -> {status.value}")
            self._notify_status_change()
    
    async def start(self) -> bool:
        """启动加速器"""
        try:
            if self.status == AcceleratorStatus.RUNNING:
                logger.warning("加速器已在运行")
                return True
            
            self._set_status(AcceleratorStatus.STARTING)
            logger.info("正在启动开发者加速器...")
            
            # 1. 确保CA证书存在
            if not self.cert_manager.ensure_ca_certificate():
                logger.error("CA证书初始化失败")
                self._set_status(AcceleratorStatus.ERROR)
                return False
            
            # 2. 尝试安装CA证书
            if not self.cert_manager.install_ca_certificate():
                logger.warning("CA证书安装失败，请手动安装")
            
            # 3. 加载节点配置
            self.node_manager.load_nodes_config()
            
            # 4. 启动节点扫描
            await self.node_manager.scan_github_ips()
            
            # 5. 启动DNS服务器
            if not self.dns_server.start():
                logger.error("DNS服务器启动失败")
                self._set_status(AcceleratorStatus.ERROR)
                return False
            
            # 6. 启动代理服务器
            if not await self.proxy_server.start():
                logger.error("代理服务器启动失败")
                self.dns_server.stop()
                self._set_status(AcceleratorStatus.ERROR)
                return False
            
            # 7. 更新DNS和代理映射
            self._update_domain_mappings()
            
            # 8. 启动自动扫描
            self.node_manager.start_auto_scan()
            
            self.start_time = time.time()
            self._set_status(AcceleratorStatus.RUNNING)
            
            logger.info("开发者加速器启动成功！")
            return True
            
        except Exception as e:
            logger.error(f"启动加速器失败: {e}")
            self._set_status(AcceleratorStatus.ERROR)
            await self.stop()
            return False
    
    async def stop(self):
        """停止加速器"""
        try:
            if self.status == AcceleratorStatus.STOPPED:
                logger.warning("加速器已停止")
                return
            
            self._set_status(AcceleratorStatus.STOPPING)
            logger.info("正在停止开发者加速器...")
            
            # 停止自动扫描
            self.node_manager.stop_auto_scan()
            
            # 停止代理服务器
            await self.proxy_server.stop()
            
            # 停止DNS服务器
            self.dns_server.stop()
            
            # 保存配置
            self.save_config()
            
            self.start_time = None
            self._set_status(AcceleratorStatus.STOPPED)
            
            logger.info("开发者加速器已停止")
            
        except Exception as e:
            logger.error(f"停止加速器失败: {e}")
            self._set_status(AcceleratorStatus.ERROR)
    
    def _update_domain_mappings(self):
        """更新域名映射"""
        current_nodes = self.node_manager.get_current_nodes()
        
        for site_key, node in current_nodes.items():
            if node and node.is_available:
                for domain in node.site_manager.site_config["domains"]:
                    # 更新DNS映射
                    self.dns_server.update_domain_ip(domain, node.ip)
                    
                    # 更新代理映射
                    self.proxy_server.update_domain_ip(domain, node.ip)
                    
                    logger.debug(f"更新域名映射: {domain} -> {node.ip}")
    
    def get_status(self) -> AcceleratorStatus:
        """获取状态"""
        return self.status
    
    def is_running(self) -> bool:
        """检查是否在运行"""
        return self.status == AcceleratorStatus.RUNNING
    
    def get_uptime(self) -> Optional[float]:
        """获取运行时间（秒）"""
        if self.start_time:
            return time.time() - self.start_time
        return None
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = self.stats.copy()
        stats["uptime"] = self.get_uptime()
        stats["status"] = self.status.value
        return stats
    
    def get_nodes_info(self) -> Dict:
        """获取节点信息"""
        return {
            "current_nodes": self.node_manager.get_current_nodes(),
            "all_nodes": self.node_manager.get_all_nodes()
        }
    
    async def test_nodes(self) -> Dict:
        """测试节点"""
        logger.info("开始测试所有节点...")
        results = await self.node_manager.test_all_nodes()
        
        # 更新域名映射
        self._update_domain_mappings()
        
        logger.info("节点测试完成")
        return results
    
    async def refresh_github_nodes(self):
        """刷新GitHub节点"""
        logger.info("开始刷新GitHub节点...")
        await self.node_manager.scan_github_ips()
        
        # 更新域名映射
        self._update_domain_mappings()
        
        logger.info("GitHub节点刷新完成")
    
    def add_custom_node(self, site_key: str, ip: str, domain: str) -> bool:
        """添加自定义节点"""
        success = self.node_manager.add_node(site_key, ip, domain)
        if success:
            self._update_domain_mappings()
            self.save_config()
        return success
    
    def remove_custom_node(self, site_key: str, ip: str, domain: str) -> bool:
        """移除自定义节点"""
        success = self.node_manager.remove_node(site_key, ip, domain)
        if success:
            self._update_domain_mappings()
            self.save_config()
        return success
    
    def get_system_proxy_config(self) -> Dict[str, str]:
        """获取系统代理配置信息"""
        return {
            "http_proxy": f"http://127.0.0.1:{self.proxy_server.http_runner._sites[0]._port if self.proxy_server.http_runner else 'N/A'}",
            "https_proxy": f"http://127.0.0.1:{self.proxy_server.https_server.port}",
            "dns_server": "127.0.0.1"
        }
    
    def save_config(self):
        """保存配置"""
        try:
            # 保存节点配置
            self.node_manager.save_nodes_config()
            
            # 保存其他配置
            app_config = {
                "auto_start": config.get("auto_start", False),
                "minimize_to_tray": config.get("minimize_to_tray", True),
                "check_updates": config.get("check_updates", True)
            }
            
            for key, value in app_config.items():
                config.set(key, value)
            
            logger.info("配置已保存")
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def load_config(self):
        """加载配置"""
        try:
            # 加载节点配置在node_manager中处理
            
            # 加载其他配置
            self.auto_start = config.get("auto_start", False)
            self.minimize_to_tray = config.get("minimize_to_tray", True)
            self.check_updates = config.get("check_updates", True)
            
            logger.info("配置已加载")
            
        except Exception as e:
            logger.error(f"加载配置失败: {e}")

# 全局加速器实例
accelerator = DevAccelerator()