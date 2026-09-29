#!/usr/bin/env python3
"""Novel Studio 5.0 顶层统一入口门面 (Entrypoint)。"""
import os
import sys
from pathlib import Path

# Windows UTF-8 控制台兼容
if sys.platform == "win32":
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    for _stream in (sys.stdout, sys.stderr, sys.stdin):
        if hasattr(_stream, "reconfigure"):
            try:
                _stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

import builtins
import pkgutil
import importlib
try:
    import engine
    for finder, name, ispkg in pkgutil.walk_packages(engine.__path__, engine.__name__ + "."):
        try:
            mod = importlib.import_module(name)
            if hasattr(mod, "GuardError"):
                builtins.GuardError = getattr(mod, "GuardError")
                break
        except Exception:
            pass
    if not hasattr(builtins, "GuardError"):
        # If GuardError is not yet defined, create a base Exception class for it
        class GuardError(Exception):
            pass
        builtins.GuardError = GuardError
except Exception:
    pass

try:
    from engine.cli import main
except SyntaxError as _exc:
    sys.stderr.write(
        f"\n❌ Python 解释器版本不兼容: {_exc}\n"
        "   要求: Python >= 3.10 标准库\n"
    )
    sys.exit(3)
except ImportError as _exc:
    sys.stderr.write(
        f"\n❌ 环境依赖异常: {_exc}\n"
        "   本引擎零外部第三方包，仅需 Python >= 3.10 标准库。\n"
    )
    sys.exit(3)

if __name__ == "__main__":
    sys.exit(main())
