"""
加速器状态枚举（独立模块）
"""
from enum import Enum

class AcceleratorStatus(Enum):
    """加速器状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"