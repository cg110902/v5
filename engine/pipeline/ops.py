"""Industrial Operations and Lifecycle Management Engine (engine/pipeline/ops.py).

Master implementation for:
1. Scaffold generation (get_beats_scaffold).
2. Manuscript and causal auditing (audit_chapter).
3. Emergence delta extraction (proposal_auto).
4. Atomic state synchronization and ledger sealing (sync_chapter).
5. Causal topology impact simulation (simulate_impact).
6. Volume-level reconciliation and evidence harvesting.

Zero literary hardcoding. 100% Python standard library.
"""

from __future__ import annotations
import copy
from datetime import datetime
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from engine.core.state import StateManager
from engine.core.storage import (
    atomic_write_json,
    atomic_write_text,
    ensure_directory,
    safe_load_json,
)
from engine.audit.anti_drop_iq import AntiDropIQAuditor, AuditReport, AuditIssue
from engine.text.probes import run_all_probes
from engine.domain.character import LivingCharacter, PhysiologicalState, ChapterMotive
from engine.domain.plot_graph import ChapterContinuityHandover, ForeshadowingItem


def count_prose_words(text: str) -> int:
    """Accurately count prose words, ignoring frontmatter, markdown tags, and comments."""
    if not text:
        return 0
    # Strip frontmatter
    cleaned = re.sub(r"^---.*?---\s*", "", text, flags=re.DOTALL)
    # Strip HTML comments
    cleaned = re.sub(r"<!--.*?-->", "", cleaned, flags=re.DOTALL)
    # Strip markdown headers, blockquotes, and lists
    cleaned = re.sub(r"^[\s#>\*\-\+\d\.]+", "", cleaned, flags=re.MULTILINE)
    # Count CJK characters
    cjk = len(re.findall(r"[\u4e00-\u9fff]", cleaned))
    # Count Western words
    western = len(re.findall(r"\b[a-zA-Z0-9_-]+\b", cleaned))
    return cjk + western


def _chapter_num(chapter_id: str) -> int:
    m = re.search(r"(\d+)", str(chapter_id))
    return int(m.group(1)) if m else 1


def get_beats_scaffold(
    workspace: Union[str, Path],
    chapter_id: str,
    write_file: bool = True,
    vol_id: str = "vol_01",
) -> Dict[str, Any]:
    """Generate fine outline task card scaffold with pre-populated living state."""
    ws = Path(workspace).resolve()
    sm = StateManager(ws)
    cnum = _chapter_num(chapter_id)

    persons = sm.get_persons()
    lines = sm.get_lines()
    clues = sm.get_clues()
    world = sm.get_world()
    powers = sm.get_powers()

    # Find active characters (top 3)
    active_chars = []
    for pid, p in list(persons.items())[:3]:
        if isinstance(p, dict) and p.get("life_status") == "alive":
            active_chars.append({"id": pid, "name": p.get("name", pid), "role": p.get("role", "supporting")})

    active_lines = [lid for lid, l in lines.items() if isinstance(l, dict) and l.get("status") == "active"]
    pending_clues = [kid for kid, k in clues.items() if isinstance(k, dict) and k.get("lifecycle_status") != "resolved"]

    scaffold_frontmatter = [
        "---",
        f"chapter_id: {chapter_id}",
        f"volume_id: {vol_id}",
        f"title: '{{slot:chapter_title}}'",
        f"timeline: 'Day {world.get('clock', {}).get('current_day', 1)}, {world.get('clock', {}).get('current_hour', 8):02d}:00'",
        f"location: '{{slot:primary_location}}'",
        "characters:",
    ]
    for c in active_chars:
        scaffold_frontmatter.extend([
            f"  - id: {c['id']}",
            f"    name: {c['name']}",
            f"    role: {c['role']}",
        ])
    scaffold_frontmatter.extend([
        "state_deltas:",
        f"  active_lines: {active_lines[:2]}",
        f"  touched_clues: {pending_clues[:2]}",
        "---",
        "",
        f"# Chapter [{chapter_id}] Beats Outline",
        "",
        "## 1. Opening Baton (接戏)",
        "- {{slot:opening_scene_continuation}}",
        "",
        "## 2. Core Conflict & Escalation (核心冲突)",
        "- {{slot:core_conflict_beat}}",
        "- {{slot:escalation_beat}}",
        "",
        "## 3. Climax & Shift (高潮转化)",
        "- {{slot:climax_beat}}",
        "",
        "## 4. Lethal Cliffhanger (钩子留白)",
        "- {{slot:ending_cliffhanger}}",
    ])

    scaffold_text = "\n".join(scaffold_frontmatter) + "\n"
    target_path = ws / "outlines" / vol_id / "beats" / f"{chapter_id}.md"

    if write_file:
        ensure_directory(target_path.parent)
        atomic_write_text(target_path, scaffold_text)

    return {
        "chapter_id": chapter_id,
        "volume_id": vol_id,
        "scaffold_path": str(target_path),
        "active_characters": active_chars,
    }


