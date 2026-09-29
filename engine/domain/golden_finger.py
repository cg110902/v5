"""Domain model for LivingGoldenFinger and its multi-stage evolution, energy ledger, and backlash dynamics.

Universal & genre-agnostic: uses structural keys, integer pools, and zero hardcoded Chinese literary terms.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class GoldenFingerStage:
    """Represents a discrete evolutionary phase of the protagonist's cheat/system/artifact."""
    stage_id: str
    stage_name: str
    stage_order: int
    unlock_chapter: int
    max_energy: int = 100
    recharge_rate_per_chapter: int = 10
    unlocked_capabilities: List[str] = field(default_factory=list)
    backlash_severity: int = 0  # 0: none, 1: fatigue, 2: pain, 3: sensory loss, 4: severe impairment, 5: life threat
    backlash_description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GoldenFingerStage:
        return cls(
            stage_id=str(data.get("stage_id", "")),
            stage_name=str(data.get("stage_name", "")),
            stage_order=int(data.get("stage_order", 1)),
            unlock_chapter=int(data.get("unlock_chapter", 1)),
            max_energy=int(data.get("max_energy", 100)),
            recharge_rate_per_chapter=int(data.get("recharge_rate_per_chapter", 10)),
            unlocked_capabilities=list(data.get("unlocked_capabilities", [])),
            backlash_severity=max(0, min(5, int(data.get("backlash_severity", 0)))),
            backlash_description=str(data.get("backlash_description", "")),
        )


@dataclass
class EnergyTransaction:
    """Double-entry transaction tracking golden finger energy consumption and recharge."""
    chapter: int
    amount: int  # Positive for recharge, negative for consumption
    transaction_type: str  # recharge, consume, overdraw, penalty
    resulting_balance: int
    capability_used: str = ""
    triggered_backlash: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EnergyTransaction:
        return cls(
            chapter=int(data.get("chapter", 1)),
            amount=int(data.get("amount", 0)),
            transaction_type=str(data.get("transaction_type", "consume")),
            resulting_balance=int(data.get("resulting_balance", 0)),
            capability_used=str(data.get("capability_used", "")),
            triggered_backlash=bool(data.get("triggered_backlash", False)),
        )


class LivingGoldenFinger:
    """Domain model representing an evolving cheat mechanism with strict resource accounting."""

    def __init__(
        self,
        system_id: str,
        owner_character_id: str = "",
        name: str = "",
        current_stage_id: str = "stage_1",
        stages: Optional[Dict[str, GoldenFingerStage]] = None,
        current_energy: int = 100,
        energy_history: Optional[List[EnergyTransaction]] = None,
        backlash_active: bool = False,
        backlash_cooldown_chapters: int = 0,
        host_id: Optional[str] = None,
    ) -> None:
        self.system_id = str(system_id)
        self.owner_character_id = str(host_id if host_id is not None else owner_character_id)
        self.name = str(name)
        self.current_stage_id = str(current_stage_id)
        self.stages: Dict[str, GoldenFingerStage] = stages or {}
        self.current_energy = int(current_energy)
        self.energy_history: List[EnergyTransaction] = energy_history or []
        self.backlash_active = bool(backlash_active)
        self.backlash_cooldown_chapters = max(0, int(backlash_cooldown_chapters))

    @property
    def host_id(self) -> str:
        return self.owner_character_id

    @property
    def current_stage(self) -> Optional[GoldenFingerStage]:
        return self.stages.get(self.current_stage_id)

    def advance_stage(self, new_stage_id: str, chapter: int) -> None:
        if new_stage_id in self.stages:
            self.current_stage_id = new_stage_id
            stage = self.stages[new_stage_id]
            stage.unlock_chapter = chapter
            # Reset to new max energy
            self.current_energy = stage.max_energy

    def recharge_tick(self, chapter: int) -> EnergyTransaction:
        stage = self.current_stage
        rate = stage.recharge_rate_per_chapter if stage else 10
        max_e = stage.max_energy if stage else 100
        recharge_amount = min(rate, max(0, max_e - self.current_energy))
        self.current_energy += recharge_amount

        # Cooldown countdown
        if self.backlash_cooldown_chapters > 0:
            self.backlash_cooldown_chapters -= 1
            if self.backlash_cooldown_chapters == 0:
                self.backlash_active = False

        tx = EnergyTransaction(
            chapter=chapter,
            amount=recharge_amount,
            transaction_type="recharge",
            resulting_balance=self.current_energy,
        )
        self.energy_history.append(tx)
        return tx

    def consume_energy(self, chapter: int, amount: int, capability: str) -> EnergyTransaction:
        stage = self.current_stage
        is_overdraw = amount > self.current_energy
        triggered_backlash = False

        if is_overdraw:
            triggered_backlash = True
            self.backlash_active = True
            severity = stage.backlash_severity if stage else 2
            self.backlash_cooldown_chapters = max(1, severity)
            tx_type = "overdraw"
            self.current_energy = max(-50, self.current_energy - amount)
        else:
            tx_type = "consume"
            self.current_energy -= amount

        tx = EnergyTransaction(
            chapter=chapter,
            amount=-amount,
            transaction_type=tx_type,
            resulting_balance=self.current_energy,
            capability_used=capability,
            triggered_backlash=triggered_backlash,
        )
        self.energy_history.append(tx)
        return tx

    def consume(self, amount: int, chapter: int = 1, capability: str = "") -> EnergyTransaction:
        """Convenience alias for consume_energy."""
        return self.consume_energy(chapter=chapter, amount=amount, capability=capability)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_id": self.system_id,
            "owner_character_id": self.owner_character_id,
            "name": self.name,
            "current_stage_id": self.current_stage_id,
            "stages": {k: v.to_dict() for k, v in self.stages.items()},
            "current_energy": self.current_energy,
            "energy_history": [tx.to_dict() for tx in self.energy_history],
            "backlash_active": self.backlash_active,
            "backlash_cooldown_chapters": self.backlash_cooldown_chapters,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LivingGoldenFinger:
        stages = {
            k: GoldenFingerStage.from_dict(v)
            for k, v in data.get("stages", {}).items()
        }
        history = [
            EnergyTransaction.from_dict(tx)
            for tx in data.get("energy_history", [])
        ]
        return cls(
            system_id=str(data.get("system_id", "")),
            owner_character_id=str(data.get("owner_character_id", "")),
            name=str(data.get("name", "")),
            current_stage_id=str(data.get("current_stage_id", "stage_1")),
            stages=stages,
            current_energy=int(data.get("current_energy", 100)),
            energy_history=history,
            backlash_active=bool(data.get("backlash_active", False)),
            backlash_cooldown_chapters=int(data.get("backlash_cooldown_chapters", 0)),
        )
