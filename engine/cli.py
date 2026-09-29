"""Novel Studio 5.0 Industrial CLI Dispatcher and Unified Command Center (engine/cli.py).

Enforces strict exit codes:
- 0: Normal success
- 1: Business / audit / integrity blocker
- 2: CLI argument / syntax error
- 3: Python environment error
- 4: Storage / corruption failure

Zero literary hardcoding. 100% Python standard library.
"""

from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

from engine.errors import (
    StudioError,
    BusinessError,
    GuardError,
    CLIArgumentError,
    StorageError,
    EnvironmentError,
)
from engine.core.state import StateManager
from engine.core.id_tracker import IdTracker
from engine.core.check import run_full_check
from engine.core.cockpit import render_cockpit
from engine.core.snapshots import create_snapshot, list_snapshots, rollback_snapshot
from engine.core.storage import atomic_write_json, ensure_directory
from engine.core.exporter import Exporter
from engine.pipeline.pack import build_pack
from engine.pipeline.ops import (
    get_beats_scaffold,
    audit_chapter,
    sync_chapter,
    build_chapter,
    finalize_chapter,
    simulate_impact,
    ask_fact,
    evidence_candidates,
    reconcile_volume,
    rollup_volume,
    get_calendar,
    add_milestone,
    list_milestones,
)
from engine.pipeline.cruise import run_cruise


def extract_global_flags(argv: List[str]) -> Tuple[Path, bool, List[str]]:
    """Extract -w/--workspace and --json flags robustly from any position in command line."""
    ws_str = "."
    is_json = False
    clean = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("-w", "--workspace") and i + 1 < len(argv):
            ws_str = argv[i + 1]
            i += 2
        elif arg.startswith("--workspace="):
            ws_str = arg.split("=", 1)[1]
            i += 1
        elif arg == "--json":
            is_json = True
            i += 1
        else:
            clean.append(arg)
            i += 1
    return Path(ws_str).resolve(), is_json, clean