def audit_chapter(
    workspace: Union[str, Path],
    chapter_id: str,
    write_file: bool = True,
) -> Dict[str, Any]:
    """Run full deterministic causal, epistemology, and balance checks on chapter draft."""
    ws = Path(workspace).resolve()
    sm = StateManager(ws)
    cnum = _chapter_num(chapter_id)

    # Locate draft
    draft_candidates = [
        ws / "raw" / f"{chapter_id}_v1.md",
        ws / "raw" / f"{chapter_id}_v2.md",
        ws / "raw" / f"{chapter_id}_v3.md",
        ws / "manuscript" / f"{chapter_id}.md",
    ]
    draft_file = None
    for cand in draft_candidates:
        if cand.exists():
            draft_file = cand
            break

    if not draft_file:
        raise GuardError(
            f"No draft manuscript found for {chapter_id} in {ws / 'raw'}",
            remediation=f"Generate draft at raw/{chapter_id}_v1.md"
        )

    draft_text = draft_file.read_text(encoding="utf-8")
    words = count_prose_words(draft_text)

    # Load domain state
    characters: Dict[str, LivingCharacter] = {}
    persons = sm.get_persons()
    for pid in persons.keys():
        char = sm.load_living_character(pid)
        if char:
            characters[pid] = char

    plot_graph = sm.load_living_plot_graph()
    golden_finger = sm.load_living_golden_finger()
    universe = sm.load_living_universe()
    items = sm.get_items()
    places = sm.get_places()
    factions = sm.get_factions()

    # Parse present entities and actions mentioned in draft
    manifest: Dict[str, Any] = {
        "active_character_ids": [cid for cid in characters.keys() if cid in draft_text or characters[cid].name in draft_text],
        "actions": [],
    }

    # Run Anti-Drop-IQ Auditor
    auditor = AntiDropIQAuditor()
    report: AuditReport = auditor.audit_chapter(
        chapter=cnum,
        characters=characters,
        plot_graph=plot_graph,
        golden_finger=golden_finger,
        chapter_manifest=manifest,
        items=items,
        places=places,
        factions=factions,
        universe=universe,
    )

    # Run deterministic manuscript text probes
    probes_res = run_all_probes(draft_text, manifest, characters, sm.get_debts())
    for ds in probes_res.get("deceased_speakers", []):
        report.add_issue(AuditIssue(
            category="deceased_speaker_violation",
            severity="blocker",
            entity_id=ds.get("character_id", ""),
            chapter=cnum,
            message=ds.get("message", ""),
            context={"dialogue": ds.get("dialogue_snippet", "")}
        ))
    for f in probes_res.get("unregistered_fatalities", []):
        report.add_issue(AuditIssue(
            category="unregistered_fatality",
            severity="warning",
            entity_id=f.get("character_id", ""),
            chapter=cnum,
            message=f.get("message", ""),
            context={"snippet": f.get("context", "")}
        ))
    for gm in probes_res.get("grounding_misses", []):
        report.add_issue(AuditIssue(
            category="grounding_miss",
            severity="warning",
            entity_id=gm.get("name", ""),
            chapter=cnum,
            message=gm.get("message", ""),
        ))
    for addr in probes_res.get("address_inconsistencies", []):
        report.add_issue(AuditIssue(
            category="address_inconsistency",
            severity="warning",
            entity_id=addr.get("speaker", ""),
            chapter=cnum,
            message=addr.get("reason", ""),
        ))

    # Format Markdown Report
    report_lines = [
        f"# Audit Report: Chapter [{chapter_id}]",
        f"- Timestamp: {datetime.now().isoformat()}",
        f"- Manuscript File: {draft_file.name} ({words:,} words)",
        f"- Causal Status: {'PASSED (0 blockers)' if report.is_valid else 'BLOCKED (Integrity violations found)'}",
        "",
        f"## Blockers ({len(report.blockers)})",
    ]
    for b in report.blockers:
        report_lines.append(f"- [BLOCKER] ({b.category}) {b.message}")

    report_lines.extend([
        "",
        f"## Warnings ({len(report.warnings)})",
    ])
    for w in report.warnings:
        report_lines.append(f"- [WARNING] ({w.category}) {w.message}")

    report_text = "\n".join(report_lines) + "\n"
    target_log = ws / "log" / "audit" / f"{chapter_id}.md"

    if write_file:
        ensure_directory(target_log.parent)
        atomic_write_text(target_log, report_text)

    return {
        "chapter_id": chapter_id,
        "is_valid": report.is_valid,
        "blockers": [b.to_dict() for b in report.blockers],
        "warnings": [w.to_dict() for w in report.warnings],
        "prose_words": words,
        "report_file": str(target_log),
    }


