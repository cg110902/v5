"""Novel Studio 5.0 角色动态认知数据追踪器 (Dynamic Cognition Tracker).

纯数据映射与键值更新，绝不包含任何主观文学性判断、模糊子串匹配或体裁硬编码。
文学合理性由 Stage 4 审校专家判定，本模块负责精确数据字段的持久化、认知差额演进与时间线维护。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from engine.core.models import Person, BeatActor
from engine.domain.character import LivingCharacter, ChapterMotive, PhysiologicalState


class CognitionTracker:
    """角色动态认知字段与时间线演变更新器"""

    @staticmethod
    def sync_actor_cognition(person: Person, actor: BeatActor, current_chapter: int) -> None:
        """根据细纲在场声明，同步更新核心角色的动态认知向量与最后露面章节（兼容旧模型）"""
        person.last_seen_ch = current_chapter

        if actor.want:
            person.cognition.current_motive = actor.want
        if actor.fear:
            person.cognition.fear_threshold = actor.fear
        if actor.cognitive_bias:
            person.cognition.cognitive_bias = actor.cognitive_bias
        if actor.status_in:
            person.physiology.injury_desc = actor.status_in

    @staticmethod
    def sync_living_cognition(
        char: LivingCharacter,
        chapter: int,
        motive: ChapterMotive,
        phys: Optional[PhysiologicalState] = None,
    ) -> Dict[str, Any]:
        """将 5.0 动态认知动机与生理状态原子化记录到 LivingCharacter"""
        prev_motive = char.get_motive_at(chapter - 1)
        shift_detected = False
        shift_desc = ""

        if prev_motive and prev_motive.primary_motive != motive.primary_motive:
            shift_detected = True
            shift_desc = f"Motive shifted from '{prev_motive.primary_motive}' to '{motive.primary_motive}'"
            if not motive.motive_shift_reason:
                motive.motive_shift_reason = shift_desc

        char.record_motive(chapter, motive)

        if phys is not None:
            char.record_physiology(chapter, phys)

        return {
            "character_id": char.character_id,
            "chapter": chapter,
            "shift_detected": shift_detected,
            "motive": motive.to_dict(),
            "has_physiology": phys is not None,
        }

    @staticmethod
    def detect_cognitive_shift(char: LivingCharacter, current_chapter: int) -> Dict[str, Any]:
        """分析角色在最近两次露面之间的认知突变与生理变化"""
        history_chapters = sorted([c for c in char.motive_history.keys() if c <= current_chapter])
        if len(history_chapters) < 2:
            return {
                "character_id": char.character_id,
                "has_previous": False,
                "motive_changed": False,
                "urgency_delta": 0,
            }

        curr_ch = history_chapters[-1]
        prev_ch = history_chapters[-2]
        m_curr = char.motive_history[curr_ch]
        m_prev = char.motive_history[prev_ch]

        motive_changed = m_curr.primary_motive != m_prev.primary_motive
        urgency_delta = m_curr.urgency - m_prev.urgency

        return {
            "character_id": char.character_id,
            "has_previous": True,
            "prev_chapter": prev_ch,
            "curr_chapter": curr_ch,
            "motive_changed": motive_changed,
            "prev_motive": m_prev.primary_motive,
            "curr_motive": m_curr.primary_motive,
            "urgency_delta": urgency_delta,
            "shift_reason": m_curr.motive_shift_reason,
            "gap_chapters": curr_ch - prev_ch,
        }

    @staticmethod
    def record_learned_fact(char: LivingCharacter, fact: str, chapter: int) -> None:
        """更新角色的认识论边界（防止全知泄漏）"""
        char.epistemology.learn(fact, chapter)
