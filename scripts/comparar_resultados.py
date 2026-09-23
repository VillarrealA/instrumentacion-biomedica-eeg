#!/usr/bin/env python3
"""Compara resultados derivados de BIOPAC y PhysioNet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compara métricas EEG sin mezclar amplitudes absolutas."
    )
    parser.add_argument("biopac_metrics", type=Path)
    parser.add_argument("physionet_metrics", type=Path)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("resultados/comparacion")
    )
    return parser.parse_args()


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    required = {"source", "channel", "fs_hz", "eyes_open", "eyes_closed", "alpha_ratio_closed_open"}
    missing = required.difference(data)
    if missing:
        raise ValueError(f"{path} no contiene: {sorted(missing)}")
    return data


def _row(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": data["source"],
        "channel": data["channel"],
        "fs_hz": data["fs_hz"],
        "duration_s": data["window_duration_s"],
        "alpha_open_uv2": data["eyes_open"]["alpha_power_uv2"],
        "alpha_closed_uv2": data["eyes_closed"]["alpha_power_uv2"],
        "relative_alpha_open": data["eyes_open"]["relative_alpha"],
        "relative_alpha_closed": data["eyes_closed"]["relative_alpha"],
        "alpha_ratio_closed_open": data["alpha_ratio_closed_open"],
    }


def main() -> int:
    args = parse_args()
    try:
        biopac = _load(args.biopac_metrics)
        physionet = _load(args.physionet_metrics)
        destination = args.output_dir
        destination.mkdir(parents=True, exist_ok=True)

        table = pd.DataFrame([_row(biopac), _row(physionet)])
        table_path = destination / "comparacion_estaciones.csv"
        table.to_csv(table_path, index=False)

        labels = ["BIOPAC", "PhysioNet"]
        ratios = [
            float(biopac["alpha_ratio_closed_open"]),
            float(physionet["alpha_ratio_closed_open"]),
        ]
        x = np.arange(len(labels), dtype=float)
        width = 0.34
        fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
        ax.bar(x - width / 2, np.ones(2), width, label="Ojos abiertos = 1")
        ax.bar(x + width / 2, ratios, width, label="Ojos cerrados / abiertos")
        ax.axhline(1.0, color="black", lw=0.9, alpha=0.6)
        ax.set_xticks(x, labels)
        ax.set_ylabel("Potencia alfa normalizada dentro de cada estación")
        ax.set_title("Reactividad alfa: comparación sin mezclar amplitudes absolutas")
        ax.grid(axis="y", alpha=0.25)
        ax.legend()
        for index, ratio in enumerate(ratios):
            ax.text(index + width / 2, ratio, f"{ratio:.2f}", ha="center", va="bottom")
        figure_path = destination / "comparacion_r_alfa.png"
        fig.savefig(figure_path, dpi=180)
        plt.close(fig)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"tabla: {table_path}")
    print(f"figura: {figure_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
