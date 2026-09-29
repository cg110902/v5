"""Industrial State Engine for Novel Studio 5.0 (engine/core/state.py).

Features:
1. 16 canonical state tables with atomic write & .corrupt isolation.
2. Transaction sentinel (.sync_pending) for crash recovery.
3. FIND-CT73 self-healing layer (numeric bounding, life_status canonicalization, ghost sweeping, entity auto-salvaging).
4. Co-occurrence matrix and entity timeline indices.
5. Per-chapter full immutable history snapshots (state/history/ch_XXX.json).
6. Direct integration with Domain Models (LivingCharacter, LivingGoldenFinger, LivingUniverse, LivingPlotGraph).

Universal & genre-agnostic. 100% Python standard library.
"""

from __future__ import annotations
import copy
from datetime import datetime
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from engine.core.storage import (
    atomic_write_json,
    ensure_directory,
    safe_load_json,
)
from engine.errors import GuardError, StorageError
from engine.domain.character import (
    LivingCharacter,
    ChapterMotive,
    PhysiologicalState,
    TrumpCard,
    ChapterTrumpDecision,
    Epistemology,
    DebtRelation,
)
from engine.domain.golden_finger import (
    LivingGoldenFinger,
    GoldenFingerStage,
    EnergyTransaction,
)
from engine.domain.universe import (
    LivingUniverse,
    SpatiotemporalGrid,
    MacroEvent,
)
from engine.domain.plot_graph import (
    LivingPlotGraph,
    ForeshadowingItem,
    SubplotBranch,
    ChapterContinuityHandover,
)

_SYNC_SENTINEL_NAME = ".sync_pending"

NUMERIC_FIELD_BOUNDS: Dict[str, Dict[str, Tuple[int, int]]] = {
    "persons": {
        "injury_level": (0, 5),
        "tier_rank": (1, 100),
        "stress_level": (0, 100),
        "stamina_pool": (0, 100),
    },
    "items": {
        "tier_rank": (1, 100),
        "condition": (0, 100),
        "max_charges": (0, 10000),
        "charges": (0, 10000),
    },
    "places": {
        "danger_level": (0, 10),
        "danger_tier": (0, 10),
    },
    "powers": {
        "current_energy": (-50, 100000),
        "backlash_severity": (0, 5),
    },
    "world": {
        "tension": (0, 100),
        "current_day": (1, 100000),
        "current_hour": (0, 23),
    },
    "debts": {
        "magnitude": (-100, 100),
    },
}

LIFE_STATUS_CANONICAL = {"alive", "deceased", "missing", "unknown"}


def write_sync_sentinel(workspace: Path, chapter_id: str) -> None:
    """Create atomic transaction sentinel before mutating tables."""
    sd = workspace / "state"
    ensure_directory(sd)
    sentinel = sd / _SYNC_SENTINEL_NAME
    atomic_write_json(sentinel, {
        "chapter_id": str(chapter_id),
        "pid": os.getpid(),
        "started_at": datetime.now().isoformat(timespec="seconds"),
    })


def clear_sync_sentinel(workspace: Path) -> None:
    """Remove transaction sentinel after commit or safe recovery."""
    sentinel = Path(workspace) / "state" / _SYNC_SENTINEL_NAME
    try:
        sentinel.unlink(missing_ok=True)
    except OSError:
        pass


def read_sync_sentinel(workspace: Path) -> Optional[Dict[str, Any]]:
    """Inspect active transaction sentinel, if any."""
    sentinel = Path(workspace) / "state" / _SYNC_SENTINEL_NAME
    if not sentinel.exists():
        return None
    try:
        return safe_load_json(sentinel, default=None)
    except Exception:
        return None


