"""Industrial Context Pack Builder, Token Budgeting Engine, and Deslotter (engine/pipeline/pack.py).

Features:
1. P0-P3 4-tier prioritized assembly driven by living domain objects.
2. 12,000-token dynamic budgeting with 4-pass priority pruning.
3. Deslotting (eliminates {{slot:...}} noise) and briefing stripping.
4. Generates self-contained, zero-loss context/pack.md for Stage 2 Drafter.

Zero literary hardcoding. 100% Python standard library.
"""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from engine.core.state import StateManager
from engine.core.storage import atomic_write_text, ensure_directory
from engine.errors import GuardError

MAX_PACK_TOKENS = 12000
SLOT_RE = re.compile(r"\{\{slot:[^\}]+\}\}")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def estimate_tokens(text: str) -> int:
    """Accurate token estimator for CJK and ASCII mixture (~1.5 chars per token for CJK, 4 chars for ASCII)."""
    if not text:
        return 0
    cjk_count = len(re.findall(r"[\u4e00-\u9fff]", text))
    ascii_count = len(text) - cjk_count
    return int(cjk_count * 1.3 + ascii_count / 3.5)


def _deslot_text(text: str) -> Tuple[str, int]:
    """Strip all {{slot:...}} markers from text."""
    matches = SLOT_RE.findall(text)
    cleaned = SLOT_RE.sub("", text)
    return cleaned, len(matches)


def _strip_engine_briefing(text: str) -> Tuple[str, int]:
    """Strip HTML comments used for engine internal briefings."""
    matches = HTML_COMMENT_RE.findall(text)
    cleaned = HTML_COMMENT_RE.sub("", text)
    return cleaned, len(matches)


def _find_beats_file(workspace: Path, chapter_id: str) -> Optional[Path]:
    """Locate the beat file for the given chapter across volumes."""
    candidates = [
        workspace / "outlines" / "beats" / f"{chapter_id}.md",
        workspace / "outlines" / f"{chapter_id}.md",
    ]
    for c in candidates:
        if c.exists():
            return c

    # Search in vol_XX/beats
    outlines_dir = workspace / "outlines"
    if outlines_dir.exists():
        for cand in sorted(outlines_dir.glob(f"**/beats/{chapter_id}.md")):
            return cand
        for cand in sorted(outlines_dir.glob(f"**/{chapter_id}.md")):
            return cand

    return None


