"""Novel Studio 5.0 宏观世界时钟与外部大势管理器 (World Clock Manager).

纯数据驱动的全局局势、时空坐标与外部事件追踪。
支持多线大势推进、区域张力动态重算与昼夜节律推进。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from engine.core.models import MacroEvent as LegacyMacroEvent
from engine.domain.universe import LivingUniverse, SpatiotemporalGrid, MacroEvent


class WorldClockManager:
    """宏观世界时钟与大势局势管理器"""

    def __init__(
        self,
        events_data: Optional[Union[List[Dict[str, Any]], LivingUniverse]] = None,
    ):
        if isinstance(events_data, LivingUniverse):
            self.universe = events_data
            self.events = self.universe.macro_events
        else:
            self.universe = LivingUniverse()
            self.events = {}
            if events_data:
                for ed in events_data:
                    if isinstance(ed, dict) and "id" in ed:
                        self.events[ed["id"]] = MacroEvent(
                            event_id=ed["id"],
                            title=ed.get("title", ""),
                            stage=ed.get("stage", "brewing"),
                            affected_regions=ed.get("affected_regions", []),
                            trigger_chapter=ed.get("trigger_chapter", 1),
                            peak_chapter=ed.get("peak_chapter", 10),
                            tension_delta=ed.get("tension_delta", 10),
                        )
            self.universe.macro_events = self.events

    def get_active_events(self) -> List[Any]:
        """获取当前活跃的外部大势事件（未解决者）"""
        return [e for e in self.events.values() if getattr(e, "stage", "") != "resolved"]

    def update_event_stage(self, event_id: str, new_stage: str) -> bool:
        """更新指定事件所处的演化阶段"""
        if event_id in self.events:
            self.events[event_id].stage = new_stage
            return True
        return False

    def advance_world_tick(
        self,
        current_chapter: int,
        elapsed_hours: int = 4,
    ) -> Dict[str, Any]:
        """按章节步长推进日历时钟，并更新所有大势事件与区域张力"""
        # 1. 推进自然时钟
        grid_data = self.universe.clock.advance_hours(elapsed_hours)

        # 2. 检查事件阶段转换
        events_updated = 0
        for ev in self.events.values():
            if ev.stage == "brewing" and current_chapter >= ev.trigger_chapter:
                ev.stage = "erupting"
                events_updated += 1
            elif ev.stage == "erupting" and current_chapter >= ev.peak_chapter:
                ev.stage = "peaking"
                events_updated += 1

        # 3. 统计当前平均世界张力
        total_tension = self.universe.tension
        for ev in self.events.values():
            if ev.stage in ("erupting", "peaking"):
                total_tension += ev.tension_delta

        return {
            "chapter": current_chapter,
            "current_day": self.universe.clock.current_day,
            "current_hour": self.universe.clock.current_hour,
            "day_phase": self.universe.clock.day_phase,
            "elapsed_hours": elapsed_hours,
            "active_events_count": len(self.get_active_events()),
            "events_updated": events_updated,
            "effective_tension": min(100, max(0, total_tension)),
        }

    def get_spatiotemporal_context(self) -> Dict[str, Any]:
        """导出当前章节时空环境切片"""
        return {
            "current_day": self.universe.clock.current_day,
            "current_hour": self.universe.clock.current_hour,
            "day_phase": self.universe.clock.day_phase,
            "weather": self.universe.clock.weather,
            "active_events": [
                {"id": ev.event_id, "title": ev.title, "stage": ev.stage}
                for ev in self.get_active_events()
            ],
        }
