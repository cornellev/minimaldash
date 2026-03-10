# Minimal Dash

Real-time EV telemetry dashboard for UC26. Reads live sensor snapshots from shared memory and renders speed + efficiency on a Kivy UI.

---

<img width="797" height="366" alt="Screenshot 2026-03-09 at 3 43 44 PM" src="https://github.com/user-attachments/assets/f24fb8f9-cc26-490d-af50-4ee2fe643bc9" />

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

This step is usually not necessary as these processes should be running as systemd services.
You can probably check with `systemctl status uc26_sensor.service`. Otherwise,

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
