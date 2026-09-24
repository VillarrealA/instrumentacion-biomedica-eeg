#!/usr/bin/env python3
"""Forma épocas y promedia registros Backyard Brains en WAV o CSV."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal
from scipy.io import wavfile


UNIT_TO_UV = {"V": 1e6, "mV": 1e3, "uV": 1.0, "µV": 1.0}


@dataclass
class Recording:
    values: np.ndarray
    fs_hz: float
    event_indices: np.ndarray
    event_names: list[str]
    unit_label: str
    input_file: Path
    events_file: Path | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analiza un WAV de Spike Recorder con su archivo -events.txt o "
            "un CSV con señal y marcas. No asigna significado clínico a las "
            "deflexiones observadas."
        )
    )
    parser.add_argument("input_file", type=Path, help="Registro .wav o .csv.")
    parser.add_argument(
        "--events",
        type=Path,
        default=None,
        help=(
            "Archivo de eventos de Spike Recorder. Si se omite, se busca "
            "<nombre>-events.txt junto al WAV."
        ),
    )
    parser.add_argument(
        "--event-name",
        action="append",
        default=None,
        help=(
            "Nombre de evento que se analizará. Puede repetirse. Si se omite, "
            "se utilizan todos los eventos que no comienzan con '_'."
        ),
    )
    parser.add_argument(
        "--channel",
        type=int,
        default=0,
        help="Canal del WAV, numerado desde 0 (predeterminado: 0).",
    )
    parser.add_argument("--time-column", default="time_s")
    parser.add_argument("--signal-column", default="signal_uv")
    parser.add_argument("--event-column", default="event")
    parser.add_argument(
        "--unit",
        choices=sorted(UNIT_TO_UV),
        default="uV",
        help="Unidad de la señal CSV; no se aplica a archivos WAV.",
    )
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
        help=(
            "Rechaza épocas cuyo pico a pico exceda este valor. La unidad es "
            "uV para CSV convertido y u.a. para WAV."
        ),
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("resultados/backyard")
    )
    return parser.parse_args()


def _sampling_rate(
    frame: pd.DataFrame, column: str, supplied: float | None
) -> float:
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


def _event_indices_from_column(values: np.ndarray) -> np.ndarray:
    markers = pd.to_numeric(pd.Series(values), errors="coerce").fillna(0).to_numpy()
    active = markers != 0
    starts = active & ~np.r_[False, active[:-1]]
    return np.flatnonzero(starts)


def _load_csv(args: argparse.Namespace) -> Recording:
    frame = pd.read_csv(args.input_file)
    for column in (args.signal_column, args.event_column):
        if column not in frame:
            raise ValueError(f"Falta la columna '{column}'.")

    fs_hz = _sampling_rate(frame, args.time_column, args.fs)
    values = pd.to_numeric(
        frame[args.signal_column], errors="coerce"
    ).to_numpy(dtype=float)
    if not np.all(np.isfinite(values)):
        raise ValueError("La señal contiene valores vacíos o no numéricos.")
    values_uv = values * UNIT_TO_UV[args.unit]
    event_indices = _event_indices_from_column(
        frame[args.event_column].to_numpy()
    )
    return Recording(
        values=values_uv,
        fs_hz=fs_hz,
        event_indices=event_indices,
        event_names=["evento CSV"] * int(event_indices.size),
        unit_label="uV",
        input_file=args.input_file,
    )


def _infer_events_path(wav_path: Path) -> Path:
    return wav_path.with_name(f"{wav_path.stem}-events.txt")


def _read_spike_recorder_events(
    path: Path, selected_names: list[str] | None
) -> tuple[np.ndarray, list[str]]:
    if not path.exists():
        raise ValueError(
            f"No se encontró el archivo de eventos '{path}'. Use --events "
            "para indicar su ubicación."
        )

    selected = set(selected_names) if selected_names else None
    timestamps: list[float] = []
    names: list[str] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",", maxsplit=1)
            if len(parts) != 2:
                raise ValueError(
                    f"Formato no reconocido en {path.name}, línea {line_number}: "
                    "se esperaba nombre,tiempo_en_segundos."
                )
            name, timestamp_text = (part.strip() for part in parts)
            if not name or name.startswith("_"):
                continue
            if selected is not None and name not in selected:
                continue
            try:
                timestamp = float(timestamp_text)
            except ValueError as exc:
                raise ValueError(
                    f"Tiempo inválido en {path.name}, línea {line_number}: "
                    f"'{timestamp_text}'."
                ) from exc
            if timestamp < 0:
                raise ValueError(
                    f"Tiempo negativo en {path.name}, línea {line_number}."
                )
            names.append(name)
            timestamps.append(timestamp)

    if selected is not None:
        missing = selected.difference(names)
        if missing:
            available_note = "No aparecen en el archivo después del filtrado."
            raise ValueError(
                f"No se encontraron los eventos solicitados: {sorted(missing)}. "
                f"{available_note}"
            )
    if not timestamps:
        raise ValueError("No se encontraron eventos utilizables en el archivo.")
    return np.asarray(timestamps, dtype=float), names


def _load_wav(args: argparse.Namespace) -> Recording:
    fs_hz, values = wavfile.read(args.input_file)
    if fs_hz <= 0:
        raise ValueError("La frecuencia de muestreo del WAV no es válida.")

    if values.ndim == 1:
        if args.channel != 0:
            raise ValueError("El WAV es mono; el único canal disponible es 0.")
        selected_values = values
    elif values.ndim == 2:
        if not 0 <= args.channel < values.shape[1]:
            raise ValueError(
                f"Canal {args.channel} fuera de rango; el WAV contiene "
                f"{values.shape[1]} canales."
            )
        selected_values = values[:, args.channel]
    else:
        raise ValueError("El WAV tiene una estructura de canales no compatible.")

    selected_values = np.asarray(selected_values, dtype=float)
    if not np.all(np.isfinite(selected_values)):
        raise ValueError("El WAV contiene valores no finitos.")

    events_path = args.events or _infer_events_path(args.input_file)
    timestamps, event_names = _read_spike_recorder_events(
        events_path, args.event_name
    )
    event_indices = np.rint(timestamps * float(fs_hz)).astype(int)
    valid = event_indices < selected_values.size
    if not np.all(valid):
        invalid_count = int(np.count_nonzero(~valid))
        raise ValueError(
            f"{invalid_count} eventos quedan fuera de la duración del WAV. "
            "Revise que el archivo -events.txt corresponda a este registro."
        )

    return Recording(
        values=selected_values,
        fs_hz=float(fs_hz),
        event_indices=event_indices,
        event_names=event_names,
        unit_label="u.a.",
        input_file=args.input_file,
        events_file=events_path,
    )


def _load_recording(args: argparse.Namespace) -> Recording:
    suffix = args.input_file.suffix.lower()
    if suffix == ".csv":
        if args.events is not None:
            raise ValueError("--events sólo se utiliza con archivos WAV.")
        if args.event_name is not None:
            raise ValueError("--event-name sólo se utiliza con archivos WAV.")
        return _load_csv(args)
    if suffix in {".wav", ".wave"}:
        if args.fs is not None:
            raise ValueError("El WAV ya contiene su frecuencia de muestreo; quite --fs.")
        return _load_wav(args)
    raise ValueError("El archivo de entrada debe tener extensión .wav o .csv.")


def _filter(
    values: np.ndarray,
    fs_hz: float,
    low: float,
    high: float,
    notch: float | None,
) -> np.ndarray:
    nyquist = fs_hz / 2.0
    high = min(high, 0.95 * nyquist)
    if not 0 < low < high < nyquist:
        raise ValueError("La banda no es compatible con la frecuencia de muestreo.")
    centered = signal.detrend(values, type="constant")
    sos = signal.butter(
        4, [low, high], btype="bandpass", fs=fs_hz, output="sos"
    )
    filtered = signal.sosfiltfilt(sos, centered)
    if notch is not None:
        if not 0 < notch < nyquist:
            raise ValueError("La frecuencia notch no es compatible con el muestreo.")
        b, a = signal.iirnotch(notch, Q=30.0, fs=fs_hz)
        filtered = signal.filtfilt(b, a, filtered)
    return filtered


def _column_suffix(unit_label: str) -> str:
    return "uv" if unit_label == "uV" else "au"


def main() -> int:
    args = parse_args()
    try:
        recording = _load_recording(args)
        filtered = _filter(
            recording.values,
            recording.fs_hz,
            args.low,
            args.high,
            args.notch,
        )
        event_indices = recording.event_indices
        if event_indices.size == 0:
            raise ValueError("No se encontraron marcas de evento.")

        n_pre = int(round(args.pre * recording.fs_hz))
        n_post = int(round(args.post * recording.fs_hz))
        if n_pre < 1 or n_post < 1:
            raise ValueError("Las ventanas pre y post deben contener muestras.")
        epoch_time_s = (
            np.arange(-n_pre, n_post + 1, dtype=float) / recording.fs_hz
        )

        accepted: list[np.ndarray] = []
        rejected_bounds = 0
        rejected_amplitude = 0
        for index in event_indices:
            first, last = index - n_pre, index + n_post + 1
            if first < 0 or last > filtered.size:
                rejected_bounds += 1
                continue
            epoch = filtered[first:last].copy()
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
            "input_file": recording.input_file.name,
            "events_file": (
                recording.events_file.name if recording.events_file else None
            ),
            "fs_hz": recording.fs_hz,
            "signal_unit": recording.unit_label,
            "wav_channel": args.channel if recording.events_file else None,
            "event_names_used": sorted(set(recording.event_names)),
            "bandpass_hz": [args.low, args.high],
            "notch_hz": args.notch,
            "epoch_window_s": [-args.pre, args.post],
            "baseline_window_s": [-args.pre, 0.0],
            "events_detected": int(event_indices.size),
            "epochs_accepted": int(epochs.shape[0]),
            "epochs_rejected_bounds": int(rejected_bounds),
            "epochs_rejected_amplitude": int(rejected_amplitude),
            "descriptive_peak_latency_s": float(post_time[peak_index]),
            "descriptive_peak_amplitude": float(post_average[peak_index]),
            "interpretation_warning": (
                "La latencia y amplitud son descriptivas; requieren revisar "
                "sincronía, repetibilidad, artefactos y calibración."
            ),
        }
        metrics_path = destination / "backyard_metricas.json"
        metrics_path.write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        suffix = _column_suffix(recording.unit_label)
        epoch_frame = pd.DataFrame({"time_s": epoch_time_s})
        for number, epoch in enumerate(epochs, start=1):
            epoch_frame[f"trial_{number:03d}_{suffix}"] = epoch
        epoch_frame[f"average_{suffix}"] = average
        epoch_frame[f"sem_{suffix}"] = sem
        epochs_path = destination / "backyard_epocas.csv"
        epoch_frame.to_csv(epochs_path, index=False)

        figure, axes = plt.subplots(
            2, 1, figsize=(10, 7), constrained_layout=True
        )
        time_continuous = (
            np.arange(filtered.size, dtype=float) / recording.fs_hz
        )
        axes[0].plot(time_continuous, filtered, lw=0.7, color="#00445A")
        for index in event_indices:
            axes[0].axvline(
                index / recording.fs_hz,
                color="#C90000",
                alpha=0.35,
                lw=0.7,
            )
        axes[0].set(
            title="Registro continuo y eventos",
            xlabel="Tiempo (s)",
            ylabel=f"Señal ({recording.unit_label})",
        )
        axes[0].grid(alpha=0.2)

        for epoch in epochs:
            axes[1].plot(
                epoch_time_s, epoch, color="0.65", alpha=0.35, lw=0.6
            )
        axes[1].fill_between(
            epoch_time_s,
            average - sem,
            average + sem,
            color="#00445A",
            alpha=0.18,
            label="±1 error estándar",
        )
        axes[1].plot(
            epoch_time_s,
            average,
            color="#00445A",
            lw=2.0,
            label="Promedio",
        )
        axes[1].axvline(0, color="#C90000", lw=1.0, label="Evento")
        axes[1].set(
            title=f"Ensayos aceptados y promedio (N={epochs.shape[0]})",
            xlabel="Tiempo respecto al evento (s)",
            ylabel=f"Señal ({recording.unit_label})",
        )
        axes[1].grid(alpha=0.2)
        axes[1].legend()
        figure_path = destination / "backyard_promedio.png"
        figure.savefig(figure_path, dpi=180)
        plt.close(figure)
    except (
        OSError,
        ValueError,
        KeyError,
        IndexError,
        pd.errors.ParserError,
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"métricas: {metrics_path}")
    print(f"épocas: {epochs_path}")
    print(f"figura: {figure_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
