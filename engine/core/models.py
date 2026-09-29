"""Novel Studio 5.0 强类型通用领域模型 (Domain Models)。

纯粹的数据结构契约，零题材硬编码，适用于任意题材（玄幻/都市/科幻/悬疑/历史）。
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class DynamicCognition:
    """角色动态认知与即时动机向量（纯数据结构，无硬编码）"""
    long_term_goal: str = ""
    current_motive: str = ""
    cognitive_bias: str = ""
    fear_threshold: str = ""
    attitude_towards_mc: str = "neutral"

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "DynamicCognition":
        if not data or not isinstance(data, dict):
            return cls()
        return cls(
            long_term_goal=str(data.get("long_term_goal", "")),
            current_motive=str(data.get("current_motive", "")),
            cognitive_bias=str(data.get("cognitive_bias", "")),
            fear_threshold=str(data.get("fear_threshold", "")),
            attitude_towards_mc=str(data.get("attitude_towards_mc", "neutral")),
        )


@dataclass
class PhysiologyState:
    """角色生理负荷状态（基于通用数值与受损等级 0~5）"""
    injury_level: int = 0  # 0: 无损, 1~2: 轻度, 3: 重度, 4~5: 濒危
    injury_desc: str = ""
    stamina_pct: int = 100
    energy_pct: int = 100
    active_debuffs: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "PhysiologyState":
        if not data or not isinstance(data, dict):
            return cls()
        return cls(
            injury_level=int(data.get("injury_level", 0)),
            injury_desc=str(data.get("injury_desc", "")),
            stamina_pct=int(data.get("stamina_pct", 100)),
            energy_pct=int(data.get("energy_pct", 100)),
            active_debuffs=list(data.get("active_debuffs", [])),
        )


@dataclass
class Person:
    """角色模型"""
    id: str
    name: str
    type: str = "person"
    role: str = "supporting"  # protagonist | antagonist | deuteragonist | ally | supporting
    tier_rank: int = 1
    tier_name: str = ""
    power_benchmark: str = ""
    status: str = "active"  # active | retired
    life_status: str = "alive"  # alive | deceased | missing | unknown
    faction: str = ""
    location: str = ""
    last_seen_ch: int = 0
    cognition: DynamicCognition = field(default_factory=DynamicCognition)
    physiology: PhysiologyState = field(default_factory=PhysiologyState)
    sensory_anchor: str = ""
    micro_actions: List[str] = field(default_factory=list)
    address_matrix: Dict[str, str] = field(default_factory=dict)
    card: str = ""

    def is_alive(self) -> bool:
        return self.life_status in ("alive", "unknown", "missing")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Person":
        cognition = DynamicCognition.from_dict(d.get("cognition"))
        physiology = PhysiologyState.from_dict(d.get("physiology"))
        return cls(
            id=str(d.get("id", "")),
            name=str(d.get("name", "")),
            type=str(d.get("type", "person")),
            role=str(d.get("role", "supporting")),
            tier_rank=int(d.get("tier_rank", 1)),
            tier_name=str(d.get("tier_name", "")),
            power_benchmark=str(d.get("power_benchmark", "")),
            status=str(d.get("status", "active")),
            life_status=str(d.get("life_status", "alive")),
            faction=str(d.get("faction", "")),
            location=str(d.get("location", "")),
            last_seen_ch=int(d.get("last_seen_ch", 0)),
            cognition=cognition,
            physiology=physiology,
            sensory_anchor=str(d.get("sensory_anchor", "")),
            micro_actions=list(d.get("micro_actions", [])),
            address_matrix=dict(d.get("address_matrix", {})),
            card=str(d.get("card", "")),
        )


@dataclass
class Item:
    """道具模型"""
    id: str
    name: str
    type: str = "item"
    holder: str = ""
    charges: int = -1  # -1 表示无限耐久或非计数型
    max_charges: int = -1
    cost_per_use: str = ""
    durability: str = ""
    tier_rank: int = 1
    sensory_anchor: str = ""
    card: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Item":
        return cls(
            id=str(d.get("id", "")),
            name=str(d.get("name", "")),
            type=str(d.get("type", "item")),
            holder=str(d.get("holder", "")),
            charges=int(d.get("charges", -1)),
            max_charges=int(d.get("max_charges", -1)),
            cost_per_use=str(d.get("cost_per_use", "")),
            durability=str(d.get("durability", "")),
            tier_rank=int(d.get("tier_rank", 1)),
            sensory_anchor=str(d.get("sensory_anchor", "")),
            card=str(d.get("card", "")),
        )


@dataclass
class Place:
    """场景模型"""
    id: str
    name: str
    type: str = "place"
    danger_tier: int = 1
    danger_level: str = ""
    sensory_anchor: str = ""
    environment_rules: List[str] = field(default_factory=list)
    card: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Place":
        return cls(
            id=str(d.get("id", "")),
            name=str(d.get("name", "")),
            type=str(d.get("type", "place")),
            danger_tier=int(d.get("danger_tier", 1)),
            danger_level=str(d.get("danger_level", "")),
            sensory_anchor=str(d.get("sensory_anchor", "")),
            environment_rules=list(d.get("environment_rules", [])),
            card=str(d.get("card", "")),
        )


@dataclass
class Faction:
    """势力模型"""
    id: str
    name: str
    type: str = "faction"
    scale_tier: int = 1
    leader: str = ""
    headquarters: str = ""
    core_assets: List[str] = field(default_factory=list)
    diplomacy: Dict[str, str] = field(default_factory=dict)
    card: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Faction":
        return cls(
            id=str(d.get("id", "")),
            name=str(d.get("name", "")),
            type=str(d.get("type", "faction")),
            scale_tier=int(d.get("scale_tier", 1)),
            leader=str(d.get("leader", "")),
            headquarters=str(d.get("headquarters", "")),
            core_assets=list(d.get("core_assets", [])),
            diplomacy=dict(d.get("diplomacy", {})),
            card=str(d.get("card", "")),
        )


@dataclass
class TrumpCard:
    """底牌模型"""
    id: str
    name: str
    visibility: str = "concealed"  # concealed | deployed | revealed
    cost: str = ""
    lethality_tier: int = 1
    holder_strategy: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TrumpCard":
        return cls(
            id=str(d.get("id", "")),
            name=str(d.get("name", "")),
            visibility=str(d.get("visibility", "concealed")),
            cost=str(d.get("cost", "")),
            lethality_tier=int(d.get("lethality_tier", 1)),
            holder_strategy=str(d.get("holder_strategy", "")),
        )


@dataclass
class Foreshadowing:
    """伏笔模型（严格三态：planted, stirred, resolved）"""
    id: str
    title: str
    category: str = "plot"
    state: str = "planted"  # planted | stirred | resolved
    planted_ch: int = 1
    stirred_ch: List[int] = field(default_factory=list)
    target_ch: int = 10
    countdown_remaining: int = 9
    secret_desc: str = ""
    known_by: List[str] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Foreshadowing":
        return cls(
            id=str(d.get("id", "")),
            title=str(d.get("title", "")),
            category=str(d.get("category", "plot")),
            state=str(d.get("state", "planted")),
            planted_ch=int(d.get("planted_ch", 1)),
            stirred_ch=list(d.get("stirred_ch", [])),
            target_ch=int(d.get("target_ch", 10)),
            countdown_remaining=int(d.get("countdown_remaining", 9)),
            secret_desc=str(d.get("secret_desc", "")),
            known_by=list(d.get("known_by", [])),
            history=list(d.get("history", [])),
        )


@dataclass
class Debt:
    """人际誓约与恩怨模型"""
    id: str
    source_char: str
    target_char: str
    type: str = "grudge"  # blood_feud | grudge | favor | promise
    desc: str = ""
    created_ch: int = 1
    status: str = "active"  # active | settled

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Debt":
        return cls(
            id=str(d.get("id", "")),
            source_char=str(d.get("source_char", d.get("source", ""))),
            target_char=str(d.get("target_char", d.get("target", ""))),
            type=str(d.get("type", "grudge")),
            desc=str(d.get("desc", "")),
            created_ch=int(d.get("created_ch", 1)),
            status=str(d.get("status", "active")),
        )


@dataclass
class Milestone:
    """里程碑模型"""
    id: str
    title: str
    target_ch: int
    desc: str = ""
    scope: str = "vol_01"
    status: str = "pending"  # pending | achieved | postponed
    achieved_ch: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Milestone":
        return cls(
            id=str(d.get("id", "")),
            title=str(d.get("title", "")),
            target_ch=int(d.get("target_ch", 0)),
            desc=str(d.get("desc", "")),
            scope=str(d.get("scope", "vol_01")),
            status=str(d.get("status", "pending")),
            achieved_ch=d.get("achieved_ch"),
        )


@dataclass
class MacroEvent:
    """宏观大势事件模型"""
    id: str
    title: str
    impact_scope: str = ""
    stage: str = "brewing"  # brewing | active | resolved
    urgency_to_scene: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MacroEvent":
        return cls(
            id=str(d.get("id", "")),
            title=str(d.get("title", "")),
            impact_scope=str(d.get("impact_scope", "")),
            stage=str(d.get("stage", "brewing")),
            urgency_to_scene=str(d.get("urgency_to_scene", "medium")),
        )


@dataclass
class BeatActor:
    """细纲在场角色定义（仅做精确键值承载）"""
    id: str = ""
    name: str = ""
    role: str = "supporting"
    want: str = ""
    fear: str = ""
    status_in: str = ""
    cognitive_bias: str = ""
    current_motive: str = ""
    deployed_cards: List[str] = field(default_factory=list)
    concealed_cards: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "BeatActor":
        return cls(
            id=str(d.get("id", "")),
            name=str(d.get("name", "")),
            role=str(d.get("role", "supporting")),
            want=str(d.get("want", "")),
            fear=str(d.get("fear", "")),
            status_in=str(d.get("status_in", "")),
            cognitive_bias=str(d.get("cognitive_bias", "")),
            current_motive=str(d.get("current_motive", "")),
            deployed_cards=list(d.get("deployed_cards", [])),
            concealed_cards=list(d.get("concealed_cards", [])),
        )


@dataclass
class BeatFrontmatter:
    """细纲 Frontmatter 结构契约"""
    chapter_id: str
    volume_id: str = "vol_01"
    title: str = ""
    chapter_type: str = "Escalation"
    pov_character: str = ""
    timeline: str = ""
    location: str = ""
    spatiotemporal: Dict[str, Any] = field(default_factory=dict)
    narrative_spine: Dict[str, Any] = field(default_factory=dict)
    scene_environment: Dict[str, Any] = field(default_factory=dict)
    present_characters: List[BeatActor] = field(default_factory=list)
    trump_cards: List[Dict[str, Any]] = field(default_factory=list)
    macro_events: List[Dict[str, Any]] = field(default_factory=list)
    epistemology: Dict[str, Any] = field(default_factory=dict)
    foreshadowing_deltas: List[Dict[str, Any]] = field(default_factory=list)
    state_deltas: Dict[str, Any] = field(default_factory=dict)
    economy_deltas: List[Dict[str, Any]] = field(default_factory=list)
    relation_deltas: List[Dict[str, Any]] = field(default_factory=list)
    new_entities: List[Dict[str, Any]] = field(default_factory=list)
    locked_facts: List[Dict[str, Any]] = field(default_factory=list)

    def get_character_ids(self) -> List[str]:
        return [c.id for c in self.present_characters if c.id]

    def get_character_names(self) -> List[str]:
        return [c.name for c in self.present_characters if c.name]
