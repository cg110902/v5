"""Industrial Web Novel Exporter and Distribution Engine (engine/core/exporter.py).

Features:
1. Export publication-ready manuscripts (clean TXT for Tomato/Qidian, Markdown for reading).
2. Two-space paragraph indent formatting (　　) standard for Chinese web literature.
3. Chapter continuity and seal verification before bundling.
4. Volume bundles and full-novel distributions.

Zero literary hardcoding. 100% Python standard library.
"""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from engine.core.state import StateManager
from engine.core.storage import atomic_write_text, ensure_directory
from engine.errors import GuardError


def _chapter_num(chapter_id: str) -> int:
    m = re.search(r"(\d+)", str(chapter_id))
    return int(m.group(1)) if m else 1


def clean_prose_for_export(raw_text: str, format_type: str = "txt") -> str:
    """Clean markdown artifacts, frontmatter, and format paragraphs with standard web novel indent."""
    # 1. Strip YAML frontmatter
    text = re.sub(r"^---.*?---\s*", "", raw_text, flags=re.DOTALL)
    # 2. Strip HTML comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # 3. Strip slot tags
    text = re.sub(r"\{\{slot:[^\}]+\}\}", "", text)

    lines = text.splitlines()
    formatted_paragraphs: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Keep or format markdown headers
        if stripped.startswith("#"):
            header_text = re.sub(r"^#+\s*", "", stripped)
            if format_type == "txt":
                formatted_paragraphs.append(f"\n{header_text}\n")
            else:
                formatted_paragraphs.append(f"\n# {header_text}\n")
            continue

        # Standard paragraph indentation: two full-width spaces for TXT
        if format_type == "txt":
            clean_para = "　　" + re.sub(r"^[　\s]+", "", stripped)
            formatted_paragraphs.append(clean_para)
        else:
            formatted_paragraphs.append(stripped)

    return "\n\n".join(formatted_paragraphs).strip() + "\n"


class Exporter:
    """Distribution packaging engine for finalized novel manuscripts."""

    def __init__(self, workspace: Union[str, Path]) -> None:
        self.workspace = Path(workspace).resolve()
        self.state_mgr = StateManager(self.workspace)
        self.dist_dir = self.workspace / "dist"
        ensure_directory(self.dist_dir)

    def export_volume(
        self,
        volume_id: str = "vol_01",
        format_type: str = "txt",
        output_file: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        """Export all sealed chapters for a volume into a single bundled distribution file."""
        final_dir = self.workspace / "final"
        if not final_dir.exists():
            raise GuardError(f"No finalized chapters found in {final_dir}")

        # Collect sealed chapter files sorted numerically
        chapter_files = sorted(
            [f for f in final_dir.glob("ch_*.md") if f.is_file()],
            key=lambda f: _chapter_num(f.stem)
        )

        if not chapter_files:
            raise GuardError(f"No sealed chapters (ch_*.md) found in {final_dir}")

        # Verify continuity
        chapter_nums = [_chapter_num(f.stem) for f in chapter_files]
        missing_holes = []
        for i in range(chapter_nums[0], chapter_nums[-1] + 1):
            if i not in chapter_nums:
                missing_holes.append(f"ch_{i:03d}")

        if missing_holes:
            raise GuardError(
                f"Chapter sequence has gaps: missing {missing_holes}",
                remediation="Ensure all chapters are sequentially sealed in final/ before exporting."
            )

        bundled_sections: List[str] = []
        total_words = 0

        # Header
        current = self.state_mgr.get_current()
        bundled_sections.append(f"【{volume_id.upper()} 分卷定稿】\n")

        for f in chapter_files:
            raw = f.read_text(encoding="utf-8")
            clean_text = clean_prose_for_export(raw, format_type=format_type)
            bundled_sections.append(clean_text)
            bundled_sections.append("\n" + ("=" * 40) + "\n")
            total_words += len(re.sub(r"\s+", "", clean_text))

        final_content = "\n".join(bundled_sections).strip() + "\n"

        target_ext = "txt" if format_type == "txt" else "md"
        out_path = Path(output_file) if output_file else self.dist_dir / f"{volume_id}.{target_ext}"
        atomic_write_text(out_path, final_content)

        return {
            "volume_id": volume_id,
            "format": format_type,
            "chapters_count": len(chapter_files),
            "total_words": total_words,
            "export_file": str(out_path),
        }

    def export_full_book(
        self,
        format_type: str = "txt",
        output_file: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        """Export entire novel manuscript across all volumes."""
        return self.export_volume(volume_id="full_book", format_type=format_type, output_file=output_file)
