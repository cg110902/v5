"""Novel Studio 5.0 业务工步与总控编排器 (Pipeline Orchestrator)。

提供一键化、原子级工业流水线编排接口：
- init: 新书初始化与全量脚手架播种
- pack: 生成自完备上下文 pack.md
- finalize: 词表消杀定稿落地
- sync: 涌现事实平账、八表合账与快照封存
- build: 复合一键收口命令 (finalize + sync + snapshot)
- check: 全书双核合规体检
"""
import os
import shutil
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from engine.errors import BusinessError, GuardError
from engine.core.storage import ensure_directory, atomic_write_json, atomic_write_text, safe_load_json
from engine.core.parser import parse_beat_file
from engine.core.ledger import LedgerManager
from engine.core.snapshots import create_snapshot
from engine.text.lexicon import LexiconEngine
from engine.text.probes import PhysicalProbes
from engine.pipeline.pack_builder import PackBuilder
from engine.pipeline.reconciler import FactReconciler


class StudioOrchestrator:
    """工作室业务编排总控"""

    def __init__(self, workspace: Path):
        self.workspace = Path(workspace).resolve()

    def init_book(self, title: str, genre: str, protagonist: str, force: bool = False) -> Dict[str, Any]:
        """初始化新书工作区"""
        ensure_directory(self.workspace)
        proj_file = self.workspace / "project.json"
        if proj_file.is_file() and not force:
            raise BusinessError(
                f"工作区 [{self.workspace}] 已存在书籍项目！",
                remediation="若需强制重置，请在 CLI 中附带 --force 参数。"
            )

        # 1. 建立目录拓扑
        subdirs = [
            "state", "outlines/vol_01/beats", "manuscript/vol_01/raw",
            "manuscript/vol_01/final", "log/audit", "log/review",
            "bible", "characters", "entities/items", "entities/factions", "entities/locations"
        ]
        for d in subdirs:
            ensure_directory(self.workspace / d)

        # 2. 播种 project.json
        project_data = {
            "schema": "novel-studio.project/v5",
            "title": title,
            "genre": genre,
            "protagonist": protagonist,
            "scope": {
                "target_words_min": 2000,
                "target_words_max": 3500,
                "chapters_per_volume": 30
            },
            "engine": {
                "token_cap": 32000,
                "cruise_max_chapters": 10
            },
            "current_status": "initialized",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        atomic_write_json(proj_file, project_data)

        # 3. 播种空状态表
        state_dir = self.workspace / "state"
        atomic_write_json(state_dir / "persons.json", [{
            "id": "p_001",
            "name": protagonist,
            "type": "person",
            "role": "protagonist",
            "tier_rank": 1,
            "life_status": "alive",
            "last_seen_ch": 0
        }])
        atomic_write_json(state_dir / "items.json", [])
        atomic_write_json(state_dir / "factions.json", [])
        atomic_write_json(state_dir / "places.json", [])
        atomic_write_json(state_dir / "lines.json", [])
        atomic_write_json(state_dir / "locked.json", [])
        atomic_write_json(state_dir / "debts.json", [])
        atomic_write_json(state_dir / "milestones.json", [])
        atomic_write_json(state_dir / "macro_events.json", [])
        atomic_write_json(state_dir / "ledger.json", {"pools": {"copper": 1000}, "transactions": []})
        atomic_write_json(state_dir / "current.json", {"chapter": 0, "persons_present": [protagonist]})
        atomic_write_json(state_dir / "sync_log.json", {})

        # 4. 播种空覆盖词表骨架
        atomic_write_json(self.workspace / "lexicon.json", {
            "schema": "novel-studio.lexicon/v2",
            "lexicon": {},
            "rotate": {},
            "protect": []
        })

        # 5. 播种模板脚手架
        tpl_dir = Path(__file__).resolve().parent.parent.parent / "templates"
        if tpl_dir.is_dir():
            # 复制 bible/
            bible_src = tpl_dir / "bible"
            if bible_src.is_dir():
                for f in bible_src.glob("*.md"):
                    dst = self.workspace / "bible" / f.name
                    if not dst.exists():
                        atomic_write_text(dst, f.read_text(encoding="utf-8"))

            # 复制 characters/
            char_src = tpl_dir / "characters"
            if char_src.is_dir():
                for f in char_src.glob("*.md"):
                    dst = self.workspace / "characters" / f.name
                    if not dst.exists():
                        atomic_write_text(dst, f.read_text(encoding="utf-8"))

            # 复制 outlines/
            out_src = tpl_dir / "outlines"
            if out_src.is_dir():
                main_plot = out_src / "main_plot.md"
                if main_plot.is_file():
                    atomic_write_text(self.workspace / "outlines" / "main_plot.md", main_plot.read_text(encoding="utf-8"))
                vol_outline = out_src / "volume_outline.md"
                if vol_outline.is_file():
                    atomic_write_text(self.workspace / "outlines" / "vol_01" / "outline.md", vol_outline.read_text(encoding="utf-8"))

        return {"status": "success", "workspace": str(self.workspace), "title": title}

    def pack_chapter(self, chapter_id: str) -> Path:
        """装配指定章节上下文数据包"""
        builder = PackBuilder(self.workspace)
        return builder.build(chapter_id)

    def finalize_chapter(self, chapter_id: str) -> Dict[str, Any]:
        """定稿章节：吸纳词表消杀，输出最终 manuscript/vol_XX/final/ch_XXX.md"""
        raw_path = self._locate_manuscript_raw(chapter_id)
        if not raw_path or not raw_path.is_file():
            raise BusinessError(f"未找到章节 [{chapter_id}] 的起草文稿 (raw/ch_XXX_vX.md)！")

        with open(raw_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        # 空正文物理熔断
        PhysicalProbes.assert_not_empty(raw_text, chapter_id=chapter_id)

        # 加载词表引擎 (基线 + 本书覆盖)
        base_lex_path = Path(__file__).resolve().parent.parent.parent / "templates" / "lexicon.json"
        engine = LexiconEngine.load_from_file(base_lex_path)

        local_lex_path = self.workspace / "lexicon.json"
        if local_lex_path.is_file():
            engine = engine.merge(LexiconEngine.load_from_file(local_lex_path))

        # 执行消杀
        final_text, stats = engine.apply(raw_text, chapter_id=chapter_id)

        # 确定定稿输出路径
        # 将 raw 替换为 final，去掉 _v1/_v2/_v3 后缀
        final_filename = f"{chapter_id}.md"
        final_dir = raw_path.parent.parent / "final"
        ensure_directory(final_dir)
        final_path = final_dir / final_filename

        atomic_write_text(final_path, final_text)

        word_count = PhysicalProbes.count_words(final_text)
        return {
            "status": "success",
            "chapter_id": chapter_id,
            "final_path": str(final_path),
            "word_count": word_count,
            "lexicon_stats": stats
        }

    def sync_chapter(self, chapter_id: str, force: bool = False) -> Dict[str, Any]:
        """事实对账与台账封存"""
        # 1. 定位 final 正文
        final_path = self._locate_manuscript_final(chapter_id)
        if not final_path or not final_path.is_file():
            raise BusinessError(f"未找到章节 [{chapter_id}] 的定稿正文 (final/{chapter_id}.md)，请先执行 finalize！")

        with open(final_path, "r", encoding="utf-8") as f:
            final_text = f.read()

        PhysicalProbes.assert_not_empty(final_text, chapter_id=chapter_id)

        # 2. 定位细纲文件
        beat_path = self._locate_beat_file(chapter_id)
        if not beat_path or not beat_path.is_file():
            raise BusinessError(f"未找到章节 [{chapter_id}] 的细纲任务卡！")

        with open(beat_path, "r", encoding="utf-8") as f:
            beat_content = f.read()
        beats, _ = parse_beat_file(beat_content)

        ledger = LedgerManager(self.workspace)
        ledger.load_all()

        # 3. 涌现事实提取平账
        reconciler = FactReconciler(self.workspace, ledger)
        reconcile_actions = reconciler.extract_and_apply_emergence(chapter_id)

        # 4. 执行状态合账
        sync_res = ledger.apply_sync(chapter_id, beats, final_text, force=force)

        # 5. 自动创建安全快照
        snap_meta = create_snapshot(self.workspace, chapter_id)

        return {
            "status": "success",
            "chapter_id": chapter_id,
            "words": sync_res.get("words", 0),
            "reconcile_actions": reconcile_actions,
            "healed": sync_res.get("healed", []),
            "snapshot": snap_meta.get("name")
        }

    def build_chapter(self, chapter_id: str) -> Dict[str, Any]:
        """一键复合命令：定稿 + 涌现平账 + 八表同步 + 快照封存"""
        finalize_res = self.finalize_chapter(chapter_id)
        sync_res = self.sync_chapter(chapter_id, force=True)
        return {
            "status": "success",
            "chapter_id": chapter_id,
            "word_count": finalize_res["word_count"],
            "lexicon_stats": finalize_res["lexicon_stats"],
            "reconcile_actions": sync_res["reconcile_actions"],
            "snapshot": sync_res["snapshot"]
        }

    def check_workspace(self) -> Dict[str, List[str]]:
        """全书与双核合规体检"""
        errors = []
        warnings = []

        # 检查损坏文件残留
        state_dir = self.workspace / "state"
        if state_dir.is_dir():
            corrupt_files = list(state_dir.glob("*.corrupt*"))
            if corrupt_files:
                errors.append(f"发现已隔离的损坏数据文件残留: {[f.name for f in corrupt_files]}")

        # 检查未消除槽位 {{slot:}}
        for p in self.workspace.rglob("*.md"):
            if "snapshots" in str(p) or "log" in str(p):
                continue
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cnt = f.read()
                    if "{{slot:" in cnt:
                        warnings.append(f"文件 [{p.relative_to(self.workspace)}] 尚存未填写的占位槽位 (slot)")
            except Exception:
                pass

        return {"errors": errors, "warnings": warnings}

    def _locate_beat_file(self, chapter_id: str) -> Optional[Path]:
        outlines_dir = self.workspace / "outlines"
        if outlines_dir.is_dir():
            for p in outlines_dir.rglob(f"{chapter_id}.md"):
                return p
        return None

    def _locate_manuscript_raw(self, chapter_id: str) -> Optional[Path]:
        ms_dir = self.workspace / "manuscript"
        if not ms_dir.is_dir():
            return None
        # 寻找优先级：_v3 > _v2 > _v1 > 无后缀
        for v in ["_v3", "_v2", "_v1", ""]:
            for p in ms_dir.rglob(f"{chapter_id}{v}.md"):
                if "raw" in str(p):
                    return p
        return None

    def _locate_manuscript_final(self, chapter_id: str) -> Optional[Path]:
        ms_dir = self.workspace / "manuscript"
        if not ms_dir.is_dir():
            return None
        for p in ms_dir.rglob(f"{chapter_id}.md"):
            if "final" in str(p):
                return p
        return None
