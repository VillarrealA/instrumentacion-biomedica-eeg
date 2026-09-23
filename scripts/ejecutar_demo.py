#!/usr/bin/env python3
"""Genera datos sintéticos y ejecuta los análisis de ejemplo."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from generar_datos_demo import generate_demo


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    open_path, closed_path, backyard_path = generate_demo(root / "datos" / "demo")
    biopac_command = [
        sys.executable,
        str(root / "scripts" / "analiza_biopac.py"),
        str(open_path),
        str(closed_path),
        "--unit",
        "uV",
        "--time-column",
        "time_s",
        "--signal-column",
        "eeg_uv",
        "--open-start",
        "2",
        "--closed-start",
        "2",
        "--duration",
        "10",
        "--channel",
        "DEMO",
        "--output-dir",
        str(root / "resultados" / "demo"),
    ]
    backyard_command = [
        sys.executable,
        str(root / "scripts" / "analiza_backyard.py"),
        str(backyard_path),
        "--time-column",
        "time_s",
        "--signal-column",
        "signal_uv",
        "--event-column",
        "event",
        "--unit",
        "uV",
        "--pre",
        "0.2",
        "--post",
        "0.5",
        "--output-dir",
        str(root / "resultados" / "demo" / "backyard"),
    ]
    biopac_completed = subprocess.run(biopac_command, check=False)
    backyard_completed = subprocess.run(backyard_command, check=False)
    return int(biopac_completed.returncode or backyard_completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
