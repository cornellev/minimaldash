import pygame
import sys
import math
from collections import deque
from read_shm import SensorShmReader
import pymap3d as pm

WINDOW_DURATION = 10.0 
TIMESTAMP_WRAP = 70 * 60
METER_TO_MILE = 1 / 1609.344

def dxy_local_tangent(lat0, lon0, lat1, lon1):
    dx, dy, _ = pm.geodetic2enu(lat1, lon1, 0.0, lat0, lon0, 0.0)
    return dx, dy

def meters_to_miles(m):
    return m * METER_TO_MILE

class TelemetryState:
    def __init__(self):
        self.last_ts = None
        self.total_distance_m =0.0
        self.total_energy_j = 0.0
        self.last_lat = None
        self.last_lon = None
        self.window_queue = deque()
        self.window_energy = 0.0
        self.window_distance = 0.0
        self.speed_mps = 0.0
        self.miles_per_kwh = 0.0

def initialize_reader():
    return SensorShmReader()

def read_snapshot(reader):
    if reader.available:
        return reader.read_snapshot_dict()
    return None

def compute_dt(state, ts):
    if state.last_ts is None:
        state.last_ts = ts
        return 0.0

    dt = ts - state.last_ts
    if dt < 0:
        dt = (TIMESTAMP_WRAP - state.last_ts) + ts
    if dt <= 0:
        return 0.0

    state.last_ts = ts
    return dt

def calculate_distance(state, lat, lon):
    distance_inc = 0.0

    if lat != 0 and lon!= 0:
        if state.last_lat is not None:
            dx, dy = dxy_local_tangent(
                state.last_lat, state.last_lon, lat, lon
            )
            distance_inc = math.hypot(dx, dy)
            state.total_distance_m += distance_inc

        state.last_lat = lat
        state.last_lon = lon

    return distance_inc

def calculate_energy(state, power, dt):
    energy_inc = power * dt
    state.total_energy_j += energy_inc
    return energy_inc

def calculate_speed(distance_inc, dt):
    if dt > 0:
        return distance_inc/dt
    return 0.0

def update_efficiency(state, ts, energy_inc, distance_inc):

    state.window_queue.append((ts, energy_inc, distance_inc))
    state.window_energy += energy_inc
    state.window_distance += distance_inc
    while state.window_queue and ts - state.window_queue[0][0] > WINDOW_DURATION:
        _, old_energy, old_dist = state.window_queue.popleft()
        state.window_energy -= old_energy
        state.window_distance -= old_dist

    if state.window_energy > 0:
        energy_kwh = state.window_energy / 3_600_000
        miles = meters_to_miles(state.window_distance)
        state.miles_per_kwh = miles / energy_kwh
    else:
        state.miles_per_kwh = 0.0

def render(screen, font, snap, state, power):

    screen.fill((0, 0, 0))

    lines = [
        f"Seq: {snap['seq']}",
        f"Power: {power:.2f} W",
        f"Speed: {state.speed_mps:.2f} m/s",
        f"Distance: {meters_to_miles(state.total_distance_m):.3f} mi",
        f"Energy: {state.total_energy_j/3_600_000:.4f} kWh",
        f"Efficiency (10s): {state.miles_per_kwh:.2f} mi/kWh",
    ]

    y = 60
    for line in lines:
        text = font.render(line, True, (255, 255, 255))
        screen.blit(text, (60, y))
        y += 40

    pygame.display.flip()

def main():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 28)
    reader = initialize_reader()
    state = TelemetryState()
    running =True
    while running:

        for e in pygame.event.get():
            if e.type == pygame.QUIT or (
                e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE
            ):
                running = False

        snap = read_snapshot(reader)
        if snap:
            ts = snap["ts"]
            dt = compute_dt(state, ts)
            current = snap["power"]["current"]
            voltage = snap["power"]["voltage"]
            power = current * voltage
            energy_inc = calculate_energy(state, power, dt)
            lat = snap["gps"]["gps_lat"]
            lon = snap["gps"]["gps_long"]
            distance_inc = calculate_distance(state, lat, lon)
            state.speed_mps = calculate_speed(distance_inc, dt)
            update_efficiency(state, ts, energy_inc, distance_inc)
            render(screen, font, snap, state, power)

        clock.tick(200)

    reader.close()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()