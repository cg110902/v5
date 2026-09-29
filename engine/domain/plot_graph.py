"""Domain model for LivingPlotGraph, ForeshadowingLifecycle, SubplotBranch, and ChapterContinuityHandover.

Universal & genre-agnostic: uses structural keys, integer chapter markers, and zero hardcoded Chinese literary terms.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ForeshadowingItem:
    """Rigid tracking of a narrative clue/hook across its entire lifecycle."""
    clue_id: str
    hook: str
    planted_chapter: int
    target_resolution_window: Tuple[int, int] = (1, 10)  # (min_ch, max_ch)
    stirred_chapters: List[int] = field(default_factory=list)
    resolved_chapter: Optional[int] = None
    lifecycle_status: str = "planted"  # planted, stirred, converged, resolved, echoed
    associated_character_ids: List[str] = field(default_factory=list)

    def stir(self, chapter: int) -> None:
        if chapter not in self.stirred_chapters:
            self.stirred_chapters.append(chapter)
        if self.lifecycle_status == "planted":
            self.lifecycle_status = "stirred"

    def resolve(self, chapter: int) -> None:
        self.resolved_chapter = chapter
        self.lifecycle_status = "resolved"

    def is_overdue(self, current_chapter: int) -> bool:
        if self.lifecycle_status == "resolved":
            return False
        return current_chapter > self.target_resolution_window[1]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["target_resolution_window"] = list(self.target_resolution_window)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ForeshadowingItem:
        raw_win = data.get("target_resolution_window", [1, 10])
        win = (int(raw_win[0]), int(raw_win[1])) if len(raw_win) >= 2 else (1, 10)
        return cls(
            clue_id=str(data.get("clue_id", "")),
            hook=str(data.get("hook", "")),
            planted_chapter=int(data.get("planted_chapter", 1)),
            target_resolution_window=win,
            stirred_chapters=list(data.get("stirred_chapters", [])),
            resolved_chapter=int(data["resolved_chapter"]) if data.get("resolved_chapter") is not None else None,
            lifecycle_status=str(data.get("lifecycle_status", "planted")),
            associated_character_ids=list(data.get("associated_character_ids", [])),
        )


@dataclass
class SubplotBranch:
    """Causal subplot thread tracking prerequisites, active status, and involvement."""
    line_id: str
    title: str
    category: str = "main"  # main, alliance, conflict, discovery, personal_arc
    status: str = "planned"  # planned, active, suspended, completed, dropped
    prerequisite_line_ids: List[str] = field(default_factory=list)
    participating_characters: List[str] = field(default_factory=list)
    chapters_active: List[int] = field(default_factory=list)

    def activate(self, chapter: int) -> None:
        self.status = "active"
        if chapter not in self.chapters_active:
            self.chapters_active.append(chapter)

    def complete(self) -> None:
        self.status = "completed"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SubplotBranch:
        return cls(
            line_id=str(data.get("line_id", "")),
            title=str(data.get("title", "")),
            category=str(data.get("category", "main")),
            status=str(data.get("status", "planned")),
            prerequisite_line_ids=list(data.get("prerequisite_line_ids", [])),
            participating_characters=list(data.get("participating_characters", [])),
            chapters_active=list(data.get("chapters_active", [])),
        )


@dataclass
class ChapterContinuityHandover:
    """Seamless baton pass capturing exact physical posture, wounds, and immediate tensions."""
    chapter: int
    ending_physical_scene: str = ""
    ending_location: str = ""
    unresolved_immediate_tensions: List[str] = field(default_factory=list)
    lingering_injuries: Dict[str, int] = field(default_factory=dict)  # char_id -> injury_level
    psychological_aftershocks: Dict[str, str] = field(default_factory=dict)  # char_id -> shock_state
    next_tick_obligations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChapterContinuityHandover:
        return cls(
            chapter=int(data.get("chapter", 1)),
            ending_physical_scene=str(data.get("ending_physical_scene", "")),
            ending_location=str(data.get("ending_location", "")),
            unresolved_immediate_tensions=list(data.get("unresolved_immediate_tensions", [])),
            lingering_injuries={k: int(v) for k, v in data.get("lingering_injuries", {}).items()},
            psychological_aftershocks=dict(data.get("psychological_aftershocks", {})),
            next_tick_obligations=list(data.get("next_tick_obligations", [])),
        )


class LivingPlotGraph:
    """Domain model governing foreshadowing convergence, subplots DAG, and chapter batons."""

    def __init__(
        self,
        foreshadowing: Optional[Dict[str, ForeshadowingItem]] = None,
        subplots: Optional[Dict[str, SubplotBranch]] = None,
        continuity_history: Optional[Dict[int, ChapterContinuityHandover]] = None,
    ) -> None:
        self.foreshadowing: Dict[str, ForeshadowingItem] = foreshadowing or {}
        self.subplots: Dict[str, SubplotBranch] = subplots or {}
        self.continuity_history: Dict[int, ChapterContinuityHandover] = continuity_history or {}

    def plant_clue(self, item: ForeshadowingItem) -> None:
        self.foreshadowing[item.clue_id] = item

    def stir_clue(self, clue_id: str, chapter: int) -> None:
        if clue_id in self.foreshadowing:
            self.foreshadowing[clue_id].stir(chapter)

    def resolve_clue(self, clue_id: str, chapter: int) -> None:
        if clue_id in self.foreshadowing:
            self.foreshadowing[clue_id].resolve(chapter)

    def get_overdue_clues(self, current_chapter: int) -> List[ForeshadowingItem]:
        return [clue for clue in self.foreshadowing.values() if clue.is_overdue(current_chapter)]

    def record_continuity(self, handover: ChapterContinuityHandover) -> None:
        self.continuity_history[handover.chapter] = handover

    def get_last_continuity(self, before_chapter: int) -> Optional[ChapterContinuityHandover]:
        past = sorted([c for c in self.continuity_history.keys() if c < before_chapter])
        if past:
            return self.continuity_history[past[-1]]
        return None

    def add_subplot(self, branch: SubplotBranch) -> None:
        """Register or update a subplot branch."""
        self.subplots[branch.line_id] = branch

    def validate_dependencies(self) -> List[str]:
        """Detect broken references or circular dependencies among subplots (DFS 3-color)."""
        errors: List[str] = []
        all_ids = set(self.subplots.keys())

        # Check broken prerequisites
        for lid, branch in self.subplots.items():
            for req in branch.prerequisite_line_ids:
                if req not in all_ids:
                    errors.append(f"Subplot [{lid}] refers to non-existent prerequisite [{req}].")

        # 3-color cycle detection: 0=unvisited, 1=visiting, 2=visited
        color: Dict[str, int] = {k: 0 for k in all_ids}

        def dfs(node: str, path: List[str]) -> bool:
            color[node] = 1
            for pre in self.subplots[node].prerequisite_line_ids:
                if pre in color:
                    if color[pre] == 1:
                        cycle_path = " -> ".join(path + [pre])
                        errors.append(f"Circular dependency detected in subplots: {cycle_path}")
                        return True
                    if color[pre] == 0:
                        if dfs(pre, path + [pre]):
                            return True
            color[node] = 2
            return False

        for k in all_ids:
            if color[k] == 0:
                dfs(k, [k])

        return errors

    def get_unblocked_subplots(self) -> List[SubplotBranch]:
        """Return planned subplots whose prerequisites are all completed."""
        completed_ids = {k for k, v in self.subplots.items() if v.status == "completed"}
        ready: List[SubplotBranch] = []
        for branch in self.subplots.values():
            if branch.status == "planned":
                if all(req in completed_ids for req in branch.prerequisite_line_ids):
                    ready.append(branch)
        return ready

    def get_active_threads_for_character(self, character_id: str) -> List[SubplotBranch]:
        """Retrieve all active or planned subplots involving a given character."""
        return [
            b for b in self.subplots.values()
            if character_id in b.participating_characters and b.status in ("planned", "active")
        ]

    def calculate_foreshadowing_health(self, current_chapter: int) -> Dict[str, Any]:
        """Analyze foreshadowing status, catching overdue clues and clues resolved without stir buildup."""
        active_count = 0
        overdue_count = 0
        unprompted_resolutions = 0  # clues resolved without ever being stirred

        for f in self.foreshadowing.values():
            if f.lifecycle_status != "resolved":
                active_count += 1
                if f.is_overdue(current_chapter):
                    overdue_count += 1
            else:
                if len(f.stirred_chapters) == 0 and (f.resolved_chapter or 0) > f.planted_chapter + 3:
                    unprompted_resolutions += 1

        return {
            "total_clues": len(self.foreshadowing),
            "active_clues": active_count,
            "overdue_clues": overdue_count,
            "unprompted_resolutions": unprompted_resolutions,
            "overdue_items": [f.to_dict() for f in self.get_overdue_clues(current_chapter)],
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "foreshadowing": {k: v.to_dict() for k, v in self.foreshadowing.items()},
            "subplots": {k: v.to_dict() for k, v in self.subplots.items()},
            "continuity_history": {str(k): v.to_dict() for k, v in self.continuity_history.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LivingPlotGraph:
        foreshadowing = {
            k: ForeshadowingItem.from_dict(v)
            for k, v in data.get("foreshadowing", {}).items()
        }
        subplots = {
            k: SubplotBranch.from_dict(v)
            for k, v in data.get("subplots", {}).items()
        }
        continuity = {
            int(k): ChapterContinuityHandover.from_dict(v)
            for k, v in data.get("continuity_history", {}).items()
        }
        return cls(
            foreshadowing=foreshadowing,
            subplots=subplots,
            continuity_history=continuity,
        )
