"""Novel Studio 5.0 状态账本中枢 (Ledger State Machine)。

管理状态全息数据表 (state/ 目录)：
- persons.json (人物台账)
- items.json (道具资产)
- factions.json (势力据点)
- places.json (地理空间)
- lines.json (伏笔三态雷达)
- locked.json (既成法定事实)
- ledger.json (经济与复式记账流水)
- debts.json (恩怨誓约)
- milestones.json (战略里程碑)
- macro_events.json (天下大势宏观时钟)
- current.json (当前第一现场)
- sync_log.json (幂等同步指纹)

核心不变量：
1. 事务预检优先于任何写盘（apply_state_deltas 先校验全部冲突，任一冲突=零写盘）；
2. 死亡不可逆公理（已故角色出场直接抛 GuardError，一票否决）；
3. 幂等性保障（同一章相同指纹重跑不虚增任何计数）。
"""
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from engine.errors import GuardError, BusinessError
from engine.core.models import (
    Person, Item, Faction, Place, Foreshadowing, Debt, Milestone, MacroEvent,
    BeatFrontmatter
)
from engine.core.storage import safe_load_json, atomic_write_json, ensure_directory


class LedgerManager:
    """全息台账管理器"""

    def __init__(self, workspace: Path):
        self.workspace = Path(workspace).resolve()
        self.state_dir = self.workspace / "state"
        ensure_directory(self.state_dir)

        # 数据表缓存
        self.persons: Dict[str, Person] = {}
        self.items: Dict[str, Item] = {}
        self.factions: Dict[str, Faction] = {}
        self.places: Dict[str, Place] = {}
        self.lines: Dict[str, Foreshadowing] = {}
        self.debts: List[Debt] = []
        self.milestones: List[Milestone] = []
        self.macro_events: List[MacroEvent] = []
        self.locked_facts: List[Dict[str, Any]] = []
        self.ledger_data: Dict[str, Any] = {}
        self.current_state: Dict[str, Any] = {}
        self.sync_log: Dict[str, Any] = {}

        self.loaded = False

    def load_all(self) -> None:
        """加载全量状态表"""
        # 1. persons
        p_raw = safe_load_json(self.state_dir / "persons.json", default=[])
        self.persons = {p["id"]: Person.from_dict(p) for p in p_raw if isinstance(p, dict) and "id" in p}

        # 2. items
        i_raw = safe_load_json(self.state_dir / "items.json", default=[])
        self.items = {it["id"]: Item.from_dict(it) for it in i_raw if isinstance(it, dict) and "id" in it}

        # 3. factions
        f_raw = safe_load_json(self.state_dir / "factions.json", default=[])
        self.factions = {fac["id"]: Faction.from_dict(fac) for fac in f_raw if isinstance(fac, dict) and "id" in fac}

        # 4. places
        pl_raw = safe_load_json(self.state_dir / "places.json", default=[])
        self.places = {pl["id"]: Place.from_dict(pl) for pl in pl_raw if isinstance(pl, dict) and "id" in pl}

        # 5. lines (伏笔)
        l_raw = safe_load_json(self.state_dir / "lines.json", default=[])
        self.lines = {ln["id"]: Foreshadowing.from_dict(ln) for ln in l_raw if isinstance(ln, dict) and "id" in ln}

        # 6. debts
        d_raw = safe_load_json(self.state_dir / "debts.json", default=[])
        self.debts = [Debt.from_dict(d) for d in d_raw if isinstance(d, dict) and "id" in d]

        # 7. milestones
        ms_raw = safe_load_json(self.state_dir / "milestones.json", default=[])
        self.milestones = [Milestone.from_dict(m) for m in ms_raw if isinstance(m, dict) and "id" in m]

        # 8. macro_events
        ev_raw = safe_load_json(self.state_dir / "macro_events.json", default=[])
        self.macro_events = [MacroEvent.from_dict(e) for e in ev_raw if isinstance(e, dict) and "id" in e]

        # 9. locked & current & ledger & sync_log
        self.locked_facts = safe_load_json(self.state_dir / "locked.json", default=[])
        self.ledger_data = safe_load_json(self.state_dir / "ledger.json", default={"pools": {}, "transactions": []})
        self.current_state = safe_load_json(self.state_dir / "current.json", default={})
        self.sync_log = safe_load_json(self.state_dir / "sync_log.json", default={})

        self.loaded = True

    def save_all(self) -> None:
        """原子持久化全量状态表"""
        atomic_write_json(self.state_dir / "persons.json", [p.to_dict() for p in self.persons.values()])
        atomic_write_json(self.state_dir / "items.json", [i.to_dict() for i in self.items.values()])
        atomic_write_json(self.state_dir / "factions.json", [f.to_dict() for f in self.factions.values()])
        atomic_write_json(self.state_dir / "places.json", [pl.to_dict() for pl in self.places.values()])
        atomic_write_json(self.state_dir / "lines.json", [ln.to_dict() for ln in self.lines.values()])
        atomic_write_json(self.state_dir / "debts.json", [d.to_dict() for d in self.debts])
        atomic_write_json(self.state_dir / "milestones.json", [m.to_dict() for m in self.milestones])
        atomic_write_json(self.state_dir / "macro_events.json", [e.to_dict() for e in self.macro_events])
        atomic_write_json(self.state_dir / "locked.json", self.locked_facts)
        atomic_write_json(self.state_dir / "ledger.json", self.ledger_data)
        atomic_write_json(self.state_dir / "current.json", self.current_state)
        atomic_write_json(self.state_dir / "sync_log.json", self.sync_log)

    def preflight_check(self, beats: BeatFrontmatter) -> List[str]:
        """事务预检：在任何写盘前执行物理不变量拦截，返回警告列表"""
        if not self.loaded:
            self.load_all()

        warnings = []

        # 1. 物理硬约束：已故角色一票否决
        ch_num = self._extract_chapter_num(beats.chapter_id)
        for actor in beats.present_characters:
            p = self.find_person(actor.id, actor.name)
            if p and p.life_status == "deceased" and p.last_seen_ch < ch_num:
                raise GuardError(
                    f"死亡不可逆物理阻断：角色 [{p.name}] (ID: {p.id}) 历史状态已标记为阵亡 (deceased)，严禁作为活人登场！",
                    remediation=f"请修改细纲移除 {p.name} 的登场，若属回忆闪回请在细纲与正文中显式标明为虚像/回忆。"
                )

        # 2. 道具充能透支预检
        items_deltas = beats.state_deltas.get("items", [])
        if isinstance(items_deltas, list):
            for it_delta in items_deltas:
                it_id = it_delta.get("id")
                it_name = it_delta.get("name")
                item = self.find_item(it_id, it_name)
                if item and item.charges >= 0:
                    delta_ch = it_delta.get("charges_delta", 0)
                    if item.charges + delta_ch < 0:
                        raise BusinessError(
                            f"道具充能透支阻断：道具 [{item.name}] 当前剩余充能 {item.charges}，无法扣减 {abs(delta_ch)}！",
                            remediation="调整细纲中的使用频次，或在细纲中先行声明为道具充能补给事件。"
                        )

        return warnings

    def apply_sync(
        self,
        chapter_id: str,
        beats: BeatFrontmatter,
        raw_text: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """原子执行单章合账，更新八表并记录幂等指纹"""
        if not self.loaded:
            self.load_all()

        # 预检拦截
        self.preflight_check(beats)

        # 计算指纹
        text_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        prev_sync = self.sync_log.get(chapter_id)
        if prev_sync and prev_sync.get("hash") == text_hash and not force:
            return {"status": "skipped", "message": f"章节 {chapter_id} 内容未变，幂等跳过合账。"}

        healed_actions = []

        # 1. 刷新在场人物生命线与认知
        ch_num = self._extract_chapter_num(chapter_id)
        for actor in beats.present_characters:
            p = self.find_person(actor.id, actor.name)
            if p:
                p.last_seen_ch = ch_num
                if actor.want:
                    p.cognition.current_motive = actor.want
                if actor.fear:
                    p.cognition.fear_threshold = actor.fear
                if actor.cognitive_bias:
                    p.cognition.cognitive_bias = actor.cognitive_bias
            else:
                # 自动打捞建档
                new_id = actor.id or f"p_{len(self.persons) + 1:03d}"
                new_person = Person(
                    id=new_id,
                    name=actor.name,
                    role=actor.role,
                    last_seen_ch=ch_num
                )
                if actor.want:
                    new_person.cognition.current_motive = actor.want
                if actor.fear:
                    new_person.cognition.fear_threshold = actor.fear
                if actor.cognitive_bias:
                    new_person.cognition.cognitive_bias = actor.cognitive_bias
                self.persons[new_id] = new_person
                healed_actions.append(f"打捞并自动登记新在场人物: {actor.name} ({new_id})")

        # 2. 处理道具流转
        items_deltas = beats.state_deltas.get("items", [])
        if isinstance(items_deltas, list):
            for it_d in items_deltas:
                item = self.find_item(it_d.get("id"), it_d.get("name"))
                if item:
                    if "holder_change" in it_d:
                        item.holder = str(it_d["holder_change"])
                    if "charges_delta" in it_d:
                        if item.charges >= 0:
                            item.charges += int(it_d["charges_delta"])

        # 3. 处理伏笔推进 (三态时钟)
        for f_delta in beats.foreshadowing_deltas:
            f_id = f_delta.get("id")
            if f_id and f_id in self.lines:
                f_obj = self.lines[f_id]
                action = f_delta.get("action", "stir")
                if action == "resolve":
                    f_obj.state = "resolved"
                elif action == "stir":
                    f_obj.state = "stirred"
                    if ch_num not in f_obj.stirred_ch:
                        f_obj.stirred_ch.append(ch_num)
                f_obj.countdown_remaining = max(0, f_obj.target_ch - ch_num)
                f_obj.history.append({"chapter": ch_num, "action": action, "note": f_delta.get("note", "")})

        # 4. 更新当前第一现场
        self.current_state.update({
            "last_synced_chapter": chapter_id,
            "chapter_num": ch_num,
            "timeline": beats.timeline,
            "location": beats.location,
            "persons_present": beats.get_character_names(),
        })

        # 5. 记录同步指纹
        self.sync_log[chapter_id] = {
            "chapter_id": chapter_id,
            "hash": text_hash,
            "words": len(raw_text),
            "actors": beats.get_character_names(),
        }

        # 6. 原子写盘
        self.save_all()

        return {
            "status": "success",
            "chapter_id": chapter_id,
            "words": len(raw_text),
            "healed": healed_actions,
        }

    def find_person(self, pid: Optional[str], name: Optional[str]) -> Optional[Person]:
        if pid and pid in self.persons:
            return self.persons[pid]
        if name:
            for p in self.persons.values():
                if p.name == name:
                    return p
        return None

    def find_item(self, iid: Optional[str], name: Optional[str]) -> Optional[Item]:
        if iid and iid in self.items:
            return self.items[iid]
        if name:
            for i in self.items.values():
                if i.name == name:
                    return i
        return None

    def find_place(self, plid: Optional[str], name: Optional[str]) -> Optional[Place]:
        if plid and plid in self.places:
            return self.places[plid]
        if name:
            for pl in self.places.values():
                if pl.name == name:
                    return pl
        return None

    def find_faction(self, fid: Optional[str], name: Optional[str]) -> Optional[Faction]:
        if fid and fid in self.factions:
            return self.factions[fid]
        if name:
            for f in self.factions.values():
                if f.name == name:
                    return f
        return None

    @staticmethod
    def _extract_chapter_num(ch_id: str) -> int:
        import re
        m = re.search(r"\d+", ch_id)
        return int(m.group(0)) if m else 0
