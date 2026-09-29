"""Domain model for LivingCharacter and its dynamic cognitive, physiological, and strategic subsystems.

Universal & genre-agnostic: uses structural keys, integer/float metrics, and zero hardcoded Chinese literary terms.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set


@dataclass
class ChapterMotive:
    """Dynamic character motivation and cognitive boundary for a specific chapter."""
    chapter: int
    primary_motive: str
    sub_motives: List[str] = field(default_factory=list)
    urgency: int = 1  # 1 (casual) to 5 (immediate existential threat)
    moral_redline: str = ""  # Specific structural rule: what character will refuse to do
    blind_spot: str = ""  # Critical cognitive oversight/vulnerability
    motive_shift_reason: str = ""  # Causal explanation if changed from previous chapter

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChapterMotive:
        return cls(
            chapter=int(data.get("chapter", 1)),
            primary_motive=str(data.get("primary_motive", "")),
            sub_motives=list(data.get("sub_motives", [])),
            urgency=int(data.get("urgency", 1)),
            moral_redline=str(data.get("moral_redline", "")),
            blind_spot=str(data.get("blind_spot", "")),
            motive_shift_reason=str(data.get("motive_shift_reason", "")),
        )


@dataclass
class PhysiologicalState:
    """Physical and physiological condition for a specific chapter."""
    chapter: int
    injury_level: int = 0  # 0: uninjured, 1: minor scratches, 2: flesh wound, 3: bone/functional impairment, 4: critical incapacitation, 5: terminal
    injury_description: str = ""
    stamina_pool: int = 100  # 0 to 100
    stress_level: int = 0  # 0 to 100
    recovery_turns_needed: int = 0
    handicaps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PhysiologicalState:
        return cls(
            chapter=int(data.get("chapter", 1)),
            injury_level=max(0, min(5, int(data.get("injury_level", 0)))),
            injury_description=str(data.get("injury_description", "")),
            stamina_pool=max(0, min(100, int(data.get("stamina_pool", 100)))),
            stress_level=max(0, min(100, int(data.get("stress_level", 0)))),
            recovery_turns_needed=max(0, int(data.get("recovery_turns_needed", 0))),
            handicaps=list(data.get("handicaps", [])),
        )


@dataclass
class TrumpCard:
    """Strategic hidden capability, artifact, ally summon, or technique."""
    trump_id: str
    name: str
    category: str = "technique"  # item, technique, bloodline, ally, forbidden_art
    tier: int = 1
    cooldown_chapters: int = 0
    current_cooldown: int = 0
    sacrifice_cost: str = ""  # Cost incurred when unleashed (e.g. burn_lifespan, destroy_gear)
    revealed_to_public: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TrumpCard:
        return cls(
            trump_id=str(data.get("trump_id", "")),
            name=str(data.get("name", "")),
            category=str(data.get("category", "technique")),
            tier=int(data.get("tier", 1)),
            cooldown_chapters=int(data.get("cooldown_chapters", 0)),
            current_cooldown=int(data.get("current_cooldown", 0)),
            sacrifice_cost=str(data.get("sacrifice_cost", "")),
            revealed_to_public=bool(data.get("revealed_to_public", False)),
        )


@dataclass
class ChapterTrumpDecision:
    """Records the strategic decision on trump card deployment for a given chapter."""
    chapter: int
    available_trumps: List[str] = field(default_factory=list)
    deployed_trumps: List[str] = field(default_factory=list)
    withheld_trumps: List[str] = field(default_factory=list)
    withholding_rationale: Dict[str, str] = field(default_factory=dict)  # trump_id -> reason

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChapterTrumpDecision:
        return cls(
            chapter=int(data.get("chapter", 1)),
            available_trumps=list(data.get("available_trumps", [])),
            deployed_trumps=list(data.get("deployed_trumps", [])),
            withheld_trumps=list(data.get("withheld_trumps", [])),
            withholding_rationale=dict(data.get("withholding_rationale", {})),
        )


@dataclass
class Epistemology:
    """Information horizon and known facts boundaries to prevent omniscience leaks."""
    known_facts: List[str] = field(default_factory=list)
    known_entity_ids: List[str] = field(default_factory=list)
    misconceptions: Dict[str, str] = field(default_factory=dict)  # topic -> false belief
    information_sources: Dict[str, int] = field(default_factory=dict)  # fact -> chapter learned

    def knows(self, fact_or_entity: str) -> bool:
        return fact_or_entity in self.known_facts or fact_or_entity in self.known_entity_ids

    def learn(self, fact: str, chapter: int) -> None:
        if fact not in self.known_facts:
            self.known_facts.append(fact)
            self.information_sources[fact] = chapter

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Epistemology:
        return cls(
            known_facts=list(data.get("known_facts", [])),
            known_entity_ids=list(data.get("known_entity_ids", [])),
            misconceptions=dict(data.get("misconceptions", {})),
            information_sources={k: int(v) for k, v in data.get("information_sources", {}).items()},
        )


@dataclass
class DebtRelation:
    """Interpersonal debt ledger tracking favors, grudges, blood feuds, and trust index."""
    target_character_id: str
    debt_type: str = "grudge"  # favor, grudge, blood_debt, monetary, promise
    magnitude: int = 0  # -100 (lethal blood feud) to +100 (unconditional sacrificial ally)
    unresolved: bool = True
    description: str = ""
    recorded_chapter: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DebtRelation:
        return cls(
            target_character_id=str(data.get("target_character_id", "")),
            debt_type=str(data.get("debt_type", "grudge")),
            magnitude=max(-100, min(100, int(data.get("magnitude", 0)))),
            unresolved=bool(data.get("unresolved", True)),
            description=str(data.get("description", "")),
            recorded_chapter=int(data.get("recorded_chapter", 1)),
        )


class LivingCharacter:
    """Domain model representing a character with autonomous, living cognitive & physical state."""

    def __init__(
        self,
        character_id: str,
        name: str,
        aliases: Optional[List[str]] = None,
        faction_id: str = "",
        role: str = "supporting",  # protagonist, antagonist, supporting, passerby
        life_status: str = "alive",  # alive, deceased, missing, unknown
        death_chapter: Optional[int] = None,
        personality_traits: Optional[List[str]] = None,
        core_fear: str = "",
        tier_rank: int = 1,
        motive_history: Optional[Dict[int, ChapterMotive]] = None,
        physiology_history: Optional[Dict[int, PhysiologicalState]] = None,
        trump_inventory: Optional[Dict[str, TrumpCard]] = None,
        trump_history: Optional[Dict[int, ChapterTrumpDecision]] = None,
        epistemology: Optional[Epistemology] = None,
        debts: Optional[Dict[str, DebtRelation]] = None,
    ) -> None:
        self.character_id = str(character_id)
        self.name = str(name)
        self.aliases = list(aliases or [])
        self.faction_id = str(faction_id)
        self.role = str(role)
        self.life_status = str(life_status).lower()
        self.death_chapter = int(death_chapter) if death_chapter is not None else None
        self.personality_traits = list(personality_traits or [])
        self.core_fear = str(core_fear)
        self.tier_rank = max(1, int(tier_rank))
        self.motive_history: Dict[int, ChapterMotive] = motive_history or {}
        self.physiology_history: Dict[int, PhysiologicalState] = physiology_history or {}
        self.trump_inventory: Dict[str, TrumpCard] = trump_inventory or {}
        self.trump_history: Dict[int, ChapterTrumpDecision] = trump_history or {}
        self.epistemology: Epistemology = epistemology or Epistemology()
        self.debts: Dict[str, DebtRelation] = debts or {}

    @property
    def is_alive(self) -> bool:
        return self.life_status == "alive"

    def mark_deceased(self, chapter: int) -> None:
        self.life_status = "deceased"
        self.death_chapter = int(chapter)

    def get_motive_at(self, chapter: int) -> Optional[ChapterMotive]:
        if chapter in self.motive_history:
            return self.motive_history[chapter]
        # Fall back to latest known motive before this chapter
        past_chapters = sorted([c for c in self.motive_history.keys() if c <= chapter])
        if past_chapters:
            return self.motive_history[past_chapters[-1]]
        return None

    def record_motive(self, chapter: int, motive: ChapterMotive) -> None:
        self.motive_history[chapter] = motive

    def get_physiology_at(self, chapter: int) -> PhysiologicalState:
        if chapter in self.physiology_history:
            return self.physiology_history[chapter]
        past_chapters = sorted([c for c in self.physiology_history.keys() if c <= chapter])
        if past_chapters:
            prev = self.physiology_history[past_chapters[-1]]
            # Natural gradual healing if recovery turns were elapsed
            recovered_injury = max(0, prev.injury_level - max(0, chapter - prev.chapter))
            return PhysiologicalState(
                chapter=chapter,
                injury_level=recovered_injury,
                injury_description=prev.injury_description if recovered_injury > 0 else "recovered",
                stamina_pool=100,
                stress_level=max(0, prev.stress_level - 10 * (chapter - prev.chapter)),
            )
        return PhysiologicalState(chapter=chapter)

    def record_physiology(self, chapter: int, state: PhysiologicalState) -> None:
        self.physiology_history[chapter] = state

    def record_trump_decision(self, chapter: int, decision: ChapterTrumpDecision) -> None:
        self.trump_history[chapter] = decision
        # Advance cooldowns for deployed cards
        for tid in decision.deployed_trumps:
            if tid in self.trump_inventory:
                self.trump_inventory[tid].current_cooldown = self.trump_inventory[tid].cooldown_chapters

    def tick_trump_cooldowns(self) -> None:
        for card in self.trump_inventory.values():
            if card.current_cooldown > 0:
                card.current_cooldown -= 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.character_id,
            "character_id": self.character_id,
            "name": self.name,
            "aliases": self.aliases,
            "faction_id": self.faction_id,
            "role": self.role,
            "life_status": self.life_status,
            "death_chapter": self.death_chapter,
            "personality_traits": self.personality_traits,
            "core_fear": self.core_fear,
            "tier_rank": self.tier_rank,
            "motive_history": {str(k): v.to_dict() for k, v in self.motive_history.items()},
            "physiology_history": {str(k): v.to_dict() for k, v in self.physiology_history.items()},
            "trump_inventory": {k: v.to_dict() for k, v in self.trump_inventory.items()},
            "trump_history": {str(k): v.to_dict() for k, v in self.trump_history.items()},
            "epistemology": self.epistemology.to_dict(),
            "debts": {k: v.to_dict() for k, v in self.debts.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LivingCharacter:
        motive_hist = {
            int(k): ChapterMotive.from_dict(v)
            for k, v in data.get("motive_history", {}).items()
        }
        phys_hist = {
            int(k): PhysiologicalState.from_dict(v)
            for k, v in data.get("physiology_history", {}).items()
        }
        trumps = {
            k: TrumpCard.from_dict(v)
            for k, v in data.get("trump_inventory", {}).items()
        }
        trump_hist = {
            int(k): ChapterTrumpDecision.from_dict(v)
            for k, v in data.get("trump_history", {}).items()
        }
        epist = Epistemology.from_dict(data.get("epistemology", {}))
        debts = {
            k: DebtRelation.from_dict(v)
            for k, v in data.get("debts", {}).items()
        }
        return cls(
            character_id=str(data.get("character_id") or data.get("id") or ""),
            name=str(data.get("name", "")),
            aliases=list(data.get("aliases", [])),
            faction_id=str(data.get("faction_id", "")),
            role=str(data.get("role", "supporting")),
            life_status=str(data.get("life_status", "alive")),
            death_chapter=int(data["death_chapter"]) if data.get("death_chapter") is not None else None,
            personality_traits=list(data.get("personality_traits", [])),
            core_fear=str(data.get("core_fear", "")),
            tier_rank=int(data.get("tier_rank", data.get("tier", 1))),
            motive_history=motive_hist,
            physiology_history=phys_hist,
            trump_inventory=trumps,
            trump_history=trump_hist,
            epistemology=epist,
            debts=debts,
        )
