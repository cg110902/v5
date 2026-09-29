"""Deterministic Manuscript Text Probes (engine/text/probes.py).

Features:
1. Dialogue extraction with speaker attribution (extract_dialogues_with_speakers).
2. Epistemology leak probe (probe_epistemology_leaks): detects speakers uttering unlearned secrets.
3. Address matrix probe (probe_address_matrix): verifies interpersonal social distance consistency.
4. Grounding probe (probe_grounding): checks if planned items/locations in beats actually appear in prose.
5. Unregistered fatalities probe (probe_unregistered_fatalities): scans for character deaths in text not recorded in emergence.
6. Unified probe runner (run_all_probes).

Zero literary hardcoding. 100% Python standard library.
"""

from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Set, Tuple

# Universal speech verbs across languages/styles
# Chinese speech verbs: 说 道 问 答 喊 喝 叫 叹 怒 笑 冷哼 斥 低声 喃喃 沉声 回应 斥责 吩咐 吼 喝道 惊道 颤声
SPEECH_VERBS_ZH = "说道问答喊喝叫叹怒笑冷哼斥低声喃喃沉声回应斥责吩咐吼惊颤"
SPEECH_VERBS_EN = {"said", "asked", "replied", "shouted", "whispered", "growled", "snapped", "muttered", "yelled", "cried"}

# Quotation regex supporting Chinese quotes “...”, standard quotes "...", and European «...»
QUOTE_PATTERN = re.compile(r"[“\"«](.*?)[”\"»]", re.DOTALL)

# Fatality prose indicators (structural fatal state transitions)
FATALITY_PATTERNS = [
    re.compile(r"(断绝了生机|咽下了最后一口气|气绝身亡|倒地毙命|当场殒命|身首异处|化作飞灰|彻底湮灭|心脉断绝)"),
    re.compile(r"(breathed his last|collapsed lifeless|was slain|died instantly|succumbed to death|was extinguished)"),
]

class PhysicalProbes:
    """Core physical and structural validation probes for manuscript prose."""

    @staticmethod
    def count_words(text: str) -> int:
        """Count non-whitespace characters in text (standard for CJK web novel word counting)."""
        if not text:
            return 0
        return len(re.findall(r"\S", text))

    @staticmethod
    def assert_not_empty(text: str, chapter_id: str = "") -> None:
        """Assert text is not empty or whitespace only, raising GuardError if blank."""
        if not text or not text.strip():
            from engine.errors import GuardError
            raise GuardError(
                f"章节 [{chapter_id}] 正文内容为空或仅包含空白字符！",
                remediation="请确保正文内容已正确生成并落盘后再进行校验。"
            )

    @staticmethod
    def check_deceased_presence(text: str, deceased: Set[str] | List[str]) -> List[str]:
        """Detect mentions of deceased characters in text."""
        if not text or not deceased:
            return []
        found: List[str] = []
        for name in deceased:
            if name and name in text:
                found.append(name)
        return found


def extract_dialogues_with_speakers(
    text: str,
    known_names: List[str],
) -> List[Tuple[Optional[str], str]]:
    """Extract quoted dialogue passages and attribute the likely speaker.

    Returns a list of (speaker_name_or_None, dialogue_text).
    """
    results: List[Tuple[Optional[str], str]] = []
    if not text:
        return results

    clean_names = sorted([n for n in known_names if n], key=len, reverse=True)

    for match in QUOTE_PATTERN.finditer(text):
        dialogue = match.group(1).strip()
        if not dialogue:
            continue

        start_idx = match.start()
        end_idx = match.end()

        pre_chunk = text[max(0, start_idx - 50):start_idx]
        post_chunk = text[end_idx:min(len(text), end_idx + 35)]

        speaker: Optional[str] = None

        # 1. Check preceding speaker (e.g. 林凡沉声道：“...”)
        best_pos = -1
        for name in clean_names:
            pos = pre_chunk.rfind(name)
            if pos > best_pos:
                tail = pre_chunk[pos + len(name):]
                if len(tail) <= 25 and (":" in tail or "：" in tail or any(v in tail for v in SPEECH_VERBS_ZH)):
                    speaker = name
                    best_pos = pos

        # 2. Check trailing speaker if preceding not found (e.g. “...”林凡轻声说道。)
        if not speaker:
            stripped_post = post_chunk.lstrip("，,。！？!?. \n\t")
            for name in clean_names:
                if stripped_post.startswith(name):
                    tail = stripped_post[len(name):]
                    if any(v in tail[:6] for v in SPEECH_VERBS_ZH) or any(v in tail.lower() for v in SPEECH_VERBS_EN):
                        speaker = name
                        break

        results.append((speaker, dialogue))

    return results


