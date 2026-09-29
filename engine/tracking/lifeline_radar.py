"""Novel Studio 5.0 角色生命线与伏笔时钟雷达 (Lifeline & Foreshadowing Radar).

纯数值差额计算与阈值比对，零文学语义判定：
1. 角色离场跨度 = current_chapter - last_seen_ch，根据数值阈值触发提醒；
2. 伏笔剩余章数 = target_ch - current_chapter，根据数值阈值触发回收警报；
3. 恩怨沉寂雷达 = 极度敌对或重大恩怨长期未触碰触发暗流预警。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from engine.core.models import Person, Foreshadowing
from engine.domain.character import LivingCharacter
from engine.domain.plot_graph import LivingPlotGraph, ForeshadowingItem


class LifelineRadar:
    """生命线与伏笔倒计时雷达"""

    @staticmethod
    def scan_lifelines(
        persons: Dict[str, Any],
        current_ch: int,
        yellow_thresh: int = 8,
        red_thresh: int = 12,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """扫描核心角色生命线离场跨度"""
        alerts: Dict[str, List[Dict[str, Any]]] = {
            "yellow": [],
            "red": [],
        }

        monitored_roles = {"protagonist", "antagonist", "deuteragonist", "ally"}

        for p in persons.values():
            role = getattr(p, "role", None) or (p.get("role") if isinstance(p, dict) else "")
            if role not in monitored_roles:
                continue

            # 存活状态判定
            is_alive = True
            if hasattr(p, "is_alive"):
                is_alive = p.is_alive() if callable(p.is_alive) else bool(p.is_alive)
            elif isinstance(p, dict):
                is_alive = p.get("life_status") == "alive"

            if not is_alive:
                continue

            pid = getattr(p, "id", None) or getattr(p, "character_id", None) or (p.get("id") if isinstance(p, dict) else "")
            name = getattr(p, "name", "") or (p.get("name") if isinstance(p, dict) else pid)

            # 获取最后露面章节
            last_seen = 0
            if hasattr(p, "last_seen_ch"):
                last_seen = int(p.last_seen_ch)
            elif hasattr(p, "motive_history") and p.motive_history:
                past_chs = [c for c in p.motive_history.keys() if c <= current_ch]
                last_seen = max(past_chs) if past_chs else 0
            elif isinstance(p, dict):
                last_seen = int(p.get("last_seen_ch", 0))

            if last_seen <= 0:
                continue

            gap = current_ch - last_seen
            item = {
                "id": pid,
                "name": name,
                "role": role,
                "last_seen_ch": last_seen,
                "gap": gap,
            }

            if gap >= red_thresh:
                alerts["red"].append(item)
            elif gap >= yellow_thresh:
                alerts["yellow"].append(item)

        return alerts

    @staticmethod
    def scan_foreshadowing_clock(
        lines: Union[Dict[str, Any], LivingPlotGraph],
        current_ch: int,
        alert_thresh: int = 3,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """扫描活跃伏笔生命周期与临期/逾期预警"""
        clock: Dict[str, List[Dict[str, Any]]] = {
            "overdue": [],
            "near_term": [],
            "active": [],
        }

        # 支持从 LivingPlotGraph 或 lines 字典输入
        items: List[Any] = []
        if isinstance(lines, LivingPlotGraph):
            items = list(lines.foreshadowing.values())
        elif isinstance(lines, dict):
            items = list(lines.values())

        for f in items:
            state = getattr(f, "state", None) or getattr(f, "lifecycle_status", None) or (f.get("state") if isinstance(f, dict) else "")
            if state in ("resolved", "completed"):
                continue

            fid = getattr(f, "id", None) or getattr(f, "clue_id", None) or (f.get("id") if isinstance(f, dict) else "")
            title = getattr(f, "title", None) or getattr(f, "hook", None) or (f.get("title") if isinstance(f, dict) else "")

            # 目标章节
            target_ch = current_ch + 10
            if hasattr(f, "target_ch"):
                target_ch = int(f.target_ch)
            elif hasattr(f, "target_resolution_window"):
                target_ch = int(f.target_resolution_window[1])
            elif isinstance(f, dict):
                target_ch = int(f.get("target_ch", f.get("target_resolution_window", [0, current_ch + 10])[-1]))

            rem = target_ch - current_ch
            info = {
                "id": fid,
                "title": title,
                "state": state,
                "target_ch": target_ch,
                "remaining": rem,
            }

            if rem <= 0:
                clock["overdue"].append(info)
            elif rem <= alert_thresh:
                clock["near_term"].append(info)
            else:
                clock["active"].append(info)

        return clock