def heal_numeric_fields(rec: Dict[str, Any], table: str, eid: str, healed: List[str]) -> None:
    """Clamp out-of-bound numeric attributes and coerce string numbers."""
    bounds = NUMERIC_FIELD_BOUNDS.get(table) or {}
    for field, (lo, hi) in bounds.items():
        if field not in rec:
            continue
        val = rec[field]
        if isinstance(val, str):
            try:
                val = int(val)
                healed.append(f"H_NUM_COERCE: {table}[{eid}].{field} '{rec[field]}' -> {val}")
                rec[field] = val
            except ValueError:
                continue
        if isinstance(val, (int, float)):
            if val < lo:
                healed.append(f"H_NUM_BOUND: {table}[{eid}].{field} {val} < {lo} -> clamped to {lo}")
                rec[field] = lo
            elif val > hi:
                healed.append(f"H_NUM_BOUND: {table}[{eid}].{field} {val} > {hi} -> clamped to {hi}")
                rec[field] = hi


def heal_life_status_field(rec: Dict[str, Any], eid: str, healed: List[str]) -> None:
    """Normalize life status to canonical alive/deceased/missing/unknown."""
    raw = rec.get("life_status")
    if raw in (None, ""):
        return
    norm = str(raw).strip().lower()
    if norm not in LIFE_STATUS_CANONICAL:
        if any(w in norm for w in ("dead", "death", "die", "kill", "slain", "perish", "deceased")):
            norm = "deceased"
        elif "miss" in norm or "lost" in norm:
            norm = "missing"
        else:
            norm = "alive"
        healed.append(f"H_STATUS: persons[{eid}].life_status '{raw}' -> '{norm}'")
        rec["life_status"] = norm
    else:
        rec["life_status"] = norm


def sweep_ghost_records(records: Dict[str, Any], table_name: str, healed: List[str]) -> None:
    """Remove empty, nameless, or malformed ghost entries."""
    to_delete = []
    for k, v in list(records.items()):
        if not isinstance(v, dict) or not v or (not v.get("name") and not v.get("id") and not v.get("title")):
            to_delete.append(k)
    for k in to_delete:
        del records[k]
        healed.append(f"H_GHOST_SWEEP: purged empty/corrupted ghost entry '{k}' from {table_name}")


