#!/usr/bin/env python3
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
    sys.exit(main())