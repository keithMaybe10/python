"""
节点管理模块
"""
import asyncio
import time
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import asdict
from threading import Lock

from config.settings import SUPPORTED_SITES, config
from utils.logger import setup_logger
from core.node_info import NodeInfo

logger = setup_logger("node_manager")

# 条件导入网络相关模块
try:
    from utils.network import NetworkUtils, IPScanner, GitHubIPFetcher
    NETWORK_AVAILABLE = True
except ImportError:
    NETWORK_AVAILABLE = False
    logger.warning("网络模块不可用，某些功能将受限")

class SiteNodeManager:
    """单个站点的节点管理器"""
    
    def __init__(self, site_key: str, site_config: Dict):
        self.site_key = site_key
        self.site_config = site_config
        self.nodes: Dict[str, NodeInfo] = {}
        self.current_node: Optional[NodeInfo] = None
        self.lock = Lock()
        self.scanner = IPScanner()
    
    def add_node(self, ip: str, domain: str) -> NodeInfo:
        """添加节点"""
        with self.lock:
            node_key = f"{ip}:{domain}"
            if node_key not in self.nodes:
                node = NodeInfo(
                    ip=ip,
                    domain=domain,
                    site_name=self.site_config["name"]
                )
                self.nodes[node_key] = node
                logger.info(f"添加节点: {self.site_config['name']} - {ip} ({domain})")
                return node
            return self.nodes[node_key]
    
    def remove_node(self, ip: str, domain: str):
        """移除节点"""
        with self.lock:
            node_key = f"{ip}:{domain}"
            if node_key in self.nodes:
                del self.nodes[node_key]
                logger.info(f"移除节点: {self.site_config['name']} - {ip} ({domain})")
                
                # 如果移除的是当前节点，需要重新选择
                if self.current_node and self.current_node.ip == ip and self.current_node.domain == domain:
                    self.current_node = None
                    self.select_best_node()
    
    def get_nodes(self) -> List[NodeInfo]:
        """获取所有节点"""
        with self.lock:
            return list(self.nodes.values())
    
    def get_available_nodes(self) -> List[NodeInfo]:
        """获取可用节点"""
        with self.lock:
            return [node for node in self.nodes.values() if node.is_available]
    
    def select_best_node(self) -> Optional[NodeInfo]:
        """选择最佳节点"""
        with self.lock:
            available_nodes = self.get_available_nodes()
            
            if not available_nodes:
                logger.warning(f"站点 {self.site_config['name']} 没有可用节点")
                self.current_node = None
                return None
            
            # 按评分排序，选择最佳节点
            best_node = min(available_nodes, key=lambda n: n.get_score())
            
            if self.current_node != best_node:
                old_node = self.current_node.ip if self.current_node else "None"
                self.current_node = best_node
                logger.info(f"站点 {self.site_config['name']} 切换节点: {old_node} -> {best_node.ip}")
            
            return self.current_node
    
    def get_current_node(self) -> Optional[NodeInfo]:
        """获取当前节点"""
        with self.lock:
            return self.current_node
    
    async def test_nodes(self) -> Dict[str, bool]:
        """测试所有节点"""
        nodes_to_test = self.get_nodes()
        if not nodes_to_test:
            return {}
        
        results = {}
        
        # 并行测试所有节点
        tasks = []
        for node in nodes_to_test:
            task = asyncio.create_task(self._test_single_node(node))
            tasks.append((node, task))
        
        # 等待所有测试完成
        for node, task in tasks:
            try:
                success, latency = await task
                node.update_test_result(success, latency)
                results[f"{node.ip}:{node.domain}"] = success
                
                logger.debug(f"节点测试: {self.site_config['name']} - {node.ip} "
                           f"成功={success}, 延迟={latency}, 成功率={node.success_rate:.2f}")
                
            except Exception as e:
                logger.error(f"测试节点 {node.ip} 时出错: {e}")
                node.update_test_result(False)
                results[f"{node.ip}:{node.domain}"] = False
        
        # 重新选择最佳节点
        self.select_best_node()
        
        return results
    
    async def _test_single_node(self, node: NodeInfo) -> Tuple[bool, Optional[float]]:
        """测试单个节点"""
        try:
            # 构造测试URL
            test_url = self.site_config.get("test_url", f"https://{node.domain}")
            
            # 如果有IP映射，需要特殊处理
            if node.ip != node.domain:
                # 使用IP访问，但设置Host头
                import aiohttp
                
                timeout = aiohttp.ClientTimeout(total=10)
                headers = {"Host": node.domain}
                
                # 构造IP URL
                from urllib.parse import urlparse
                parsed = urlparse(test_url)
                ip_url = f"{parsed.scheme}://{node.ip}{parsed.path}"
                if parsed.port:
                    ip_url = f"{parsed.scheme}://{node.ip}:{parsed.port}{parsed.path}"
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    start_time = time.time()
                    async with session.get(ip_url, headers=headers, ssl=False) as response:
                        latency = (time.time() - start_time) * 1000
                        success = response.status == 200
                        return success, latency
            else:
                # 直接测试延迟
                latency = NetworkUtils.test_ip_latency(node.ip, 443, 5)
                success = latency is not None
                return success, latency
                
        except Exception as e:
            logger.debug(f"测试节点 {node.ip} 失败: {e}")
            return False, None

