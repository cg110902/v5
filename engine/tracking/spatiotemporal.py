"""Novel Studio 5.0 时空拓扑与日历推进中枢 (Spatiotemporal Engine)。

纯数值日历时钟与距离路由，零自然语言或特定题材时段硬编码。
"""
from typing import Dict, Any, Optional


class SpatiotemporalEngine:
    """时空与位移数值引擎"""

    def __init__(self, topo_data: Optional[Dict[str, Any]] = None):
        self.topo_data = topo_data or {
            "current_day": 1,
            "current_hour": 0,
            "current_turn": 1,
            "routes": {}
        }

    def get_travel_cost(self, loc_a: str, loc_b: str, mode: str = "default") -> int:
        """测算两地间通行耗时（整数单位：小时）"""
        if not loc_a or not loc_b or loc_a == loc_b:
            return 0

        routes = self.topo_data.get("routes", {})
        key = f"{loc_a}->{loc_b}"
        rev_key = f"{loc_b}->{loc_a}"
        
        info = routes.get(key) or routes.get(rev_key)
        if isinstance(info, dict) and mode in info:
            return int(info[mode])
        if isinstance(info, (int, float)):
            return int(info)

        return 1

    def advance_time(self, hours: int) -> Dict[str, Any]:
        """纯数值推进日历时钟"""
        cur_day = int(self.topo_data.get("current_day", 1))
        cur_hour = int(self.topo_data.get("current_hour", 0))
        cur_turn = int(self.topo_data.get("current_turn", 1))

        total_hours = cur_hour + hours
        day_inc = total_hours // 24
        new_hour = total_hours % 24
        new_day = cur_day + day_inc
        new_turn = cur_turn + 1

        self.topo_data["current_day"] = new_day
        self.topo_data["current_hour"] = new_hour
        self.topo_data["current_turn"] = new_turn

        return {
            "current_day": new_day,
            "current_hour": new_hour,
            "current_turn": new_turn,
            "elapsed_hours": hours
        }
