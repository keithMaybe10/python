"""
网络工具模块
"""
import socket
import time
import asyncio
import aiohttp
import requests
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import platform

from utils.logger import setup_logger

logger = setup_logger("network")

class NetworkUtils:
    """网络工具类"""
    
    @staticmethod
    def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
        """检查端口是否可用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                return result != 0
        except Exception:
            return False
    
    @staticmethod
    def get_available_port(start_port: int = 8000, end_port: int = 9000) -> int:
        """获取可用端口"""
        for port in range(start_port, end_port):
            if NetworkUtils.is_port_available(port):
                return port
        raise RuntimeError("没有可用端口")
    
    @staticmethod
    def resolve_domain(domain: str, dns_server: str = "8.8.8.8") -> List[str]:
        """解析域名获取IP地址"""
        try:
            # 使用系统DNS解析
            result = socket.getaddrinfo(domain, None, socket.AF_INET)
            ips = list(set([ip[4][0] for ip in result]))
            logger.info(f"域名 {domain} 解析到 IP: {ips}")
            return ips
        except Exception as e:
            logger.error(f"解析域名 {domain} 失败: {e}")
            return []
    
    @staticmethod
    def test_ip_latency(ip: str, port: int = 443, timeout: int = 5) -> Optional[float]:
        """测试IP延迟"""
        try:
            start_time = time.time()
            sock = socket.create_connection((ip, port), timeout)
            sock.close()
            latency = (time.time() - start_time) * 1000  # 转换为毫秒
            logger.debug(f"IP {ip}:{port} 延迟: {latency:.2f}ms")
            return latency
        except Exception as e:
            logger.debug(f"测试 IP {ip}:{port} 延迟失败: {e}")
            return None
    
    @staticmethod
    def test_http_connectivity(url: str, timeout: int = 10) -> Tuple[bool, Optional[float], Optional[str]]:
        """测试HTTP连接性"""
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            latency = (time.time() - start_time) * 1000
            success = response.status_code == 200
            server = response.headers.get('Server', 'Unknown')
            
            logger.debug(f"HTTP测试 {url}: 成功={success}, 延迟={latency:.2f}ms, 服务器={server}")
            return success, latency, server
        except Exception as e:
            logger.debug(f"HTTP测试 {url} 失败: {e}")
            return False, None, None
    
    @staticmethod
    async def test_http_connectivity_async(session: aiohttp.ClientSession, url: str, timeout: int = 10) -> Tuple[bool, Optional[float], Optional[str]]:
        """异步测试HTTP连接性"""
        try:
            start_time = time.time()
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                latency = (time.time() - start_time) * 1000
                success = response.status == 200
                server = response.headers.get('Server', 'Unknown')
                
                logger.debug(f"异步HTTP测试 {url}: 成功={success}, 延迟={latency:.2f}ms, 服务器={server}")
                return success, latency, server
        except Exception as e:
            logger.debug(f"异步HTTP测试 {url} 失败: {e}")
            return False, None, None

class IPScanner:
    """IP扫描器"""
    
    def __init__(self, max_workers: int = 50):
        self.max_workers = max_workers
    
    def scan_ips_parallel(self, ips: List[str], port: int = 443, timeout: int = 5) -> Dict[str, float]:
        """并行扫描IP延迟"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ip = {
                executor.submit(NetworkUtils.test_ip_latency, ip, port, timeout): ip 
                for ip in ips
            }
            
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    latency = future.result()
                    if latency is not None:
                        results[ip] = latency
                except Exception as e:
                    logger.error(f"扫描IP {ip} 时出错: {e}")
        
        # 按延迟排序
        sorted_results = dict(sorted(results.items(), key=lambda x: x[1]))
        logger.info(f"扫描完成，找到 {len(sorted_results)} 个可用IP")
        return sorted_results
    
    async def scan_urls_async(self, urls: List[str], timeout: int = 10) -> Dict[str, Tuple[bool, Optional[float], Optional[str]]]:
        """异步扫描URL连接性"""
        results = {}
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                NetworkUtils.test_http_connectivity_async(session, url, timeout)
                for url in urls
            ]
            
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            
            for url, result in zip(urls, completed_tasks):
                if isinstance(result, Exception):
                    logger.error(f"扫描URL {url} 时出错: {result}")
                    results[url] = (False, None, None)
                else:
                    results[url] = result
        
        logger.info(f"URL扫描完成，测试了 {len(urls)} 个URL")
        return results

class GitHubIPFetcher:
    """GitHub IP获取器"""
    
    GITHUB_META_URL = "https://api.github.com/meta"
    
    @staticmethod
    def fetch_github_ips() -> List[str]:
        """获取GitHub官方IP段"""
        try:
            response = requests.get(GitHubIPFetcher.GITHUB_META_URL, timeout=10)
            if response.status_code == 200:
                meta = response.json()
                
                # 获取所有IP段
                all_ranges = []
                for key in ['web', 'api', 'git', 'pages', 'importer']:
                    if key in meta:
                        all_ranges.extend(meta[key])
                
                # 解析IP段为具体IP（简化版，只取每个段的前几个IP）
                ips = []
                for ip_range in all_ranges:
                    if '/' in ip_range:
                        # 简化处理，只处理/24网段
                        if ip_range.endswith('/24'):
                            base_ip = ip_range.replace('/24', '')
                            base_parts = base_ip.split('.')
                            if len(base_parts) == 4:
                                # 添加该网段的前10个IP
                                for i in range(1, 11):
                                    ip = f"{base_parts[0]}.{base_parts[1]}.{base_parts[2]}.{i}"
                                    ips.append(ip)
                    else:
                        ips.append(ip_range)
                
                logger.info(f"获取到 {len(ips)} 个GitHub IP")
                return list(set(ips))  # 去重
            else:
                logger.error(f"获取GitHub IP失败，状态码: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"获取GitHub IP失败: {e}")
            return []
    
    @staticmethod
    def get_fallback_ips() -> List[str]:
        """获取备用IP列表"""
        return [
            "140.82.112.3",
            "140.82.112.4", 
            "140.82.113.3",
            "140.82.113.4",
            "140.82.114.3",
            "140.82.114.4"
        ]