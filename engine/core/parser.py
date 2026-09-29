"""Novel Studio 5.0 极简鲁棒 Frontmatter 与 YAML 处理器。

完全采用 Python 3.10+ 标准库实现，零第三方依赖（永不 import PyYAML）。
专用于解析与生成带有 YAML Frontmatter 的 Markdown 工件（如 beats/ch_XXX.md, audit/ch_XXX.md）。
"""
import re
from typing import Tuple, Dict, Any, List, Optional
from engine.core.models import BeatFrontmatter, BeatActor


def split_frontmatter(content: str) -> Tuple[str, str]:
    """将文本切分为 frontmatter 字符串与 markdown 正文"""
    if not content:
        return "", ""
    lines = content.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return "", content

    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return "", content

    fm_str = "".join(lines[1:end_idx])
    body_str = "".join(lines[end_idx + 1:])
    return fm_str, body_str


def _parse_scalar(val: str) -> Any:
    val = val.strip()
    if not val:
        return ""
    if val == "[]":
        return []
    if val == "{}":
        return {}
    if val.lower() == "true":
        return True
    if val.lower() == "false":
        return False
    if val.lower() in ("null", "none", "~"):
        return None
    # 尝试整数
    if re.match(r"^-?\d+$", val):
        return int(val)
    # 尝试浮点数
    if re.match(r"^-?\d+\.\d+$", val):
        return float(val)
    # 处理引号
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        return val[1:-1]
    # 处理内联列表 [a, b, c]
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        if not inner:
            return []
        items = []
        for part in re.split(r",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", inner):
            items.append(_parse_scalar(part))
        return items
    return val


def parse_simple_yaml(text: str) -> Dict[str, Any]:
    """解析通用 YAML 子集（支持嵌套字典、列表与内联结构）"""
    lines = text.splitlines()
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Any, Optional[str]]] = [(-1, root, None)]

    def clean_line(raw: str) -> Tuple[int, str]:
        # 去除纯注释
        s = raw.split("#")[0]
        if not s.strip():
            return 0, ""
        indent = len(raw) - len(raw.lstrip(" "))
        return indent, s.strip()

    i = 0
    while i < len(lines):
        raw = lines[i]
        indent, line = clean_line(raw)
        if not line:
            i += 1
            continue

        # 调整 stack
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()

        cur_indent, cur_obj, cur_key = stack[-1]

        # 1. 列表项 "- value" 或 "- key: value"
        if line.startswith("- "):
            item_content = line[2:].strip()
            if not isinstance(cur_obj, list):
                # 如果当前容器不是 list，将父对象的当前 key 转为 list
                # 这种情况下应该已经在 stack 顶部或者需要调整
                pass

            if ":" in item_content and not (item_content.startswith("{") or item_content.startswith("[")):
                k, v = item_content.split(":", 1)
                sub_dict = {k.strip(): _parse_scalar(v)}
                if isinstance(cur_obj, list):
                    cur_obj.append(sub_dict)
                    stack.append((indent, sub_dict, k.strip()))
            else:
                if isinstance(cur_obj, list):
                    cur_obj.append(_parse_scalar(item_content))
            i += 1
            continue

        # 2. 键值对 "key: value" 或 "key:"
        if ":" in line:
            parts = line.split(":", 1)
            k = parts[0].strip()
            v = parts[1].strip() if len(parts) > 1 else ""

            if not v:
                # 预判下一行是 list 还是 dict
                next_is_list = False
                for j in range(i + 1, len(lines)):
                    nxt_ind, nxt_line = clean_line(lines[j])
                    if nxt_line:
                        if nxt_line.startswith("- "):
                            next_is_list = True
                        break

                new_container: Any = [] if next_is_list else {}
                if isinstance(cur_obj, dict):
                    cur_obj[k] = new_container
                    stack.append((indent, new_container, k))
                elif isinstance(cur_obj, list):
                    cur_obj.append({k: new_container})
                    stack.append((indent, new_container, k))
            else:
                parsed_val = _parse_scalar(v)
                if isinstance(cur_obj, dict):
                    cur_obj[k] = parsed_val
                elif isinstance(cur_obj, list):
                    cur_obj.append({k: parsed_val})

        i += 1

    return root