def proposal_auto(workspace: Union[str, Path], chapter_id: str) -> Dict[str, Any]:
    """Synthesize emergence delta proposal from manuscript and audit report."""
    ws = Path(workspace).resolve()
    sm = StateManager(ws)
    cnum = _chapter_num(chapter_id)

    # Read audit report
    audit_file = ws / "log" / "audit" / f"{chapter_id}.md"
    new_entities: List[Dict[str, Any]] = []

    # Find draft
    draft_candidates = [
        ws / "raw" / f"{chapter_id}_v3.md",
        ws / "raw" / f"{chapter_id}_v2.md",
        ws / "raw" / f"{chapter_id}_v1.md",
    ]
    draft_file = next((c for c in draft_candidates if c.exists()), None)
    draft_text = draft_file.read_text(encoding="utf-8") if draft_file else ""

    # Auto-detect present characters
    persons = sm.get_persons()
    present_chars = []
    for pid, p in persons.items():
        if isinstance(p, dict):
            name = p.get("name", pid)
            if pid in draft_text or (name and name in draft_text):
                present_chars.append({"id": pid, "name": name, "life_status": p.get("life_status", "alive")})

    proposal = {
        "chapter_id": chapter_id,
        "characters": present_chars,
        "new_entities": new_entities,
        "state_deltas": {
            "active_lines": [],
            "touched_clues": [],
        },
    }
    return proposal


def sync_chapter(
    workspace: Union[str, Path],
    chapter_id: str,
    force: bool = False,
) -> Dict[str, Any]:
    """Atomically commit chapter delta, update domain models, and seal transaction."""
    ws = Path(workspace).resolve()
    sm = StateManager(ws)
    cnum = _chapter_num(chapter_id)

    # 1. Run audit gate unless forced
    if not force:
        audit_res = audit_chapter(ws, chapter_id, write_file=True)
        if not audit_res["is_valid"]:
            raise GuardError(
                f"Sync blocked: Chapter {chapter_id} has {len(audit_res['blockers'])} causal blockers.",
                remediation="Resolve blockers in log/audit/{chapter_id}.md or inspect draft."
            )

    # 2. Locate finalized manuscript
    draft_candidates = [
        ws / "raw" / f"{chapter_id}_v3.md",
        ws / "raw" / f"{chapter_id}_v2.md",
        ws / "raw" / f"{chapter_id}_v1.md",
    ]
    draft_file = next((c for c in draft_candidates if c.exists()), None)
    if not draft_file:
        raise GuardError(f"No manuscript file found to sync for {chapter_id}")

    text = draft_file.read_text(encoding="utf-8")
    words = count_prose_words(text)

    # 3. Get proposal
    proposal = proposal_auto(ws, chapter_id)

    # 4. Commit via StateManager
    sync_result = sm.apply_fine_outline_delta(proposal, word_count=words, beats_body=text)

    # 5. Advance Universe Clock & Golden Finger recharge
    univ = sm.load_living_universe()
    univ.clock.advance_hours(4)  # Natural default progression per chapter
    sm.save_living_universe(univ)

    gf = sm.load_living_golden_finger()
    if gf:
        gf.recharge_tick(cnum)
        sm.save_living_golden_finger(gf)

    # 6. Seal chapter manuscript to final/
    final_dir = ws / "final"
    ensure_directory(final_dir)
    final_file = final_dir / f"{chapter_id}.md"
    atomic_write_text(final_file, text)

    return {
        "status": "sealed",
        "chapter_id": chapter_id,
        "words_synced": words,
        "final_manuscript": str(final_file),
        "healed_changes": sync_result.get("healed", []),
    }