def build_parser() -> argparse.ArgumentParser:
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("-w", "--workspace", default=None, help="Workspace path (defaults to current dir)")
    parent_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    parser = argparse.ArgumentParser(
        prog="studio.py",
        parents=[parent_parser],
        description="Novel Studio 5.0 - Industrial Living-Domain Novel Engineering Engine",
    )
    parser.add_argument("--version", action="version", version="Novel Studio 5.0.0")

    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # init
    p_init = subparsers.add_parser("init", parents=[parent_parser], help="Initialize new novel project")
    p_init.add_argument("title_pos", nargs="?", default=None, help="Novel title (positional)")
    p_init.add_argument("-t", "--title", default=None, help="Novel title (flag)")
    p_init.add_argument("-g", "--genre", default="General", help="Genre")
    p_init.add_argument("-p", "--protagonist", default="Protagonist", help="Protagonist name")
    p_init.add_argument("--force", action="store_true", help="Force overwrite existing")

    # scaffold
    p_scaff = subparsers.add_parser("scaffold", parents=[parent_parser], help="Generate fine outline beats scaffold")
    p_scaff.add_argument("chapter_id", help="Chapter ID (e.g. ch_001)")
    p_scaff.add_argument("-v", "--volume", default="vol_01", help="Volume ID (defaults to vol_01)")

    # pack
    p_pack = subparsers.add_parser("pack", parents=[parent_parser], help="Assemble self-contained context pack")
    p_pack.add_argument("chapter_id", help="Chapter ID (e.g. ch_001)")

    # audit
    p_audit = subparsers.add_parser("audit", parents=[parent_parser], help="Audit manuscript causality and rationality")
    p_audit.add_argument("chapter_id", help="Chapter ID (e.g. ch_001)")

    # sync
    p_sync = subparsers.add_parser("sync", parents=[parent_parser], help="Sync fine outline & emergence delta to state tables")
    p_sync.add_argument("chapter_id", help="Chapter ID (e.g. ch_001)")
    p_sync.add_argument("--force", action="store_true", help="Force sync bypassing audit blockers")

    # build
    p_build = subparsers.add_parser("build", parents=[parent_parser], help="Atomic chapter build: lexicon, audit, sync, snapshot")
    p_build.add_argument("chapter_id", help="Chapter ID (e.g. ch_001)")
    p_build.add_argument("--skip-lexicon", action="store_true", help="Skip lexicon cleanup")
    p_build.add_argument("--force", action="store_true", help="Force build bypassing audit blockers")

    # finalize (alias for build)
    p_final = subparsers.add_parser("finalize", parents=[parent_parser], help="Alias for build")
    p_final.add_argument("chapter_id", help="Chapter ID (e.g. ch_001)")
    p_final.add_argument("--skip-lexicon", action="store_true", help="Skip lexicon cleanup")
    p_final.add_argument("--force", action="store_true", help="Force build bypassing audit blockers")

    # check
    p_check = subparsers.add_parser("check", parents=[parent_parser], help="Execute 10-point integrity scanner")
    p_check.add_argument("chapter_id", nargs="?", default=None, help="Optional chapter ID")

    # cockpit
    p_cockpit = subparsers.add_parser("cockpit", parents=[parent_parser], help="Display telemetry dashboard")

    # trace
    p_trace = subparsers.add_parser("trace", parents=[parent_parser], help="Trace entity lifecycle trajectory across tables")
    p_trace.add_argument("target_id", help="Entity ID to trace (e.g. C_001)")

    # id
    p_id = subparsers.add_parser("id", parents=[parent_parser], help="ID governance operations")
    p_id_sub = p_id.add_subparsers(dest="id_action", help="ID action")
    p_id_next = p_id_sub.add_parser("next", parents=[parent_parser], help="Get next available ID")
    p_id_next.add_argument("category", help="Category (character, item, trump, clue, line, place, faction, etc.)")
    p_id_list = p_id_sub.add_parser("list", parents=[parent_parser], help="List all IDs")
    p_id_list.add_argument("category", nargs="?", default=None, help="Optional filter category")

    # impact
    p_impact = subparsers.add_parser("impact", parents=[parent_parser], help="Simulate causal blast radius for an entity")
    p_impact.add_argument("entity_id", help="Entity ID")
    p_impact.add_argument("--action", default="retcon", help="Action type (retcon, delete, modify)")

    # cruise
    p_cruise = subparsers.add_parser("cruise", parents=[parent_parser], help="Autonomous chapter cruise runner")
    p_cruise.add_argument("--count", type=int, default=1, help="Number of chapters to advance")
    p_cruise.add_argument("--start", default=None, help="Optional start chapter ID")

    # snapshot
    p_snap = subparsers.add_parser("snapshot", parents=[parent_parser], help="Snapshot defense operations")
    p_snap_sub = p_snap.add_subparsers(dest="snap_action", help="Snapshot action")
    p_snap_c = p_snap_sub.add_parser("create", parents=[parent_parser], help="Create snapshot")
    p_snap_c.add_argument("name", help="Snapshot label")
    p_snap_l = p_snap_sub.add_parser("list", parents=[parent_parser], help="List snapshots")
    p_snap_r = p_snap_sub.add_parser("rollback", parents=[parent_parser], help="Rollback snapshot")
    p_snap_r.add_argument("name", help="Snapshot name to restore")

    # ask
    p_ask = subparsers.add_parser("ask", parents=[parent_parser], help="Instantaneous factual lookup across all 16 state tables")
    p_ask.add_argument("query", help="Query keyword or entity name")

    # evidence
    p_ev = subparsers.add_parser("evidence", parents=[parent_parser], help="Harvest verbatim evidence quotes from chapter")
    p_ev.add_argument("chapter_id", help="Chapter ID (e.g. ch_001)")

    # reconcile
    p_rec = subparsers.add_parser("reconcile", parents=[parent_parser], help="Volume consistency reconciliation sweep")
    p_rec.add_argument("volume_id", nargs="?", default="vol_01", help="Volume ID (defaults to vol_01)")
    p_rec.add_argument("--write", action="store_true", help="Write report to log/review/")

    # rollup
    p_roll = subparsers.add_parser("rollup", parents=[parent_parser], help="Rollup volume statistics")
    p_roll.add_argument("volume_id", nargs="?", default="vol_01", help="Volume ID (defaults to vol_01)")

    # export
    p_exp = subparsers.add_parser("export", parents=[parent_parser], help="Export publication manuscript")
    p_exp.add_argument("-v", "--volume", default=None, help="Volume ID (defaults to all)")
    p_exp.add_argument("-f", "--format", choices=["txt", "md"], default="txt", help="Format (txt or md)")
    p_exp.add_argument("-o", "--output", default=None, help="Output destination file")

    # milestone
    p_ms = subparsers.add_parser("milestone", parents=[parent_parser], help="Strategic milestone tracking operations")
    p_ms_sub = p_ms.add_subparsers(dest="ms_action", help="Milestone action")
    p_ms_add = p_ms_sub.add_parser("add", parents=[parent_parser], help="Add milestone")
    p_ms_add.add_argument("--title", required=True, help="Milestone title")
    p_ms_add.add_argument("--target-ch", "--target_ch", type=int, required=True, help="Target chapter")
    p_ms_add.add_argument("--desc", default="", help="Description")
    p_ms_add.add_argument("--id", default=None, help="Optional milestone ID")
    p_ms_list = p_ms_sub.add_parser("list", parents=[parent_parser], help="List milestones")

    # calendar
    p_cal = subparsers.add_parser("calendar", parents=[parent_parser], help="Production calendar of upcoming chapters and clues")
    p_cal.add_argument("--count", type=int, default=3, help="Number of chapters to look ahead")

    return parser


