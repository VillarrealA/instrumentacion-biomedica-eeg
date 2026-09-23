"""Funciones comunes para la práctica docente de EEG."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal


ALPHA_BAND_HZ = (8.0, 13.0)
ANALYSIS_BAND_HZ = (0.5, 40.0)


def _finite_vector(values: np.ndarray) -> np.ndarray:
    data = np.asarray(values, dtype=float).reshape(-1)
    data = data[np.isfinite(data)]
    if data.size < 16:
        raise ValueError("La señal contiene muy pocas muestras válidas.")
    return data


def select_window(
    values: np.ndarray,
    fs_hz: float,
    start_s: float,
    duration_s: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Selecciona una ventana y devuelve tiempo local y señal."""
    data = _finite_vector(values)
    if fs_hz <= 0:
        raise ValueError("La frecuencia de muestreo debe ser positiva.")
    if start_s < 0 or duration_s <= 0:
        raise ValueError("El inicio debe ser no negativo y la duración positiva.")

    first = int(round(start_s * fs_hz))
    count = int(round(duration_s * fs_hz))
    last = first + count
    if first >= data.size or last > data.size:
        available = data.size / fs_hz
        raise ValueError(
            f"La ventana solicitada excede el registro de {available:.3f} s."
        )
    selected = data[first:last]
    time_s = np.arange(selected.size, dtype=float) / fs_hz
    return time_s, selected


def preprocess_eeg(
    values_uv: np.ndarray,
    fs_hz: float,
    band_hz: tuple[float, float] = ANALYSIS_BAND_HZ,
    notch_hz: float | None = None,
) -> np.ndarray:
    """Retira la media y aplica filtros de fase cero."""
    data = _finite_vector(values_uv)
    centered = signal.detrend(data, type="constant")

    low_hz, high_hz = band_hz
    nyquist = fs_hz / 2.0
    high_hz = min(high_hz, nyquist * 0.95)
    if not 0 < low_hz < high_hz < nyquist:
        raise ValueError("La banda de análisis no es compatible con el muestreo.")

    sos = signal.butter(
        4,
        [low_hz, high_hz],
        btype="bandpass",
        fs=fs_hz,
        output="sos",
    )
    filtered = signal.sosfiltfilt(sos, centered)

    if notch_hz is not None and 0 < notch_hz < nyquist:
        b_notch, a_notch = signal.iirnotch(notch_hz, Q=30.0, fs=fs_hz)
        filtered = signal.filtfilt(b_notch, a_notch, filtered)
    return filtered


