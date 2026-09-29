"""Novel Studio 5.0 自完备上下文装配器 (Pack Builder)。

核心功能：
1. 根据单章细纲 (beats/ch_XXX.md) 的实际登场人物与场景，实施 P0~P3 四级按需装配；
2. 物理屏蔽全书中 90% 与当章无关的角色与旁支设定，杜绝模型注意力分散与上下文膨胀；
3. 输出自完备无损数据包 pack.md，供 Stage 2 Drafter 起手单次全读。
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
from engine.core.parser import parse_beat_file
from engine.core.ledger import LedgerManager
from engine.core.storage import atomic_write_text


class PackBuilder:
    """自完备上下文装配引擎"""

    def __init__(self, workspace: Path):
        self.workspace = Path(workspace).resolve()
        self.ledger = LedgerManager(self.workspace)
        self.ledger.load_all()

    def build(self, chapter_id: str) -> Path:
        """为指定章节生成自完备 pack.md"""
        # 定位细纲文件
        beat_path = self._locate_beat_file(chapter_id)
        if not beat_path or not beat_path.is_file():
            raise FileNotFoundError(f"未找到章节 [{chapter_id}] 的细纲任务卡！")

        with open(beat_path, "r", encoding="utf-8") as f:
            content = f.read()

        beats, body = parse_beat_file(content)

        pack_sections = []

        # P0 级：单章指令核心与创作公理
        pack_sections.append(f"# 【{chapter_id} 《{beats.title}》 创作全景装配包 (Pack)】\n")
        pack_sections.append("## 一、 当章核心编剧细纲 (Intent Source)\n")
        pack_sections.append(body.strip())
        pack_sections.append("\n---\n")

        # P1 级：在场角色全息动态卡（仅装配在场人物，屏蔽其余无关角色）
        pack_sections.append("## 二、 当章在场人物动态矩阵 (Present Characters)\n")
        for actor in beats.present_characters:
            p = self.ledger.find_person(actor.id, actor.name)
            p_desc = f"- **【{actor.name}】** (ID: {actor.id or 'auto'}, 角色定位: {actor.role})\n"
            p_desc += f"  - 即时诉求 (Want): {actor.want or '暂无'}\n"
            p_desc += f"  - 即时软肋 (Fear): {actor.fear or '暂无'}\n"
            p_desc += f"  - 入场状态 (Status In): {actor.status_in or '正常'}\n"
            if actor.cognitive_bias:
                p_desc += f"  - 当期偏见 (Bias): {actor.cognitive_bias}\n"
            if actor.current_motive:
                p_desc += f"  - 当期动机 (Motive): {actor.current_motive}\n"
            if actor.deployed_cards:
                p_desc += f"  - 本章决定打出底牌: {', '.join(actor.deployed_cards)}\n"
            if actor.concealed_cards:
                p_desc += f"  - 本章隐瞒保留底牌: {', '.join(actor.concealed_cards)}\n"
            if p:
                if p.sensory_anchor:
                    p_desc += f"  - 标志物象 (Sensory Anchor): {p.sensory_anchor}\n"
                if p.micro_actions:
                    p_desc += f"  - 惯性神态动作: {', '.join(p.micro_actions)}\n"
                if p.address_matrix:
                    p_desc += f"  - 称谓规则: {dict(p.address_matrix)}\n"
            pack_sections.append(p_desc)

        # 挂载本章底牌调度矩阵
        if beats.trump_cards:
            pack_sections.append("\n### 🃏 本章底牌与筹码调度 (Trump Cards)\n")
            for tc in beats.trump_cards:
                if isinstance(tc, dict):
                    t_name = tc.get("trump_name", "")
                    t_holder = tc.get("holder", "")
                    t_used = tc.get("used_in_chapter", False)
                    t_rev = tc.get("revealed_to_readers", False)
                else:
                    t_name = getattr(tc, "trump_name", "")
                    t_holder = getattr(tc, "holder", "")
                    t_used = getattr(tc, "used_in_chapter", False)
                    t_rev = getattr(tc, "revealed_to_readers", False)
                used_str = "【本章出牌】" if t_used else "【隐忍保留】"
                pack_sections.append(f"- {used_str} 《{t_name}》 (持有者: {t_holder}, 对读者公开: {t_rev})\n")
        pack_sections.append("\n---\n")

        # P2 级：时空坐标与微观场景环境法则
        pack_sections.append("## 三、 时空坐标与场景法则 (Spatiotemporal & Environment)\n")
        st = beats.spatiotemporal or {}
        loc = st.get("location") or "未知场景"
        day = st.get("current_day", 1)
        hour = st.get("current_hour", 12)
        weather = st.get("weather", "平稳")
        pack_sections.append(f"- 时空定位: 第 {day} 天 {hour:02d}:00 ｜ 地点: 【{loc}】 ｜ 气象: {weather}\n")

        # 从台账拉取地点深度物理属性
        place = self.ledger.find_place("", loc)
        sensory = (place.sensory_anchor if place and place.sensory_anchor else "") or beats.scene_environment.get("sensory_focus", "暂无")
        rules = (place.environment_rules if place and place.environment_rules else []) or beats.scene_environment.get("environment_rules", [])
        pack_sections.append(f"- 核心感官聚焦（严格禁嗅觉）: {sensory}\n")
        if rules:
            pack_sections.append("- 空间客观限制与物理法则:\n")
            for r in rules:
                pack_sections.append(f"  * {r}\n")

        # 宏观世界事件时钟
        if beats.macro_events:
            pack_sections.append("\n### 🌍 世界宏观局势时钟 (Macro World Clock)\n")
            for me in beats.macro_events:
                if isinstance(me, dict):
                    m_id = me.get("event_id", "")
                    m_stage = me.get("stage", "")
                else:
                    m_id = getattr(me, "event_id", "")
                    m_stage = getattr(me, "stage", "")
                pack_sections.append(f"- 事件: {m_id} ｜ 当前演化阶段: {m_stage}\n")
        pack_sections.append("\n---\n")

        # P3 级：前章断章残局承接（若存在上一章 final，提取末尾 300 字）
        prev_slice = self._get_previous_chapter_ending(chapter_id)
        if prev_slice:
            pack_sections.append("## 四、 上一章章末物理承接画面 (Previous Chapter Ending)\n")
            pack_sections.append(f"> {prev_slice}\n")
            pack_sections.append("> *(提示：本章第一句话必须物理承接上文姿态/动作/现场，严禁跳跃)*\n\n---\n")

        # P0 级底座：世界核心客观公理与创作禁令
        world_axioms = self._load_world_axioms()
        if world_axioms:
            pack_sections.append("## 五、 世界底层公理与绝对红线 (World Axioms & Guardrails)\n")
            pack_sections.append(world_axioms.strip())
            pack_sections.append("\n")

        pack_content = "\n".join(pack_sections)
        target_pack = self.workspace / "pack.md"
        atomic_write_text(target_pack, pack_content)
        return target_pack

    def _locate_beat_file(self, chapter_id: str) -> Optional[Path]:
        """定位细纲文件路径"""
        outlines_dir = self.workspace / "outlines"
        if not outlines_dir.is_dir():
            return None
        for p in outlines_dir.rglob(f"{chapter_id}.md"):
            return p
        return None

    def _get_previous_chapter_ending(self, chapter_id: str) -> str:
        """获取前一章 final 正文末尾片段"""
        import re
        m = re.search(r"\d+", chapter_id)
        if not m:
            return ""
        ch_num = int(m.group(0))
        if ch_num <= 1:
            return ""

        prev_id = f"ch_{ch_num - 1:03d}"
        ms_dir = self.workspace / "manuscript"
        if not ms_dir.is_dir():
            return ""

        for p in ms_dir.rglob(f"{prev_id}.md"):
            if "final" in str(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        lines = [line.strip() for line in f if line.strip()]
                        if lines:
                            tail = "\n".join(lines[-4:])
                            return tail[-300:]
                except Exception:
                    pass
        return ""

    def _load_world_axioms(self) -> str:
        """读取世界底层公理"""
        axioms_file = self.workspace / "bible" / "01_world_axioms.md"
        if axioms_file.is_file():
            try:
                with open(axioms_file, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
        return ""