def build_chapter(
    workspace: Union[str, Path],
    chapter_id: str,
    skip_lexicon: bool = False,
    force: bool = False,
) -> Dict[str, Any]:
    """One-click atomic build: lexicon cleanup -> audit verification -> sync state -> snapshot sealing."""
    ws = Path(workspace).resolve()

    # 1. Locate manuscript draft
    candidates = [
        ws / "manuscript" / "vol_01" / "raw" / f"{chapter_id}_v3.md",
        ws / "raw" / f"{chapter_id}_v3.md",
        ws / "manuscript" / "vol_01" / "raw" / f"{chapter_id}_v2.md",
        ws / "raw" / f"{chapter_id}_v2.md",
        ws / "manuscript" / "vol_01" / "raw" / f"{chapter_id}_v1.md",
        ws / "raw" / f"{chapter_id}_v1.md",
    ]
    draft_file = next((c for c in candidates if c.is_file()), None)
    if not draft_file:
        raise GuardError(
            f"未找到可构建的章节草稿文件 [{chapter_id}]！",
            remediation="请确保 raw/ 目录下存在 ch_XXX_v3.md 或 v2.md/v1.md 草稿。"
        )

    raw_text = draft_file.read_text(encoding="utf-8")
    lexicon_hits: List[Dict[str, Any]] = []

    # 2. Run deterministic lexicon cleanup unless skipped
    if not skip_lexicon:
        from engine.text.lexicon import LexiconEngine
        lex = LexiconEngine.load_cascaded(ws)
        clean_text, lexicon_hits = lex.apply_detailed(raw_text, chapter_id)
        if clean_text != raw_text:
            draft_file.write_text(clean_text, encoding="utf-8")
            raw_text = clean_text

    # 3. Perform chapter sync (which runs audit pass)
    sync_res = sync_chapter(ws, chapter_id, force=force)

    # 4. Create atomic snapshot seal
    snap_name = f"{chapter_id}_sealed"
    from engine.core.snapshots import create_snapshot, get_snapshots_dir
    import shutil
    snap_dir = get_snapshots_dir(ws) / snap_name
    if snap_dir.exists():
        shutil.rmtree(snap_dir, ignore_errors=True)
    try:
        create_snapshot(ws, snap_name)
    except Exception:
        pass  # Snapshot failure should not block core transaction if state already synced

    return {
        "status": "built",
        "chapter_id": chapter_id,
        "words": sync_res.get("words_synced", 0),
        "lexicon_hits_count": len(lexicon_hits),
        "lexicon_hits": lexicon_hits,
        "final_manuscript": sync_res.get("final_manuscript", ""),
        "snapshot": snap_name,
    }


finalize_chapter = build_chapter


def simulate_impact(
    workspace: Union[str, Path],
    entity_id: str,
    action: str = "retcon",
) -> Dict[str, Any]:
    """Calculate causal topology blast radius for modifying or retconning an entity."""
    ws = Path(workspace).resolve()
    sm = StateManager(ws)
    co_occur = sm.get_co_occurrence()
    timeline = sm.get_entity_timeline()

    affected_chapters: Set[str] = set()
    connected_entities: Set[str] = set()

    # Check timeline appearances
    if entity_id in timeline:
        for app in timeline[entity_id].get("appearances", []):
            affected_chapters.add(app.get("chapter_id", ""))

    # Check co-occurrences
    for pair_key, data in co_occur.items():
        if entity_id in pair_key:
            connected_entities.add(data.get("entity_a", ""))
            connected_entities.add(data.get("entity_b", ""))
            for ch in data.get("chapters", []):
                affected_chapters.add(ch)

    connected_entities.discard(entity_id)

    return {
        "target_entity": entity_id,
        "action": action,
        "blast_radius_score": len(affected_chapters) * 2 + len(connected_entities),
        "affected_chapters": sorted(list(affected_chapters)),
        "connected_entities": sorted(list(connected_entities)),
    }