class StateManager:
    """Unified manager for Novel Studio 5.0's 16 state tables, indices, and snapshots."""

    def __init__(self, workspace: Union[str, Path]) -> None:
        self.workspace = Path(workspace).resolve()
        self.state_dir = self.workspace / "state"
        self.history_dir = self.state_dir / "history"
        self.indices_dir = self.state_dir / "indices"

        # Ensure directory structure
        ensure_directory(self.state_dir)
        ensure_directory(self.history_dir)
        ensure_directory(self.indices_dir)

        # 16 State Files
        self.persons_file = self.state_dir / "persons.json"
        self.items_file = self.state_dir / "items.json"
        self.factions_file = self.state_dir / "factions.json"
        self.places_file = self.state_dir / "places.json"
        self.lines_file = self.state_dir / "lines.json"
        self.locked_file = self.state_dir / "locked.json"
        self.ledger_file = self.state_dir / "ledger.json"
        self.current_file = self.state_dir / "current.json"
        self.milestones_file = self.state_dir / "milestones.json"
        self.timeline_file = self.state_dir / "timeline.json"
        self.debts_file = self.state_dir / "debts.json"
        self.relations_file = self.state_dir / "relations.json"
        self.clues_file = self.state_dir / "clues.json"
        self.synopsis_file = self.state_dir / "synopsis.json"
        self.powers_file = self.state_dir / "powers.json"
        self.world_file = self.state_dir / "world.json"

        # Indices
        self.co_occurrence_file = self.indices_dir / "co_occurrence.json"
        self.entity_timeline_file = self.indices_dir / "entity_timeline.json"

    # --- Generic Table Accessors ---
    def _get_dict(self, path: Path) -> Dict[str, Any]:
        return safe_load_json(path, default={})

    def _get_list(self, path: Path) -> List[Any]:
        return safe_load_json(path, default=[])

    def _save_data(self, path: Path, data: Any) -> None:
        atomic_write_json(path, data)

    # 16 Table Getters & Savers
    def get_persons(self) -> Dict[str, Any]: return self._get_dict(self.persons_file)
    def save_persons(self, data: Dict[str, Any]) -> None: self._save_data(self.persons_file, data)

    def get_items(self) -> Dict[str, Any]: return self._get_dict(self.items_file)
    def save_items(self, data: Dict[str, Any]) -> None: self._save_data(self.items_file, data)

    def get_factions(self) -> Dict[str, Any]: return self._get_dict(self.factions_file)
    def save_factions(self, data: Dict[str, Any]) -> None: self._save_data(self.factions_file, data)

    def get_places(self) -> Dict[str, Any]: return self._get_dict(self.places_file)
    def save_places(self, data: Dict[str, Any]) -> None: self._save_data(self.places_file, data)

    def get_lines(self) -> Dict[str, Any]: return self._get_dict(self.lines_file)
    def save_lines(self, data: Dict[str, Any]) -> None: self._save_data(self.lines_file, data)

    def get_locked_facts(self) -> List[Any]: return self._get_list(self.locked_file)
    def save_locked_facts(self, data: List[Any]) -> None: self._save_data(self.locked_file, data)

    def get_ledger(self) -> List[Any]: return self._get_list(self.ledger_file)
    def save_ledger(self, data: List[Any]) -> None: self._save_data(self.ledger_file, data)

    def get_current(self) -> Dict[str, Any]: return self._get_dict(self.current_file)
    def save_current(self, data: Dict[str, Any]) -> None: self._save_data(self.current_file, data)

    def get_milestones(self) -> List[Any]: return self._get_list(self.milestones_file)
    def save_milestones(self, data: List[Any]) -> None: self._save_data(self.milestones_file, data)

    def get_timeline(self) -> List[Any]: return self._get_list(self.timeline_file)
    def save_timeline(self, data: List[Any]) -> None: self._save_data(self.timeline_file, data)

    def get_debts(self) -> Dict[str, Any]: return self._get_dict(self.debts_file)
    def save_debts(self, data: Dict[str, Any]) -> None: self._save_data(self.debts_file, data)

    def get_relations(self) -> Dict[str, Any]: return self._get_dict(self.relations_file)
    def save_relations(self, data: Dict[str, Any]) -> None: self._save_data(self.relations_file, data)

    def get_clues(self) -> Dict[str, Any]: return self._get_dict(self.clues_file)
    def save_clues(self, data: Dict[str, Any]) -> None: self._save_data(self.clues_file, data)

    def get_synopsis(self) -> Dict[str, Any]: return self._get_dict(self.synopsis_file)
    def save_synopsis(self, data: Dict[str, Any]) -> None: self._save_data(self.synopsis_file, data)

    def get_powers(self) -> Dict[str, Any]: return self._get_dict(self.powers_file)
    def save_powers(self, data: Dict[str, Any]) -> None: self._save_data(self.powers_file, data)

    def get_world(self) -> Dict[str, Any]: return self._get_dict(self.world_file)
    def save_world(self, data: Dict[str, Any]) -> None: self._save_data(self.world_file, data)

    # --- Indices ---
    def get_co_occurrence(self) -> Dict[str, Any]: return self._get_dict(self.co_occurrence_file)
    def get_entity_timeline(self) -> Dict[str, Any]: return self._get_dict(self.entity_timeline_file)

    def update_co_occurrence(self, chapter_id: str, entity_ids: List[str]) -> None:
        """Record pairs of entities appearing together in the same chapter."""
        db = self.get_co_occurrence()
        clean_ids = sorted(list(set([eid for eid in entity_ids if eid])))
        for i in range(len(clean_ids)):
            for j in range(i + 1, len(clean_ids)):
                pair_key = f"{clean_ids[i]}::{clean_ids[j]}"
                entry = db.setdefault(pair_key, {
                    "entity_a": clean_ids[i],
                    "entity_b": clean_ids[j],
                    "count": 0,
                    "chapters": [],
                })
                entry["count"] += 1
                if chapter_id not in entry["chapters"]:
                    entry["chapters"].append(chapter_id)
        self._save_data(self.co_occurrence_file, db)

    def update_entity_timeline(self, chapter_id: str, present_entities: Dict[str, Dict[str, Any]]) -> None:
        """Record chronological trajectory snapshot for each present entity."""
        db = self.get_entity_timeline()
        for eid, snapshot in present_entities.items():
            entry = db.setdefault(eid, {
                "id": eid,
                "name": snapshot.get("name", eid),
                "appearances": [],
            })
            entry["appearances"].append({
                "chapter_id": chapter_id,
                "timestamp": datetime.now().isoformat(),
                "snapshot": snapshot,
            })
        self._save_data(self.entity_timeline_file, db)

    # --- Snapshots ---
    def save_chapter_snapshot(self, chapter_id: str) -> Path:
        """Create an immutable, full-state point-in-time snapshot for this chapter."""
        snap_data = {
            "chapter_id": str(chapter_id),
            "timestamp": datetime.now().isoformat(),
            "current": self.get_current(),
            "persons": self.get_persons(),
            "items": self.get_items(),
            "factions": self.get_factions(),
            "places": self.get_places(),
            "lines": self.get_lines(),
            "locked": self.get_locked_facts(),
            "debts": self.get_debts(),
            "relations": self.get_relations(),
            "clues": self.get_clues(),
            "synopsis": self.get_synopsis(),
            "powers": self.get_powers(),
            "world": self.get_world(),
        }
        target_path = self.history_dir / f"{chapter_id}.json"
        atomic_write_json(target_path, snap_data)
        return target_path

    # --- Domain Model Bridges ---
    def load_living_character(self, cid: str) -> Optional[LivingCharacter]:
        persons = self.get_persons()
        data = persons.get(cid)
        if not data:
            return None
        # Merge debts
        debts = self.get_debts().get(cid, {})
        data["debts"] = debts
        return LivingCharacter.from_dict(data)

    def save_living_character(self, char: LivingCharacter) -> None:
        persons = self.get_persons()
        char_dict = char.to_dict()
        # Extract debts to separate debts table
        debts_dict = char_dict.pop("debts", {})
        persons[char.character_id] = char_dict
        self.save_persons(persons)

        if debts_dict:
            debts = self.get_debts()
            debts[char.character_id] = debts_dict
            self.save_debts(debts)

    def load_living_golden_finger(self) -> Optional[LivingGoldenFinger]:
        powers = self.get_powers()
        gf_data = powers.get("golden_finger")
        if not gf_data:
            return None
        return LivingGoldenFinger.from_dict(gf_data)

    def save_living_golden_finger(self, gf: LivingGoldenFinger) -> None:
        powers = self.get_powers()
        powers["golden_finger"] = gf.to_dict()
        self.save_powers(powers)

    def load_living_universe(self) -> LivingUniverse:
        world = self.get_world()
        return LivingUniverse.from_dict(world)

    def save_living_universe(self, univ: LivingUniverse) -> None:
        self.save_world(univ.to_dict())

    def load_living_plot_graph(self) -> LivingPlotGraph:
        clues = self.get_clues()
        lines = self.get_lines()
        syn = self.get_synopsis()
        data = {
            "foreshadowing": clues,
            "subplots": lines,
            "continuity_history": syn.get("continuity_history", {}),
        }
        return LivingPlotGraph.from_dict(data)

    def save_living_plot_graph(self, pg: LivingPlotGraph) -> None:
        d = pg.to_dict()
        self.save_clues(d.get("foreshadowing", {}))
        self.save_lines(d.get("subplots", {}))
        syn = self.get_synopsis()
        syn["continuity_history"] = d.get("continuity_history", {})
        self.save_synopsis(syn)

    # --- Transactional Sync Pass ---
    def apply_fine_outline_delta(
        self,
        frontmatter: Dict[str, Any],
        word_count: int = 0,
        beats_body: str = "",
    ) -> Dict[str, Any]:
        """Atomically apply chapter beats and emergence delta to state tables."""
        chapter_id = str(frontmatter.get("chapter_id", "ch_001"))
        healed: List[str] = []
        warnings: List[str] = []

        # 1. Engage transaction sentinel
        write_sync_sentinel(self.workspace, chapter_id)

        try:
            # 2. Self-healing pass on current tables
            persons = self.get_persons()
            items = self.get_items()
            factions = self.get_factions()
            places = self.get_places()
            lines = self.get_lines()

            sweep_ghost_records(persons, "persons", healed)
            sweep_ghost_records(items, "items", healed)
            sweep_ghost_records(factions, "factions", healed)
            sweep_ghost_records(places, "places", healed)

            for pid, prec in persons.items():
                heal_numeric_fields(prec, "persons", pid, healed)
                heal_life_status_field(prec, pid, healed)

            for iid, irec in items.items():
                heal_numeric_fields(irec, "items", iid, healed)

            # 3. Process present characters & auto-salvage
            present_chars = frontmatter.get("characters", frontmatter.get("present_characters", []))
            all_present_ids = []
            present_snapshots: Dict[str, Dict[str, Any]] = {}

            for c in present_chars:
                cid = c.get("id") if isinstance(c, dict) else str(c)
                if not cid:
                    continue
                all_present_ids.append(cid)
                if cid not in persons:
                    # Auto-salvage entity
                    cname = c.get("name", cid) if isinstance(c, dict) else cid
                    persons[cid] = {
                        "id": cid,
                        "name": cname,
                        "role": "supporting",
                        "life_status": "alive",
                        "injury_level": 0,
                        "tier_rank": 1,
                    }
                    healed.append(f"H_SALVAGE: auto-salvaged missing character '{cid}' ({cname})")

                # Update character state if dict provided
                if isinstance(c, dict):
                    prec = persons[cid]
                    if "injury_level" in c: prec["injury_level"] = int(c["injury_level"])
                    if "life_status" in c: prec["life_status"] = str(c["life_status"])
                    heal_numeric_fields(prec, "persons", cid, healed)
                    heal_life_status_field(prec, cid, healed)
                    present_snapshots[cid] = copy.deepcopy(prec)

            # 4. Process new entities from emergence
            new_entities = frontmatter.get("new_entities", [])
            for ne in new_entities:
                if isinstance(ne, dict):
                    nid = ne.get("id")
                    ntype = ne.get("type", "person")
                    if nid and ntype == "person":
                        persons[nid] = ne
                        healed.append(f"H_EMERGENCE: registered emergent person '{nid}'")
                    elif nid and ntype == "item":
                        items[nid] = ne
                        healed.append(f"H_EMERGENCE: registered emergent item '{nid}'")

            # 5. Process state deltas (lines, clues, milestones)
            state_deltas = frontmatter.get("state_deltas", {})
            for lid in state_deltas.get("active_lines", []):
                if lid in lines:
                    lines[lid]["status"] = "active"

            # 6. Update current state pointer
            current = self.get_current()
            current["chapter_id"] = chapter_id
            current["volume_id"] = frontmatter.get("volume_id", current.get("volume_id", "vol_01"))
            current["last_synced_at"] = datetime.now().isoformat()
            if word_count > 0:
                current["word_count"] = word_count
                current.setdefault("total_words", 0)
                current["total_words"] = current.get("total_words", 0) + word_count

            # 7. Update ledger transaction record
            ledger = self.get_ledger()
            ledger_entry = {
                "chapter_id": chapter_id,
                "timestamp": datetime.now().isoformat(),
                "word_count": word_count,
                "healed_count": len(healed),
                "present_characters": all_present_ids,
            }
            ledger.append(ledger_entry)

            # 8. Save all updated tables
            self.save_persons(persons)
            self.save_items(items)
            self.save_factions(factions)
            self.save_places(places)
            self.save_lines(lines)
            self.save_current(current)
            self.save_ledger(ledger)

            # 9. Update co-occurrence and entity timeline
            self.update_co_occurrence(chapter_id, all_present_ids)
            self.update_entity_timeline(chapter_id, present_snapshots)

            # 10. Save immutable chapter history snapshot
            self.save_chapter_snapshot(chapter_id)

            # 11. Clear sentinel on success
            clear_sync_sentinel(self.workspace)

            return {
                "status": "success",
                "chapter_id": chapter_id,
                "healed": healed,
                "warnings": warnings,
                "present_characters": all_present_ids,
            }

        except Exception as e:
            # If failed, keep sentinel or report crash
            raise GuardError(
                f"State synchronization failed for chapter '{chapter_id}': {str(e)}",
                remediation="Check .sync_pending sentinel or recover from last history snapshot."
            ) from e
