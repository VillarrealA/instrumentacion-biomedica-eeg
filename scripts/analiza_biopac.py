#!/usr/bin/env python3
"""Analiza dos exportaciones BIOPAC: ojos abiertos y ojos cerrados."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from eeg_core import (
    analyze_pair,
    convert_to_uv,
    infer_sampling_rate,
    save_analysis,
)


TIME_NAMES = ("time", "tiempo", "seconds", "second", "sec", "s")


def _read_table(path: Path) -> pd.DataFrame:
    attempts = [
        {"sep": None, "engine": "python"},
        {"sep": "\t"},
        {"sep": ","},
        {"sep": ";"},
    ]
    last_error: Exception | None = None
    for options in attempts:
        try:
            frame = pd.read_csv(path, **options)
            if frame.shape[1] >= 1 and frame.shape[0] >= 16:
                return frame
        except Exception as exc:  # pragma: no cover - conserva el último error
            last_error = exc
    raise ValueError(f"No fue posible leer {path}: {last_error}")


def _match_column(frame: pd.DataFrame, requested: str | None) -> str | None:
    if requested is None:
        return None
    if requested in frame.columns:
        return requested
    lookup = {str(column).strip().lower(): str(column) for column in frame.columns}
    key = requested.strip().lower()
    if key in lookup:
        return lookup[key]
    raise ValueError(f"No existe la columna '{requested}'. Disponibles: {list(frame.columns)}")


def _guess_time_column(frame: pd.DataFrame) -> str | None:
    for column in frame.columns:
        key = str(column).strip().lower()
        if key in TIME_NAMES or any(token in key for token in ("time", "tiempo")):
            return str(column)
    return None


def _numeric(frame: pd.DataFrame, column: str) -> np.ndarray:
    converted = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
    return converted[np.isfinite(converted)]


def load_export(
    path: Path,
    time_column: str | None,
    signal_column: str | None,
    fs_hz: float | None,
) -> tuple[np.ndarray, float, str, str | None]:
    frame = _read_table(path)
    chosen_time = _match_column(frame, time_column) or _guess_time_column(frame)
    chosen_signal = _match_column(frame, signal_column)

    if chosen_signal is None:
        candidates: list[str] = []
        for column in frame.columns:
            name = str(column)
            if name == chosen_time:
                continue
            numeric = pd.to_numeric(frame[column], errors="coerce")
            if numeric.notna().sum() >= 16:
                candidates.append(name)
        if not candidates:
            raise ValueError(f"No se encontró una columna de señal en {path}.")
        chosen_signal = candidates[0]

    values = _numeric(frame, chosen_signal)
    inferred_fs = fs_hz
    if inferred_fs is None:
        if chosen_time is None:
            raise ValueError(
                f"{path} no contiene columna de tiempo. Indique --fs."
            )
        time_values = _numeric(frame, chosen_time)
        if time_values.size != values.size:
            raise ValueError("Tiempo y señal no tienen el mismo número de muestras válidas.")
        inferred_fs = infer_sampling_rate(time_values)
    return values, float(inferred_fs), chosen_signal, chosen_time


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analiza EEG BIOPAC de ojos abiertos y cerrados."
    )
    parser.add_argument("open_csv", type=Path, help="CSV de ojos abiertos")
    parser.add_argument("closed_csv", type=Path, help="CSV de ojos cerrados")
    parser.add_argument("--fs", type=float, default=None, help="Muestreo si no hay tiempo")
    parser.add_argument("--time-column", default=None)
    parser.add_argument("--signal-column", default=None)
    parser.add_argument("--unit", default="uV", choices=["V", "mV", "uV"])
    parser.add_argument("--open-start", type=float, default=0.0)
    parser.add_argument("--closed-start", type=float, default=0.0)
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--notch", type=float, default=None)
    parser.add_argument("--channel", default="EEG")
    parser.add_argument("--output-dir", type=Path, default=Path("resultados/biopac"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        open_values, fs_open, signal_name_open, time_name_open = load_export(
            args.open_csv, args.time_column, args.signal_column, args.fs
        )
        closed_values, fs_closed, signal_name_closed, time_name_closed = load_export(
            args.closed_csv, args.time_column, args.signal_column, args.fs
        )
        if not np.isclose(fs_open, fs_closed, rtol=1e-3):
            raise ValueError(
                f"Las frecuencias difieren: {fs_open:.6g} y {fs_closed:.6g} Hz."
            )

        result, arrays = analyze_pair(
            convert_to_uv(open_values, args.unit),
            convert_to_uv(closed_values, args.unit),
            fs_hz=(fs_open + fs_closed) / 2.0,
            source="BIOPAC",
            channel=args.channel,
            duration_s=args.duration,
            open_start_s=args.open_start,
            closed_start_s=args.closed_start,
            notch_hz=args.notch,
            metadata={
                "open_file": args.open_csv.name,
                "closed_file": args.closed_csv.name,
                "input_unit": args.unit,
                "open_signal_column": signal_name_open,
                "closed_signal_column": signal_name_closed,
                "open_time_column": time_name_open,
                "closed_time_column": time_name_closed,
            },
        )
        paths = save_analysis(result, arrays, args.output_dir, "biopac")
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"R_alfa = {result['alpha_ratio_closed_open']:.4f}")
    for label, path in paths.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
