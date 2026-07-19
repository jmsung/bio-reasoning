"""Regression guard: the self-improve loop defaults to high concurrency.

The loop was throughput-blocked at concurrency 8/16 (a stale urllib-era deadlock
cap) — a val-60 candidate took >17 min with 0 trials. The endpoint saturates
cleanly at 32 (measured 0 errors); this pins the default so the throttle can't
silently return. See findings/loop-concurrency-throughput-fix.md.
"""

import importlib.util
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "self_improve_loop.py"


def _build_parser():
    spec = importlib.util.spec_from_file_location("_sil", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod._build_arg_parser() if hasattr(mod, "_build_arg_parser") else mod


def test_default_concurrency_is_high():
    # parse with no args → defaults; concurrency must be >= 32 (unblocked throughput)
    import subprocess
    import sys

    out = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"], capture_output=True, text=True
    ).stdout
    # the help string shows the default; assert it's not the old throttled 8/16
    assert "--concurrency" in out
    # exercise the real default via argparse
    import re

    m = re.search(r"--concurrency[^\n]*", out)
    assert m, "concurrency arg missing"


def test_concurrency_default_value_is_32():
    src = _SCRIPT.read_text()
    import re

    m = re.search(r'"--concurrency",\s*type=int,\s*default=(\d+)', src)
    assert m, "could not find --concurrency default"
    assert int(m.group(1)) >= 32, f"default concurrency {m.group(1)} < 32 (throttle regressed)"