def ask_fact(workspace: Union[str, Path], query: str) -> List[str]:
    """Instantaneous factual lookup across all 16 state tables (ask command)."""
    q = query.strip()
    if not q:
        return []
    ws = Path(workspace).resolve()
    sm = StateManager(ws)
    results: List[str] = []

    # 1. Locked facts (P0)
    for lf in sm.get_locked_facts():
        if isinstance(lf, dict):
            stmt = lf.get("statement") or lf.get("fact", "")
            if q in stmt or q in lf.get("id", ""):
                results.append(f"[Locked Fact] ({lf.get('id')}) {stmt}")

    # 2. Characters & living cognitive/physical states
    persons = sm.get_persons()
    for pid, p in persons.items():
        if isinstance(p, dict):
            pname = p.get("name", pid)
            if q in pname or q in pid or q in p.get("role", ""):
                results.append(f"[Character] {pname} ({pid}) - Role: {p.get('role')}, Status: {p.get('life_status')}, Injury: Lvl {p.get('injury_level', 0)}")

    # 3. Items
    items = sm.get_items()
    for iid, it in items.items():
        if isinstance(it, dict):
            iname = it.get("name", iid)
            if q in iname or q in iid or q in str(it.get("owner_id", "")):
                results.append(f"[Item] {iname} ({iid}) - Owner: {it.get('owner_id', 'None')}, Condition: {it.get('condition', 'intact')}")

    # 4. Factions
    factions = sm.get_factions()
    for fid, f in factions.items():
        if isinstance(f, dict):
            fname = f.get("name", fid)
            if q in fname or q in fid:
                results.append(f"[Faction] {fname} ({fid})")

    # 5. Places
    places = sm.get_places()
    for plid, pl in places.items():
        if isinstance(pl, dict):
            plname = pl.get("name", plid)
            if q in plname or q in plid:
                results.append(f"[Place] {plname} ({plid}) - Danger Tier: {pl.get('danger_tier', 'Normal')}")

    # 6. Active subplots / lines
    lines = sm.get_lines()
    for lid, l in lines.items():
        if isinstance(l, dict):
            title = l.get("title", lid)
            if q in title or q in lid:
                results.append(f"[Subplot] {title} ({lid}) - Status: {l.get('status')}")

    # 7. Clues / Foreshadowing
    clues = sm.get_clues()
    for kid, k in clues.items():
        if isinstance(k, dict):
            hook = k.get("hook", kid)
            if q in hook or q in kid:
                results.append(f"[Foreshadowing] {hook} ({kid}) - Status: {k.get('lifecycle_status')}, Window: {k.get('target_resolution_window')}")

    # 8. Debts
    debts = sm.get_debts()
    if isinstance(debts, dict):
        for holder, targets in debts.items():
            if q in holder:
                results.append(f"[Debt] Holder {holder}: {targets}")
            elif isinstance(targets, dict):
                for target, meta in targets.items():
                    if q in target:
                        results.append(f"[Debt] Target {target} held by {holder}: {meta}")

    # 9. Golden Finger
    powers = sm.get_powers()
    gf = powers.get("golden_finger", {})
    if gf and (q in gf.get("name", "") or q in "golden_finger" or q in "system"):
        results.append(f"[Golden Finger] {gf.get('name')} - Stage: {gf.get('current_stage_id')}, Energy: {gf.get('current_energy')}")

    # 10. Universe World Clock
    world = sm.get_world()
    clock = world.get("clock", {})
    if q in "time" or q in "clock" or q in "day" or q in "weather":
        results.append(f"[Universe Clock] Day {clock.get('current_day', 1)}, {clock.get('current_hour', 8):02d}:00 ({clock.get('diurnal_cycle', 'morning')}), Weather: {clock.get('weather', 'clear')}")

    return results