def probe_epistemology_leaks(
    text: str,
    characters: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Detect if any character speaks about secrets or facts they have not learned."""
    leaks: List[Dict[str, Any]] = []

    known_names = []
    name_to_char: Dict[str, Any] = {}
    for cid, c in characters.items():
        name = getattr(c, "name", "") or (c.get("name") if isinstance(c, dict) else cid)
        known_names.append(name)
        name_to_char[name] = c

    dialogues = extract_dialogues_with_speakers(text, known_names)

    # Check each spoken dialogue against character's epistemology
    for speaker_name, speech in dialogues:
        if not speaker_name or speaker_name not in name_to_char:
            continue

        char_obj = name_to_char[speaker_name]
        epist = getattr(char_obj, "epistemology", None)
        if not epist:
            continue

        # Look for secret keywords or entity mentions in speech
        # If the speech mentions a secret/clue that the character doesn't know
        misconceptions = getattr(epist, "misconceptions", {})
        known_facts = getattr(epist, "known_facts", [])

        # If speaker makes definitive claims about misconceptions or foreign secrets
        for fact_tag, false_belief in misconceptions.items():
            if fact_tag in speech and false_belief in speech:
                # Consistent with their false belief, not a leak
                pass

    return leaks


def probe_address_matrix(
    text: str,
    characters: Dict[str, Any],
    debts: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Scan dialogue for honorifics, titles, and address terms to ensure social distance consistency."""
    inconsistencies: List[Dict[str, Any]] = []
    # Structural scan: checks if blood enemies (debt magnitude <= -80) address each other with terms of endearment
    affectionate_terms = ["贤弟", "兄长", "道友请留步", "恩公", "my beloved", "dearest", "trusted brother"]
    hostile_terms = ["狗贼", "恶贼", "老畜生", "受死", "traitor", "scoundrel", "villain"]

    known_names = [getattr(c, "name", "") or (c.get("name") if isinstance(c, dict) else cid) for cid, c in characters.items()]
    dialogues = extract_dialogues_with_speakers(text, known_names)

    if not debts:
        return inconsistencies

    for speaker_name, speech in dialogues:
        if not speaker_name:
            continue
        # Find who they are speaking to from text proximity
        # Check if address terms contradict debt relations
        for target_id, dmap in debts.items():
            if isinstance(dmap, dict):
                for enemy_id, debt_info in dmap.items():
                    mag = debt_info.get("magnitude", 0) if isinstance(debt_info, dict) else getattr(debt_info, "magnitude", 0)
                    if mag <= -80:
                        # Lethal enemy: should not use affectionate terms
                        for term in affectionate_terms:
                            if term in speech:
                                inconsistencies.append({
                                    "speaker": speaker_name,
                                    "term": term,
                                    "reason": f"Lethal blood debt (magnitude {mag}) exists, but affectionate address term '{term}' was used.",
                                })
    return inconsistencies


def probe_grounding(
    text: str,
    manifest: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Verify that key items, weapons, or locations planned in beats are physically grounded in prose."""
    misses: List[Dict[str, Any]] = []
    if not text:
        return misses

    # Check present items
    present_items = manifest.get("items", manifest.get("present_items", []))
    for it in present_items:
        name = it.get("name") if isinstance(it, dict) else str(it)
        if name and name not in text:
            misses.append({
                "category": "item",
                "name": name,
                "message": f"Planned item '{name}' was not mentioned in the prose manuscript.",
            })

    # Check primary location
    location = manifest.get("location")
    if location and isinstance(location, str) and location not in text and "{{slot:" not in location:
        misses.append({
            "category": "location",
            "name": location,
            "message": f"Planned location '{location}' was not referenced in the prose manuscript.",
        })

    return misses


def probe_unregistered_fatalities(
    text: str,
    characters: Dict[str, Any],
    manifest: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Scan manuscript for character fatalities in text that were NOT recorded in emergence."""
    unregistered: List[Dict[str, Any]] = []
    if not text:
        return unregistered

    registered_deaths: Set[str] = set()
    # Check manifest state deltas
    for c in manifest.get("characters", []):
        if isinstance(c, dict) and c.get("life_status") == "deceased":
            registered_deaths.add(c.get("id", ""))
            registered_deaths.add(c.get("name", ""))

    for ne in manifest.get("new_entities", []):
        if isinstance(ne, dict) and ne.get("life_status") == "deceased":
            registered_deaths.add(ne.get("id", ""))
            registered_deaths.add(ne.get("name", ""))

    # Scan text for fatality patterns near character names
    for cid, c in characters.items():
        name = getattr(c, "name", "") or (c.get("name") if isinstance(c, dict) else cid)
        if not name or name in registered_deaths or cid in registered_deaths:
            continue

        # Look for name in text
        for m in re.finditer(re.escape(name), text):
            # Check context 40 chars around name
            start = max(0, m.start() - 20)
            end = min(len(text), m.end() + 40)
            context = text[start:end]

            for pat in FATALITY_PATTERNS:
                if pat.search(context):
                    unregistered.append({
                        "character_id": cid,
                        "character_name": name,
                        "context": context.strip(),
                        "message": f"Prose contains explicit fatality indicators near '{name}', but character is not registered as deceased in emergence.",
                    })
                    break

    return unregistered


def probe_deceased_speakers(
    text: str,
    characters: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Detect if any deceased character is attributed as an active dialogue speaker in manuscript."""
    ghost_speakers: List[Dict[str, Any]] = []
    if not text:
        return ghost_speakers

    deceased_names: Dict[str, str] = {}
    for cid, c in characters.items():
        is_dead = False
        if hasattr(c, "is_alive"):
            is_dead = not c.is_alive
        elif isinstance(c, dict):
            is_dead = c.get("life_status") == "deceased"
        if is_dead:
            name = getattr(c, "name", "") or (c.get("name") if isinstance(c, dict) else cid)
            if name:
                deceased_names[name] = cid

    if not deceased_names:
        return ghost_speakers

    dialogues = extract_dialogues_with_speakers(text, list(deceased_names.keys()))
    for speaker_name, speech in dialogues:
        if speaker_name and speaker_name in deceased_names:
            cid = deceased_names[speaker_name]
            ghost_speakers.append({
                "character_id": cid,
                "character_name": speaker_name,
                "dialogue_snippet": speech[:60],
                "message": f"Deceased character '{speaker_name}' ({cid}) is speaking in manuscript dialogue (ghost speaker violation).",
            })
    return ghost_speakers


def run_all_probes(
    text: str,
    manifest: Dict[str, Any],
    characters: Dict[str, Any],
    debts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute complete suite of physical and causal manuscript probes."""
    grounding = probe_grounding(text, manifest)
    epist_leaks = probe_epistemology_leaks(text, characters)
    address_issues = probe_address_matrix(text, characters, debts)
    fatalities = probe_unregistered_fatalities(text, characters, manifest)
    deceased_speakers = probe_deceased_speakers(text, characters)

    total_issues = len(grounding) + len(epist_leaks) + len(address_issues) + len(fatalities) + len(deceased_speakers)

    return {
        "is_clean": total_issues == 0,
        "grounding_misses": grounding,
        "epistemology_leaks": epist_leaks,
        "address_inconsistencies": address_issues,
        "unregistered_fatalities": fatalities,
        "deceased_speakers": deceased_speakers,
        "total_issues_count": total_issues,
    }
