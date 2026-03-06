A real-time electric vehicle telemetry display built with Pygame. Reads live sensor data from shared memory and renders a dash showing power, speed, distance, energy consumption, and rolling efficiency.

---

## Features

- **Live sensor ingestion** — reads from shared memory via `SensorShmReader` at up to 200 Hz
- **GPS-based distance tracking** — uses local tangent plane (ENU) projection for accurate incremental distance
- **Energy accounting** — integrates power over time to compute total energy consumed in kWh
- **Rolling efficiency** — computes miles/kWh over a configurable sliding window (default: 10 seconds)
- **Dash screen** — clean Pygame display designed for in-vehicle use

---

## Display Fields

| Field | Description |
|---|---|
| `Seq` | Snapshot sequence number |
| `Power` | Instantaneous power (W) |
| `Speed` | Current speed (m/s) |
| `Distance` | Total distance traveled (miles) |
| `Energy` | Total energy consumed (kWh) |
| `Efficiency (10s)` | Rolling average efficiency (mi/kWh) |

---

## Requirements

```
pygame
pymap3d
```

You will also need:
- `read_shm.py` — provides `SensorShmReader`, which exposes live sensor snapshots via shared memory

Install dependencies:

```bash
pip install pygame pymap3d
```

---

## Usage

```bash
python dash.py
```

Press `Ctrl+C` or close the window to exit.

---

## Expected Snapshot Format

`SensorShmReader.read_snapshot_dict()` should return a dictionary with the following structure:

```python
{
    "seq": int,
    "ts": float,           # timestamp in seconds
    "power": {
        "current": float,  # amps
        "voltage": float,  # volts
    },
    "gps": {
        "gps_lat": float,
        "gps_long": float,
    }
}
```

---

## Configuration

| Constant | Default | Description |
|---|---|---|
| `WINDOW_DURATION` | `10.0` s | Sliding window for efficiency calculation |
| `TIMESTAMP_WRAP` | `4200` s (70 min) | Timestamp rollover period |

---

## Project Structure

```
.
├── dash.py      # Main dashboard application 
└── README.md
```
