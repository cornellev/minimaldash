# Minimal Dash

Real-time EV telemetry dashboard for UC26. Reads live sensor snapshots from shared memory and renders speed + efficiency on a Kivy UI.

---
<p align="center">
<img width="789" height="456" alt="Screenshot 2026-03-21 at 3 00 10 PM" src="https://github.com/user-attachments/assets/35a6306e-c61e-4db4-a2ed-56ef1f563a83" />
</p>



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
python3 -m venv kivy_venv
source kivy_venv/bin/activate
pip install --upgrade pip
python -m pip install "kivy[full]"
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
