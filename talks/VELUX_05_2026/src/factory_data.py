"""
Synthetic factory time-series for the VELUX IIoT talk demo.

The goal is shape-realism, not accuracy. The generated data should look
plausible to engineers who run a real factory, with:

  - PackML-style state changes
  - Shift rhythm (06:00 / 14:00 / 22:00 handovers, brief idle at each)
  - Plausible correlations (current draw rises with throughput, temperature
    trails current through a low-pass response, vibration rises when running)
  - Embedded scenarios: bearing wear + spike, brief stuck-at, planned maintenance

Output is written as a long-format parquet (one row per measurement) that
mimics how a Kafka topic would look:

    timestamp, factory_id, line_id, machine_id, signal, value, value_str

Plus a separate events parquet (alarms, MES messages, operator notes).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_RESOLUTION_SECONDS = 10
DEFAULT_DAYS = 2


@dataclass(frozen=True)
class Machine:
    line: str
    name: str
    kind: str  # one of: folding, cutting, assembly, bonding, quality
    target_rate: float  # pieces per minute when in shift


# Skjern factory layout — three lines, six machines.
# Names are deliberately VELUX-shaped (frame folding, glass cutting, sash
# assembly, edge bonding, quality station).
MACHINES: list[Machine] = [
    Machine("line_1", "folder_01", "folding", 14.0),
    Machine("line_1", "sash_assembler", "assembly", 6.0),
    Machine("line_2", "folder_02", "folding", 14.0),
    Machine("line_2", "glass_cutter", "cutting", 10.0),
    Machine("line_3", "edge_bonder", "bonding", 11.0),
    Machine("line_3", "quality_station", "quality", 20.0),
]


# ---------------------------------------------------------------------------
# Baseline signal generators
# ---------------------------------------------------------------------------

def _shift_factor(timestamps: pd.DatetimeIndex) -> np.ndarray:
    """1.0 during a shift, 0.0 in a 30-min handover window at 06/14/22."""
    hour = timestamps.hour + timestamps.minute / 60
    factor = np.ones(len(timestamps), dtype=float)
    for handover in (6, 14, 22):
        near = (hour > handover - 0.25) & (hour < handover + 0.25)
        factor[near] = 0.0
    return factor


def baseline_throughput(
    timestamps: pd.DatetimeIndex,
    target_rate: float,
    noise: float = 1.2,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Pieces per minute. Goes to zero during shift handovers."""
    rng = rng or np.random.default_rng()
    shift = _shift_factor(timestamps)
    base = target_rate * shift
    base = base + rng.normal(0, noise, size=len(timestamps)) * shift
    return np.clip(base, 0.0, None)


