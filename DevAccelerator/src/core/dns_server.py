"""
DNS服务器模块
"""
import socket
import threading
import time
from typing import Dict, List, Optional
import struct

from dnslib import DNSRecord, DNSHeader, RR, A, QTYPE
from dnslib.server import DNSServer, BaseResolver

from config.settings import DNS_PORT, DNS_SERVERS, SUPPORTED_SITES
from utils.logger import setup_logger
from utils.network import NetworkUtils

logger = setup_logger("dns_server")

class CustomDNSResolver(BaseResolver):
    """自定义DNS解析器"""
    
    def __init__(self):
        self.domain_ip_mapping: Dict[str, str] = {}
        self.upstream_servers = DNS_SERVERS
        self.cache: Dict[str, tuple] = {}  # (ip, timestamp)
        self.cache_ttl = 300  # 5分钟缓存
    
    def update_domain_mapping(self, domain: str, ip: str):
        """更新域名IP映射"""
        self.domain_ip_mapping[domain] = ip
        logger.info(f"更新域名映射: {domain} -> {ip}")
    
    def clear_domain_mapping(self, domain: str):
        """清除域名映射"""
        if domain in self.domain_ip_mapping:
            del self.domain_ip_mapping[domain]
            logger.info(f"清除域名映射: {domain}")
    
    def get_cached_ip(self, domain: str) -> Optional[str]:
        """获取缓存的IP"""
        if domain in self.cache:
            ip, timestamp = self.cache[domain]
            if time.time() - timestamp < self.cache_ttl:
                return ip
            else:
                del self.cache[domain]
        return None
    
    def cache_ip(self, domain: str, ip: str):
        """缓存IP"""
        self.cache[domain] = (ip, time.time())
    
    def resolve_upstream(self, domain: str) -> Optional[str]:
        """使用上游DNS服务器解析"""
        for dns_server in self.upstream_servers:
            try:
                # 创建DNS查询
                query = DNSRecord.question(domain, "A")
                
                # 发送UDP查询
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(3)
                sock.sendto(query.pack(), (dns_server, 53))
                
                # 接收响应
                data, _ = sock.recvfrom(1024)
                sock.close()
                
                # 解析响应
                response = DNSRecord.parse(data)
                for rr in response.rr:
                    if rr.rtype == QTYPE.A:
                        ip = str(rr.rdata)
                        logger.debug(f"上游DNS解析 {domain} -> {ip} (服务器: {dns_server})")
                        self.cache_ip(domain, ip)
                        return ip
                        
            except Exception as e:
                logger.debug(f"使用DNS服务器 {dns_server} 解析 {domain} 失败: {e}")
                continue
        
        return None
    
    def should_intercept_domain(self, domain: str) -> bool:
        """判断是否应该拦截该域名"""
        # 检查是否在支持的站点列表中
        for site_config in SUPPORTED_SITES.values():
            if domain in site_config["domains"]:
                return True
            # 检查子域名
            for supported_domain in site_config["domains"]:
                if domain.endswith(f".{supported_domain}") or domain == supported_domain:
                    return True
        return False
    
    def resolve(self, request, handler):
        """解析DNS请求"""
        reply = request.reply()
        
        try:
            # 获取查询的域名
            qname = str(request.q.qname).rstrip('.')
            qtype = request.q.qtype
            
            logger.debug(f"DNS查询: {qname} ({QTYPE[qtype]})")
            
            # 只处理A记录查询
            if qtype != QTYPE.A:
                # 对于非A记录，转发给上游DNS
                return self._forward_to_upstream(request)
            
            # 检查是否需要拦截
            if self.should_intercept_domain(qname):
                # 检查是否有自定义映射
                if qname in self.domain_ip_mapping:
                    ip = self.domain_ip_mapping[qname]
                    reply.add_answer(RR(qname, QTYPE.A, rdata=A(ip), ttl=60))
                    logger.info(f"DNS拦截: {qname} -> {ip}")
                    return reply
                
                # 检查缓存
                cached_ip = self.get_cached_ip(qname)
                if cached_ip:
                    reply.add_answer(RR(qname, QTYPE.A, rdata=A(cached_ip), ttl=60))
                    logger.debug(f"DNS缓存命中: {qname} -> {cached_ip}")
                    return reply
                
                # 使用上游DNS解析
                ip = self.resolve_upstream(qname)
                if ip:
                    reply.add_answer(RR(qname, QTYPE.A, rdata=A(ip), ttl=60))
                    return reply
            else:
                # 非拦截域名，直接转发
                return self._forward_to_upstream(request)
                
        except Exception as e:
            logger.error(f"DNS解析出错: {e}")
        
        # 返回空响应
        return reply
    
    def _forward_to_upstream(self, request):
        """转发请求到上游DNS服务器"""
        for dns_server in self.upstream_servers:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(3)
                sock.sendto(request.pack(), (dns_server, 53))
                
                data, _ = sock.recvfrom(1024)
                sock.close()
                
                response = DNSRecord.parse(data)
                return response
                
            except Exception as e:
                logger.debug(f"转发到DNS服务器 {dns_server} 失败: {e}")
                continue
        
        # 如果所有上游服务器都失败，返回空响应
        return request.reply()

class DNSServerManager:
    """DNS服务器管理器"""
    
    def __init__(self):
        self.resolver = CustomDNSResolver()
        self.server: Optional[DNSServer] = None
        self.running = False
        self.port = DNS_PORT
    
    def start(self) -> bool:
        """启动DNS服务器"""
        try:
            if self.running:
                logger.warning("DNS服务器已在运行")
                return True
            
            # 检查端口是否可用
            if not NetworkUtils.is_port_available(self.port):
                logger.error(f"DNS端口 {self.port} 不可用")
                return False
            
            # 创建DNS服务器
            self.server = DNSServer(
                self.resolver,
                port=self.port,
                address="127.0.0.1",
                tcp=False  # 只使用UDP
            )
            
            # 在后台线程中启动服务器
            server_thread = threading.Thread(target=self._run_server, daemon=True)
            server_thread.start()
            
            # 等待服务器启动
            time.sleep(1)
            
            if self.running:
                logger.info(f"DNS服务器启动成功，监听端口: {self.port}")
                return True
            else:
                logger.error("DNS服务器启动失败")
                return False
                
        except Exception as e:
            logger.error(f"启动DNS服务器失败: {e}")
            return False
    
    def _run_server(self):
        """运行DNS服务器"""
        try:
            self.running = True
            self.server.start()
        except Exception as e:
            logger.error(f"DNS服务器运行出错: {e}")
            self.running = False
    
    def stop(self):
        """停止DNS服务器"""
        try:
            if self.server and self.running:
                self.server.stop()
                self.running = False
                logger.info("DNS服务器已停止")
        except Exception as e:
            logger.error(f"停止DNS服务器失败: {e}")
    
    def update_domain_ip(self, domain: str, ip: str):
        """更新域名IP映射"""
        self.resolver.update_domain_mapping(domain, ip)
    
    def clear_domain_ip(self, domain: str):
        """清除域名IP映射"""
        self.resolver.clear_domain_mapping(domain)
    
    def is_running(self) -> bool:
        """检查DNS服务器是否在运行"""
        return self.running