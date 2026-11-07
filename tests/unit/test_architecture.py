"""Constitution VI and II: the domain is framework-free and has no unexplained numbers."""

import ast
import pkgutil
import subprocess
import sys
from pathlib import Path

DOMAIN_DIR = Path(__file__).resolve().parents[2] / "src" / "strava_predictor" / "domain"
ALLOWED_NUMBERS = {0, 1}
FORBIDDEN_MODULES = ("fastapi", "starlette", "jinja2")


def _domain_modules() -> list[str]:
    return [
        f"strava_predictor.domain.{info.name}" for info in pkgutil.iter_modules([str(DOMAIN_DIR)])
    ]


def test_domain_has_modules():
    assert _domain_modules(), "domain package has no modules"


def test_domain_does_not_import_web_frameworks():
    modules = ", ".join(repr(name) for name in _domain_modules())
    script = (
        "import importlib, sys\n"
        f"for name in [{modules}]:\n"
        "    importlib.import_module(name)\n"
        f"bad = [m for m in {FORBIDDEN_MODULES!r} if m in sys.modules]\n"
        "print(','.join(bad))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == ""


def test_domain_has_no_bare_numbers():
    offenders = []
    for path in DOMAIN_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, int | float)
                and not isinstance(node.value, bool)
                and node.value not in ALLOWED_NUMBERS
            ):
                offenders.append(f"{path.name}:{node.lineno} {node.value!r}")
    assert offenders == [], "numbers must live in config.py: " + ", ".join(offenders)
