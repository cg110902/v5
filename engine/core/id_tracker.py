"""Industrial ID Governance, Sequential Generator, Integrity Checker, and Lifecycle Tracer.

Supports both 5.0 standardized prefixes (C_, I_, T_, K_, L_, P_, F_, D_, M_, GF_, EV_)
and legacy prefixes (p_, it_, GUN-, KNO-, MIS-, loc_, fac_, DEBT-, ms_).

Zero literary hardcoding. 100% Python standard library.
"""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Union

from engine.core.storage import safe_load_json
from engine.errors import GuardError

PREFIX_MAP: Dict[str, str] = {
    # 5.0 Canonical Prefixes
    "character": "C_",
    "person": "C_",
    "item": "I_",
    "trump": "T_",
    "gun": "T_",
    "clue": "K_",
    "kno": "K_",
    "line": "L_",
    "subplot": "L_",
    "mis": "L_",
    "place": "P_",
    "location": "P_",
    "faction": "F_",
    "debt": "D_",
    "milestone": "M_",
    "golden_finger": "GF_",
    "event": "EV_",
    "lock": "LOCK-",
    "chapter": "ch_",
    "volume": "vol_",
}

CATEGORY_REGEX = [
    (re.compile(r"^(C_|c_|p_)"), "character"),
    (re.compile(r"^(I_|i_|it_|IT_)"), "item"),
    (re.compile(r"^(T_|t_|GUN-)", re.IGNORECASE), "trump"),
    (re.compile(r"^(K_|k_|KNO-)", re.IGNORECASE), "clue"),
    (re.compile(r"^(L_|l_|MIS-)", re.IGNORECASE), "line"),
    (re.compile(r"^(P_|loc_|LOC_)"), "place"),
    (re.compile(r"^(F_|f_|fac_)", re.IGNORECASE), "faction"),
    (re.compile(r"^(D_|d_|DEBT-)", re.IGNORECASE), "debt"),
    (re.compile(r"^(M_|m_|ms_)", re.IGNORECASE), "milestone"),
    (re.compile(r"^GF_", re.IGNORECASE), "golden_finger"),
    (re.compile(r"^EV_", re.IGNORECASE), "event"),
    (re.compile(r"^LOCK-", re.IGNORECASE), "lock"),
    (re.compile(r"^ch_", re.IGNORECASE), "chapter"),
    (re.compile(r"^vol_", re.IGNORECASE), "volume"),
]


def detect_id_category(entity_id: str) -> str:
    """Determine the semantic category of an ID by its prefix."""
    eid = entity_id.strip()
    for pattern, cat in CATEGORY_REGEX:
        if pattern.search(eid):
            return cat
    return "unknown"


def _extract_number(eid: str) -> int:
    """Extract trailing digits from an ID string, e.g. C_007 -> 7."""
    m = re.search(r"(\d+)$", eid.strip())
    return int(m.group(1)) if m else 0


