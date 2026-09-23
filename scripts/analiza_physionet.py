#!/usr/bin/env python3
"""Descarga y analiza R01/R02 de EEGMMIDB mediante MNE."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from eeg_core import analyze_pair, save_analysis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analiza ojos abiertos/cerrados de EEGMMIDB."
    )
    parser.add_argument("--subject", type=int, default=1, help="Sujeto 1 a 109")
    parser.add_argument("--channel", default="O1")
    parser.add_argument("--start", type=float, default=5.0)
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--notch", type=float, default=None)
    parser.add_argument("--cache-dir", type=Path, default=Path("datos/physionet"))
    parser.add_argument(
        "--output-dir", type=Path, default=Path("resultados/physionet")
    )
    return parser.parse_args()


def _download(subject: int, cache_dir: Path) -> list[str]:
    from mne.datasets import eegbci

    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        paths = eegbci.load_data(
            subjects=subject,
            runs=[1, 2],
            path=str(cache_dir),
            update_path=False,
            verbose=False,
        )
    except TypeError:
        paths = eegbci.load_data(
            subject=subject,
            runs=[1, 2],
            path=str(cache_dir),
            update_path=False,
            verbose=False,
        )
    return [str(path) for path in paths]


def _load_edf(path: str, requested_channel: str) -> tuple[np.ndarray, float, str]:
    import mne
    from mne.datasets import eegbci

    raw = mne.io.read_raw_edf(path, preload=True, verbose=False)
    eegbci.standardize(raw)
    normalized = {name.upper().strip(". "): name for name in raw.ch_names}
    key = requested_channel.upper().strip(". ")
    if key not in normalized:
        available = ", ".join(raw.ch_names)
        raise ValueError(f"Canal {requested_channel} no disponible. Canales: {available}")
    channel = normalized[key]
    values_uv = raw.get_data(picks=[channel])[0] * 1e6
    return values_uv, float(raw.info["sfreq"]), channel


def main() -> int:
    args = parse_args()
    if not 1 <= args.subject <= 109:
        print("Error: el sujeto debe estar entre 1 y 109.", file=sys.stderr)
        return 2

    try:
        paths = _download(args.subject, args.cache_dir)
        if len(paths) != 2:
            raise RuntimeError("La descarga no devolvió R01 y R02.")
        open_uv, fs_open, channel_open = _load_edf(paths[0], args.channel)
        closed_uv, fs_closed, channel_closed = _load_edf(paths[1], args.channel)
        if not np.isclose(fs_open, fs_closed):
            raise RuntimeError("R01 y R02 tienen frecuencias de muestreo distintas.")
        if channel_open != channel_closed:
            raise RuntimeError("R01 y R02 resolvieron canales distintos.")

        result, arrays = analyze_pair(
            open_uv,
            closed_uv,
            fs_hz=fs_open,
            source=f"PhysioNet EEGMMIDB S{args.subject:03d}",
            channel=channel_open,
            duration_s=args.duration,
            open_start_s=args.start,
            closed_start_s=args.start,
            notch_hz=args.notch,
            metadata={
                "dataset": "EEG Motor Movement/Imagery Dataset v1.0.0",
                "doi": "10.13026/C28G6P",
                "eyes_open_run": "R01",
                "eyes_closed_run": "R02",
                "open_file": Path(paths[0]).name,
                "closed_file": Path(paths[1]).name,
            },
        )
        paths_saved = save_analysis(result, arrays, args.output_dir, "physionet")
    except (OSError, ValueError, RuntimeError, ImportError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"R_alfa = {result['alpha_ratio_closed_open']:.4f}")
    for label, path in paths_saved.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