def handle_init(args: argparse.Namespace, ws: Path) -> Dict[str, Any]:
    cfg_file = ws / "project.json"
    if cfg_file.exists() and not args.force:
        raise BusinessError(f"Workspace already initialized at {ws}", remediation="Use --force to reinitialize.")

    ensure_directory(ws / "bible")
    ensure_directory(ws / "state")
    ensure_directory(ws / "outlines" / "vol_01" / "beats")
    ensure_directory(ws / "raw")
    ensure_directory(ws / "final")
    ensure_directory(ws / "context")
    ensure_directory(ws / "log" / "audit")
    ensure_directory(ws / "snapshots")

    title = args.title or args.title_pos or "Untitled Novel"
    protagonist = args.protagonist or "Protagonist"

    # Write project.json
    proj_data = {
        "title": title,
        "genre": args.genre,
        "protagonist": protagonist,
        "created_at": "2026-09-27T00:00:00",
        "version": "5.0.0",
    }
    atomic_write_json(cfg_file, proj_data)

    # Initialize 16 state tables
    sm = StateManager(ws)
    sm.save_persons({
        "C_001": {
            "id": "C_001",
            "name": args.protagonist,
            "role": "protagonist",
            "life_status": "alive",
            "injury_level": 0,
            "tier_rank": 1,
        }
    })
    sm.save_items({})
    sm.save_factions({})
    sm.save_places({})
    sm.save_lines({"L_001": {"id": "L_001", "title": "Main Quest: Origin Awakening", "category": "main", "status": "active"}})
    sm.save_locked_facts([{"id": "LOCK-001", "statement": f"{args.protagonist} is the sole bearer of the origin legacy."}])
    sm.save_current({"chapter_id": "ch_001", "volume_id": "vol_01", "total_words": 0})
    sm.save_ledger([])
    sm.save_milestones([{"id": "M_001", "title": "Breakthrough First Tier", "target_chapter": 10, "status": "pending"}])
    sm.save_timeline([])
    sm.save_debts({})
    sm.save_relations({})
    sm.save_clues({})
    sm.save_synopsis({})
    sm.save_powers({
        "golden_finger": {
            "system_id": "GF_001",
            "owner_character_id": "C_001",
            "name": "Origin Matrix",
            "current_stage_id": "stage_1",
            "stages": {
                "stage_1": {
                    "stage_id": "stage_1",
                    "stage_name": "Awakening",
                    "stage_order": 1,
                    "unlock_chapter": 1,
                    "max_energy": 100,
                    "recharge_rate_per_chapter": 15,
                }
            },
            "current_energy": 100,
        }
    })
    sm.save_world({
        "universe_id": "universe_prime",
        "clock": {"current_day": 1, "current_hour": 8, "diurnal_cycle": "morning", "weather": "clear"},
        "regional_tension": {},
    })

    return {"status": "success", "message": f"Initialized Novel Studio 5.0 project '{args.title}'", "workspace": str(ws)}


