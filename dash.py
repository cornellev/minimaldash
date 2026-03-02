import pygame
import sys
import time
import math
from collections import deque
from read_shm import SensorShmReader
import pymap3d as pm


WINDOW_DURATION = 10.0
METER_TO_MILE = 1 / 1609.344


def dxy_local_tangent(lat0, lon0, lat1, lon1):
    dx, dy, _ = pm.geodetic2enu(lat1, lon1, 0.0, lat0, lon0, 0.0)
    return dx, dy


def meters_to_miles(m):
    return m * METER_TO_MILE


def init_pygame():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 24)
    font_small = pygame.font.SysFont("Arial", 18)
    lightning = pygame.transform.scale(
        pygame.image.load("images/lightning.png"), (24, 24)
    )
    map_icon = pygame.transform.scale(
        pygame.image.load("images/map.png"), (24, 24)
    )
    return screen, clock, font, font_small, lightning, map_icon


class TelemetryState:
    def __init__(self):
        self.total_energy = 0.0
        self.last_time = time.time()
        self.total_distance_m = 0.0
        self.last_lat = None
        self.last_lon = None
        self.queue = deque()
        self.window_power = 0.0
        self.window_distance = 0.0
        self.miles_per_kwh = 0.0
        self.start_time = None


def update_physics(state, snap):
    now = time.time()
    dt = now - state.last_time
    state.last_time = now

    current = snap["power"]["current"]
    voltage = snap["power"]["voltage"]
    power = voltage * current
    state.total_energy += power * dt

    lat = snap["gps"]["gps_lat"]
    lon = snap["gps"]["gps_long"]

    distance_inc = 0.0
    if lat != 0 and lon != 0:
        if state.last_lat is not None:
            dx, dy = dxy_local_tangent(state.last_lat, state.last_lon, lat, lon)
            distance_inc = math.hypot(dx, dy)
            state.total_distance_m += distance_inc
        state.last_lat, state.last_lon = lat, lon

    if state.start_time is None and state.last_lat is not None:
        state.start_time = now

    update_efficiency(state, now, power, distance_inc)
    return power


def update_efficiency(state, now, power, distance_inc):
    if state.start_time is None:
        return

    state.queue.append((now, power, distance_inc))
    state.window_power += power
    state.window_distance += distance_inc

    while state.queue and now - state.queue[0][0] > WINDOW_DURATION:
        _, old_power, old_dist = state.queue.popleft()
        state.window_power -= old_power
        state.window_distance -= old_dist

    if state.window_power > 0:
        avg_power = state.window_power / len(state.queue)
        energy_kwh = (avg_power * WINDOW_DURATION) / 3600
        distance_miles = meters_to_miles(state.window_distance)
        state.miles_per_kwh = (
            distance_miles / energy_kwh if energy_kwh > 0 else 0.0
        )


def draw_ui(screen, font, font_small, lightning, map_icon, snap, state, power):
    screen.fill((0, 0, 0))
    y, lh = 50, 35

    def text(line, size="small", color=(255, 255, 255), x=70):
        nonlocal y
        f = font if size == "big" else font_small
        screen.blit(f.render(line, True, color), (x, y))
        y += lh

    text(f"Seq: {snap['seq']}", "big")
    screen.blit(lightning, (50, y))
    text("Power:", "big", (100, 200, 255), 80)

    text(f"Current: {snap['power']['current']:.2f} A | "
         f"Voltage: {snap['power']['voltage']:.2f} V | "
         f"Power: {power:.2f} W")

    text(f"Energy: {state.total_energy/3600000:.4f} kWh",
         color=(255, 255, 100))

    text(f"Efficiency (10s): {state.miles_per_kwh:.2f} mi/kWh | "
         f"Distance: {meters_to_miles(state.total_distance_m):.3f} mi",
         color=(100, 255, 100))

    pygame.display.flip()


def main():
    screen, clock, font, font_small, lightning, map_icon = init_pygame()
    reader = SensorShmReader()
    state = TelemetryState()

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (
                e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE
            ):
                running = False

        if reader.available:
            snap = reader.read_snapshot_dict()
            if snap:
                power = update_physics(state, snap)
                draw_ui(screen, font, font_small,
                        lightning, map_icon, snap, state, power)

        clock.tick(200)

    reader.close()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
