#!/usr/bin/env python3
"""Genera señales sintéticas para comprobar ambos flujos de análisis."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def generate_demo(output_dir: Path, fs_hz: float = 160.0, duration_s: float = 20.0) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260923)
    time_s = np.arange(int(fs_hz * duration_s), dtype=float) / fs_hz

    common = 3.0 * np.sin(2 * np.pi * 2.0 * time_s)
    open_uv = (
        common
        + 5.0 * np.sin(2 * np.pi * 10.0 * time_s + 0.2)
        + rng.normal(0.0, 5.5, time_s.size)
    )
    closed_uv = (
        common
        + 18.0 * np.sin(2 * np.pi * 10.0 * time_s + 0.2)
        + rng.normal(0.0, 5.5, time_s.size)
    )

    # Transitorios fuera de la ventana predeterminada de 2 a 12 s.
    blink = 65.0 * np.exp(-0.5 * ((time_s - 16.0) / 0.12) ** 2)
    open_uv += blink
    closed_uv += blink

    open_path = output_dir / "demo_biopac_abiertos.csv"
    closed_path = output_dir / "demo_biopac_cerrados.csv"
    pd.DataFrame({"time_s": time_s, "eeg_uv": open_uv}).to_csv(open_path, index=False)
    pd.DataFrame({"time_s": time_s, "eeg_uv": closed_uv}).to_csv(closed_path, index=False)
    backyard_fs_hz = 500.0
    backyard_duration_s = 20.0
    backyard_time_s = np.arange(int(backyard_fs_hz * backyard_duration_s), dtype=float) / backyard_fs_hz
    backyard_uv = rng.normal(0.0, 5.0, backyard_time_s.size)
    event = np.zeros(backyard_time_s.size, dtype=int)
    event_times_s = np.arange(1.0, 19.0, 1.0)
    for event_time_s in event_times_s:
        index = int(round(event_time_s * backyard_fs_hz))
        event[index] = 1
        latency_s = backyard_time_s - event_time_s
        response = (
            -4.0 * np.exp(-0.5 * ((latency_s - 0.10) / 0.025) ** 2)
            + 7.0 * np.exp(-0.5 * ((latency_s - 0.22) / 0.045) ** 2)
        )
        backyard_uv += response
    backyard_path = output_dir / "demo_backyard_eventos.csv"
    pd.DataFrame(
        {"time_s": backyard_time_s, "signal_uv": backyard_uv, "event": event}
    ).to_csv(backyard_path, index=False)
    return open_path, closed_path, backyard_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera EEG sintético de demostración.")
    parser.add_argument("--output-dir", type=Path, default=Path("datos/demo"))
    args = parser.parse_args()
    open_path, closed_path, backyard_path = generate_demo(args.output_dir)
    print(open_path)
    print(closed_path)
    print(backyard_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
