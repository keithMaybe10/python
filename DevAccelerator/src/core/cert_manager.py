"""
证书管理模块
"""
import os
import subprocess
import platform
from pathlib import Path
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from typing import Optional, Tuple

from config.settings import CERTS_DIR
from utils.logger import setup_logger

logger = setup_logger("cert_manager")

class CertificateManager:
    """证书管理器"""
    
    def __init__(self):
        self.certs_dir = CERTS_DIR
        self.ca_key_file = self.certs_dir / "ca.key"
        self.ca_cert_file = self.certs_dir / "ca.crt"
    
    def generate_ca_certificate(self) -> bool:
        """生成CA证书"""
        try:
            # 生成CA私钥
            ca_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # 生成CA证书
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "DevAccelerator"),
                x509.NameAttribute(NameOID.COMMON_NAME, "DevAccelerator Root CA"),
            ])
            
            ca_cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                ca_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=3650)  # 10年
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.IPAddress("127.0.0.1"),
                ]),
                critical=False,
            ).add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            ).add_extension(
                x509.KeyUsage(
                    key_cert_sign=True,
                    crl_sign=True,
                    digital_signature=False,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            ).sign(ca_key, hashes.SHA256())
            
            # 保存CA私钥
            with open(self.ca_key_file, "wb") as f:
                f.write(ca_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # 保存CA证书
            with open(self.ca_cert_file, "wb") as f:
                f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
            
            logger.info(f"CA证书生成成功: {self.ca_cert_file}")
            return True
            
        except Exception as e:
            logger.error(f"生成CA证书失败: {e}")
            return False
    
    def load_ca_certificate(self) -> Optional[Tuple[rsa.RSAPrivateKey, x509.Certificate]]:
        """加载CA证书"""
        try:
            if not (self.ca_key_file.exists() and self.ca_cert_file.exists()):
                return None
            
            # 加载CA私钥
            with open(self.ca_key_file, "rb") as f:
                ca_key = serialization.load_pem_private_key(f.read(), password=None)
            
            # 加载CA证书
            with open(self.ca_cert_file, "rb") as f:
                ca_cert = x509.load_pem_x509_certificate(f.read())
            
            return ca_key, ca_cert
            
        except Exception as e:
            logger.error(f"加载CA证书失败: {e}")
            return None
    
    def generate_server_certificate(self, domain: str) -> Optional[Tuple[str, str]]:
        """为域名生成服务器证书"""
        try:
            # 加载CA证书
            ca_data = self.load_ca_certificate()
            if not ca_data:
                logger.error("CA证书不存在，请先生成CA证书")
                return None
            
            ca_key, ca_cert = ca_data
            
            # 生成服务器私钥
            server_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # 生成服务器证书
            subject = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "DevAccelerator"),
                x509.NameAttribute(NameOID.COMMON_NAME, domain),
            ])
            
            server_cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                ca_cert.issuer
            ).public_key(
                server_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(domain),
                    x509.DNSName(f"*.{domain}"),
                ]),
                critical=False,
            ).add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            ).add_extension(
                x509.KeyUsage(
                    key_cert_sign=False,
                    crl_sign=False,
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=True,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            ).sign(ca_key, hashes.SHA256())
            
            # 转换为PEM格式字符串
            server_key_pem = server_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')
            
            server_cert_pem = server_cert.public_bytes(
                serialization.Encoding.PEM
            ).decode('utf-8')
            
            logger.info(f"为域名 {domain} 生成服务器证书成功")
            return server_key_pem, server_cert_pem
            
        except Exception as e:
            logger.error(f"为域名 {domain} 生成服务器证书失败: {e}")
            return None
    
    def install_ca_certificate(self) -> bool:
        """提供CA证书安装指导（不自动安装）"""
        try:
            system = platform.system().lower()
            cert_path = str(self.ca_cert_file.absolute())
            
            logger.info("CA证书已生成，请手动安装以获得最佳体验")
            logger.info(f"证书位置: {cert_path}")
            
            if system == "windows":
                logger.info("Windows安装方法:")
                logger.info("1. 双击证书文件")
                logger.info("2. 选择'安装证书'")
                logger.info("3. 选择'本地计算机'或'当前用户'")
                logger.info("4. 选择'受信任的根证书颁发机构'")
            elif system == "darwin":  # macOS
                logger.info("macOS安装方法:")
                logger.info("1. 双击证书文件")
                logger.info("2. 在钥匙串访问中找到证书")
                logger.info("3. 双击证书，设置为'始终信任'")
            elif system == "linux":
                logger.info("Linux安装方法:")
                logger.info("1. 复制证书到 /usr/local/share/ca-certificates/")
                logger.info("2. 运行 sudo update-ca-certificates")
                logger.info("3. 或在浏览器中手动导入证书")
            
            # 不自动安装，避免需要管理员权限
            return True
                
        except Exception as e:
            logger.error(f"生成证书安装指导失败: {e}")
            return False
    
    def get_cert_install_instructions(self) -> dict:
        """获取证书安装说明"""
        system = platform.system().lower()
        cert_path = str(self.ca_cert_file.absolute())
        
        instructions = {
            "cert_path": cert_path,
            "system": system,
            "instructions": []
        }
        
        if system == "windows":
            instructions["instructions"] = [
                f"1. 找到证书文件: {cert_path}",
                "2. 双击证书文件",
                "3. 点击'安装证书'",
                "4. 选择'当前用户'或'本地计算机'",
                "5. 选择'将所有的证书都放入下列存储'",
                "6. 点击'浏览'，选择'受信任的根证书颁发机构'",
                "7. 点击'确定'完成安装"
            ]
        elif system == "darwin":
            instructions["instructions"] = [
                f"1. 找到证书文件: {cert_path}",
                "2. 双击证书文件",
                "3. 在钥匙串访问中找到 'DevAccelerator Root CA'",
                "4. 双击证书，展开'信任'部分",
                "5. 将'使用此证书时'设置为'始终信任'",
                "6. 关闭窗口并输入密码确认"
            ]
        elif system == "linux":
            instructions["instructions"] = [
                f"1. 证书文件位置: {cert_path}",
                "2. 方法一 - 系统级安装（需要sudo权限）:",
                f"   sudo cp {cert_path} /usr/local/share/ca-certificates/devaccelerator.crt",
                "   sudo update-ca-certificates",
                "3. 方法二 - 浏览器手动导入:",
                "   在Firefox/Chrome的设置中导入证书到'受信任的根证书颁发机构'"
            ]
        
        return instructions
    
    def is_ca_certificate_valid(self) -> bool:
        """检查CA证书是否有效"""
        try:
            ca_data = self.load_ca_certificate()
            if not ca_data:
                return False
            
            ca_key, ca_cert = ca_data
            
            # 检查证书是否过期
            now = datetime.utcnow()
            if now < ca_cert.not_valid_before or now > ca_cert.not_valid_after:
                logger.warning("CA证书已过期或尚未生效")
                return False
            
            logger.info("CA证书有效")
            return True
            
        except Exception as e:
            logger.error(f"检查CA证书有效性失败: {e}")
            return False
    
    def ensure_ca_certificate(self) -> bool:
        """确保CA证书存在且有效"""
        if not self.is_ca_certificate_valid():
            logger.info("CA证书无效，重新生成...")
            if not self.generate_ca_certificate():
                return False
        
        return True