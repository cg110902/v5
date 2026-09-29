"""Novel Studio 5.0 配置中心。

优先级：工作区 project.json.engine > 工作区 project.json.scope > 引擎内置 DEFAULT_CONFIG。
"""
from typing import Any, Dict
import json
from pathlib import Path


DEFAULT_CONFIG: Dict[str, Any] = {
    # 工业流水线参数
    "token_cap": 32000,
    "cruise_max_chapters": 10,
    "cruise_human_gate": 0,
    "cruise_wait_timeout": 300,
    
    # 篇幅与结构指引（写手指引，非硬阻断）
    "target_words_min": 2000,
    "target_words_max": 3500,
    "chapters_per_volume": 30,
    
    # 长程雷达监测阈值
    "lifeline_yellow_card": 8,   # 连续未登场章数黄牌
    "lifeline_red_card": 12,     # 连续未登场章数红牌
    "foreshadowing_alert": 3,    # 伏笔到期预警章数
    "foreshadowing_overdue": 0,  # 伏笔逾期必须结算
    
    # 默认经济池
    "default_pools": {
        "copper": 1000,
        "silver": 50,
        "gold": 0
    }
}


class Config:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.data: Dict[str, Any] = dict(DEFAULT_CONFIG)
        self.project_meta: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        project_file = self.workspace / "project.json"
        if project_file.is_file():
            try:
                with open(project_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    self.project_meta = meta
                    if isinstance(meta, dict):
                        # 合并 scope
                        if "scope" in meta and isinstance(meta["scope"], dict):
                            self.data.update(meta["scope"])
                        # 合并 engine 旋钮
                        if "engine" in meta and isinstance(meta["engine"], dict):
                            self.data.update(meta["engine"])
            except Exception:
                pass

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        project_file = self.workspace / "project.json"
        if project_file.is_file():
            try:
                with open(project_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                if "engine" not in meta or not isinstance(meta["engine"], dict):
                    meta["engine"] = {}
                meta["engine"][key] = value
                with open(project_file, "w", encoding="utf-8") as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