def baseline_current(
    throughput: np.ndarray,
    idle_current: float = 1.5,
    slope: float = 0.4,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Motor current correlates with throughput, with a small idle draw."""
    rng = rng or np.random.default_rng()
    return idle_current + slope * throughput + rng.normal(0, 0.25, size=len(throughput))


def baseline_temperature(
    current: np.ndarray,
    resolution_seconds: int,
    start_temp: float = 25.0,
    time_constant_s: float = 3600.0,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Temperature trails motor load via a first-order low-pass response."""
    rng = rng or np.random.default_rng()
    temp = np.empty_like(current)
    temp[0] = start_temp
    alpha = 1 - np.exp(-resolution_seconds / time_constant_s)
    for i in range(1, len(current)):
        target = 25.0 + 8.0 * (current[i] / 6.0)  # warms under sustained load
        temp[i] = temp[i - 1] + alpha * (target - temp[i - 1])
    return temp + rng.normal(0, 0.2, size=len(temp))


def baseline_vibration_rms(
    throughput: np.ndarray,
    idle_level: float = 0.30,
    run_level: float = 2.50,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Vibration RMS in mm/s. Low when idle, ~run_level when running."""
    rng = rng or np.random.default_rng()
    running = throughput > 1.0
    v = np.where(running, run_level, idle_level)
    return v + rng.normal(0, 0.15, size=len(throughput))


# ---------------------------------------------------------------------------
# Scenario injection
# ---------------------------------------------------------------------------

def inject_bearing_wear(
    series: np.ndarray,
    timestamps: pd.DatetimeIndex,
    start: pd.Timestamp,
    end: pd.Timestamp,
    peak_multiplier: float = 2.2,
) -> np.ndarray:
    """Linear ramp from 1x at start to peak_multiplier at end."""
    series = series.copy()
    mask = (timestamps >= start) & (timestamps <= end)
    if mask.any():
        idx = np.where(mask)[0]
        ramp = np.linspace(0.0, peak_multiplier - 1.0, len(idx))
        series[idx] = series[idx] * (1.0 + ramp)
    # After the ramp, hold at peak (wear doesn't get better).
    after = timestamps > end
    if after.any():
        series[after] = series[after] * peak_multiplier
    return series


def inject_anomaly_spike(
    series: np.ndarray,
    timestamps: pd.DatetimeIndex,
    when: pd.Timestamp,
    duration: timedelta = timedelta(minutes=3),
    multiplier: float = 3.5,
) -> np.ndarray:
    series = series.copy()
    mask = (timestamps >= when) & (timestamps <= when + duration)
    series[mask] = series[mask] * multiplier
    return series


def inject_stuck_at(
    throughput: np.ndarray,
    current: np.ndarray,
    timestamps: pd.DatetimeIndex,
    when: pd.Timestamp,
    duration: timedelta = timedelta(minutes=8),
    stalled_current_a: float = 5.5,
) -> tuple[np.ndarray, np.ndarray]:
    """Throughput drops to zero, current pegs high (motor stalled)."""
    throughput = throughput.copy()
    current = current.copy()
    mask = (timestamps >= when) & (timestamps <= when + duration)
    throughput[mask] = 0.0
    current[mask] = stalled_current_a
    return throughput, current


def inject_planned_maintenance(
    throughput: np.ndarray,
    current: np.ndarray,
    vibration: np.ndarray,
    timestamps: pd.DatetimeIndex,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    throughput = throughput.copy()
    current = current.copy()
    vibration = vibration.copy()
    mask = (timestamps >= start) & (timestamps <= end)
    throughput[mask] = 0.0
    current[mask] = 0.2
    vibration[mask] = 0.05
    return throughput, current, vibration


# ---------------------------------------------------------------------------
# PackML state derivation
# ---------------------------------------------------------------------------

def derive_packml_state(throughput: np.ndarray, current: np.ndarray) -> np.ndarray:
    """Very simple state derivation for demo purposes."""
    state = np.where(
        throughput > 1.0,
        "Execute",
        np.where(current < 0.5, "Stopped", "Idle"),
    )
    # Anything with current > 5 A AND throughput == 0 looks like a fault.
    fault = (throughput == 0.0) & (current > 5.0)
    state = np.where(fault, "Aborted", state)
    return state


# ---------------------------------------------------------------------------
# Top-level: build the dataset
# ---------------------------------------------------------------------------

def build_dataset(
    start: pd.Timestamp,
    days: int = DEFAULT_DAYS,
    resolution_seconds: int = DEFAULT_RESOLUTION_SECONDS,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (measurements_long_df, events_df)."""
    rng = np.random.default_rng(seed)

    n_samples = days * 24 * 3600 // resolution_seconds
    timestamps = pd.date_range(start, periods=n_samples, freq=f"{resolution_seconds}s")

    records: list[pd.DataFrame] = []

    for m in MACHINES:
        thr = baseline_throughput(timestamps, target_rate=m.target_rate, rng=rng)
        cur = baseline_current(thr, rng=rng)
        temp = baseline_temperature(cur, resolution_seconds=resolution_seconds, rng=rng)
        vib = baseline_vibration_rms(thr, rng=rng)

        # Per-machine scenarios — keep these readable; the talk explains them.
        if m.name == "folder_02":
            # Bearing wear: ramps from day-1 18:00 to day-2 06:00, then holds.
            # Spike anomaly on day-2 at 09:30.
            vib = inject_bearing_wear(
                vib,
                timestamps,
                start + timedelta(hours=18),
                start + timedelta(days=1, hours=6),
                peak_multiplier=2.2,
            )
            vib = inject_anomaly_spike(
                vib,
                timestamps,
                start + timedelta(days=1, hours=9, minutes=30),
                duration=timedelta(minutes=3),
                multiplier=3.5,
            )

        if m.name == "glass_cutter":
            # Brief stuck-at event on day 1 at 10:30 for 8 minutes.
            # Placed mid-shift on purpose so the event isn't blurred by the
            # 14:00 handover window.
            thr, cur = inject_stuck_at(
                thr,
                cur,
                timestamps,
                start + timedelta(hours=10, minutes=30),
                duration=timedelta(minutes=8),
            )

        if m.name == "sash_assembler":
            # Planned maintenance on day 2 from 02:00 to 04:00.
            thr, cur, vib = inject_planned_maintenance(
                thr,
                cur,
                vib,
                timestamps,
                start + timedelta(days=1, hours=2),
                start + timedelta(days=1, hours=4),
            )

        state = derive_packml_state(thr, cur)

        signal_pairs = [
            ("throughput_pcs_per_min", thr),
            ("motor_current_a", cur),
            ("temperature_c", temp),
            ("vibration_rms_mm_s", vib),
        ]
        for signal_name, values in signal_pairs:
            records.append(
                pd.DataFrame(
                    {
                        "timestamp": timestamps,
                        "factory_id": "skjern_1",
                        "line_id": m.line,
                        "machine_id": m.name,
                        "signal": signal_name,
                        "value": values.astype(float),
                        "value_str": None,
                    }
                )
            )

        records.append(
            pd.DataFrame(
                {
                    "timestamp": timestamps,
                    "factory_id": "skjern_1",
                    "line_id": m.line,
                    "machine_id": m.name,
                    "signal": "packml_state",
                    "value": np.nan,
                    "value_str": state,
                }
            )
        )

    measurements = pd.concat(records, ignore_index=True)
    events = _build_events(start)
    return measurements, events


def _build_events(start: pd.Timestamp) -> pd.DataFrame:
    """A small, realistic events log keyed to the embedded scenarios."""
    rows = [
        # Planned maintenance on sash_assembler
        dict(
            timestamp=start + timedelta(days=1, hours=2),
            line_id="line_1", machine_id="sash_assembler",
            event_type="mes_message", severity="info", code="PM_START",
            message="Planned maintenance window started. Estimated end 04:00.",
        ),
        dict(
            timestamp=start + timedelta(days=1, hours=4, minutes=5),
            line_id="line_1", machine_id="sash_assembler",
            event_type="mes_message", severity="info", code="PM_END",
            message="Planned maintenance complete. Returning to production.",
        ),
        # Stuck-at on glass_cutter
        dict(
            timestamp=start + timedelta(hours=10, minutes=30),
            line_id="line_2", machine_id="glass_cutter",
            event_type="alarm", severity="error", code="DRV_F042",
            message="Drive fault: motor over-current sustained. Check axis 2.",
        ),
        dict(
            timestamp=start + timedelta(hours=10, minutes=32),
            line_id="line_2", machine_id="glass_cutter",
            event_type="operator_note", severity="info", code="OP_NOTE",
            message="Glas blev hængende på transportbåndet. Manuelt frigjort. Kører igen.",
        ),
        dict(
            timestamp=start + timedelta(hours=10, minutes=38),
            line_id="line_2", machine_id="glass_cutter",
            event_type="mes_message", severity="info", code="RESUMED",
            message="Production resumed after manual intervention.",
        ),
        # Bearing wear on folder_02
        dict(
            timestamp=start + timedelta(hours=20, minutes=10),
            line_id="line_2", machine_id="folder_02",
            event_type="alarm", severity="warning", code="VIB_W01",
            message="Vibration RMS rising above baseline (1.2x).",
        ),
        dict(
            timestamp=start + timedelta(days=1, hours=8, minutes=15),
            line_id="line_2", machine_id="folder_02",
            event_type="alarm", severity="warning", code="VIB_W02",
            message="Vibration RMS sustained above warning threshold for 12h.",
        ),
        dict(
            timestamp=start + timedelta(days=1, hours=9, minutes=30),
            line_id="line_2", machine_id="folder_02",
            event_type="alarm", severity="error", code="VIB_E01",
            message="Vibration spike: 3.5x baseline. Inspect main bearing.",
        ),
        dict(
            timestamp=start + timedelta(days=1, hours=9, minutes=45),
            line_id="line_2", machine_id="folder_02",
            event_type="operator_note", severity="info", code="OP_NOTE",
            message="Maskinen lyder anderledes. Vil have vedligehold til at kigge på det inden næste skift.",
        ),
    ]
    df = pd.DataFrame(rows)
    df.insert(1, "factory_id", "skjern_1")
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def write_parquet(
    measurements: pd.DataFrame,
    events: pd.DataFrame,
    data_dir: Path,
) -> tuple[Path, Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    m_path = data_dir / "synthetic_factory.parquet"
    e_path = data_dir / "synthetic_events.parquet"
    measurements.to_parquet(m_path, index=False)
    events.to_parquet(e_path, index=False)
    return m_path, e_path