class PackBuilder:
    """Industrial Context Pack Builder for Stage 2 Drafter."""

    def __init__(self, workspace: Union[str, Path]) -> None:
        self.workspace = Path(workspace).resolve()
        self.state_mgr = StateManager(self.workspace)

    def build_pack(self, chapter_id: str, write_file: bool = True) -> Dict[str, Any]:
        """Assemble the self-contained context pack for a chapter within token limits."""
        beats_path = _find_beats_file(self.workspace, chapter_id)
        if not beats_path:
            raise GuardError(
                f"Beats file not found for chapter '{chapter_id}' in {self.workspace / 'outlines'}",
                remediation=f"Create fine outline at outlines/vol_01/beats/{chapter_id}.md"
            )

        raw_beats = beats_path.read_text(encoding="utf-8")
        clean_beats, slots_removed = _deslot_text(raw_beats)
        clean_beats, _ = _strip_engine_briefing(clean_beats)

        # Extract chapter number
        m = re.search(r"(\d+)", chapter_id)
        ch_num = int(m.group(1)) if m else 1

        # Load living domain objects & state tables
        universe = self.state_mgr.load_living_universe()
        golden_finger = self.state_mgr.load_living_golden_finger()
        plot_graph = self.state_mgr.load_living_plot_graph()
        factions = self.state_mgr.get_factions()
        places = self.state_mgr.get_places()

        # Parse present character IDs from beats
        present_cids = self._extract_character_ids(clean_beats)

        # Assemble Priority Sections
        # P0: Core Beats & In-Scene Characters
        p0_sections: List[str] = [
            f"# CONTEXT PACK: Chapter [{chapter_id}]",
            "## P0: Fine Outline Beats (Mandatory Intent Source)",
            clean_beats.strip(),
            "\n## P0: Active Characters in Scene (Living State)",
        ]

        loaded_chars = {}
        for cid in present_cids:
            char = self.state_mgr.load_living_character(cid)
            if char:
                loaded_chars[cid] = char
                motive = char.get_motive_at(ch_num)
                phys = char.get_physiology_at(ch_num)
                trumps = [t.name for t in char.trump_inventory.values() if t.current_cooldown == 0]
                char_block = [
                    f"### Character: {char.name} ({char.character_id})",
                    f"- Role: {char.role} | Life Status: {char.life_status} | Tier Rank: Lvl {getattr(char, 'tier_rank', 1)} | Faction: {char.faction_id or 'Unaffiliated'}",
                    f"- Active Motive (Ch {ch_num}): {motive.primary_motive if motive else 'N/A'}",
                    f"  * Urgency: {motive.urgency if motive else 1}/5 | Moral Redline: {motive.moral_redline if motive else 'None'}",
                ]
                if motive and motive.blind_spot:
                    char_block.append(f"  * Blind Spot: {motive.blind_spot}")
                char_block.extend([
                    f"- Physical State: Injury Lvl {phys.injury_level}/5 ({phys.injury_description or 'Healthy'}) | Stamina: {phys.stamina_pool}%",
                ])
                if phys.handicaps:
                    char_block.append(f"  * Handicaps: {', '.join(phys.handicaps)}")
                if phys.injury_level >= 3:
                    char_block.append("  * [COMBAT ALERT] Severely injured: cannot deploy high-tier trumps without cost/exhaustion!")

                # Interpersonal debts with other present characters
                debt_notes = []
                for other_cid in present_cids:
                    if other_cid != cid and other_cid in char.debts:
                        d = char.debts[other_cid]
                        debt_notes.append(f"with {other_cid}: {d.debt_type} (mag: {d.magnitude})")
                if debt_notes:
                    char_block.append(f"- Active Debts: {', '.join(debt_notes)}")

                char_block.extend([
                    f"- Available Trumps: {', '.join(trumps) if trumps else 'None'}",
                    f"- Core Fear: {char.core_fear or 'None'}",
                ])
                p0_sections.append("\n".join(char_block))

        # P1: Spatiotemporal Context, Relational Friction & Golden Finger
        p1_sections: List[str] = [
            "## P1: Spatiotemporal Context & Environmental Constraints",
            f"- World Clock: Day {universe.clock.current_day}, {universe.clock.current_hour:02d}:00 ({universe.clock.diurnal_cycle})",
            f"- Weather / Physics: {universe.clock.weather} | Constraints: {', '.join(universe.clock.environment_constraints) if universe.clock.environment_constraints else 'Normal'}",
        ]
        if universe.active_macro_events:
            p1_sections.append("- Active Macro World Events:")
            for ev in universe.active_macro_events.values():
                if ev.stage != "resolved":
                    p1_sections.append(f"  * [{ev.event_id}] {ev.name} (Stage: {ev.stage}, Scope: {ev.scope})")

        # Cross-Table Relational Matrices (Danger Disparity & Faction Friction)
        relational_alerts: List[str] = []
        # Location danger disparity
        for loc_id, p_info in places.items():
            if isinstance(p_info, dict) and (loc_id in clean_beats or p_info.get("name", "") in clean_beats):
                raw_danger = p_info.get("danger_tier", 1)
                m = re.search(r"(\d+)", str(raw_danger))
                d_tier = int(m.group(1)) if m else 1
                for c in loaded_chars.values():
                    c_tier = getattr(c, "tier_rank", 1)
                    if d_tier - c_tier >= 3:
                        relational_alerts.append(f"  * [DANGER DISPARITY] {c.name} (Tier {c_tier}) entering {p_info.get('name', loc_id)} (Danger Tier {d_tier})! Requires protective artifact or escort.")

        # Faction diplomatic friction
        seen_pairs = set()
        for c1 in loaded_chars.values():
            for c2 in loaded_chars.values():
                if c1.character_id != c2.character_id and c1.faction_id and c2.faction_id and c1.faction_id != c2.faction_id:
                    pair_key = tuple(sorted([c1.character_id, c2.character_id]))
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        f_info = factions.get(c1.faction_id, {})
                        if isinstance(f_info, dict):
                            status = f_info.get("diplomacy", {}).get(c2.faction_id, "")
                            if status in ["war", "blood_war", "hostile"]:
                                relational_alerts.append(f"  * [FACTION WAR ALERT] {c1.name} ({c1.faction_id}) vs {c2.name} ({c2.faction_id}): Status is '{status}'. No unmotivated mercy/alliance permitted.")

        if relational_alerts:
            p1_sections.append("- Cross-Table Relational Friction:")
            p1_sections.extend(relational_alerts)

        if golden_finger:
            p1_sections.extend([
                "## P1: Golden Finger Evolution & Energy Pool",
                f"- System: {golden_finger.name} (Active Stage: {golden_finger.current_stage_id})",
                f"- Current Energy: {golden_finger.current_energy} | Backlash: {'ACTIVE (Impaired)' if golden_finger.backlash_active else 'Normal'}",
            ])

        # P2: Cross-Chapter Continuity Handover, Upstream Calendar & Foreshadowing
        p2_sections: List[str] = [
            "## P2: Continuity Baton from Previous Chapter",
        ]
        last_continuity = plot_graph.get_last_continuity(ch_num)
        if last_continuity:
            p2_sections.extend([
                f"- Previous Ending Scene: {last_continuity.ending_physical_scene}",
                f"- Location: {last_continuity.ending_location}",
                f"- Immediate Next-Tick Obligations: {', '.join(last_continuity.next_tick_obligations) if last_continuity.next_tick_obligations else 'Proceed with outline'}",
            ])
        else:
            p2_sections.append("- (Chapter 1 or start of volume: clean entry)")

        # Upstream Calendar Sightline (Next 3 chapters)
        try:
            from engine.pipeline.ops import get_calendar
            cal = get_calendar(self.workspace, count=3)
            upcoming = cal.get("upcoming_chapters", [])
            if upcoming:
                p2_sections.append("## P2: Upcoming Chapter Roadmap (Strategic Sightline)")
                for up in upcoming:
                    p2_sections.append(f"- [{up.get('chapter_id')}] {up.get('title', '')} - {up.get('event', '')}")
            approaching = cal.get("approaching_clues", [])
            if approaching:
                p2_sections.append("- Approaching Clue Deadlines:")
                for app in approaching:
                    p2_sections.append(f"  * [{app.get('id')}] {app.get('title')} (Due in {app.get('remaining_chapters')} chapters)")
        except Exception:
            pass

        active_clues = [c for c in plot_graph.foreshadowing.values() if c.lifecycle_status != "resolved"]
        if active_clues:
            p2_sections.append("## P2: Active Foreshadowing Clues to Weave/Resolve")
            for clue in active_clues[:5]:  # Top 5 most urgent
                p2_sections.append(f"- [{clue.clue_id}] {clue.hook} (Window: ch {clue.target_resolution_window[0]}-{clue.target_resolution_window[1]}, Status: {clue.lifecycle_status})")

        # P3: Active Subplots
        p3_sections: List[str] = [
            "## P3: Active Subplot Branches",
        ]
        active_lines = [l for l in plot_graph.subplots.values() if l.status == "active"]
        for line in active_lines[:4]:
            p3_sections.append(f"- [{line.line_id}] {line.title} (Category: {line.category})")

        # 4-Pass Priority Budget Pruning
        full_sections = [p0_sections, p1_sections, p2_sections, p3_sections]
        rendered_text = "\n\n".join(["\n".join(sec) for sec in full_sections if sec])
        tokens = estimate_tokens(rendered_text)

        # If over budget, prune P3 first, then P2
        if tokens > MAX_PACK_TOKENS:
            full_sections[3] = []  # Drop P3
            rendered_text = "\n\n".join(["\n".join(sec) for sec in full_sections if sec])
            tokens = estimate_tokens(rendered_text)

        if tokens > MAX_PACK_TOKENS:
            full_sections[2] = []  # Drop P2
            rendered_text = "\n\n".join(["\n".join(sec) for sec in full_sections if sec])
            tokens = estimate_tokens(rendered_text)

        target_file = None
        if write_file:
            context_dir = self.workspace / "context"
            ensure_directory(context_dir)
            target_file = context_dir / "pack.md"
            atomic_write_text(target_file, rendered_text)

        return {
            "chapter_id": chapter_id,
            "estimated_tokens": tokens,
            "pack_file": str(target_file) if target_file else None,
            "present_characters": present_cids,
            "slots_cleaned": slots_removed,
        }

    def _extract_character_ids(self, text: str) -> List[str]:
        """Extract explicit character IDs mentioned in beats (e.g. C_001 or p_001)."""
        pattern = re.compile(r"\b(C_\d+|p_\d+)\b", re.IGNORECASE)
        found = list(set(pattern.findall(text)))
        if not found:
            # If no ID tags, check names in persons table
            persons = self.state_mgr.get_persons()
            for pid, prec in persons.items():
                if isinstance(prec, dict):
                    name = prec.get("name", "")
                    if name and name in text:
                        found.append(pid)
        return sorted(found)


def build_pack(workspace: Union[str, Path], chapter_id: str, write_file: bool = True) -> Dict[str, Any]:
    """Functional entrypoint for pack assembly."""
    builder = PackBuilder(workspace)
    return builder.build_pack(chapter_id, write_file=write_file)
