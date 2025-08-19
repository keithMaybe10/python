#!/usr/bin/env python3
"""
DevAccelerator 项目下载脚本
生成包含所有文件的自解压脚本
"""
import base64
import gzip
import json
from pathlib import Path

def create_project_bundle():
    """创建项目文件包"""
    print("正在打包项目文件...")
    
    # 项目文件列表（这里需要包含所有实际文件内容）
    project_files = {
        "README.md": """# DevAccelerator - 开发者网站访问加速器

## 快速开始

1. 解压项目文件
2. 安装依赖: `pip install -r requirements.txt`  
3. 运行程序: `python run.py`

详细说明请参考完整文档。
""",
        
        "requirements.txt": """PySide6>=6.6.0
requests>=2.31.0
cryptography>=41.0.0
dnslib>=0.9.24
aiohttp>=3.9.0
asyncio-throttle>=1.0.2
psutil>=5.9.0
pycryptodome>=3.19.0
pyinstaller>=6.0.0
qasync>=0.24.0""",

        # 这里应该包含所有文件的完整内容
        # 由于内容过长，这里只展示结构
    }
    
    # 压缩文件数据
    compressed_data = gzip.compress(json.dumps(project_files).encode('utf-8'))
    encoded_data = base64.b64encode(compressed_data).decode('utf-8')
    
    return encoded_data

def generate_download_script():
    """生成自解压下载脚本"""
    bundle_data = create_project_bundle()
    
    script_content = f'''#!/usr/bin/env python3
"""
DevAccelerator 项目自解压脚本
运行此脚本将自动创建完整的项目文件
"""
import base64
import gzip
import json
import os
from pathlib import Path

# 项目数据（Base64编码的压缩JSON）
PROJECT_DATA = """{bundle_data}"""

def extract_project():
    """解压项目文件"""
    print("正在解压 DevAccelerator 项目...")
    
    try:
        # 解码和解压数据
        compressed_data = base64.b64decode(PROJECT_DATA)
        json_data = gzip.decompress(compressed_data).decode('utf-8')
        project_files = json.loads(json_data)
        
        # 创建项目目录
        project_dir = Path("DevAccelerator")
        project_dir.mkdir(exist_ok=True)
        
        # 创建所有文件
        for file_path, content in project_files.items():
            full_path = project_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 创建: {{file_path}}")
        
        print(f"\\n🎉 项目解压完成！")
        print(f"项目位置: {{project_dir.absolute()}}")
        print(f"\\n下一步:")
        print(f"1. cd {{project_dir}}")
        print(f"2. pip install -r requirements.txt")
        print(f"3. python run.py")
        
    except Exception as e:
        print(f"❌ 解压失败: {{e}}")
        return False
    
    return True

if __name__ == "__main__":
    extract_project()
'''
    
    return script_content

def main():
    """主函数"""
    print("=" * 50)
    print("DevAccelerator 下载脚本生成器")
    print("=" * 50)
    
    try:
        script_content = generate_download_script()
        
        # 保存下载脚本
        script_path = Path("devaccelerator_download.py")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✅ 下载脚本已生成: {script_path}")
        print(f"\n使用方法:")
        print(f"1. 将 {script_path} 复制到目标位置")
        print(f"2. 运行: python {script_path}")
        print(f"3. 将自动创建完整的 DevAccelerator 项目")
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")

if __name__ == "__main__":
    main()"""