def parse_beat_file(content: str) -> Tuple[BeatFrontmatter, str]:
    """从细纲 markdown 内容中解析出 BeatFrontmatter 与正文"""
    fm_str, body = split_frontmatter(content)
    if not fm_str:
        return BeatFrontmatter(chapter_id="unknown"), content

    d = parse_simple_yaml(fm_str)

    # 构造 present_characters
    raw_actors = d.get("present_characters", [])
    actors = []
    if isinstance(raw_actors, list):
        for item in raw_actors:
            if isinstance(item, dict):
                actors.append(BeatActor.from_dict(item))

    frontmatter = BeatFrontmatter(
        chapter_id=str(d.get("chapter_id", "unknown")),
        volume_id=str(d.get("volume_id", "vol_01")),
        title=str(d.get("title", "")),
        chapter_type=str(d.get("chapter_type", "Escalation")),
        pov_character=str(d.get("pov_character", "")),
        timeline=str(d.get("timeline", "")),
        location=str(d.get("location", "")),
        spatiotemporal=d.get("spatiotemporal", {}) if isinstance(d.get("spatiotemporal"), dict) else {},
        narrative_spine=d.get("narrative_spine", {}) if isinstance(d.get("narrative_spine"), dict) else {},
        scene_environment=d.get("scene_environment", {}) if isinstance(d.get("scene_environment"), dict) else {},
        present_characters=actors,
        trump_cards=d.get("trump_cards", []) if isinstance(d.get("trump_cards"), list) else [],
        macro_events=d.get("macro_events", []) if isinstance(d.get("macro_events"), list) else [],
        epistemology=d.get("epistemology", {}) if isinstance(d.get("epistemology"), dict) else {},
        foreshadowing_deltas=d.get("foreshadowing_deltas", []) if isinstance(d.get("foreshadowing_deltas"), list) else [],
        state_deltas=d.get("state_deltas", {}) if isinstance(d.get("state_deltas"), dict) else {},
        economy_deltas=d.get("economy_deltas", []) if isinstance(d.get("economy_deltas"), list) else [],
        relation_deltas=d.get("relation_deltas", []) if isinstance(d.get("relation_deltas"), list) else [],
        new_entities=d.get("new_entities", []) if isinstance(d.get("new_entities"), list) else [],
        locked_facts=d.get("locked_facts", []) if isinstance(d.get("locked_facts"), list) else [],
    )
    return frontmatter, body


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse frontmatter as dictionary and return (frontmatter_dict, markdown_body)."""
    fm_str, body = split_frontmatter(content)
    if not fm_str:
        return {}, content
    data = parse_simple_yaml(fm_str)
    return data if isinstance(data, dict) else {}, body


def parse_flow_mapping(text: str) -> Dict[str, Any]:
    """Parse inline YAML mapping such as '{life_status: deceased, condition: "broken"}'.'"""
    s = text.strip()
    if s.startswith("{") and s.endswith("}"):
        s = s[1:-1].strip()
    if not s:
        return {}
    res: Dict[str, Any] = {}
    for part in re.split(r",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", s):
        if ":" in part:
            k, v = part.split(":", 1)
            res[k.strip()] = _parse_scalar(v.strip())
    return res


def parse_volume_outline(outline_text: str, chapter_id: str) -> Optional[Dict[str, str]]:
    """Extract chapter beats planning from volume outline Markdown (vol_XX/outline.md)."""
    header_pattern = rf"^###\s+{re.escape(chapter_id)}[:\s]*(.*)$"
    lines = outline_text.splitlines()
    found = False
    title = ""
    chunk_lines: List[str] = []

    for line in lines:
        if not found:
            match = re.match(header_pattern, line, re.IGNORECASE)
            if match:
                found = True
                title = match.group(1).strip()
        else:
            if line.startswith("### ") or line.startswith("## ") or line.startswith("---"):
                break
            chunk_lines.append(line)

    if not found:
        return None

    info: Dict[str, str] = {"chapter_id": chapter_id, "title": title}
    kv_pattern = r"^-\s*\*\*(.*?)\*\*[:：]\s*(.*)$"
    for cl in chunk_lines:
        m = re.match(kv_pattern, cl)
        if m:
            key = m.group(1).strip()
            val = m.group(2).strip()
            info[key] = val

    return info


def dump_mini_yaml(data: Any, indent: int = 0) -> str:
    """Serialize Python dictionaries and lists into standard formatted YAML string."""
    if data == {} and indent == 0:
        return "{}"
    if data == [] and indent == 0:
        return "[]"
    lines: List[str] = []
    prefix = " " * indent

    if isinstance(data, dict):
        for k, v in data.items():
            key_str = str(k)
            if v is None:
                lines.append(f"{prefix}{key_str}: null")
            elif isinstance(v, bool):
                lines.append(f"{prefix}{key_str}: {'true' if v else 'false'}")
            elif isinstance(v, (int, float)):
                lines.append(f"{prefix}{key_str}: {v}")
            elif isinstance(v, str):
                if "\n" in v:
                    lines.append(f"{prefix}{key_str}: |")
                    for sub in v.splitlines():
                        lines.append(f"{prefix}  {sub}")
                elif any(c in v for c in ":#{}[]*,&!|>'\"%@`"):
                    lines.append(f'{prefix}{key_str}: "{v}"')
                else:
                    lines.append(f"{prefix}{key_str}: {v}")
            elif isinstance(v, list):
                if not v:
                    lines.append(f"{prefix}{key_str}: []")
                else:
                    lines.append(f"{prefix}{key_str}:")
                    for item in v:
                        if isinstance(item, (int, float, bool)):
                            lines.append(f"{prefix}  - {item}")
                        elif isinstance(item, str):
                            lines.append(f'{prefix}  - "{item}"')
                        elif isinstance(item, dict):
                            sub_yaml = dump_mini_yaml(item, indent=indent + 4).lstrip()
                            lines.append(f"{prefix}  - {sub_yaml}")
            elif isinstance(v, dict):
                lines.append(f"{prefix}{key_str}:")
                sub_dict = dump_mini_yaml(v, indent=indent + 2)
                lines.append(sub_dict)

    return "\n".join(lines)
