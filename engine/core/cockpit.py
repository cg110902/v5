"""Novel Studio 5.0 Cockpit Telemetry and Real-Time Story Status Dashboard (engine/core/cockpit.py).

Zero literary hardcoding. 100% Python standard library.
"""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from engine.core.storage import safe_load_json


def render_cockpit(workspace: Union[str, Path]) -> str:
    """Generate a clean visual dashboard summarizing current novel telemetry."""
    ws = Path(workspace).resolve()
    state_dir = ws / "state"

    def _load(fname: str, default: Any) -> Any:
        p = state_dir / fname
        return safe_load_json(p, default=default) if p.exists() else default

    current = _load("current.json", {})
    persons = _load("persons.json", {})
    items = _load("items.json", {})
    lines = _load("lines.json", {})
    clues = _load("clues.json", {})
    powers = _load("powers.json", {})
    world = _load("world.json", {})
    ledger = _load("ledger.json", [])

    ch_id = current.get("chapter_id", "ch_001")
    vol_id = current.get("volume_id", "vol_01")
    total_words = current.get("total_words", 0)

    # Character metrics
    alive_count = sum(1 for p in persons.values() if isinstance(p, dict) and p.get("life_status") == "alive")
    deceased_count = sum(1 for p in persons.values() if isinstance(p, dict) and p.get("life_status") == "deceased")
    wounded = [
        f"{p.get('name', pid)} (Lvl {p.get('injury_level')})"
        for pid, p in persons.items()
        if isinstance(p, dict) and int(p.get("injury_level", 0)) >= 2 and p.get("life_status") == "alive"
    ]

    # Golden finger
    gf = powers.get("golden_finger", {})
    gf_name = gf.get("name", "N/A")
    gf_stage = gf.get("current_stage_id", "N/A")
    gf_energy = gf.get("current_energy", "N/A")
    gf_backlash = "YES" if gf.get("backlash_active") else "NO"

    # Universe
    clock = world.get("clock", {})
    day = clock.get("current_day", 1)
    hour = clock.get("current_hour", 8)
    diurnal = clock.get("diurnal_cycle", "morning")
    tension_map = world.get("regional_tension", {})
    hotspots = [f"{loc}:{score}" for loc, score in tension_map.items() if int(score) >= 50]

    # Plot & Clues
    active_lines = sum(1 for l in lines.values() if isinstance(l, dict) and l.get("status") == "active")
    overdue_clues = []
    m = re.search(r"(\d+)", ch_id)
    cnum = int(m.group(1)) if m else 1
    for kid, k in clues.items():
        if isinstance(k, dict) and k.get("lifecycle_status") != "resolved":
            win = k.get("target_resolution_window", [1, 100])
            if isinstance(win, (list, tuple)) and len(win) >= 2 and cnum > win[1]:
                overdue_clues.append(kid)

    protagonist = next((p.get("name", pid) for pid, p in persons.items() if isinstance(p, dict) and p.get("role") == "protagonist"), "N/A")

    lines_out = [
        "=" * 60,
        f"  NOVEL STUDIO 5.0 - TELEMETRY COCKPIT",
        "=" * 60,
        f" Current Position   : Volume [{vol_id}] | Chapter [{ch_id}]",
        f" Total Word Count   : {total_words:,} words (Ledger chapters: {len(ledger)})",
        "-" * 60,
        f" [Characters]       : Protagonist: {protagonist} | Alive: {alive_count} | Deceased: {deceased_count}",
        f"  Severe Wounds     : {', '.join(wounded) if wounded else 'None (all healthy)'}",
        "-" * 60,
        f" [Golden Finger]    : {gf_name} ({gf_stage})",
        f"  Energy Pool       : {gf_energy} | Backlash Active: {gf_backlash}",
        "-" * 60,
        f" [Spatiotemporal]   : Day {day}, {hour:02d}:00 ({diurnal})",
        f"  Tension Hotspots  : {', '.join(hotspots) if hotspots else 'Normal (No severe hotspots)'}",
        "-" * 60,
        f" [Plot Dynamics]    : Active Subplots: {active_lines}",
        f"  Overdue Clues     : {', '.join(overdue_clues) if overdue_clues else 'None (all on schedule)'}",
        "=" * 60,
    ]

    return "\n".join(lines_out)