def main(argv: Optional[List[str]] = None) -> int:
    raw_argv = sys.argv[1:] if argv is None else list(argv)
    ws, is_json, clean_argv = extract_global_flags(raw_argv)

    parser = build_parser()
    try:
        args = parser.parse_args(clean_argv)
    except SystemExit as e:
        return 2 if e.code != 0 else 0

    if not args.subcommand:
        parser.print_help()
        return 2

    try:
        res: Any = None

        if args.subcommand == "init":
            res = handle_init(args, ws)

        elif args.subcommand == "scaffold":
            res = get_beats_scaffold(ws, args.chapter_id, write_file=True, vol_id=args.volume)

        elif args.subcommand == "pack":
            res = build_pack(ws, args.chapter_id, write_file=True)

        elif args.subcommand == "audit":
            res = audit_chapter(ws, args.chapter_id, write_file=True)
            if not res.get("is_valid"):
                if is_json:
                    print(json.dumps(res, ensure_ascii=False, indent=2))
                else:
                    print(f"❌ Audit BLOCKED for {args.chapter_id}: {len(res.get('blockers', []))} blockers found.")
                    for b in res.get("blockers", []):
                        print(f"   - {b['message']}")
                return 1

        elif args.subcommand == "sync":
            res = sync_chapter(ws, args.chapter_id, force=args.force)

        elif args.subcommand in ("build", "finalize"):
            res = build_chapter(ws, args.chapter_id, skip_lexicon=args.skip_lexicon, force=args.force)

        elif args.subcommand == "check":
            res = run_full_check(ws, args.chapter_id)
            if not res.get("is_valid"):
                if is_json:
                    print(json.dumps(res, ensure_ascii=False, indent=2))
                else:
                    print(f"❌ Integrity Check BLOCKED: {res['errors_count']} errors found.")
                    for err in res["errors"]:
                        print(f"   - {err}")
                return 1

        elif args.subcommand == "cockpit":
            dashboard_text = render_cockpit(ws)
            if is_json:
                res = {"dashboard": dashboard_text}
            else:
                print(dashboard_text)
                return 0

        elif args.subcommand == "trace":
            idt = IdTracker(ws)
            res = idt.trace_id(args.target_id)

        elif args.subcommand == "id":
            idt = IdTracker(ws)
            if args.id_action == "next":
                res = {"category": args.category, "next_id": idt.id_next(args.category)}
            elif args.id_action == "list":
                res = idt.id_list(args.category)
            else:
                parser.error("Must specify 'next' or 'list' for id command.")

        elif args.subcommand == "impact":
            res = simulate_impact(ws, args.entity_id, action=args.action)

        elif args.subcommand == "cruise":
            res = run_cruise(ws, count=args.count, start_chapter=args.start)
            if res.get("halted_at"):
                if is_json:
                    print(json.dumps(res, ensure_ascii=False, indent=2))
                else:
                    print(f"⚠️ Cruise halted at {res['halted_at']}: {res['reason']}")
                return 1

        elif args.subcommand == "snapshot":
            if args.snap_action == "create":
                snap_path = create_snapshot(ws, args.name)
                res = {"status": "created", "snapshot": str(snap_path)}
            elif args.snap_action == "list":
                res = {"snapshots": list_snapshots(ws)}
            elif args.snap_action == "rollback":
                rollback_snapshot(ws, args.name)
                res = {"status": "restored", "snapshot": args.name}
            else:
                parser.error("Must specify create/list/rollback for snapshot.")

        elif args.subcommand == "ask":
            res = ask_fact(ws, args.query)
            if not is_json:
                print(f"[OK] [ASK] Facts matching '{args.query}' ({len(res)} results):")
                for r in res:
                    print(f"   {r}")
                return 0

        elif args.subcommand == "evidence":
            res = evidence_candidates(ws, args.chapter_id)

        elif args.subcommand == "reconcile":
            res = reconcile_volume(ws, volume_id=args.volume_id, write_file=args.write)

        elif args.subcommand == "rollup":
            res = rollup_volume(ws, volume_id=args.volume_id)

        elif args.subcommand == "export":
            exporter = Exporter(ws)
            if args.volume:
                res = exporter.export_volume(volume_id=args.volume, format_type=args.format, output_file=args.output)
            else:
                res = exporter.export_full_book(format_type=args.format, output_file=args.output)

        elif args.subcommand == "milestone":
            if getattr(args, "ms_action", "") == "add":
                target_ch = getattr(args, "target_ch", None) or getattr(args, "target_chapter", 1)
                res = add_milestone(ws, title=args.title, target_ch=target_ch, desc=args.desc, milestone_id=args.id)
            elif getattr(args, "ms_action", "") == "list":
                res = {"milestones": list_milestones(ws)}
            else:
                parser.error("Must specify 'add' or 'list' for milestone command.")

        elif args.subcommand == "calendar":
            res = get_calendar(ws, count=args.count)
            if not is_json:
                print(f"📅 Production Calendar (Current: {res['current_chapter']}, Vol: {res['volume_id']}):")
                print("   Upcoming Chapters:")
                for ch in res["upcoming_chapters"]:
                    print(f"   - {ch.get('chapter_id')}: {ch.get('title')} ({ch.get('summary', ch.get('event', ''))})")
                if res["approaching_clues"]:
                    print("   Approaching Clues/Deadlines:")
                    for cl in res["approaching_clues"]:
                        print(f"   ⚠️ [{cl.get('id')}] {cl.get('title')} (due ch {cl.get('target_chapter')}, {cl.get('remaining_chapters')} chs remaining)")
                return 0

        else:
            parser.print_help()
            return 2

        # Output formatting
        if is_json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            if isinstance(res, dict):
                print(f"[OK] [{args.subcommand.upper()}] Success")
                if args.subcommand == "id" and getattr(args, "id_action", "") == "list":
                    for cat, items in res.items():
                        print(f"  [{cat}]:")
                        for item in items:
                            name = item.get("name") or item.get("title") or item.get("hook") or item.get("id")
                            print(f"    - {item.get('id')}: {name}")
                elif args.subcommand == "trace":
                    print(f"  ID: {res.get('id')} ({res.get('category')})")
                    if res.get("current_record"):
                        rec = res.get("current_record")
                        print(f"  Record: {rec.get('name', '')} {rec.get('role', '')}")
                    print(f"  Appearances: {len(res.get('appearances', []))} chapters")
                    print(f"  Co-occurrences: {len(res.get('co_occurrences', []))} pairs")
                else:
                    for k, v in res.items():
                        if isinstance(v, (str, int, float, bool)):
                            print(f"   {k}: {v}")
                        elif isinstance(v, list) and len(v) <= 5:
                            print(f"   {k}: {v}")
            else:
                print(f"[OK] Success: {res}")

        return 0

    except GuardError as e:
        sys.stderr.write(f"\n❌ [Guard Block]: {e.message}\n")
        if e.remediation:
            sys.stderr.write(f"   💡 Remediation: {e.remediation}\n")
        return 1
    except BusinessError as e:
        sys.stderr.write(f"\n❌ [Business Error]: {e.message}\n")
        if e.remediation:
            sys.stderr.write(f"   💡 Remediation: {e.remediation}\n")
        return 1
    except CLIArgumentError as e:
        sys.stderr.write(f"\n❌ [CLI Argument Error]: {e.message}\n")
        return 2
    except EnvironmentError as e:
        sys.stderr.write(f"\n❌ [Environment Error]: {e.message}\n")
        return 3
    except StorageError as e:
        sys.stderr.write(f"\n💥 [Storage System Failure]: {e.message}\n")
        return 4
    except Exception as e:
        sys.stderr.write(f"\n💥 [Unexpected System Error]: {str(e)}\n")
        return 4


if __name__ == "__main__":
    sys.exit(main())
