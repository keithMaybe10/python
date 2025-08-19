"""
节点信息数据结构（独立模块）
"""
import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class NodeInfo:
    """节点信息"""
    ip: str
    domain: str
    site_name: str
    latency: Optional[float] = None
    success_rate: float = 0.0
    last_test_time: float = 0.0
    is_available: bool = False
    test_count: int = 0
    success_count: int = 0
    
    def update_test_result(self, success: bool, latency: Optional[float] = None):
        """更新测试结果"""
        self.test_count += 1
        if success:
            self.success_count += 1
            if latency is not None:
                self.latency = latency
        
        self.success_rate = self.success_count / self.test_count if self.test_count > 0 else 0.0
        self.is_available = success and (latency is not None and latency < 5000)  # 5秒超时
        self.last_test_time = time.time()
    
    def get_score(self) -> float:
        """获取节点评分（用于排序）"""
        if not self.is_available or self.latency is None:
            return float('inf')
        
        # 综合考虑延迟和成功率
        latency_score = self.latency
        success_rate_bonus = (1.0 - self.success_rate) * 1000  # 成功率低的节点增加延迟惩罚
        
        return latency_score + success_rate_bonus