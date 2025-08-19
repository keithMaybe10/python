"""
代理服务器模块
"""
import asyncio
import ssl
import socket
import threading
from typing import Dict, Optional, Tuple
import aiohttp
from aiohttp import web, ClientSession, ClientTimeout

from config.settings import PROXY_PORT, HTTPS_PROXY_PORT, PROXY_TIMEOUT
from core.cert_manager import CertificateManager
from utils.logger import setup_logger
from utils.network import NetworkUtils

logger = setup_logger("proxy_server")

class HTTPProxyHandler:
    """HTTP代理处理器"""
    
    def __init__(self, domain_ip_mapping: Dict[str, str]):
        self.domain_ip_mapping = domain_ip_mapping
    
    async def handle_request(self, request):
        """处理HTTP请求"""
        try:
            # 获取目标URL
            url = str(request.url)
            method = request.method
            headers = dict(request.headers)
            
            # 移除代理相关的头部
            headers.pop('Host', None)
            headers.pop('Proxy-Connection', None)
            
            # 检查是否需要重定向IP
            target_url = self._rewrite_url(url)
            
            logger.debug(f"代理请求: {method} {url} -> {target_url}")
            
            # 创建客户端会话
            timeout = ClientTimeout(total=PROXY_TIMEOUT)
            async with ClientSession(timeout=timeout) as session:
                # 转发请求
                async with session.request(
                    method=method,
                    url=target_url,
                    headers=headers,
                    data=await request.read() if method in ['POST', 'PUT', 'PATCH'] else None,
                    allow_redirects=False
                ) as response:
                    # 构造响应
                    resp_headers = dict(response.headers)
                    resp_headers.pop('Transfer-Encoding', None)  # 移除传输编码
                    
                    body = await response.read()
                    
                    return web.Response(
                        status=response.status,
                        headers=resp_headers,
                        body=body
                    )
                    
        except Exception as e:
            logger.error(f"代理请求失败: {e}")
            return web.Response(status=500, text=f"代理错误: {str(e)}")
    
    def _rewrite_url(self, url: str) -> str:
        """重写URL，替换为最优IP"""
        try:
            from urllib.parse import urlparse, urlunparse
            
            parsed = urlparse(url)
            hostname = parsed.hostname
            
            # 检查是否需要替换IP
            if hostname and hostname in self.domain_ip_mapping:
                new_ip = self.domain_ip_mapping[hostname]
                
                # 重构URL
                new_netloc = f"{new_ip}:{parsed.port}" if parsed.port else new_ip
                new_parsed = parsed._replace(netloc=new_netloc)
                new_url = urlunparse(new_parsed)
                
                logger.debug(f"URL重写: {url} -> {new_url}")
                return new_url
            
            return url
            
        except Exception as e:
            logger.error(f"URL重写失败: {e}")
            return url

