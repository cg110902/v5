"""Novel Studio 5.0 确定性词表机械消杀引擎 (Lexicon Engine 2.0).

核心原则：
1. 词表内容 100% 外部数据驱动（来自 templates/lexicon.json 或 workspace/lexicon.json），代码零硬编码；
2. 长词优先（Longest-Match-First）：按 key 长度降序排序，避免子串先被截断；
3. 保护词豁免（Protected List）：protect 中的词组整体保护，绝不改动其中任何字；
4. 确定性哈希轮换（Deterministic Rotate）：根据 md5(chapter_id + 原词) 确定轮换起点，同章同次序完全幂等，跨章错开，章内高频词依序轮转；
5. 单遍不链式正则替换（Single-Pass Idempotent）：正则单遍扫描，不重扫刚插入的词。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from engine.errors import BusinessError


def _pick_rotation(candidates: List[str], chapter_id: str, src: str, occurrence_idx: int) -> str:
    """为第 occurrence_idx 次出现的 src 选择轮换候选（确定性 · 跨章错开 · 章内轮转）。"""
    seed = hashlib.md5(f"{chapter_id}|{src}".encode("utf-8")).hexdigest()
    offset = int(seed[:8], 16) % len(candidates)
    return candidates[(offset + occurrence_idx) % len(candidates)]


class LexiconEngine:
    """确定性词表消杀引擎"""

    def __init__(self, lexicon_data: Optional[Dict[str, Any]] = None):
        data = lexicon_data or {}
        self.lexicon_map: Dict[str, str] = dict(data.get("lexicon", {}))
        self.rotate_map: Dict[str, List[str]] = dict(data.get("rotate", {}))
        
        # protect 可以是列表，也可以是包含各分组名称的字典
        raw_protect = data.get("protect", [])
        if isinstance(raw_protect, dict):
            protect_list: List[str] = []
            for v in raw_protect.values():
                if isinstance(v, list):
                    protect_list.extend(v)
            self.protect_list = list(dict.fromkeys(protect_list))
        elif isinstance(raw_protect, list):
            self.protect_list = list(dict.fromkeys(raw_protect))
        else:
            self.protect_list = []

    @classmethod
    def load_from_file(cls, filepath: Union[str, Path]) -> "LexiconEngine":
        """从单个文件加载词表"""
        p = Path(filepath).resolve()
        if not p.is_file():
            return cls()
        try:
            with open(p, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
                return cls(data)
        except Exception as e:
            raise BusinessError(f"读取词表文件 [{p}] 失败: {e}")

    @classmethod
    def load_cascaded(cls, workspace: Union[str, Path], templates_dir: Optional[Union[str, Path]] = None) -> "LexiconEngine":
        """级联加载：全局基线 (templates/lexicon.json) -> 本书覆盖 (workspace/lexicon.json)"""
        ws = Path(workspace).resolve()
        engine = cls()

        # 1. 尝试基线词表
        candidate_template_paths: List[Path] = []
        if templates_dir:
            candidate_template_paths.append(Path(templates_dir) / "lexicon.json")
        # 常见相对路径查找
        candidate_template_paths.append(ws.parent / "templates" / "lexicon.json")
        candidate_template_paths.append(Path(__file__).resolve().parent.parent.parent / "templates" / "lexicon.json")

        for tp in candidate_template_paths:
            if tp.is_file():
                engine = cls.load_from_file(tp)
                break

        # 2. 尝试工作区专有覆盖
        ws_lexicon = ws / "lexicon.json"
        if ws_lexicon.is_file():
            ws_engine = cls.load_from_file(ws_lexicon)
            engine = engine.merge(ws_engine)

        return engine

    def merge(self, override: "LexiconEngine") -> "LexiconEngine":
        """合并覆盖词表（高优先级覆盖低优先级，恒等替换即停用下层规则）"""
        new_lex = dict(self.lexicon_map)
        for k, v in override.lexicon_map.items():
            if k == v:
                # 恒等映射 = 显式停用下层规则
                new_lex.pop(k, None)
            else:
                new_lex[k] = v

        new_rot = dict(self.rotate_map)
        new_rot.update(override.rotate_map)

        new_prot = list(dict.fromkeys(self.protect_list + override.protect_list))
        return LexiconEngine({
            "lexicon": new_lex,
            "rotate": new_rot,
            "protect": new_prot,
        })

    def apply(self, text: str, chapter_id: str = "ch_001") -> Tuple[str, Dict[str, int]]:
        """执行单遍确定性替换与消杀，返回 (处理后文本, 命中频次字典)。"""
        if not text:
            return text, {}

        processed, hits = self.apply_detailed(text, chapter_id)
        stats = {h["word"]: h["count"] for h in hits}
        return processed, stats

    def apply_detailed(self, text: str, chapter_id: str = "ch_001") -> Tuple[str, List[Dict[str, Any]]]:
        """执行单遍确定性替换与消杀，返回 (处理后文本, 详细命中清单)。"""
        if not text:
            return text, []

        active_lex = {k: v for k, v in self.lexicon_map.items() if k != v}
        active_rot = {k: v for k, v in self.rotate_map.items() if isinstance(v, list) and len(v) > 0}
        protect_set = set(p for p in self.protect_list if p)

        all_rules: Dict[str, Any] = dict(active_lex)
        all_rules.update(active_rot)

        if not all_rules and not protect_set:
            return text, []

        _PROTECT_SENTINEL = object()
        table: Dict[str, Any] = dict(all_rules)
        for p in protect_set:
            table[p] = _PROTECT_SENTINEL

        # 排序：长词优先匹配
        keys = sorted(table.keys(), key=len, reverse=True)
        pattern = re.compile("|".join(re.escape(k) for k in keys if k))

        counts: Dict[str, int] = {}
        chosen: Dict[str, Dict[str, int]] = {}

        def replacer(match: re.Match) -> str:
            word = match.group(0)
            spec = table[word]
            if spec is _PROTECT_SENTINEL:
                # 受保护词，原样返回，不计入命中
                return word

            n = counts.get(word, 0)
            counts[word] = n + 1

            if isinstance(spec, list):
                pick = _pick_rotation(spec, chapter_id, word, n)
                bucket = chosen.setdefault(word, {})
                bucket[pick] = bucket.get(pick, 0) + 1
                return pick
            elif isinstance(spec, str):
                return spec
            return word

        processed_text = pattern.sub(replacer, text)

        hits: List[Dict[str, Any]] = []
        for w, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            spec = all_rules[w]
            entry: Dict[str, Any] = {"word": w, "count": c}
            if isinstance(spec, list):
                entry["mode"] = "rotate"
                entry["candidates"] = spec
                entry["to"] = "／".join(f"{k}×{v}" for k, v in sorted(chosen.get(w, {}).items(), key=lambda kv: -kv[1]))
            else:
                entry["mode"] = "replace" if spec else "delete"
                entry["to"] = spec
            hits.append(entry)

        return processed_text, hits
