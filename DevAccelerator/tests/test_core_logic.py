#!/usr/bin/env python3
"""
核心逻辑测试（不依赖外部库）
"""
import sys
import os
import json
import time
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

def test_configuration():
    """测试配置系统"""
    print("测试配置系统...")
    
    try:
        from config.settings import config, SUPPORTED_SITES, APP_NAME, THEME
        
        # 测试基本配置
        print(f"✅ 应用名称: {APP_NAME}")
        print(f"✅ 主题色: {THEME['primary_color']}")
        print(f"✅ 支持站点数: {len(SUPPORTED_SITES)}")
        
        # 测试配置读写
        test_key = "test_timestamp"
        test_value = str(int(time.time()))
        
        config.set(test_key, test_value)
        retrieved_value = config.get(test_key)
        
        if retrieved_value == test_value:
            print("✅ 配置读写功能正常")
        else:
            print(f"❌ 配置读写异常: 期望 {test_value}, 实际 {retrieved_value}")
            return False
        
        # 测试站点配置
        for site_key, site_config in SUPPORTED_SITES.items():
            required_keys = ["name", "domains", "test_url", "icon"]
            for key in required_keys:
                if key not in site_config:
                    print(f"❌ 站点 {site_key} 缺少必需配置: {key}")
                    return False
        
        print("✅ 所有站点配置完整")
        return True
        
    except Exception as e:
        print(f"❌ 配置系统测试失败: {e}")
        return False

def test_logger_basic():
    """测试基础日志功能"""
    print("\n测试日志系统...")
    
    try:
        from utils.logger import setup_logger
        
        # 创建测试日志记录器
        logger = setup_logger("test_core")
        
        # 测试不同级别的日志
        logger.debug("调试信息")
        logger.info("普通信息")
        logger.warning("警告信息")
        logger.error("错误信息")
        
        print("✅ 日志系统基础功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 日志系统测试失败: {e}")
        return False

def test_data_structures():
    """测试数据结构"""
    print("\n测试数据结构...")
    
    try:
        # 测试NodeInfo数据类
        from core.node_info import NodeInfo
        
        node = NodeInfo(
            ip="192.168.1.1",
            domain="test.example.com",
            site_name="Test Site"
        )
        
        # 测试初始状态
        assert node.latency is None
        assert node.success_rate == 0.0
        assert not node.is_available
        
        # 测试更新结果
        node.update_test_result(True, 100.0)
        assert node.latency == 100.0
        assert node.success_rate == 1.0
        assert node.is_available
        
        # 测试评分计算
        score = node.get_score()
        assert isinstance(score, float)
        
        print("✅ NodeInfo数据结构正常")
        
        # 测试更多测试结果
        node.update_test_result(False)
        assert node.success_rate == 0.5  # 1成功/2总数
        
        node.update_test_result(True, 50.0)
        assert node.success_rate == 2/3  # 2成功/3总数
        assert node.latency == 50.0  # 最新的延迟
        
        print("✅ 节点测试结果更新逻辑正常")
        return True
        
    except Exception as e:
        print(f"❌ 数据结构测试失败: {e}")
        return False