def welch_psd(
    values_uv: np.ndarray,
    fs_hz: float,
    segment_s: float = 2.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Estima la densidad espectral de potencia con Welch."""
    data = _finite_vector(values_uv)
    nperseg = min(data.size, max(32, int(round(segment_s * fs_hz))))
    noverlap = nperseg // 2
    frequencies, psd = signal.welch(
        data,
        fs=fs_hz,
        window="hann",
        nperseg=nperseg,
        noverlap=noverlap,
        detrend="constant",
        scaling="density",
    )
    return frequencies, psd


def band_power(
    frequencies_hz: np.ndarray,
    psd_uv2_hz: np.ndarray,
    low_hz: float,
    high_hz: float,
) -> float:
    """Integra la PSD dentro de una banda."""
    mask = (frequencies_hz >= low_hz) & (frequencies_hz <= high_hz)
    if np.count_nonzero(mask) < 2:
        raise ValueError("No hay resolución frecuencial suficiente para la banda.")
    integral = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    return float(integral(psd_uv2_hz[mask], frequencies_hz[mask]))


def condition_metrics(
    values_uv: np.ndarray,
    fs_hz: float,
    notch_hz: float | None = None,
) -> tuple[dict[str, float], np.ndarray, np.ndarray, np.ndarray]:
    """Calcula métricas y devuelve señal filtrada y PSD."""
    filtered = preprocess_eeg(values_uv, fs_hz, notch_hz=notch_hz)
    frequencies, psd = welch_psd(filtered, fs_hz)
    alpha_power = band_power(frequencies, psd, *ALPHA_BAND_HZ)
    total_power = band_power(frequencies, psd, *ANALYSIS_BAND_HZ)
    relative_alpha = alpha_power / total_power if total_power > 0 else float("nan")
    metrics = {
        "mean_uv": float(np.mean(filtered)),
        "std_uv": float(np.std(filtered, ddof=0)),
        "peak_to_peak_uv": float(np.ptp(filtered)),
        "alpha_power_uv2": alpha_power,
        "total_power_0_5_40_uv2": total_power,
        "relative_alpha": float(relative_alpha),
    }
    return metrics, filtered, frequencies, psd


def analyze_pair(
    open_uv: np.ndarray,
    closed_uv: np.ndarray,
    fs_hz: float,
    source: str,
    channel: str,
    duration_s: float,
    open_start_s: float,
    closed_start_s: float,
    notch_hz: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    """Analiza ojos abiertos/cerrados con parámetros comunes."""
    time_open, open_window = select_window(open_uv, fs_hz, open_start_s, duration_s)
    time_closed, closed_window = select_window(
        closed_uv, fs_hz, closed_start_s, duration_s
    )
    open_metrics, open_filtered, frequencies, open_psd = condition_metrics(
        open_window, fs_hz, notch_hz
    )
    closed_metrics, closed_filtered, frequencies_closed, closed_psd = (
        condition_metrics(closed_window, fs_hz, notch_hz)
    )
    if not np.allclose(frequencies, frequencies_closed):
        raise RuntimeError("Las dos condiciones produjeron ejes de frecuencia distintos.")

    alpha_open = open_metrics["alpha_power_uv2"]
    alpha_closed = closed_metrics["alpha_power_uv2"]
    ratio = alpha_closed / alpha_open if alpha_open > 0 else float("nan")

    result: dict[str, Any] = {
        "source": source,
        "channel": channel,
        "fs_hz": float(fs_hz),
        "signal_unit": "uV",
        "window_duration_s": float(duration_s),
        "eyes_open_start_s": float(open_start_s),
        "eyes_closed_start_s": float(closed_start_s),
        "analysis_band_hz": list(ANALYSIS_BAND_HZ),
        "alpha_band_hz": list(ALPHA_BAND_HZ),
        "notch_hz": notch_hz,
        "welch_segment_s": 2.0,
        "eyes_open": open_metrics,
        "eyes_closed": closed_metrics,
        "alpha_ratio_closed_open": float(ratio),
        "metadata": metadata or {},
    }
    arrays = {
        "time_open_s": time_open,
        "time_closed_s": time_closed,
        "open_filtered_uv": open_filtered,
        "closed_filtered_uv": closed_filtered,
        "frequency_hz": frequencies,
        "open_psd_uv2_hz": open_psd,
        "closed_psd_uv2_hz": closed_psd,
    }
    return result, arrays


def save_analysis(
    result: dict[str, Any],
    arrays: dict[str, np.ndarray],
    output_dir: str | Path,
    prefix: str,
) -> dict[str, Path]:
    """Guarda métricas, resumen, figura y serie procesada."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    metrics_path = destination / f"{prefix}_metricas.json"
    metrics_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    summary = pd.DataFrame(
        [
            {
                "source": result["source"],
                "channel": result["channel"],
                "fs_hz": result["fs_hz"],
                "duration_s": result["window_duration_s"],
                "alpha_open_uv2": result["eyes_open"]["alpha_power_uv2"],
                "alpha_closed_uv2": result["eyes_closed"]["alpha_power_uv2"],
                "relative_alpha_open": result["eyes_open"]["relative_alpha"],
                "relative_alpha_closed": result["eyes_closed"]["relative_alpha"],
                "alpha_ratio_closed_open": result["alpha_ratio_closed_open"],
            }
        ]
    )
    summary_path = destination / f"{prefix}_resumen.csv"
    summary.to_csv(summary_path, index=False)

    processed = pd.DataFrame(
        {
            "time_s": arrays["time_open_s"],
            "eyes_open_uv": arrays["open_filtered_uv"],
            "eyes_closed_uv": arrays["closed_filtered_uv"],
        }
    )
    processed_path = destination / f"{prefix}_procesada.csv"
    processed.to_csv(processed_path, index=False)

    figure_path = destination / f"{prefix}_analisis.png"
    _save_figure(result, arrays, figure_path)
    return {
        "metrics": metrics_path,
        "summary": summary_path,
        "processed": processed_path,
        "figure": figure_path,
    }


def _save_figure(
    result: dict[str, Any],
    arrays: dict[str, np.ndarray],
    path: Path,
) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), constrained_layout=True)
    axes[0].plot(
        arrays["time_open_s"], arrays["open_filtered_uv"], label="Ojos abiertos", lw=0.9
    )
    axes[0].plot(
        arrays["time_closed_s"],
        arrays["closed_filtered_uv"],
        label="Ojos cerrados",
        lw=0.9,
        alpha=0.8,
    )
    axes[0].set_xlabel("Tiempo dentro de la ventana (s)")
    axes[0].set_ylabel("EEG filtrado (µV)")
    axes[0].set_title(f"{result['source']} — canal {result['channel']}")
    axes[0].grid(alpha=0.25)
    axes[0].legend()

    mask = (arrays["frequency_hz"] >= 0.5) & (arrays["frequency_hz"] <= 40.0)
    axes[1].semilogy(
        arrays["frequency_hz"][mask],
        arrays["open_psd_uv2_hz"][mask],
        label="Ojos abiertos",
    )
    axes[1].semilogy(
        arrays["frequency_hz"][mask],
        arrays["closed_psd_uv2_hz"][mask],
        label="Ojos cerrados",
    )
    axes[1].axvspan(8, 13, color="tab:orange", alpha=0.18, label="Banda alfa")
    axes[1].set_xlabel("Frecuencia (Hz)")
    axes[1].set_ylabel("PSD (µV²/Hz)")
    axes[1].grid(alpha=0.25)
    axes[1].legend()
    ratio = result["alpha_ratio_closed_open"]
    axes[1].set_title(f"R_alfa = {ratio:.3f}")
    fig.savefig(path, dpi=180)
    plt.close(fig)


def infer_sampling_rate(time_s: np.ndarray) -> float:
    """Estima fs mediante la mediana de las diferencias temporales."""
    time_s = _finite_vector(time_s)
    differences = np.diff(time_s)
    differences = differences[differences > 0]
    if differences.size < 2:
        raise ValueError("No fue posible inferir la frecuencia de muestreo.")
    return float(1.0 / np.median(differences))


def convert_to_uv(values: np.ndarray, unit: str) -> np.ndarray:
    scales = {"v": 1e6, "mv": 1e3, "uv": 1.0, "µv": 1.0}
    key = unit.strip().lower()
    if key not in scales:
        raise ValueError("Unidad no reconocida. Use V, mV o uV.")
    return np.asarray(values, dtype=float) * scales[key]
