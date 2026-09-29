"""Deterministic Anti-Drop-IQ Auditor and Double-Entry Ledger Reconciler.

Enforces:
1. Motive-Action consistency (emotional motivation closure, no irrational mercy or unmotivated betrothal/betrayal).
2. Epistemological boundary (anti-omniscience, characters cannot act on unlearned secrets).
3. Human vulnerability & stress closure (fear triggers must reflect in stress/handicaps).
4. Trump card deployment rationality (no unjustified hoarding in fatal situations).
5. Foreshadowing lifecycle closure (overdue hooks flagged).
6. Double-entry ledger balance (physical wounds, life status, item counts, energy overdrafts).

Zero hardcoded Chinese literary tropes or genre-specific keywords in Python. Pure structural validation.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
import re
from typing import Any, Dict, List, Optional, Set

from engine.domain.character import LivingCharacter, ChapterMotive, PhysiologicalState
from engine.domain.golden_finger import LivingGoldenFinger
from engine.domain.plot_graph import LivingPlotGraph, ForeshadowingItem


@dataclass
class AuditIssue:
    """Represents a specific structural rationality or balance defect."""
    category: str  # epistemology_leak, motive_contradiction, unjustified_trump_withholding, stress_apathy, overdue_foreshadowing, ledger_imbalance, resurrection_violation, fatal_environment_violation, trump_item_unowned, trump_item_destroyed, trump_item_depleted, faction_diplomacy_contradiction, combat_injury_apathy, golden_finger_backlash_disconnection, deceased_speaker_violation
    severity: str  # blocker, warning
    entity_id: str
    chapter: int
    message: str
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditReport:
    """Comprehensive outcome of the multi-dimensional causal audit."""
    chapter: int
    is_valid: bool = True
    blockers: List[AuditIssue] = field(default_factory=list)
    warnings: List[AuditIssue] = field(default_factory=list)

    def add_issue(self, issue: AuditIssue) -> None:
        if issue.severity == "blocker":
            self.blockers.append(issue)
            self.is_valid = False
        else:
            self.warnings.append(issue)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter": self.chapter,
            "is_valid": self.is_valid,
            "blockers_count": len(self.blockers),
            "warnings_count": len(self.warnings),
            "blockers": [b.to_dict() for b in self.blockers],
            "warnings": [w.to_dict() for w in self.warnings],
        }


class AntiDropIQAuditor:
    """Structural validator that enforces behavioral rationality and ledger truth."""

    def __init__(self, strict_mode: bool = False) -> None:
        self.strict_mode = bool(strict_mode)

    def audit_chapter(
        self,
        chapter: int,
        characters: Dict[str, LivingCharacter],
        plot_graph: LivingPlotGraph,
        golden_finger: Optional[LivingGoldenFinger] = None,
        chapter_manifest: Optional[Dict[str, Any]] = None,
        items: Optional[Dict[str, Any]] = None,
        places: Optional[Dict[str, Any]] = None,
        factions: Optional[Dict[str, Any]] = None,
        universe: Optional[Any] = None,
    ) -> AuditReport:
        """Run full deterministic causal and balance checks for a chapter."""
        report = AuditReport(chapter=chapter)
        manifest = chapter_manifest or {}

        # 1. Life status and resurrection check
        self._check_life_status_integrity(chapter, characters, manifest, report)

        # 2. Epistemological horizon check (Anti-omniscience)
        self._check_epistemology(chapter, characters, manifest, report)

        # 3. Motive-action consistency (No unmotivated betrayal or irrational mercy)
        self._check_motive_consistency(chapter, characters, manifest, report)

        # 4. Human vulnerability and fear closure
        self._check_fear_and_stress(chapter, characters, manifest, report)

        # 5. Trump card rationality
        self._check_trump_rationality(chapter, characters, manifest, report)

        # 6. Foreshadowing closure
        self._check_foreshadowing(chapter, plot_graph, report)

        # 7. Physical continuity and ledger balance
        self._check_physical_and_energy_balance(chapter, characters, golden_finger, manifest, report)

        # 8. Subplot and causal DAG cycle/prerequisite check
        self._check_subplot_dag(chapter, plot_graph, report)

        # 9. Environmental and location danger gating
        self._check_environment_and_tier_gating(chapter, characters, places, manifest, report)

        # 10. Item trump card ledger consistency
        self._check_trump_item_consistency(chapter, characters, items, manifest, report)

        # 11. Faction diplomacy contradiction check
        self._check_faction_diplomacy_contradictions(chapter, characters, factions, manifest, report)

        # 12. Physiological combat impairment check
        self._check_physiological_combat_impairment(chapter, characters, manifest, report)

        # 13. Golden Finger physiology coupling
        self._check_golden_finger_physiology_coupling(chapter, characters, golden_finger, manifest, report)

        # 14. Deceased speaker check from manifest
        self._check_deceased_speakers(chapter, characters, manifest, report)

        return report

    def _check_life_status_integrity(
        self,
        chapter: int,
        characters: Dict[str, LivingCharacter],
        manifest: Dict[str, Any],
        report: AuditReport,
    ) -> None:
        active_character_ids = manifest.get("active_character_ids", [])
        for cid in active_character_ids:
            char = characters.get(cid)
            if not char:
                continue
            if not char.is_alive and char.death_chapter is not None and chapter > char.death_chapter:
                report.add_issue(
                    AuditIssue(
                        category="resurrection_violation",
                        severity="blocker",
                        entity_id=cid,
                        chapter=chapter,
                        message=f"Character '{cid}' is deceased (died ch {char.death_chapter}) but is declared active in chapter {chapter} without formal resurrection.",
                        context={"death_chapter": char.death_chapter, "active_chapter": chapter},
                    )
                )

    def _check_epistemology(
        self,
        chapter: int,
        characters: Dict[str, LivingCharacter],
        manifest: Dict[str, Any],
        report: AuditReport,
    ) -> None:
        # manifest['actions'] format: [{"actor_id": "C_001", "required_knowledge": ["secret_map", "traitor_identity"]}]
        actions = manifest.get("actions", [])
        for act in actions:
            actor_id = act.get("actor_id", "")
            req_facts = act.get("required_knowledge", [])
            char = characters.get(actor_id)
            if not char or not req_facts:
                continue
            for fact in req_facts:
                if not char.epistemology.knows(fact):
                    report.add_issue(
                        AuditIssue(
                            category="epistemology_leak",
                            severity="blocker",
                            entity_id=actor_id,
                            chapter=chapter,
                            message=f"Character '{actor_id}' acted on unlearned secret '{fact}' in chapter {chapter} (Omniscience leak).",
                            context={"required_knowledge": fact, "known_facts": char.epistemology.known_facts},
                        )
                    )

    def _check_motive_consistency(
        self,
        chapter: int,
        characters: Dict[str, LivingCharacter],
        manifest: Dict[str, Any],
        report: AuditReport,
    ) -> None:
        # manifest['actions'] format: [{"actor_id": "C_002", "target_id": "C_001", "action_tag": "betray"}]
        actions = manifest.get("actions", [])
        for act in actions:
            actor_id = act.get("actor_id", "")
            target_id = act.get("target_id", "")
            action_tag = act.get("action_tag", "")
            char = characters.get(actor_id)
            if not char:
                continue

            # Check moral redline
            motive = char.get_motive_at(chapter)
            if motive and motive.moral_redline and motive.moral_redline in action_tag:
                # If urgency < 5 and no explicit shift reason, redline breach is irrational
                if motive.urgency < 5 and not motive.motive_shift_reason:
                    report.add_issue(
                        AuditIssue(
                            category="motive_contradiction",
                            severity="blocker",
                            entity_id=actor_id,
                            chapter=chapter,
                            message=f"Character '{actor_id}' violated moral redline '{motive.moral_redline}' with action '{action_tag}' without extreme stakes or shift rationale.",
                            context={"moral_redline": motive.moral_redline, "urgency": motive.urgency},
                        )
                    )

            # Check debts / emotional motivation (irrational mercy)
            if target_id and target_id in char.debts:
                debt = char.debts[target_id]
                # If blood debt (magnitude <= -80), and action is "forgive" or "spare" without higher motive
                if debt.magnitude <= -80 and action_tag in ["unconditional_spare", "forgive", "ally"]:
                    if not motive or (motive.urgency < 4 and "strategic_compromise" not in motive.sub_motives):
                        report.add_issue(
                            AuditIssue(
                                category="motive_contradiction",
                                severity="blocker",
                                entity_id=actor_id,
                                chapter=chapter,
                                message=f"Character '{actor_id}' showed unmotivated mercy to lethal enemy '{target_id}' (Debt magnitude {debt.magnitude}) without strategic necessity.",
                                context={"target_id": target_id, "debt": debt.to_dict()},
                            )
                        )

    def _check_fear_and_stress(
        self,
        chapter: int,
        characters: Dict[str, LivingCharacter],
        manifest: Dict[str, Any],
        report: AuditReport,
    ) -> None:
        # manifest['scene_triggers'] format: ["trigger_darkness", "trigger_betrayal"]
        scene_triggers = manifest.get("scene_triggers", [])
        if not scene_triggers:
            return

        for cid, char in characters.items():
            if not char.core_fear or cid not in manifest.get("active_character_ids", []):
                continue
            if char.core_fear in scene_triggers:
                phys = char.get_physiology_at(chapter)
                # If core fear triggered, stress level must rise or have handicap
                if phys.stress_level < 40 and not phys.handicaps:
                    report.add_issue(
                        AuditIssue(
                            category="stress_apathy",
                            severity="warning" if not self.strict_mode else "blocker",
                            entity_id=cid,
                            chapter=chapter,
                            message=f"Character '{cid}' encountered core fear '{char.core_fear}', but stress level ({phys.stress_level}) did not reflect emotional response.",
                            context={"core_fear": char.core_fear, "stress_level": phys.stress_level},
                        )
                    )

    def _check_trump_rationality(
        self,
        chapter: int,
        characters: Dict[str, LivingCharacter],
        manifest: Dict[str, Any],
        report: AuditReport,
    ) -> None:
        for cid, char in characters.items():
            if cid not in manifest.get("active_character_ids", []):
                continue
            phys = char.get_physiology_at(chapter)
            motive = char.get_motive_at(chapter)
            is_fatal_crisis = (phys.injury_level >= 4) or (motive and motive.urgency >= 5)

            if is_fatal_crisis and char.trump_inventory:
                # Check trump decision
                decision = char.trump_history.get(chapter)
                if not decision:
                    continue
                # If life is endangered, no trumps were deployed, and withheld trumps have no rationale
                if not decision.deployed_trumps and decision.withheld_trumps:
                    unjustified = [
                        t for t in decision.withheld_trumps
                        if not decision.withholding_rationale.get(t)
                    ]
                    if unjustified:
                        report.add_issue(
                            AuditIssue(
                                category="unjustified_trump_withholding",
                                severity="blocker",
                                entity_id=cid,
                                chapter=chapter,
                                message=f"Character '{cid}' faced fatal stakes (injury {phys.injury_level}, urgency {motive.urgency if motive else 0}) but withheld trump cards {unjustified} with zero stated rationale.",
                                context={"withheld_unjustified": unjustified, "injury_level": phys.injury_level},
                            )
                        )

    def _check_foreshadowing(
        self,
        chapter: int,
        plot_graph: LivingPlotGraph,
        report: AuditReport,
    ) -> None:
        overdue = plot_graph.get_overdue_clues(chapter)
        for clue in overdue:
            report.add_issue(
                AuditIssue(
                    category="overdue_foreshadowing",
                    severity="warning",
                    entity_id=clue.clue_id,
                    chapter=chapter,
                    message=f"Foreshadowing clue '{clue.clue_id}' ({clue.hook}) is overdue for resolution (Target window: {clue.target_resolution_window}, current chapter: {chapter}).",
                    context={"window": list(clue.target_resolution_window), "hook": clue.hook},
                )
            )

    def _check_physical_and_energy_balance(
        self,
        chapter: int,
        characters: Dict[str, LivingCharacter],
        golden_finger: Optional[LivingGoldenFinger],
        manifest: Dict[str, Any],
        report: AuditReport,
    ) -> None:
        # Check instantaneous healing without time or cure
        for cid, char in characters.items():
            if chapter in char.physiology_history and (chapter - 1) in char.physiology_history:
                curr = char.physiology_history[chapter]
                prev = char.physiology_history[chapter - 1]
                # If severe injury dropped to 0 in 1 chapter without healing event
                healing_events = manifest.get("healing_events", [])
                if prev.injury_level >= 3 and curr.injury_level == 0 and cid not in healing_events:
                    report.add_issue(
                        AuditIssue(
                            category="ledger_imbalance",
                            severity="blocker",
                            entity_id=cid,
                            chapter=chapter,
                            message=f"Character '{cid}' jumped from severe injury ({prev.injury_level}) to uninjured (0) in one chapter without a recorded healing event.",
                            context={"prev_injury": prev.injury_level, "curr_injury": curr.injury_level},
                        )
                    )

        # Check Golden Finger energy balance
        if golden_finger and golden_finger.energy_history:
            latest_txs = [tx for tx in golden_finger.energy_history if tx.chapter == chapter]
            for tx in latest_txs:
                if tx.resulting_balance < -50:
                    report.add_issue(
                        AuditIssue(
                            category="ledger_imbalance",
                            severity="blocker",
                            entity_id=golden_finger.system_id,
                            chapter=chapter,
                            message=f"Golden Finger '{golden_finger.system_id}' suffered catastrophic overdraft below structural limit ({tx.resulting_balance} < -50).",
                            context={"resulting_balance": tx.resulting_balance},
                        )
                    )

    def _check_subplot_dag(
        self,
        chapter: int,
        plot_graph: LivingPlotGraph,
        report: AuditReport,
    ) -> None:
        """Enforce acyclic DAG structure and prerequisite completion for active subplots."""
        dag_errors = plot_graph.validate_dependencies()
        for err in dag_errors:
            report.add_issue(
                AuditIssue(
                    category="subplot_dag_error",
                    severity="blocker",
                    entity_id="subplots",
                    chapter=chapter,
                    message=f"Subplot DAG causal error: {err}",
                )
            )

        # Check if active subplots have all prerequisites completed
        for lid, branch in plot_graph.subplots.items():
            if branch.status == "active":
                for pre in branch.prerequisite_line_ids:
                    pre_branch = plot_graph.subplots.get(pre)
                    if pre_branch and pre_branch.status != "completed":
                        report.add_issue(
                            AuditIssue(
                                category="subplot_prerequisite_unmet",
                                severity="blocker",
                                entity_id=lid,
                                chapter=chapter,
                                message=f"Subplot '{lid}' ({branch.title}) is active, but its prerequisite '{pre}' ({pre_branch.title}) is '{pre_branch.status}' (not completed)!",
                                context={"subplot_id": lid, "unmet_prerequisite": pre},
                            )
                        )

    def _check_environment_and_tier_gating(
        self,
        chapter: int,
        characters: Dict[str, LivingCharacter],
        places: Optional[Dict[str, Any]],
        manifest: Dict[str, Any],
        report: AuditReport,
    ) -> None:
        """Enforce environmental survival rules: low-tier characters entering high-tier danger zones."""
        place_source = places if places is not None else manifest.get("places")
        if not place_source:
            return

        active_loc_ids: List[str] = []
        if manifest.get("location"):
            active_loc_ids.append(str(manifest.get("location")))
        if manifest.get("active_locations"):
            active_loc_ids.extend([str(loc) for loc in manifest.get("active_locations", [])])

        active_chars = [
            characters[cid] for cid in manifest.get("active_character_ids", [])
            if cid in characters
        ]
        if not active_chars:
            return

        max_active_tier = max([getattr(c, "tier_rank", 1) for c in active_chars] or [1])

        for loc_id in active_loc_ids:
            loc_data = place_source.get(loc_id)
            if not loc_data:
                for p_id, p_val in place_source.items():
                    if isinstance(p_val, dict) and p_val.get("name") == loc_id:
                        loc_data = p_val
                        break
            if not loc_data or not isinstance(loc_data, dict):
                continue

            raw_danger = loc_data.get("danger_tier", 1)
            if isinstance(raw_danger, int):
                danger_tier = raw_danger
            else:
                m = re.search(r"(\d+)", str(raw_danger))
                danger_tier = int(m.group(1)) if m else 1

            for char in active_chars:
                char_tier = getattr(char, "tier_rank", 1)
                disparity = danger_tier - char_tier
                if disparity >= 3:
                    has_barrier = any(
                        t.category == "item" or "shield" in t.name.lower() or "barrier" in t.name.lower()
                        for t in char.trump_inventory.values()
                    )
                    has_protection_item = bool(manifest.get("protection_items"))
                    has_high_tier_escort = max_active_tier >= danger_tier - 1
                    phys = char.get_physiology_at(chapter)
                    took_damage = phys.injury_level >= 3 or len(phys.handicaps) > 0

                    if not (has_barrier or has_protection_item or has_high_tier_escort or took_damage):
                        report.add_issue(
                            AuditIssue(
                                category="fatal_environment_violation",
                                severity="blocker",
                                entity_id=char.character_id,
                                chapter=chapter,
                                message=f"Character '{char.character_id}' (Tier {char_tier}) is present in extreme danger location '{loc_id}' (Danger Tier {danger_tier}) without defensive artifact, high-tier escort, or survival mechanism.",
                                context={"character_tier": char_tier, "danger_tier": danger_tier, "location": loc_id},
                            )
                        )

    def _check_trump_item_consistency(
        self,
        chapter: int,
        characters: Dict[str, LivingCharacter],
        items: Optional[Dict[str, Any]],
        manifest: Dict[str, Any],
        report: AuditReport,
    ) -> None:
        """Enforce item trump card deployment validity against physical item ledger."""
        item_source = items if items is not None else manifest.get("items")
        if not item_source:
            return

        for cid, char in characters.items():
            decision = char.trump_history.get(chapter)
            deployed = list(decision.deployed_trumps) if decision else []
            if not deployed:
                manifest_deployed = manifest.get("deployed_trumps", {})
                if isinstance(manifest_deployed, dict):
                    deployed = manifest_deployed.get(cid, [])
                elif isinstance(manifest_deployed, list):
                    deployed = manifest_deployed

            for tid in deployed:
                tcard = char.trump_inventory.get(tid)
                item_record = item_source.get(tid)
                if not item_record and tcard:
                    for iid, irec in item_source.items():
                        if isinstance(irec, dict) and (irec.get("name") == tcard.name or iid == tcard.name):
                            item_record = irec
                            break

                if not item_record or not isinstance(item_record, dict):
                    continue

                # 1. Ownership check
                owner = item_record.get("owner_id") or item_record.get("holder")
                if owner and owner != cid:
                    report.add_issue(
                        AuditIssue(
                            category="trump_item_unowned",
                            severity="blocker",
                            entity_id=cid,
                            chapter=chapter,
                            message=f"Character '{cid}' deployed item trump '{tcard.name if tcard else tid}', but item ledger records owner as '{owner}'.",
                            context={"trump_id": tid, "recorded_owner": owner},
                        )
                    )

                # 2. Destruction check
                cond = item_record.get("condition", "intact")
                if cond in ["destroyed", "shattered", "obliterated"] or item_record.get("is_destroyed"):
                    report.add_issue(
                        AuditIssue(
                            category="trump_item_destroyed",
                            severity="blocker",
                            entity_id=cid,
                            chapter=chapter,
                            message=f"Character '{cid}' deployed item trump '{tcard.name if tcard else tid}', but item is destroyed ({cond}) in state ledger.",
                            context={"trump_id": tid, "condition": cond},
                        )
                    )

                # 3. Charges check
                charges = item_record.get("charges")
                if charges is not None and int(charges) <= 0:
                    report.add_issue(
                        AuditIssue(
                            category="trump_item_depleted",
                            severity="blocker",
                            entity_id=cid,
                            chapter=chapter,
                            message=f"Character '{cid}' deployed item trump '{tcard.name if tcard else tid}', but item has 0 charges remaining.",
                            context={"trump_id": tid, "charges": charges},
                        )
                    )

    def _check_faction_diplomacy_contradictions(
        self,
        chapter: int,
        characters: Dict[str, LivingCharacter],
        factions: Optional[Dict[str, Any]],
        manifest: Dict[str, Any],
        report: AuditReport,
    ) -> None:
        """Enforce faction war state consistency: members cannot act as unconditional allies without justification."""
        faction_source = factions if factions is not None else manifest.get("factions")
        if not faction_source:
            return

        actions = manifest.get("actions", [])
        for act in actions:
            actor_id = act.get("actor_id", "")
            target_id = act.get("target_id", "")
            action_tag = act.get("action_tag", "")

            if not actor_id or not target_id or actor_id == target_id:
                continue

            char_a = characters.get(actor_id)
            char_b = characters.get(target_id)
            if not char_a or not char_b:
                continue

            fac_a_id = getattr(char_a, "faction_id", "")
            fac_b_id = getattr(char_b, "faction_id", "")
            if not fac_a_id or not fac_b_id or fac_a_id == fac_b_id:
                continue

            fac_a = faction_source.get(fac_a_id, {})
            if isinstance(fac_a, dict):
                diplomacy = fac_a.get("diplomacy", {})
                status = diplomacy.get(fac_b_id, "")
                if status in ["war", "blood_war", "hostile"]:
                    if action_tag in ["ally", "cooperate", "trade", "unconditional_spare", "confide_secret"]:
                        debt = char_a.debts.get(target_id)
                        has_life_debt = debt is not None and debt.magnitude >= 50
                        motive = char_a.get_motive_at(chapter)
                        has_shift = motive is not None and bool(motive.motive_shift_reason)

                        if not (has_life_debt or has_shift):
                            report.add_issue(
                                AuditIssue(
                                    category="faction_diplomacy_contradiction",
                                    severity="blocker",
                                    entity_id=actor_id,
                                    chapter=chapter,
                                    message=f"Character '{actor_id}' ({fac_a_id}) performed friendly action '{action_tag}' with enemy '{target_id}' ({fac_b_id}) under faction status '{status}' with no life debt or shift rationale.",
                                    context={"faction_a": fac_a_id, "faction_b": fac_b_id, "diplomacy": status},
                                )
                            )

    def _check_physiological_combat_impairment(
        self,
        chapter: int,
        characters: Dict[str, LivingCharacter],
        manifest: Dict[str, Any],
        report: AuditReport,
    ) -> None:
        """Enforce anti-invincible face paralysis: severely injured characters deploying high-tier trumps must pay a cost."""
        for cid, char in characters.items():
            phys = char.get_physiology_at(chapter)
            if phys.injury_level < 3:
                continue

            decision = char.trump_history.get(chapter)
            deployed = list(decision.deployed_trumps) if decision else []
            if not deployed:
                manifest_deployed = manifest.get("deployed_trumps", {})
                if isinstance(manifest_deployed, dict):
                    deployed = manifest_deployed.get(cid, [])
                elif isinstance(manifest_deployed, list):
                    deployed = manifest_deployed

            for tid in deployed:
                tcard = char.trump_inventory.get(tid)
                if not tcard or tcard.tier < 3:
                    continue

                paid_sacrifice = bool(tcard.sacrifice_cost)
                stamina_exhausted = phys.stamina_pool <= 20
                injury_escalated = phys.injury_level >= 4
                has_handicap = len(phys.handicaps) > 0

                if not (paid_sacrifice or stamina_exhausted or injury_escalated or has_handicap):
                    report.add_issue(
                        AuditIssue(
                            category="combat_injury_apathy",
                            severity="blocker",
                            entity_id=cid,
                            chapter=chapter,
                            message=f"Character '{cid}' deployed Tier-{tcard.tier} lethal trump '{tcard.name}' while severely crippled (Injury Lvl {phys.injury_level}) with zero stamina penalty, handicap, or sacrifice cost paid.",
                            context={"injury_level": phys.injury_level, "trump_tier": tcard.tier, "stamina_pool": phys.stamina_pool},
                        )
                    )

    def _check_golden_finger_physiology_coupling(
        self,
        chapter: int,
        characters: Dict[str, LivingCharacter],
        golden_finger: Optional[LivingGoldenFinger],
        manifest: Dict[str, Any],
        report: AuditReport,
    ) -> None:
        """Enforce coupling between Golden Finger backlash/overdraft and protagonist physiology."""
        if not golden_finger:
            return

        has_backlash = golden_finger.backlash_active
        if not has_backlash and golden_finger.energy_history:
            latest_txs = [tx for tx in golden_finger.energy_history if tx.chapter == chapter]
            has_backlash = any(tx.resulting_balance < 0 for tx in latest_txs)

        if not has_backlash:
            return

        protag = None
        for char in characters.values():
            if char.role == "protagonist" or char.character_id == getattr(golden_finger, "host_id", ""):
                protag = char
                break
        if not protag:
            return

        phys = protag.get_physiology_at(chapter)
        reflects_backlash = (phys.injury_level >= 1) or (phys.stress_level >= 30) or (len(phys.handicaps) > 0)
        if not reflects_backlash:
            report.add_issue(
                AuditIssue(
                    category="golden_finger_backlash_disconnection",
                    severity="blocker",
                    entity_id=golden_finger.system_id,
                    chapter=chapter,
                    message=f"Golden Finger '{golden_finger.system_id}' suffered active backlash/overdraft in chapter {chapter}, but host '{protag.character_id}' physiology exhibits zero injury, low stress ({phys.stress_level}), and no handicaps.",
                    context={"stress_level": phys.stress_level, "injury_level": phys.injury_level},
                )
            )

    def _check_deceased_speakers(
        self,
        chapter: int,
        characters: Dict[str, LivingCharacter],
        manifest: Dict[str, Any],
        report: AuditReport,
    ) -> None:
        """Enforce deceased characters cannot speak in dialogue."""
        attributed_speakers = manifest.get("attributed_speakers", [])
        for spk in attributed_speakers:
            c = characters.get(spk)
            if not c:
                for cand in characters.values():
                    if cand.name == spk:
                        c = cand
                        break
            if c and not c.is_alive and c.death_chapter is not None and chapter > c.death_chapter:
                report.add_issue(
                    AuditIssue(
                        category="deceased_speaker_violation",
                        severity="blocker",
                        entity_id=c.character_id,
                        chapter=chapter,
                        message=f"Deceased character '{c.name}' ({c.character_id}) (died ch {c.death_chapter}) was attributed as an active dialogue speaker in chapter {chapter}.",
                        context={"death_chapter": c.death_chapter},
                    )
                )
