from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from eeg_core import analyze_pair, band_power, welch_psd  # noqa: E402


def test_band_power_detects_ten_hz() -> None:
    fs_hz = 160.0
    time_s = np.arange(int(10 * fs_hz)) / fs_hz
    values = 12.0 * np.sin(2 * np.pi * 10.0 * time_s)
    frequencies, psd = welch_psd(values, fs_hz)
    alpha = band_power(frequencies, psd, 8.0, 13.0)
    theta = band_power(frequencies, psd, 4.0, 8.0)
    assert alpha > 20 * theta


def test_alpha_ratio_increases_for_closed_condition() -> None:
    fs_hz = 160.0
    time_s = np.arange(int(12 * fs_hz)) / fs_hz
    rng = np.random.default_rng(42)
    open_uv = 4.0 * np.sin(2 * np.pi * 10.0 * time_s) + rng.normal(0, 2, time_s.size)
    closed_uv = 16.0 * np.sin(2 * np.pi * 10.0 * time_s) + rng.normal(0, 2, time_s.size)
    result, arrays = analyze_pair(
        open_uv,
        closed_uv,
        fs_hz=fs_hz,
        source="prueba",
        channel="O1",
        duration_s=10.0,
        open_start_s=1.0,
        closed_start_s=1.0,
    )
    assert result["alpha_ratio_closed_open"] > 8.0
    assert arrays["open_filtered_uv"].size == int(10 * fs_hz)