class HTTPSProxyServer:
    """HTTPS代理服务器"""
    
    def __init__(self, cert_manager: CertificateManager):
        self.cert_manager = cert_manager
        self.domain_ip_mapping: Dict[str, str] = {}
        self.server_certs: Dict[str, Tuple[str, str]] = {}  # domain -> (key, cert)
        self.running = False
        self.server_socket: Optional[socket.socket] = None
        self.port = HTTPS_PROXY_PORT
    
    def update_domain_ip(self, domain: str, ip: str):
        """更新域名IP映射"""
        self.domain_ip_mapping[domain] = ip
        logger.info(f"更新HTTPS代理映射: {domain} -> {ip}")
    
    def clear_domain_ip(self, domain: str):
        """清除域名IP映射"""
        if domain in self.domain_ip_mapping:
            del self.domain_ip_mapping[domain]
        if domain in self.server_certs:
            del self.server_certs[domain]
        logger.info(f"清除HTTPS代理映射: {domain}")
    
    def get_or_create_cert(self, domain: str) -> Optional[Tuple[str, str]]:
        """获取或创建域名证书"""
        if domain in self.server_certs:
            return self.server_certs[domain]
        
        # 生成新证书
        cert_data = self.cert_manager.generate_server_certificate(domain)
        if cert_data:
            self.server_certs[domain] = cert_data
            return cert_data
        
        return None
    
    def start(self) -> bool:
        """启动HTTPS代理服务器"""
        try:
            if self.running:
                logger.warning("HTTPS代理服务器已在运行")
                return True
            
            # 检查端口是否可用
            if not NetworkUtils.is_port_available(self.port):
                logger.error(f"HTTPS代理端口 {self.port} 不可用")
                return False
            
            # 创建服务器套接字
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('127.0.0.1', self.port))
            self.server_socket.listen(128)
            
            self.running = True
            
            # 在后台线程中运行
            server_thread = threading.Thread(target=self._run_server, daemon=True)
            server_thread.start()
            
            logger.info(f"HTTPS代理服务器启动成功，监听端口: {self.port}")
            return True
            
        except Exception as e:
            logger.error(f"启动HTTPS代理服务器失败: {e}")
            return False
    
    def _run_server(self):
        """运行HTTPS代理服务器"""
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                
                # 在新线程中处理客户端连接
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.running:  # 只在服务器运行时记录错误
                    logger.error(f"接受客户端连接失败: {e}")
    
    def _handle_client(self, client_socket: socket.socket, client_address):
        """处理客户端连接"""
        try:
            # 读取CONNECT请求
            request_data = client_socket.recv(4096).decode('utf-8')
            
            # 解析CONNECT请求
            lines = request_data.split('\r\n')
            if not lines or not lines[0].startswith('CONNECT'):
                client_socket.close()
                return
            
            # 提取目标主机和端口
            connect_line = lines[0]
            target = connect_line.split(' ')[1]
            
            if ':' in target:
                hostname, port = target.split(':')
                port = int(port)
            else:
                hostname = target
                port = 443
            
            logger.debug(f"HTTPS CONNECT: {hostname}:{port}")
            
            # 发送连接成功响应
            client_socket.send(b'HTTP/1.1 200 Connection established\r\n\r\n')
            
            # 获取目标IP
            target_ip = self.domain_ip_mapping.get(hostname, hostname)
            
            # 连接到目标服务器
            target_socket = socket.create_connection((target_ip, port), timeout=PROXY_TIMEOUT)
            
            # 开始数据转发
            self._relay_data(client_socket, target_socket)
            
        except Exception as e:
            logger.error(f"处理HTTPS客户端连接失败: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def _relay_data(self, client_socket: socket.socket, target_socket: socket.socket):
        """双向转发数据"""
        def forward_data(src: socket.socket, dst: socket.socket):
            try:
                while True:
                    data = src.recv(4096)
                    if not data:
                        break
                    dst.send(data)
            except:
                pass
            finally:
                try:
                    src.close()
                    dst.close()
                except:
                    pass
        
        # 创建两个转发线程
        client_to_target = threading.Thread(
            target=forward_data,
            args=(client_socket, target_socket),
            daemon=True
        )
        target_to_client = threading.Thread(
            target=forward_data,
            args=(target_socket, client_socket),
            daemon=True
        )
        
        client_to_target.start()
        target_to_client.start()
        
        # 等待任一线程结束
        client_to_target.join()
        target_to_client.join()
    
    def stop(self):
        """停止HTTPS代理服务器"""
        try:
            self.running = False
            if self.server_socket:
                self.server_socket.close()
            logger.info("HTTPS代理服务器已停止")
        except Exception as e:
            logger.error(f"停止HTTPS代理服务器失败: {e}")

class ProxyServerManager:
    """代理服务器管理器"""
    
    def __init__(self, cert_manager: CertificateManager):
        self.cert_manager = cert_manager
        self.http_app: Optional[web.Application] = None
        self.http_runner: Optional[web.AppRunner] = None
        self.https_server = HTTPSProxyServer(cert_manager)
        self.domain_ip_mapping: Dict[str, str] = {}
        self.running = False
    
    def update_domain_ip(self, domain: str, ip: str):
        """更新域名IP映射"""
        self.domain_ip_mapping[domain] = ip
        self.https_server.update_domain_ip(domain, ip)
    
    def clear_domain_ip(self, domain: str):
        """清除域名IP映射"""
        if domain in self.domain_ip_mapping:
            del self.domain_ip_mapping[domain]
        self.https_server.clear_domain_ip(domain)
    
    async def start(self) -> bool:
        """启动代理服务器"""
        try:
            if self.running:
                logger.warning("代理服务器已在运行")
                return True
            
            # 启动HTTP代理
            if not await self._start_http_proxy():
                return False
            
            # 启动HTTPS代理
            if not self.https_server.start():
                await self._stop_http_proxy()
                return False
            
            self.running = True
            logger.info("代理服务器启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动代理服务器失败: {e}")
            return False
    
    async def _start_http_proxy(self) -> bool:
        """启动HTTP代理"""
        try:
            # 创建HTTP应用
            self.http_app = web.Application()
            
            # 创建代理处理器
            proxy_handler = HTTPProxyHandler(self.domain_ip_mapping)
            
            # 添加路由（捕获所有请求）
            self.http_app.router.add_route('*', '/{path:.*}', proxy_handler.handle_request)
            
            # 创建运行器
            self.http_runner = web.AppRunner(self.http_app)
            await self.http_runner.setup()
            
            # 创建站点
            site = web.TCPSite(self.http_runner, '127.0.0.1', PROXY_PORT)
            await site.start()
            
            logger.info(f"HTTP代理服务器启动成功，监听端口: {PROXY_PORT}")
            return True
            
        except Exception as e:
            logger.error(f"启动HTTP代理服务器失败: {e}")
            return False
    
    async def _stop_http_proxy(self):
        """停止HTTP代理"""
        try:
            if self.http_runner:
                await self.http_runner.cleanup()
                self.http_runner = None
            self.http_app = None
            logger.info("HTTP代理服务器已停止")
        except Exception as e:
            logger.error(f"停止HTTP代理服务器失败: {e}")
    
    async def stop(self):
        """停止代理服务器"""
        try:
            self.running = False
            
            # 停止HTTP代理
            await self._stop_http_proxy()
            
            # 停止HTTPS代理
            self.https_server.stop()
            
            logger.info("代理服务器已停止")
            
        except Exception as e:
            logger.error(f"停止代理服务器失败: {e}")
    
    def is_running(self) -> bool:
        """检查代理服务器是否在运行"""
        return self.running