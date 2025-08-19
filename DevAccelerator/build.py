#!/usr/bin/env python3
"""
DevAccelerator 构建脚本
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(cmd, description):
    """运行命令"""
    print(f"正在{description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description}成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description}失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def install_dependencies():
    """安装依赖"""
    return run_command("pip install -r requirements.txt", "安装依赖")

def run_tests():
    """运行测试"""
    return run_command("python tests/test_core_logic.py", "运行测试")

def build_executable():
    """构建可执行文件"""
    system = platform.system().lower()
    
    # PyInstaller 命令
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "DevAccelerator",
        "--add-data", "src;src",
        "--hidden-import", "PySide6",
        "--hidden-import", "qasync",
        "run.py"
    ]
    
    # Windows特定设置
    if system == "windows":
        cmd.extend([
            "--icon", "assets/icon.ico",  # 如果有图标文件
            "--version-file", "version.txt"  # 如果有版本文件
        ])
    
    return run_command(" ".join(cmd), "构建可执行文件")

def create_installer():
    """创建安装包"""
    system = platform.system().lower()
    
    if system == "windows":
        # 使用NSIS或Inno Setup创建Windows安装程序
        return run_command("makensis installer.nsi", "创建Windows安装程序")
    elif system == "darwin":
        # 创建macOS应用包
        return run_command("create-dmg dist/DevAccelerator.app", "创建macOS安装包")
    elif system == "linux":
        # 创建AppImage或deb包
        return run_command("linuxdeploy-x86_64.AppImage", "创建Linux AppImage")
    
    return True

def main():
    """主函数"""
    print("=" * 50)
    print("DevAccelerator 构建系统")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return 1
    
    print(f"✅ Python版本: {sys.version}")
    print(f"✅ 操作系统: {platform.system()} {platform.release()}")
    
    # 构建步骤
    steps = [
        ("安装依赖", install_dependencies),
        ("运行测试", run_tests),
        ("构建可执行文件", build_executable),
        ("创建安装包", create_installer),
    ]
    
    success_count = 0
    for step_name, step_func in steps:
        print(f"\n--- {step_name} ---")
        if step_func():
            success_count += 1
        else:
            print(f"❌ {step_name}失败，构建中止")
            break
    
    print(f"\n{'=' * 50}")
    print(f"构建结果: {success_count}/{len(steps)} 步骤成功")
    
    if success_count == len(steps):
        print("🎉 构建完成！")
        
        # 显示输出文件
        dist_dir = Path("dist")
        if dist_dir.exists():
            print("\n输出文件:")
            for file in dist_dir.iterdir():
                print(f"  - {file}")
        
        return 0
    else:
        print("❌ 构建失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())