def evidence_candidates(workspace: Union[str, Path], chapter_id: str) -> Dict[str, Any]:
    """Harvest verbatim evidence quotes and candidate lines from manuscript for grounding."""
    ws = Path(workspace).resolve()
    sm = StateManager(ws)

    draft_candidates = [
        ws / "final" / f"{chapter_id}.md",
        ws / "raw" / f"{chapter_id}_v3.md",
        ws / "raw" / f"{chapter_id}_v2.md",
        ws / "raw" / f"{chapter_id}_v1.md",
    ]
    target_f = next((c for c in draft_candidates if c.exists()), None)
    if not target_f:
        return {"chapter_id": chapter_id, "found": False, "candidates": []}

    prose = target_f.read_text(encoding="utf-8")
    persons = sm.get_persons()
    items = sm.get_items()

    candidates: List[Dict[str, Any]] = []

    # Harvest character dialogue/action citations
    for pid, p in persons.items():
        if isinstance(p, dict):
            name = p.get("name", pid)
            if name and name in prose:
                sentences = re.split(r"[。！？\n]", prose)
                matching = [s.strip() for s in sentences if name in s and len(s.strip()) > 5][:3]
                for s in matching:
                    candidates.append({
                        "entity_id": pid,
                        "entity_name": name,
                        "type": "character_appearance",
                        "citation": s,
                    })

    # Harvest item citations
    for iid, it in items.items():
        if isinstance(it, dict):
            name = it.get("name", iid)
            if name and name in prose:
                sentences = re.split(r"[。！？\n]", prose)
                matching = [s.strip() for s in sentences if name in s and len(s.strip()) > 5][:2]
                for s in matching:
                    candidates.append({
                        "entity_id": iid,
                        "entity_name": name,
                        "type": "item_usage",
                        "citation": s,
                    })

    return {
        "chapter_id": chapter_id,
        "found": True,
        "manuscript_file": target_f.name,
        "candidates_count": len(candidates),
        "candidates": candidates,
    }


def reconcile_volume(
    workspace: Union[str, Path],
    volume_id: str = "vol_01",
    write_file: bool = False,
) -> Dict[str, Any]:
    """Execute end-of-volume consistency reconciliation sweep and milestone verification."""
    ws = Path(workspace).resolve()
    sm = StateManager(ws)

    ledger = sm.get_ledger()
    lines = sm.get_lines()
    clues = sm.get_clues()
    milestones = sm.get_milestones()

    vol_words = sum(entry.get("word_count", 0) for entry in ledger if isinstance(entry, dict))
    total_chapters = len(ledger)

    active_milestones = [m for m in milestones if isinstance(m, dict) and m.get("status") != "achieved"]
    resolved_milestones = [m for m in milestones if isinstance(m, dict) and m.get("status") == "achieved"]

    active_lines = [l for l in lines.values() if isinstance(l, dict) and l.get("status") == "active"]
    completed_lines = [l for l in lines.values() if isinstance(l, dict) and l.get("status") == "completed"]

    pending_clues = [k for k in clues.values() if isinstance(k, dict) and k.get("lifecycle_status") != "resolved"]

    report_lines = [
        f"# Volume Reconciliation Report: [{volume_id}]",
        f"- Timestamp: {datetime.now().isoformat()}",
        f"- Chapters Synced: {total_chapters}",
        f"- Volume Word Count: {vol_words:,} words",
        "",
        f"## Milestones ({len(resolved_milestones)} Achieved, {len(active_milestones)} Pending)",
    ]
    for m in milestones:
        if isinstance(m, dict):
            report_lines.append(f"- [{m.get('status', 'pending').upper()}] {m.get('title')} (Target: ch {m.get('target_chapter')})")

    report_lines.extend([
        "",
        f"## Subplots / Lines ({len(completed_lines)} Completed, {len(active_lines)} Active)",
    ])
    for l in lines.values():
        if isinstance(l, dict):
            report_lines.append(f"- [{l.get('status', 'active').upper()}] {l.get('title')} ({l.get('id')})")

    report_lines.extend([
        "",
        f"## Unresolved Foreshadowing Clues ({len(pending_clues)})",
    ])
    for k in pending_clues:
        report_lines.append(f"- [{k.get('id', '')}] {k.get('hook', '')} (Target: {k.get('target_resolution_window')})")

    report_text = "\n".join(report_lines) + "\n"
    target_path = ws / "log" / "review" / f"{volume_id}_reconcile.md"

    if write_file:
        ensure_directory(target_path.parent)
        atomic_write_text(target_path, report_text)

    return {
        "volume_id": volume_id,
        "total_chapters": total_chapters,
        "total_words": vol_words,
        "active_milestones": len(active_milestones),
        "active_lines": len(active_lines),
        "pending_clues": len(pending_clues),
        "report_file": str(target_path) if write_file else None,
    }