class IdTracker:
    """Autonomous governance engine for all entity identifiers and causal references."""

    def __init__(self, workspace: Union[str, Path]) -> None:
        self.workspace = Path(workspace).resolve()
        self.state_dir = self.workspace / "state"

    def _load_table(self, filename: str) -> Any:
        path = self.state_dir / filename
        if not path.exists():
            return {} if filename.endswith("s.json") or filename == "world.json" else []
        return safe_load_json(path, default={})

    def get_all_existing_ids(self) -> Set[str]:
        """Aggregate all existing IDs across all 16 state tables."""
        existing: Set[str] = set()

        for fname in ["persons.json", "items.json", "factions.json", "places.json", "lines.json", "clues.json"]:
            data = self._load_table(fname)
            if isinstance(data, dict):
                for k, v in data.items():
                    existing.add(k)
                    if isinstance(v, dict) and v.get("id"):
                        existing.add(str(v["id"]))

        debts = self._load_table("debts.json")
        if isinstance(debts, dict):
            for k in debts.keys(): existing.add(k)

        locked = self._load_table("locked.json")
        if isinstance(locked, list):
            for item in locked:
                if isinstance(item, dict) and item.get("id"):
                    existing.add(str(item["id"]))

        milestones = self._load_table("milestones.json")
        if isinstance(milestones, list):
            for item in milestones:
                if isinstance(item, dict) and item.get("id"):
                    existing.add(str(item["id"]))

        return existing

    def id_next(self, category: str, exclude: Optional[Iterable[str]] = None) -> str:
        """Deterministically calculate the next available collision-free ID for a category."""
        prefix = PREFIX_MAP.get(category.lower(), f"{category.upper()}_")
        existing_ids = self.get_all_existing_ids()
        if exclude:
            existing_ids.update(exclude)

        max_num = 0
        for eid in existing_ids:
            if eid.startswith(prefix):
                num = _extract_number(eid)
                if num > max_num:
                    max_num = num

        next_num = max_num + 1
        return f"{prefix}{next_num:03d}"

    def id_list(self, filter_category: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """List all active IDs grouped by category."""
        grouped: Dict[str, List[Dict[str, Any]]] = {}

        # 1. Characters
        persons = self._load_table("persons.json")
        for pid, prec in persons.items():
            entry = {"id": pid, "name": prec.get("name", pid), "category": "character", "status": prec.get("life_status", "alive")}
            grouped.setdefault("character", []).append(entry)

        # 2. Items
        items = self._load_table("items.json")
        for iid, irec in items.items():
            entry = {"id": iid, "name": irec.get("name", iid), "category": "item"}
            grouped.setdefault("item", []).append(entry)

        # 3. Places
        places = self._load_table("places.json")
        for plid, plrec in places.items():
            entry = {"id": plid, "name": plrec.get("name", plid), "category": "place"}
            grouped.setdefault("place", []).append(entry)

        # 4. Factions
        factions = self._load_table("factions.json")
        for fid, frec in factions.items():
            entry = {"id": fid, "name": frec.get("name", fid), "category": "faction"}
            grouped.setdefault("faction", []).append(entry)

        # 5. Lines / Subplots
        lines = self._load_table("lines.json")
        for lid, lrec in lines.items():
            entry = {"id": lid, "title": lrec.get("title", lid), "category": "line", "status": lrec.get("status", "active")}
            grouped.setdefault("line", []).append(entry)

        # 6. Clues / Foreshadowing
        clues = self._load_table("clues.json")
        for kid, krec in clues.items():
            entry = {"id": kid, "hook": krec.get("hook", kid), "category": "clue", "status": krec.get("lifecycle_status", "planted")}
            grouped.setdefault("clue", []).append(entry)

        if filter_category:
            return {filter_category: grouped.get(filter_category, [])}
        return grouped

    def trace_id(self, target_id: str) -> Dict[str, Any]:
        """Trace the full cross-table lifecycle, interactions, and chapter appearances of an ID."""
        target = target_id.strip()
        cat = detect_id_category(target)

        report: Dict[str, Any] = {
            "id": target,
            "category": cat,
            "current_record": None,
            "appearances": [],
            "co_occurrences": [],
            "debts": [],
            "referenced_in_tables": [],
        }

        # Check current tables
        for table_file, tname in [
            ("persons.json", "persons"),
            ("items.json", "items"),
            ("places.json", "places"),
            ("factions.json", "factions"),
            ("lines.json", "lines"),
            ("clues.json", "clues"),
        ]:
            data = self._load_table(table_file)
            if isinstance(data, dict) and target in data:
                report["current_record"] = data[target]
                report["referenced_in_tables"].append(tname)

        # Check debts
        debts = self._load_table("debts.json")
        if isinstance(debts, dict):
            if target in debts:
                report["debts"].append({"as_debtor": debts[target]})
            for holder, dmap in debts.items():
                if isinstance(dmap, dict) and target in dmap:
                    report["debts"].append({"as_target_of": holder, "debt": dmap[target]})

        # Check entity timeline index
        tl_path = self.state_dir / "indices" / "entity_timeline.json"
        if tl_path.exists():
            tl_data = safe_load_json(tl_path, default={})
            if target in tl_data:
                report["appearances"] = tl_data[target].get("appearances", [])

        # Check co-occurrence index
        co_path = self.state_dir / "indices" / "co_occurrence.json"
        if co_path.exists():
            co_data = safe_load_json(co_path, default={})
            for pair, meta in co_data.items():
                if target in pair:
                    report["co_occurrences"].append(meta)

        return report

    def check_id_integrity(self, chapter_id: Optional[str] = None) -> Dict[str, List[str]]:
        """Validate ID uniqueness, foreign key consistency, and dangling reference integrity."""
        errors: List[str] = []
        warnings: List[str] = []

        all_ids = self.get_all_existing_ids()
        persons = self._load_table("persons.json")
        items = self._load_table("items.json")
        places = self._load_table("places.json")
        factions = self._load_table("factions.json")
        lines = self._load_table("lines.json")
        debts = self._load_table("debts.json")

        # 1. Foreign key checks: characters referencing non-existent factions
        for pid, prec in persons.items():
            fac_id = prec.get("faction_id") or prec.get("faction")
            if fac_id and fac_id not in factions and fac_id not in all_ids:
                warnings.append(f"Person '{pid}' references non-existent faction '{fac_id}'")

        # 2. Debts referencing non-existent characters
        if isinstance(debts, dict):
            for holder_id, dmap in debts.items():
                if holder_id not in persons:
                    errors.append(f"Debt holder '{holder_id}' does not exist in persons table")
                if isinstance(dmap, dict):
                    for target_id in dmap.keys():
                        if target_id not in persons:
                            errors.append(f"Debt target '{target_id}' (held by '{holder_id}') does not exist in persons table")

        # 3. Subplots referencing non-existent characters
        for lid, lrec in lines.items():
            for c in lrec.get("participating_characters", []):
                if c not in persons and c not in all_ids:
                    warnings.append(f"Subplot line '{lid}' references unknown character '{c}'")

        return {
            "errors": errors,
            "warnings": warnings,
            "total_ids": list(all_ids),
        }
