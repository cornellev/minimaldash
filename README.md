# Minimal Dash

Real-time EV telemetry dashboard for UC26. Reads live sensor snapshots from shared memory and renders speed + efficiency on a Kivy UI.

---

## Project Structure

```text
minimaldash/
├─ uisensor.py                              # Main dashboard (live shared-memory data)
├─ uitest.py                                # Dashboard simulator
└─ README.md
```

---

## Quick Start (Local Development)

### 1. Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install kivy
```

### 2. Build and run sensor writer (Linux target)

```bash
cd uc26_sensor_reader
g++ -O2 -std=c++17 write_shm.cpp -lpigpiod_if2 -lrt -pthread -o shm_writer
sudo pigpiod
./shm_writer
```

### 3. Run dashboard on LCD display session

```bash
export DISPLAY=:0
python uisensor.py
```