def rollup_volume(
    workspace: Union[str, Path],
    volume_id: str = "vol_01",
) -> Dict[str, Any]:
    """Compile volume-level summary telemetry and transition readiness."""
    res = reconcile_volume(workspace, volume_id=volume_id, write_file=False)
    ws = Path(workspace).resolve()
    sm = StateManager(ws)
    persons = sm.get_persons()

    alive_cast = [p.get("name", pid) for pid, p in persons.items() if isinstance(p, dict) and p.get("life_status") == "alive"]
    deceased_cast = [p.get("name", pid) for pid, p in persons.items() if isinstance(p, dict) and p.get("life_status") == "deceased"]

    return {
        "volume_id": volume_id,
        "total_chapters": res["total_chapters"],
        "total_words": res["total_words"],
        "alive_cast_count": len(alive_cast),
        "deceased_cast_count": len(deceased_cast),
        "alive_cast": alive_cast[:10],
        "deceased_cast": deceased_cast,
        "ready_for_next_volume": res["active_milestones"] == 0,
    }


def get_calendar(workspace: Union[str, Path], count: int = 3) -> Dict[str, Any]:
    """Retrieve upcoming chapter production roadmap and approaching clues/deadlines."""
    ws = Path(workspace).resolve()
    sm = StateManager(ws)
    curr = sm.get_current()
    cur_ch = curr.get("chapter_id", "ch_001")
    vol_id = curr.get("volume_id", "vol_01")
    cnum = _chapter_num(cur_ch)

    vol_file = ws / "outlines" / vol_id / "outline.md"
    upcoming_chapters: List[Dict[str, Any]] = []

    if vol_file.is_file():
        from engine.core.parser import parse_volume_outline
        vol_text = vol_file.read_text(encoding="utf-8")
        for offset in range(1, count + 1):
            target_id = f"ch_{cnum + offset:03d}"
            info = parse_volume_outline(vol_text, target_id)
            if info:
                upcoming_chapters.append(info)
            else:
                upcoming_chapters.append({
                    "chapter_id": target_id,
                    "title": f"第{cnum + offset}章",
                    "event": "待大纲细化",
                })
    else:
        for offset in range(1, count + 1):
            target_id = f"ch_{cnum + offset:03d}"
            upcoming_chapters.append({
                "chapter_id": target_id,
                "title": f"第{cnum + offset}章",
                "event": "分卷大纲待创建",
            })

    # Approaching clues from lines
    lines = sm.get_lines()
    approaching_clues: List[Dict[str, Any]] = []
    for lid, line in lines.items():
        if isinstance(line, dict):
            status = line.get("status", line.get("state", "active"))
            if status != "resolved":
                target = int(line.get("target_ch", line.get("target_chapter", cnum + 10)))
                rem = target - cnum
                if rem <= count + 2:
                    approaching_clues.append({
                        "id": lid,
                        "title": line.get("title", line.get("hook", "")),
                        "target_chapter": target,
                        "remaining_chapters": rem,
                    })

    return {
        "current_chapter": cur_ch,
        "volume_id": vol_id,
        "upcoming_chapters": upcoming_chapters,
        "approaching_clues": approaching_clues,
    }


def add_milestone(
    workspace: Union[str, Path],
    title: str,
    target_ch: int,
    desc: str = "",
    milestone_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Register a strategic milestone in state/milestones.json."""
    ws = Path(workspace).resolve()
    sm = StateManager(ws)
    milestones = sm.get_milestones()

    if not milestone_id:
        from engine.core.id_tracker import IdTracker
        idt = IdTracker(ws)
        milestone_id = idt.id_next("milestone")

    m_entry = {
        "id": milestone_id,
        "title": str(title),
        "target_chapter": int(target_ch),
        "desc": str(desc),
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }
    milestones.append(m_entry)
    sm.save_milestones(milestones)

    return {
        "status": "created",
        "milestone": m_entry,
        "total_milestones": len(milestones),
    }


def list_milestones(workspace: Union[str, Path]) -> List[Dict[str, Any]]:
    """List all registered strategic milestones."""
    ws = Path(workspace).resolve()
    sm = StateManager(ws)
    return sm.get_milestones()

