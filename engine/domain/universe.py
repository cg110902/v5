"""Domain model for LivingUniverse, SpatiotemporalGrid, MacroEventNetwork, and RegionalTension.

Universal & genre-agnostic: uses structural keys, integer time coordinates, and zero hardcoded Chinese literary terms.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class SpatiotemporalGrid:
    """Rigid spatiotemporal coordinates and local environmental physical parameters."""
    current_day: int = 1
    current_hour: int = 8  # 0 to 23
    diurnal_cycle: str = "morning"  # dawn, morning, noon, afternoon, dusk, night, midnight
    weather: str = "clear"
    environment_constraints: List[str] = field(default_factory=list)  # e.g. ["visibility_low", "anti_flight_barrier"]

    def advance_hours(self, hours: int) -> None:
        self.current_hour += hours
        days_passed = self.current_hour // 24
        self.current_day += days_passed
        self.current_hour = self.current_hour % 24
        self._update_diurnal_cycle()

    def _update_diurnal_cycle(self) -> None:
        h = self.current_hour
        if 5 <= h < 7:
            self.diurnal_cycle = "dawn"
        elif 7 <= h < 12:
            self.diurnal_cycle = "morning"
        elif 12 <= h < 14:
            self.diurnal_cycle = "noon"
        elif 14 <= h < 18:
            self.diurnal_cycle = "afternoon"
        elif 18 <= h < 20:
            self.diurnal_cycle = "dusk"
        elif 20 <= h < 24:
            self.diurnal_cycle = "night"
        else:
            self.diurnal_cycle = "midnight"

    @property
    def day_phase(self) -> str:
        return self.diurnal_cycle

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SpatiotemporalGrid:
        return cls(
            current_day=int(data.get("current_day", 1)),
            current_hour=int(data.get("current_hour", 8)),
            diurnal_cycle=str(data.get("diurnal_cycle", "morning")),
            weather=str(data.get("weather", "clear")),
            environment_constraints=list(data.get("environment_constraints", [])),
        )


@dataclass
class MacroEvent:
    """Geopolitical macro event running in the background of the universe."""
    event_id: str
    name: str = ""
    scope: str = "regional"  # local, regional, continental, global, planar
    stage: str = "brewing"  # brewing, erupting, peaking, aftermath, resolved
    start_chapter: int = 1
    expected_end_chapter: int = 10
    regional_tension_impact: int = 20  # Delta to local tension
    affected_factions: List[str] = field(default_factory=list)
    affected_locations: List[str] = field(default_factory=list)
    ripples_for_chapter: str = ""

    def __init__(
        self,
        event_id: str,
        name: str = "",
        title: str = "",
        scope: str = "regional",
        stage: str = "brewing",
        start_chapter: int = 1,
        trigger_chapter: Optional[int] = None,
        expected_end_chapter: int = 10,
        peak_chapter: Optional[int] = None,
        regional_tension_impact: int = 20,
        tension_delta: Optional[int] = None,
        affected_factions: Optional[List[str]] = None,
        affected_locations: Optional[List[str]] = None,
        affected_regions: Optional[List[str]] = None,
        ripples_for_chapter: str = "",
    ):
        self.event_id = str(event_id)
        self.name = str(name or title)
        self.scope = str(scope)
        self.stage = str(stage)
        self.start_chapter = int(trigger_chapter if trigger_chapter is not None else start_chapter)
        self.expected_end_chapter = int(peak_chapter if peak_chapter is not None else expected_end_chapter)
        self.regional_tension_impact = int(tension_delta if tension_delta is not None else regional_tension_impact)
        self.affected_factions = list(affected_factions or [])
        locs = affected_locations or affected_regions or []
        self.affected_locations = list(locs)
        self.ripples_for_chapter = str(ripples_for_chapter)

    @property
    def title(self) -> str:
        return self.name

    @property
    def trigger_chapter(self) -> int:
        return self.start_chapter

    @property
    def peak_chapter(self) -> int:
        return self.expected_end_chapter

    @property
    def tension_delta(self) -> int:
        return self.regional_tension_impact

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MacroEvent:
        return cls(
            event_id=str(data.get("event_id", "")),
            name=str(data.get("name") or data.get("title") or ""),
            scope=str(data.get("scope", "regional")),
            stage=str(data.get("stage", "brewing")),
            start_chapter=int(data.get("start_chapter", data.get("trigger_chapter", 1))),
            expected_end_chapter=int(data.get("expected_end_chapter", data.get("peak_chapter", 10))),
            regional_tension_impact=int(data.get("regional_tension_impact", data.get("tension_delta", 20))),
            affected_factions=list(data.get("affected_factions", [])),
            affected_locations=list(data.get("affected_locations", data.get("affected_regions", []))),
            ripples_for_chapter=str(data.get("ripples_for_chapter", "")),
        )


class LivingUniverse:
    """Domain model tracking environmental physics, world clock, and macro world events."""

    def __init__(
        self,
        universe_id: str = "universe_prime",
        clock: Optional[SpatiotemporalGrid] = None,
        active_macro_events: Optional[Dict[str, MacroEvent]] = None,
        regional_tension: Optional[Dict[str, int]] = None,
        location_states: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        self.universe_id = str(universe_id)
        self.clock: SpatiotemporalGrid = clock or SpatiotemporalGrid()
        self.active_macro_events: Dict[str, MacroEvent] = active_macro_events or {}
        self.regional_tension: Dict[str, int] = regional_tension or {}  # location_id -> 0..100
        self.location_states: Dict[str, Dict[str, Any]] = location_states or {}

    @property
    def tension(self) -> int:
        """Average regional tension across universe locations, defaulting to 20."""
        if not self.regional_tension:
            return 20
        return sum(self.regional_tension.values()) // len(self.regional_tension)

    def get_tension(self, location_id: str) -> int:
        return self.regional_tension.get(location_id, 0)

    def set_tension(self, location_id: str, score: int) -> None:
        self.regional_tension[location_id] = max(0, min(100, score))

    @property
    def macro_events(self) -> Dict[str, MacroEvent]:
        return self.active_macro_events

    def add_macro_event(self, event: MacroEvent) -> None:
        """Alias for trigger_macro_event."""
        self.trigger_macro_event(event)

    def trigger_macro_event(self, event: MacroEvent) -> None:
        self.active_macro_events[event.event_id] = event
        for loc in event.affected_locations:
            current = self.get_tension(loc)
            self.set_tension(loc, current + event.regional_tension_impact)

    def update_event_stage(self, event_id: str, new_stage: str) -> None:
        if event_id in self.active_macro_events:
            event = self.active_macro_events[event_id]
            event.stage = new_stage
            if new_stage == "resolved":
                # Alleviate tension
                for loc in event.affected_locations:
                    current = self.get_tension(loc)
                    self.set_tension(loc, current - event.regional_tension_impact)

    def get_events_affecting_location(self, location_id: str) -> List[MacroEvent]:
        return [
            ev for ev in self.active_macro_events.values()
            if location_id in ev.affected_locations and ev.stage != "resolved"
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "universe_id": self.universe_id,
            "clock": self.clock.to_dict(),
            "active_macro_events": {k: v.to_dict() for k, v in self.active_macro_events.items()},
            "regional_tension": self.regional_tension,
            "location_states": self.location_states,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LivingUniverse:
        clock = SpatiotemporalGrid.from_dict(data.get("clock", {}))
        events = {
            k: MacroEvent.from_dict(v)
            for k, v in data.get("active_macro_events", {}).items()
        }
        return cls(
            universe_id=str(data.get("universe_id", "universe_prime")),
            clock=clock,
            active_macro_events=events,
            regional_tension={k: int(v) for k, v in data.get("regional_tension", {}).items()},
            location_states=dict(data.get("location_states", {})),
        )