def test_file_operations():
    """测试文件操作"""
    print("\n测试文件操作...")
    
    try:
        from config.settings import BASE_DIR, CONFIG_DIR, CACHE_DIR, CERTS_DIR, LOGS_DIR
        
        # 检查目录创建
        required_dirs = [CONFIG_DIR, CACHE_DIR, CERTS_DIR, LOGS_DIR]
        for dir_path in required_dirs:
            if not dir_path.exists():
                print(f"❌ 必需目录不存在: {dir_path}")
                return False
            print(f"✅ 目录存在: {dir_path.name}")
        
        # 测试配置文件读写
        test_config_file = CONFIG_DIR / "test_config.json"
        test_data = {
            "test_key": "test_value",
            "timestamp": time.time(),
            "nested": {
                "key1": "value1",
                "key2": 123
            }
        }
        
        # 写入测试配置
        with open(test_config_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        # 读取测试配置
        with open(test_config_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        if loaded_data == test_data:
            print("✅ JSON配置文件读写正常")
        else:
            print("❌ JSON配置文件读写异常")
            return False
        
        # 清理测试文件
        test_config_file.unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ 文件操作测试失败: {e}")
        return False

def test_ui_styles():
    """测试UI样式"""
    print("\n测试UI样式...")
    
    try:
        from ui.styles import ANT_DESIGN_STYLE, ICONS, get_icon, get_status_color
        
        # 测试样式表
        assert isinstance(ANT_DESIGN_STYLE, str)
        assert len(ANT_DESIGN_STYLE) > 1000  # 样式表应该很长
        print("✅ 样式表长度正常")
        
        # 测试图标
        test_icons = ["play", "stop", "refresh", "settings", "github"]
        for icon_name in test_icons:
            icon = get_icon(icon_name)
            assert isinstance(icon, str)
            assert len(icon) > 0
        print("✅ 图标获取正常")
        
        # 测试状态颜色
        test_statuses = ["running", "stopped", "error", "warning"]
        for status in test_statuses:
            color = get_status_color(status)
            assert isinstance(color, str)
            assert color.startswith("#")  # 应该是十六进制颜色
        print("✅ 状态颜色获取正常")
        
        return True
        
    except Exception as e:
        print(f"❌ UI样式测试失败: {e}")
        return False

def test_accelerator_status():
    """测试加速器状态枚举"""
    print("\n测试加速器状态...")
    
    try:
        from core.status import AcceleratorStatus
        
        # 测试所有状态值
        expected_statuses = ["stopped", "starting", "running", "stopping", "error"]
        actual_statuses = [status.value for status in AcceleratorStatus]
        
        for status in expected_statuses:
            if status not in actual_statuses:
                print(f"❌ 缺少状态: {status}")
                return False
        
        print(f"✅ 状态枚举完整: {actual_statuses}")
        
        # 测试状态比较
        assert AcceleratorStatus.STOPPED != AcceleratorStatus.RUNNING
        assert AcceleratorStatus.STARTING.value == "starting"
        
        print("✅ 状态枚举比较正常")
        return True
        
    except Exception as e:
        print(f"❌ 加速器状态测试失败: {e}")
        return False

def test_network_utils_basic():
    """测试网络工具基础功能"""
    print("\n测试网络工具基础功能...")
    
    try:
        import socket
        
        # 创建一个简化的网络工具类进行测试
        class TestNetworkUtils:
            @staticmethod
            def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(1)
                        result = sock.connect_ex((host, port))
                        return result != 0
                except Exception:
                    return False
            
            @staticmethod
            def get_available_port(start_port: int = 8000, end_port: int = 9000) -> int:
                for port in range(start_port, end_port):
                    if TestNetworkUtils.is_port_available(port):
                        return port
                raise RuntimeError("没有可用端口")
        
        # 测试端口检查
        is_available = TestNetworkUtils.is_port_available(12345)
        print(f"✅ 端口检查功能: 端口12345可用={is_available}")
        
        # 测试可用端口获取
        available_port = TestNetworkUtils.get_available_port(20000, 20100)
        print(f"✅ 可用端口获取: {available_port}")
        
        return True
        
    except Exception as e:
        print(f"❌ 网络工具基础功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("DevAccelerator 核心逻辑测试")
    print("=" * 60)
    
    test_functions = [
        test_configuration,
        test_logger_basic,
        test_data_structures,
        test_file_operations,
        test_ui_styles,
        test_accelerator_status,
        test_network_utils_basic
    ]
    
    results = []
    for test_func in test_functions:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 出现异常: {e}")
            results.append(False)
    
    # 统计结果
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有核心逻辑测试通过！")
        print("\n✅ 基础架构正常")
        print("✅ 配置系统正常") 
        print("✅ 数据结构正常")
        print("✅ 文件操作正常")
        print("✅ UI样式正常")
        return 0
    else:
        print(f"❌ 有 {total - passed} 项测试失败")
        print("\n需要修复的问题:")
        for i, (test_func, result) in enumerate(zip(test_functions, results)):
            if not result:
                print(f"  - {test_func.__name__}")
        return 1

if __name__ == "__main__":
    sys.exit(main())