class NodeManager:
    """节点管理器"""
    
    def __init__(self):
        self.site_managers: Dict[str, SiteNodeManager] = {}
        self.initialize_site_managers()
        self.auto_scan_enabled = True
        self.scan_task: Optional[asyncio.Task] = None
    
    def initialize_site_managers(self):
        """初始化站点管理器"""
        for site_key, site_config in SUPPORTED_SITES.items():
            self.site_managers[site_key] = SiteNodeManager(site_key, site_config)
    
    def get_site_manager(self, site_key: str) -> Optional[SiteNodeManager]:
        """获取站点管理器"""
        return self.site_managers.get(site_key)
    
    def add_node(self, site_key: str, ip: str, domain: str) -> bool:
        """添加节点"""
        site_manager = self.get_site_manager(site_key)
        if site_manager:
            site_manager.add_node(ip, domain)
            return True
        return False
    
    def remove_node(self, site_key: str, ip: str, domain: str) -> bool:
        """移除节点"""
        site_manager = self.get_site_manager(site_key)
        if site_manager:
            site_manager.remove_node(ip, domain)
            return True
        return False
    
    def get_current_nodes(self) -> Dict[str, Optional[NodeInfo]]:
        """获取所有站点的当前节点"""
        result = {}
        for site_key, site_manager in self.site_managers.items():
            result[site_key] = site_manager.get_current_node()
        return result
    
    def get_all_nodes(self) -> Dict[str, List[NodeInfo]]:
        """获取所有节点"""
        result = {}
        for site_key, site_manager in self.site_managers.items():
            result[site_key] = site_manager.get_nodes()
        return result
    
    async def scan_github_ips(self):
        """扫描GitHub IP"""
        try:
            logger.info("开始扫描GitHub IP...")
            
            # 获取GitHub官方IP列表
            github_ips = GitHubIPFetcher.fetch_github_ips()
            if not github_ips:
                github_ips = GitHubIPFetcher.get_fallback_ips()
            
            logger.info(f"获取到 {len(github_ips)} 个GitHub IP")
            
            # 测试IP延迟
            scanner = IPScanner(max_workers=20)
            ip_results = scanner.scan_ips_parallel(github_ips, 443, 5)
            
            # 添加可用的IP到GitHub节点管理器
            github_manager = self.get_site_manager("github.com")
            if github_manager:
                # 清除旧节点
                old_nodes = github_manager.get_nodes()
                for node in old_nodes:
                    github_manager.remove_node(node.ip, node.domain)
                
                # 添加新节点（取前10个最快的）
                sorted_ips = sorted(ip_results.items(), key=lambda x: x[1])[:10]
                for ip, latency in sorted_ips:
                    for domain in SUPPORTED_SITES["github.com"]["domains"]:
                        github_manager.add_node(ip, domain)
                
                logger.info(f"添加了 {len(sorted_ips)} 个GitHub节点")
            
        except Exception as e:
            logger.error(f"扫描GitHub IP失败: {e}")
    
    async def test_all_nodes(self) -> Dict[str, Dict[str, bool]]:
        """测试所有节点"""
        results = {}
        
        tasks = []
        for site_key, site_manager in self.site_managers.items():
            task = asyncio.create_task(site_manager.test_nodes())
            tasks.append((site_key, task))
        
        for site_key, task in tasks:
            try:
                site_results = await task
                results[site_key] = site_results
            except Exception as e:
                logger.error(f"测试站点 {site_key} 节点失败: {e}")
                results[site_key] = {}
        
        return results
    
    def start_auto_scan(self):
        """启动自动扫描"""
        if self.scan_task and not self.scan_task.done():
            return
        
        self.auto_scan_enabled = True
        self.scan_task = asyncio.create_task(self._auto_scan_loop())
        logger.info("自动扫描已启动")
    
    def stop_auto_scan(self):
        """停止自动扫描"""
        self.auto_scan_enabled = False
        if self.scan_task and not self.scan_task.done():
            self.scan_task.cancel()
        logger.info("自动扫描已停止")
    
    async def _auto_scan_loop(self):
        """自动扫描循环"""
        while self.auto_scan_enabled:
            try:
                # 扫描GitHub IP
                await self.scan_github_ips()
                
                # 等待5分钟
                await asyncio.sleep(300)
                
                # 测试所有节点
                await self.test_all_nodes()
                
                # 等待5分钟
                await asyncio.sleep(300)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"自动扫描出错: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再继续
    
    def save_nodes_config(self):
        """保存节点配置"""
        try:
            nodes_data = {}
            for site_key, site_manager in self.site_managers.items():
                nodes_data[site_key] = []
                for node in site_manager.get_nodes():
                    nodes_data[site_key].append(asdict(node))
            
            config.set("nodes", nodes_data)
            logger.info("节点配置已保存")
            
        except Exception as e:
            logger.error(f"保存节点配置失败: {e}")
    
    def load_nodes_config(self):
        """加载节点配置"""
        try:
            nodes_data = config.get("nodes", {})
            
            for site_key, nodes_list in nodes_data.items():
                site_manager = self.get_site_manager(site_key)
                if site_manager:
                    for node_data in nodes_list:
                        node = NodeInfo(**node_data)
                        site_manager.nodes[f"{node.ip}:{node.domain}"] = node
            
            logger.info("节点配置已加载")
            
        except Exception as e:
            logger.error(f"加载节点配置失败: {e}")