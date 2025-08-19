#!/usr/bin/env python3
"""
DevAccelerator 项目创建脚本
自动创建完整的项目结构和文件
"""
import os
import sys
from pathlib import Path

def create_project_structure():
    """创建项目目录结构"""
    print("创建项目目录结构...")
    
    directories = [
        "src/config",
        "src/core", 
        "src/ui",
        "src/utils",
        "tests",
        "docs",
        "assets",
        "config",
        "cache", 
        "certs",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {directory}")

def create_file_content_map():
    """返回所有文件的内容映射"""
    files = {}
    
    # requirements.txt
    files["requirements.txt"] = """PySide6>=6.6.0
requests>=2.31.0
cryptography>=41.0.0
dnslib>=0.9.24
aiohttp>=3.9.0
asyncio-throttle>=1.0.2
psutil>=5.9.0
pycryptodome>=3.19.0
pyinstaller>=6.0.0
qasync>=0.24.0"""

    # run.py
    files["run.py"] = '''#!/usr/bin/env python3
"""
DevAccelerator启动脚本
"""
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# 导入并运行主程序
from main import main

if __name__ == "__main__":
    sys.exit(main())'''

    # 更多文件内容...
    # 由于内容太长，这里只展示框架
    # 实际使用时需要包含所有文件的完整内容
    
    return files

def create_all_files():
    """创建所有项目文件"""
    print("\n创建项目文件...")
    
    files = create_file_content_map()
    
    for file_path, content in files.items():
        file_path_obj = Path(file_path)
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path_obj, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 创建文件: {file_path}")

def main():
    """主函数"""
    print("=" * 60)
    print("DevAccelerator 项目创建工具")
    print("=" * 60)
    
    # 检查当前目录
    current_dir = Path.cwd()
    project_dir = current_dir / "DevAccelerator"
    
    if project_dir.exists():
        response = input(f"目录 {project_dir} 已存在，是否覆盖？(y/N): ")
        if response.lower() != 'y':
            print("操作已取消")
            return 1
    
    # 切换到项目目录
    project_dir.mkdir(exist_ok=True)
    os.chdir(project_dir)
    
    try:
        # 创建项目结构
        create_project_structure()
        
        # 创建所有文件
        create_all_files()
        
        print(f"\n🎉 项目创建完成！")
        print(f"项目位置: {project_dir}")
        print(f"\n下一步:")
        print(f"1. cd {project_dir}")
        print(f"2. pip install -r requirements.txt")
        print(f"3. python run.py")
        
        return 0
        
    except Exception as e:
        print(f"❌ 项目创建失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())"""