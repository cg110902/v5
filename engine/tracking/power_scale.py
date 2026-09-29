"""Novel Studio 5.0 战力位阶数据契约管理器 (Power Scale Manager)。

纯数据契约与阶层边界核验，零文学文本识别，零题材设定硬编码。
全书具体战力体系定义完全由外部配置文件（state/power_scale.json 或 bible/02_power_system.md）驱动。
"""
from typing import Dict, Any, Optional
from engine.errors import BusinessError


class PowerScaleManager:
    """战力位阶数值管理器"""

    def __init__(self, scale_data: Optional[Dict[str, Any]] = None):
        self.scale_data = scale_data or {"max_tier": 12, "tiers": {}}

    def get_tier_info(self, tier_rank: int) -> Optional[Dict[str, Any]]:
        """获取指定位阶配置"""
        tiers = self.scale_data.get("tiers", {})
        return tiers.get(str(tier_rank))

    def validate_tier_rank(self, tier_rank: int) -> None:
        """纯数值边界校验"""
        max_tier = int(self.scale_data.get("max_tier", 12))
        if tier_rank < 1 or tier_rank > max_tier:
            raise BusinessError(
                f"战力位阶越界：位阶数值 {tier_rank} 超出法定许可范围 [1, {max_tier}]！",
                remediation=f"请调整实体卡或细纲中的 tier_rank 至 1 到 {max_tier} 之间。"
            )
