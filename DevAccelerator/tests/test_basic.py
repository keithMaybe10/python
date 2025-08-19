#!/usr/bin/env python3
"""
基础功能测试
"""
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    
    try:
        # 测试配置模块
        from config.settings import APP_NAME, SUPPORTED_SITES
        print(f"✅ 配置模块导入成功: {APP_NAME}")
        
        # 测试工具模块
        from utils.logger import setup_logger
        from utils.network import NetworkUtils
        print("✅ 工具模块导入成功")
        
        # 测试核心模块
        from core.cert_manager import CertificateManager
        from core.node_manager import NodeManager
        print("✅ 核心模块导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_logger():
    """测试日志系统"""
    print("\n测试日志系统...")
    
    try:
        from utils.logger import setup_logger
        
        logger = setup_logger("test")
        logger.info("这是一条测试日志")
        logger.warning("这是一条警告日志")
        logger.error("这是一条错误日志")
        
        print("✅ 日志系统工作正常")
        return True
        
    except Exception as e:
        print(f"❌ 日志系统测试失败: {e}")
        return False

def test_network_utils():
    """测试网络工具"""
    print("\n测试网络工具...")
    
    try:
        from utils.network import NetworkUtils
        
        # 测试端口检查
        is_available = NetworkUtils.is_port_available(12345)
        print(f"✅ 端口检查功能正常: 端口12345可用={is_available}")
        
        # 测试域名解析
        ips = NetworkUtils.resolve_domain("github.com")
        if ips:
            print(f"✅ 域名解析功能正常: github.com -> {ips[:2]}...")
        else:
            print("⚠️ 域名解析返回空结果（可能是网络问题）")
        
        return True
        
    except Exception as e:
        print(f"❌ 网络工具测试失败: {e}")
        return False

def test_certificate_manager():
    """测试证书管理器"""
    print("\n测试证书管理器...")
    
    try:
        from core.cert_manager import CertificateManager
        
        cert_manager = CertificateManager()
        
        # 测试CA证书生成
        success = cert_manager.generate_ca_certificate()
        if success:
            print("✅ CA证书生成成功")
            
            # 测试CA证书加载
            ca_data = cert_manager.load_ca_certificate()
            if ca_data:
                print("✅ CA证书加载成功")
                
                # 测试服务器证书生成
                server_cert = cert_manager.generate_server_certificate("test.example.com")
                if server_cert:
                    print("✅ 服务器证书生成成功")
                else:
                    print("❌ 服务器证书生成失败")
            else:
                print("❌ CA证书加载失败")
        else:
            print("❌ CA证书生成失败")
        
        return success
        
    except Exception as e:
        print(f"❌ 证书管理器测试失败: {e}")
        return False

def test_node_manager():
    """测试节点管理器"""
    print("\n测试节点管理器...")
    
    try:
        from core.node_manager import NodeManager
        
        node_manager = NodeManager()
        
        # 测试添加节点
        success = node_manager.add_node("github.com", "140.82.112.3", "github.com")
        if success:
            print("✅ 节点添加成功")
        
        # 测试获取节点
        all_nodes = node_manager.get_all_nodes()
        print(f"✅ 获取节点信息成功: {len(all_nodes)} 个站点")
        
        return True
        
    except Exception as e:
        print(f"❌ 节点管理器测试失败: {e}")
        return False

def test_configuration():
    """测试配置系统"""
    print("\n测试配置系统...")
    
    try:
        from config.settings import config, SUPPORTED_SITES
        
        # 测试配置读写
        config.set("test_key", "test_value")
        value = config.get("test_key")
        
        if value == "test_value":
            print("✅ 配置读写功能正常")
        else:
            print("❌ 配置读写功能异常")
        
        # 测试支持的站点配置
        print(f"✅ 支持的站点数量: {len(SUPPORTED_SITES)}")
        for site_key, site_config in SUPPORTED_SITES.items():
            print(f"  - {site_config['name']}: {len(site_config['domains'])} 个域名")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置系统测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("DevAccelerator 基础功能测试")
    print("=" * 50)
    
    test_results = []
    
    # 运行各项测试
    test_results.append(test_imports())
    test_results.append(test_logger())
    test_results.append(test_network_utils())
    test_results.append(test_certificate_manager())
    test_results.append(test_node_manager())
    test_results.append(test_configuration())
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("✅ 所有基础功能测试通过！")
        return 0
    else:
        print(f"❌ 有 {total - passed} 项测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())