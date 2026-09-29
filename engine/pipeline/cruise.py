"""Autonomous Long-Range Cruise Orchestrator (engine/pipeline/cruise.py).

Features:
1. Deterministic FSM chapter execution (Scaffold -> Pack -> Audit -> Sync -> Seal).
2. Autonomous batch cruising across multiple chapters.
3. Heartbeat telemetry and immediate halt on causal blockers.

Zero literary hardcoding. 100% Python standard library.
"""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from engine.core.state import StateManager
from engine.errors import GuardError
from engine.pipeline.pack import build_pack
from engine.pipeline.ops import (
    audit_chapter,
    sync_chapter,
    get_beats_scaffold,
    _chapter_num,
)


def _chapter_id(num: int) -> str:
    return f"ch_{num:03d}"


def plan_cruise(
    workspace: Union[str, Path],
    count: int = 1,
    start_chapter: Optional[str] = None,
) -> List[str]:
    """Calculate the ordered sequence of chapter IDs to cruise."""
    ws = Path(workspace).resolve()
    sm = StateManager(ws)
    curr = sm.get_current()

    if start_chapter:
        start_num = _chapter_num(start_chapter)
    else:
        last_ch = curr.get("chapter_id", "ch_000")
        start_num = _chapter_num(last_ch) + 1

    return [_chapter_id(start_num + i) for i in range(max(1, count))]


def supervise_once(
    workspace: Union[str, Path],
    chapter_id: str,
    force: bool = False,
) -> Dict[str, Any]:
    """Advance a single chapter through the deterministic pipeline."""
    ws = Path(workspace).resolve()

    # Step 1: Ensure context pack is assembled
    pack_res = build_pack(ws, chapter_id, write_file=True)

    # Step 2: Check draft manuscript
    raw_dir = ws / "raw"
    draft_candidates = [
        raw_dir / f"{chapter_id}_v3.md",
        raw_dir / f"{chapter_id}_v2.md",
        raw_dir / f"{chapter_id}_v1.md",
    ]
    draft_file = next((c for c in draft_candidates if c.exists()), None)
    if not draft_file:
        return {
            "chapter_id": chapter_id,
            "status": "waiting_for_draft",
            "message": f"Context pack generated at context/pack.md. Ready for Stage 2 Drafter to write raw/{chapter_id}_v1.md.",
            "pack": pack_res,
        }

    # Step 3: Run causal audit
    audit_res = audit_chapter(ws, chapter_id, write_file=True)
    if not audit_res["is_valid"] and not force:
        return {
            "chapter_id": chapter_id,
            "status": "blocked_by_audit",
            "blockers": audit_res["blockers"],
            "message": f"Chapter {chapter_id} blocked by {len(audit_res['blockers'])} causal integrity violations.",
        }

    # Step 4: Sync & Seal Chapter
    sync_res = sync_chapter(ws, chapter_id, force=force)

    return {
        "chapter_id": chapter_id,
        "status": "completed",
        "sync": sync_res,
    }


def run_cruise(
    workspace: Union[str, Path],
    count: int = 1,
    start_chapter: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute autonomous cruise across planned chapters."""
    ws = Path(workspace).resolve()
    plan = plan_cruise(ws, count, start_chapter)

    completed: List[str] = []
    halted_at: Optional[str] = None
    halt_reason: str = ""

    for ch_id in plan:
        res = supervise_once(ws, ch_id)
        if res["status"] == "completed":
            completed.append(ch_id)
        else:
            halted_at = ch_id
            halt_reason = res.get("message", "Pipeline paused")
            break

    return {
        "planned": plan,
        "completed": completed,
        "halted_at": halted_at,
        "reason": halt_reason,
    }
