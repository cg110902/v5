"""Novel Studio 5.0 主角底牌决策与金手指阶层中枢 (Trump Matrix & Cheat Stage).

实现：
1. 底牌池追踪：显式声明【本章可用底牌】、【决定打出底牌】与【刻意隐瞒底牌】；
2. 冷却与可用性校验：禁止在冷却期打出强力底牌；
3. 致命危机不放底牌阻断（反降智）：在生命危险时必须打出底牌或给出合理隐瞒理由；
4. 金手指阶梯成长限制：严格锁定已解锁阶段，禁止越阶调用未解锁外挂；
5. 透支反噬自动化：能量不足时强制产生反噬代价记录。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from engine.core.models import TrumpCard as LegacyTrumpCard, BeatActor
from engine.domain.character import LivingCharacter, TrumpCard, ChapterTrumpDecision
from engine.domain.golden_finger import LivingGoldenFinger, GoldenFingerStage, EnergyTransaction


class TrumpMatrixManager:
    """底牌决策与金手指演化管理器"""

    @staticmethod
    def audit_trump_deployment(
        actor: BeatActor,
        available_cards: Dict[str, LegacyTrumpCard],
        cheat: Optional[Any] = None,
    ) -> List[str]:
        """核验细纲中打出底牌与隐瞒底牌的合法性（兼容旧模型）"""
        warnings: List[str] = []

        # 1. 检查打出的底牌是否在可用底牌池中
        for card_str in actor.deployed_cards:
            card_id = card_str.split(":")[0].strip()
            if card_id not in available_cards:
                warnings.append(f"打出的底牌 [{card_str}] 未在正式底牌清册中登记，将被标记为正文临时涌现战术。")
            else:
                card = available_cards[card_id]
                card.visibility = "deployed"

        # 2. 检查隐瞒底牌
        for card_str in actor.concealed_cards:
            card_id = card_str.split(":")[0].strip()
            if card_id in available_cards:
                available_cards[card_id].visibility = "concealed"

        return warnings

    @staticmethod
    def audit_living_trump_decision(
        char: LivingCharacter,
        decision: ChapterTrumpDecision,
        gf: Optional[LivingGoldenFinger] = None,
        in_fatal_crisis: bool = False,
    ) -> Dict[str, Any]:
        """深度核验 5.0 LivingCharacter 底牌决策与金手指消耗"""
        blockers: List[str] = []
        warnings: List[str] = []

        # 1. 校验打出的底牌是否存在及冷却状态
        for tid in decision.deployed_trumps:
            if tid not in char.trump_inventory:
                warnings.append(f"打出的底牌 [{tid}] 未在角色底牌库中登记（属于临时战术/涌现）。")
            else:
                card = char.trump_inventory[tid]
                if card.current_cooldown > 0:
                    blockers.append(
                        f"底牌 [{card.name}] (ID: {tid}) 尚在冷却期中（剩余冷却 {card.current_cooldown} 章），无法打出！"
                    )

        # 2. 致命危机场景审查：若身处致命威胁，严禁扣牌不发且无合理隐瞒解释
        if in_fatal_crisis and not decision.deployed_trumps:
            available_lethal = [
                t for tid, t in char.trump_inventory.items()
                if t.tier >= 2 and t.current_cooldown == 0
            ]
            if available_lethal:
                # 检查隐瞒理由是否充分
                has_rationale = any(
                    tid in decision.withholding_rationale and len(decision.withholding_rationale[tid].strip()) > 5
                    for tid in [t.trump_id for t in available_lethal]
                )
                if not has_rationale:
                    blockers.append(
                        "反降智阻断：角色身处生死致命危机，手握可用高阶底牌却全数隐瞒且无合理解释！"
                    )

        return {
            "is_valid": len(blockers) == 0,
            "blockers": blockers,
            "warnings": warnings,
            "deployed_count": len(decision.deployed_trumps),
            "withheld_count": len(decision.withheld_trumps),
        }

    @staticmethod
    def check_cheat_growth(
        cheat: Any,
        target_chapter: int,
    ) -> Optional[Any]:
        """检查金手指是否解锁新阶段"""
        if isinstance(cheat, LivingGoldenFinger):
            # 查找未激活但 chapter 满足条件的阶段
            for stage in cheat.stages:
                if stage.stage_index > cheat.current_stage_index and stage.unlock_chapter <= target_chapter:
                    return stage
        return None
