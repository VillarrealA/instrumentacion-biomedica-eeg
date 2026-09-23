#!/usr/bin/env python3
"""Forma épocas y promedia respuestas Backyard Brains exportadas a CSV."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal


UNIT_TO_UV = {"V": 1e6, "mV": 1e3, "uV": 1.0, "µV": 1.0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analiza una señal con marcas de evento; no asigna significado "
            "clínico a las deflexiones observadas."
        )
    )
    parser.add_argument("csv", type=Path)
    parser.add_argument("--time-column", default="time_s")
    parser.add_argument("--signal-column", default="signal_uv")
    parser.add_argument("--event-column", default="event")
    parser.add_argument("--unit", choices=sorted(UNIT_TO_UV), default="uV")
    parser.add_argument("--fs", type=float, default=None)
    parser.add_argument("--pre", type=float, default=0.2)
    parser.add_argument("--post", type=float, default=0.6)
    parser.add_argument("--low", type=float, default=0.5)
    parser.add_argument("--high", type=float, default=30.0)
    parser.add_argument("--notch", type=float, default=None)
    parser.add_argument(
        "--reject-peak-to-peak",
        type=float,
        default=None,
        help="Rechaza épocas cuyo pico a pico exceda este valor en uV.",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("resultados/backyard")
    )
    return parser.parse_args()


def _sampling_rate(frame: pd.DataFrame, column: str, supplied: float | None) -> float:
    if supplied is not None:
        if supplied <= 0:
            raise ValueError("--fs debe ser positivo.")
        return float(supplied)
    if column not in frame:
        raise ValueError("Falta la columna de tiempo; proporcione --fs.")
    time_s = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
    dt = np.diff(time_s)
    dt = dt[np.isfinite(dt) & (dt > 0)]
    if dt.size == 0:
        raise ValueError("No puede estimarse la frecuencia de muestreo.")
    return float(1.0 / np.median(dt))


def _filter(values_uv: np.ndarray, fs_hz: float, low: float, high: float, notch: float | None) -> np.ndarray:
    nyquist = fs_hz / 2.0
    high = min(high, 0.95 * nyquist)
    if not 0 < low < high < nyquist:
        raise ValueError("La banda no es compatible con la frecuencia de muestreo.")
    centered = signal.detrend(values_uv, type="constant")
    sos = signal.butter(4, [low, high], btype="bandpass", fs=fs_hz, output="sos")
    filtered = signal.sosfiltfilt(sos, centered)
    if notch is not None:
        if not 0 < notch < nyquist:
            raise ValueError("La frecuencia notch no es compatible con el muestreo.")
        b, a = signal.iirnotch(notch, Q=30.0, fs=fs_hz)
        filtered = signal.filtfilt(b, a, filtered)
    return filtered


def _event_indices(values: np.ndarray) -> np.ndarray:
    markers = pd.to_numeric(pd.Series(values), errors="coerce").fillna(0).to_numpy()
    active = markers != 0
    starts = active & ~np.r_[False, active[:-1]]
    return np.flatnonzero(starts)


def main() -> int:
    args = parse_args()
    try:
        frame = pd.read_csv(args.csv)
        for column in (args.signal_column, args.event_column):
            if column not in frame:
                raise ValueError(f"Falta la columna '{column}'.")

        fs_hz = _sampling_rate(frame, args.time_column, args.fs)
        values = pd.to_numeric(frame[args.signal_column], errors="coerce").to_numpy(dtype=float)
        if not np.all(np.isfinite(values)):
            raise ValueError("La señal contiene valores vacíos o no numéricos.")
        values_uv = values * UNIT_TO_UV[args.unit]
        filtered_uv = _filter(values_uv, fs_hz, args.low, args.high, args.notch)
        event_indices = _event_indices(frame[args.event_column].to_numpy())
        if event_indices.size == 0:
            raise ValueError("No se encontraron marcas de evento distintas de cero.")

        n_pre = int(round(args.pre * fs_hz))
        n_post = int(round(args.post * fs_hz))
        if n_pre < 1 or n_post < 1:
            raise ValueError("Las ventanas pre y post deben contener muestras.")
        epoch_time_s = np.arange(-n_pre, n_post + 1, dtype=float) / fs_hz

        accepted: list[np.ndarray] = []
        rejected_bounds = 0
        rejected_amplitude = 0
        for index in event_indices:
            first, last = index - n_pre, index + n_post + 1
            if first < 0 or last > filtered_uv.size:
                rejected_bounds += 1
                continue
            epoch = filtered_uv[first:last].copy()
            epoch -= float(np.mean(epoch[:n_pre]))
            if (
                args.reject_peak_to_peak is not None
                and float(np.ptp(epoch)) > args.reject_peak_to_peak
            ):
                rejected_amplitude += 1
                continue
            accepted.append(epoch)

        if not accepted:
            raise ValueError("Ninguna época cumplió los criterios de selección.")
        epochs = np.vstack(accepted)
        average = np.mean(epochs, axis=0)
        sem = (
            np.std(epochs, axis=0, ddof=1) / np.sqrt(epochs.shape[0])
            if epochs.shape[0] > 1
            else np.zeros_like(average)
        )
        post_mask = epoch_time_s >= 0
        post_average = average[post_mask]
        post_time = epoch_time_s[post_mask]
        peak_index = int(np.argmax(np.abs(post_average)))

        destination = args.output_dir
        destination.mkdir(parents=True, exist_ok=True)
        metrics = {
            "source": "Backyard Brains",
            "input_file": args.csv.name,
            "fs_hz": fs_hz,
            "signal_unit": "uV",
            "bandpass_hz": [args.low, args.high],
            "notch_hz": args.notch,
            "epoch_window_s": [-args.pre, args.post],
            "baseline_window_s": [-args.pre, 0.0],
            "events_detected": int(event_indices.size),
            "epochs_accepted": int(epochs.shape[0]),
            "epochs_rejected_bounds": int(rejected_bounds),
            "epochs_rejected_amplitude": int(rejected_amplitude),
            "descriptive_peak_latency_s": float(post_time[peak_index]),
            "descriptive_peak_amplitude_uv": float(post_average[peak_index]),
            "interpretation_warning": (
                "La latencia y amplitud son descriptivas; requieren revisar "
                "sincronía, repetibilidad y artefactos."
            ),
        }
        metrics_path = destination / "backyard_metricas.json"
        metrics_path.write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        epoch_frame = pd.DataFrame({"time_s": epoch_time_s})
        for number, epoch in enumerate(epochs, start=1):
            epoch_frame[f"trial_{number:03d}_uv"] = epoch
        epoch_frame["average_uv"] = average
        epoch_frame["sem_uv"] = sem
        epochs_path = destination / "backyard_epocas.csv"
        epoch_frame.to_csv(epochs_path, index=False)

        figure, axes = plt.subplots(2, 1, figsize=(10, 7), constrained_layout=True)
        time_continuous = np.arange(filtered_uv.size, dtype=float) / fs_hz
        axes[0].plot(time_continuous, filtered_uv, lw=0.7, color="#00445A")
        for index in event_indices:
            axes[0].axvline(index / fs_hz, color="#C90000", alpha=0.35, lw=0.7)
        axes[0].set(title="Registro continuo y eventos", xlabel="Tiempo (s)", ylabel="Señal (uV)")
        axes[0].grid(alpha=0.2)

        for epoch in epochs:
            axes[1].plot(epoch_time_s, epoch, color="0.65", alpha=0.35, lw=0.6)
        axes[1].fill_between(epoch_time_s, average - sem, average + sem, color="#00445A", alpha=0.18, label="±1 error estándar")
        axes[1].plot(epoch_time_s, average, color="#00445A", lw=2.0, label="Promedio")
        axes[1].axvline(0, color="#C90000", lw=1.0, label="Evento")
        axes[1].set(title=f"Ensayos aceptados y promedio (N={epochs.shape[0]})", xlabel="Tiempo respecto al evento (s)", ylabel="Señal (uV)")
        axes[1].grid(alpha=0.2)
        axes[1].legend()
        figure_path = destination / "backyard_promedio.png"
        figure.savefig(figure_path, dpi=180)
        plt.close(figure)
    except (OSError, ValueError, KeyError, pd.errors.ParserError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"métricas: {metrics_path}")
    print(f"épocas: {epochs_path}")
    print(f"figura: {figure_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
