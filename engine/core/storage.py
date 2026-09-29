"""Novel Studio 5.0 原子化存储与损坏防护引擎 (Storage Layer)。

实现：
1. tempfile + os.replace 原子写盘，防止系统崩溃或断电导致写入半截文件；
2. 损坏 JSON 自动隔离为 *.corrupt-<timestamp>.json 并抛出 StorageError (退出码 4)；
3. 严格遵循 UTF-8 编码与标准 JSON 格式。
"""
import os
import json
import tempfile
import time
from pathlib import Path
from typing import Any, Union
from engine.errors import StorageError


def ensure_directory(path: Union[str, Path]) -> Path:
    """确保目录存在"""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def atomic_write_text(filepath: Union[str, Path], content: str) -> None:
    """原子写入文本文件"""
    target = Path(filepath).resolve()
    ensure_directory(target.parent)

    tmp_file = None
    try:
        # 在目标文件同级目录下创建临时文件，确保同物理卷以便 os.replace 原子重命名
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=str(target.parent),
            prefix=f".{target.name}.tmp_",
            delete=False,
            encoding="utf-8"
        ) as f:
            tmp_file = Path(f.name)
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        os.replace(str(tmp_file), str(target))
    except Exception as e:
        if tmp_file and tmp_file.exists():
            try:
                tmp_file.unlink()
            except Exception:
                pass
        raise StorageError(
            f"原子写入文件失败: {target} (原因: {str(e)})",
            remediation="检查磁盘空间、文件系统权限或目标文件是否被外部进程锁定占用。"
        ) from e


def atomic_write_json(filepath: Union[str, Path], data: Any, indent: int = 2) -> None:
    """原子写入 JSON 文件"""
    content = json.dumps(data, ensure_ascii=False, indent=indent) + "\n"
    atomic_write_text(filepath, content)


def safe_load_json(filepath: Union[str, Path], default: Any = None) -> Any:
    """安全读取 JSON 文件，损坏时自动隔离并抛出硬阻断 (Exit Code 4)"""
    target = Path(filepath).resolve()
    if not target.is_file():
        if default is not None:
            return default
        raise StorageError(
            f"状态数据文件不存在: {target}",
            remediation=f"请先运行初始化命令或检查工作区路径是否正确。"
        )

    try:
        with open(target, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        # 损坏文件自动隔离
        ts = int(time.time())
        corrupt_target = target.parent / f"{target.stem}.corrupt-{ts}{target.suffix}"
        try:
            os.replace(str(target), str(corrupt_target))
        except Exception:
            pass

        raise StorageError(
            f"数据文件已损坏无法解析: {target.name} (已隔离备份为: {corrupt_target.name})",
            remediation="状态文件损坏属于系统级故障。已将受损文件隔离，请使用 snapshot rollback 恢复至上一个健康快照。"
        ) from e


# 常用友好别名
load_json = safe_load_json
save_json = atomic_write_json
