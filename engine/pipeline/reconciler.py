"""Novel Studio 5.0 细纲意图与正文涌现事实双向平账中枢 (Fact Reconciler)。

核心功能：
1. 解析 Stage 4 Auditor 终审质检报告 (log/audit/ch_XXX.md)；
2. 提取正文中临场涌现的新死亡角色、新有名实体与道具资产流转；
3. 将涌现事实强制更新入 state/ 八表台账，达成意图与实况的双向闭环。
"""
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from engine.core.ledger import LedgerManager
from engine.core.models import Person, Item


class FactReconciler:
    """双向事实平账中枢"""

    def __init__(self, workspace: Path, ledger: LedgerManager):
        self.workspace = Path(workspace).resolve()
        self.ledger = ledger

    def extract_and_apply_emergence(self, chapter_id: str) -> List[str]:
        """从审计报告提取涌现事实并应用至台账，返回操作记录"""
        report_path = self.workspace / "log" / "audit" / f"{chapter_id}.md"
        if not report_path.is_file():
            return []

        try:
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return []

        actions = []

        ch_num = LedgerManager._extract_chapter_num(chapter_id)

        # 1. 提取阵亡角色：- [阵亡/死亡] 角色: <name> ｜ 说明: <desc>
        death_pattern = re.compile(r"-\s*\[(?:阵亡/死亡|阵亡|死亡)\]\s*角色:\s*([^\s|｜]+)", re.IGNORECASE)
        for match in death_pattern.finditer(content):
            dead_name = match.group(1).strip()
            p = self.ledger.find_person(None, dead_name)
            if p:
                p.life_status = "deceased"
                p.last_seen_ch = ch_num
                actions.append(f"正文涌现平账：将角色 [{dead_name}] (ID: {p.id}) 状态标记为已阵亡 (deceased)")
            else:
                # 登记新建立已阵亡角色
                new_id = f"p_{len(self.ledger.persons) + 1:03d}"
                self.ledger.persons[new_id] = Person(
                    id=new_id,
                    name=dead_name,
                    life_status="deceased",
                    last_seen_ch=ch_num
                )
                actions.append(f"正文涌现平账：登记新登场并立即阵亡角色 [{dead_name}] ({new_id})")

        # 2. 提取新登场实体：- [新登场] 类型: person|item ｜ 名称: <name> ｜ 描述: <desc>
        new_entity_pattern = re.compile(
            r"-\s*\[新登场\]\s*类型:\s*([^\s|｜]+)\s*[|｜]\s*名称:\s*([^\s|｜]+)(?:\s*[|｜]\s*描述:\s*([^\n\r]+))?",
            re.IGNORECASE
        )
        for match in new_entity_pattern.finditer(content):
            etype = match.group(1).strip().lower()
            ename = match.group(2).strip()
            edesc = match.group(3).strip() if match.group(3) else ""

            if etype == "person":
                if not self.ledger.find_person(None, ename):
                    nid = f"p_{len(self.ledger.persons) + 1:03d}"
                    self.ledger.persons[nid] = Person(id=nid, name=ename, power_benchmark=edesc)
                    actions.append(f"正文涌现平账：登记新有名配角 [{ename}] ({nid})")
            elif etype == "item":
                if not self.ledger.find_item(None, ename):
                    nid = f"it_{len(self.ledger.items) + 1:03d}"
                    self.ledger.items[nid] = Item(id=nid, name=ename, sensory_anchor=edesc)
                    actions.append(f"正文涌现平账：登记新道具资产 [{ename}] ({nid})")

        # 3. 提取道具流转：- [道具变动] 名称: <name> ｜ 持有人: <holder>
        item_trans_pattern = re.compile(
            r"-\s*\[道具变动\]\s*名称:\s*([^\s|｜]+)\s*[|｜]\s*持有人:\s*([^\s|｜]+)",
            re.IGNORECASE
        )
        for match in item_trans_pattern.finditer(content):
            item_name = match.group(1).strip()
            new_holder = match.group(2).strip()
            item = self.ledger.find_item(None, item_name)
            if item:
                item.holder = new_holder
                actions.append(f"正文涌现平账：道具 [{item_name}] 持有人变更为 [{new_holder}]")

        return actions
