"""Novel Studio 5.0 安全时光机系统 (Snapshot Time-Machine)。

功能：
1. 一键创建工作区快照（含 state/, outlines/, manuscript/, log/）；
2. 一键安全回滚（回滚前先自动备份当前现场为 pre_rollback_<时间戳>）；
3. 清单对齐清除机制（回滚时按快照清单清理快照创建后新增的残留文件，绝无幽灵文件污染）。
"""
import os
import shutil
import time
import json
from pathlib import Path
from typing import List, Dict, Any
from engine.errors import BusinessError
from engine.core.storage import ensure_directory, atomic_write_json


PROTECTED_SNAPSHOT_DIRS = ["state", "outlines", "manuscript", "log"]


def get_snapshots_dir(workspace: Path) -> Path:
    d = Path(workspace).resolve() / "snapshots"
    ensure_directory(d)
    return d


def create_snapshot(workspace: Path, name: str) -> Dict[str, Any]:
    """创建安全快照"""
    ws = Path(workspace).resolve()
    snap_root = get_snapshots_dir(ws)
    target_dir = snap_root / name

    if target_dir.exists():
        raise BusinessError(
            f"快照 [{name}] 已存在，禁止重名覆盖！",
            remediation="请使用新的快照名称，或先删除旧快照。"
        )

    ensure_directory(target_dir)

    manifest_files = []
    for d_name in PROTECTED_SNAPSHOT_DIRS:
        src = ws / d_name
        if src.is_dir():
            dst = target_dir / d_name
            shutil.copytree(str(src), str(dst), dirs_exist_ok=True)
            for root, _, files in os.walk(str(src)):
                for f in files:
                    rel_path = Path(root).relative_to(ws) / f
                    manifest_files.append(str(rel_path).replace("\\", "/"))

    meta = {
        "name": name,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": int(time.time()),
        "file_count": len(manifest_files),
        "manifest": manifest_files
    }
    atomic_write_json(target_dir / "manifest.json", meta)

    return meta


def list_snapshots(workspace: Path) -> List[Dict[str, Any]]:
    """列出所有历史快照"""
    snap_root = get_snapshots_dir(workspace)
    results = []
    for item in sorted(snap_root.iterdir()):
        if item.is_dir() and (item / "manifest.json").is_file():
            try:
                with open(item / "manifest.json", "r", encoding="utf-8") as f:
                    results.append(json.load(f))
            except Exception:
                results.append({"name": item.name, "created_at": "unknown"})
    return results


def rollback_snapshot(workspace: Path, name: str) -> Dict[str, Any]:
    """安全回滚至指定快照"""
    ws = Path(workspace).resolve()
    snap_root = get_snapshots_dir(ws)
    target_dir = snap_root / name

    if not target_dir.is_dir():
        raise BusinessError(
            f"目标快照 [{name}] 不存在！",
            remediation="请通过 snapshot list 查看有效的历史快照清单。"
        )

    manifest_path = target_dir / "manifest.json"
    if not manifest_path.is_file():
        raise BusinessError(f"快照 [{name}] 缺少清单元数据 manifest.json，已被破坏！")

    with open(manifest_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # 1. 自动备份当前现场
    auto_backup_name = f"pre_rollback_{int(time.time())}"
    create_snapshot(workspace, auto_backup_name)

    # 2. 清理当前目录中的受管目录，避免残留
    for d_name in PROTECTED_SNAPSHOT_DIRS:
        cur_d = ws / d_name
        if cur_d.is_dir():
            shutil.rmtree(str(cur_d))

    # 3. 从快照恢复
    for d_name in PROTECTED_SNAPSHOT_DIRS:
        snap_d = target_dir / d_name
        if snap_d.is_dir():
            shutil.copytree(str(snap_d), str(ws / d_name))

    return {
        "status": "success",
        "restored_snapshot": name,
        "auto_backup": auto_backup_name,
        "restored_files": meta.get("file_count", 0)
    }
