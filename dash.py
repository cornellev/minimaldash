import pygame
import sys
import time
from collections import deque
import math
from read_shm import SensorShmReader
import pymap3d as pm

def dxy_local_tangent(lat0, lon0, lat1, lon1):
    dx, dy, _ = pm.geodetic2enu(
        lat1, lon1, 0.0,
        lat0, lon0, 0.0
    )
    return dx, dy

def meters_to_miles(meters):
    """Convert meters to miles."""
    return meters / 1609.344

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)
font_small = pygame.font.SysFont("Arial", 18)

reader = SensorShmReader()

# Load lightning icon
lightning_icon = pygame.image.load('images/lightning.png')  # Change filename if needed
lightning_icon = pygame.transform.scale(lightning_icon, (24, 24))  # Resize to 24x24 pixels
map_icon = pygame.image.load('images/map.png')  # Change filename if needed
map_icon = pygame.transform.scale(map_icon, (24, 24))  # Resize to 24x24 pixels

# Energy tracking variables
total_energy = 0.0  # Joules
last_time = time.time()

# Efficiency tracking with deque (10 second window)
WINDOW_DURATION = 10.0  # seconds
data_queue = deque()
reference_lat = None
reference_lon = None
total_distance_m = 0.0  # Total distance traveled in meters
last_lat = None
last_lon = None
miles_per_kwh = 0.0  # Current efficiency
start_time = None  # Track when we started collecting data
queue_ready = False  # Flag to indicate we have 10 seconds of data
window_power_W = 0.0  # Running sum of power in window
window_distance_m = 0.0  # Running sum of distance in window

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: 
                running = False
    
    screen.fill((0, 0, 0))
    
    if reader.available:
        snap = reader.read_snapshot_dict()
        
        if snap is not None:
            # Calculate time step
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # Calculate instantaneous power and integrate energy
            current = snap['power']['current']
            voltage = snap['power']['voltage']
            power = voltage * current  # Watts
            energy_increment = power * dt  # Joules
            total_energy += energy_increment 
            
            # Get GPS coordinates
            current_lat = snap['gps']['gps_lat']
            current_lon = snap['gps']['gps_long']
            
            # Initialize reference point and start time on first valid GPS reading
            if reference_lat is None and current_lat != 0 and current_lon != 0:
                reference_lat = current_lat
                reference_lon = current_lon
                last_lat = current_lat
                last_lon = current_lon
                start_time = current_time
            
            # Calculate distance increment
            distance_increment_m = 0.0
            if reference_lat is not None and current_lat != 0 and current_lon != 0:
                # Calculate distance from last position using pymap3d
                dx, dy = dxy_local_tangent(last_lat, last_lon, current_lat, current_lon)
                distance_increment_m = math.sqrt(dx**2 + dy**2)
                total_distance_m += distance_increment_m
                
                last_lat = current_lat
                last_lon = current_lon
            if start_time is not None:
                # Always add new data point to queue
                data_queue.append((current_time, power, distance_increment_m))
                
                if not queue_ready:
                    # First 10 seconds - building up the queue, use for loop
                    if current_time - start_time >= WINDOW_DURATION:
                        queue_ready = True
                    
                    window_power_W = 0.0
                    window_distance_m = 0.0
                    for timestamp, pwr, distance in data_queue:
                        window_power_W += pwr
                        window_distance_m += distance
                else:
                    #one in, one out with running sums
                    window_power_W += power
                    window_distance_m += distance_increment_m
                    old_timestamp, old_power, old_distance = data_queue.popleft()
                    window_power_W -= old_power
                    window_distance_m -= old_distance
                if window_power_W > 0:
                    avg_power_W = window_power_W / len(data_queue)
                    window_energy_J = avg_power_W * WINDOW_DURATION
                    window_energy_kWh = window_energy_J / 3600  # Watt-seconds to kWh
                    window_distance_miles = meters_to_miles(window_distance_m)
                    miles_per_kwh = window_distance_miles / window_energy_kWh
            
            y_pos = 50
            line_height = 35
            
            # Display sequence number
            text = font.render(f"Seq: {snap['seq']}", True, (255, 255, 255))
            screen.blit(text, (50, y_pos))
            y_pos += line_height
            
            # Display power data with lightning icon
            screen.blit(lightning_icon, (50, y_pos))
            text = font.render("Power:", True, (100, 200, 255))
            screen.blit(text, (80, y_pos))
            y_pos += line_height
            text = font_small.render(
                f"  Current: {current:.2f} A  |  Voltage: {voltage:.2f} V  |  Power: {power:.2f} W",
                True, (255, 255, 255)
            )
            screen.blit(text, (70, y_pos))
            y_pos += line_height
            
            # Display energy consumption
            text = font_small.render(
                f"  Energy: {total_energy/3600000:.4f} kWh ({total_energy:.2f} J)",
                True, (255, 255, 100)
            )
            screen.blit(text, (70, y_pos))
            y_pos += line_height
            
            # Display efficiency (miles/kWh) - 10 second rolling window
            text = font_small.render(
                f"  Efficiency (10s): {miles_per_kwh:.2f} mi/kWh  |  Distance: {meters_to_miles(total_distance_m):.3f} mi",
                True, (100, 255, 100)
            )
            screen.blit(text, (70, y_pos))
            y_pos += line_height
            
            # Display motor data
            text = font.render("Motor:", True, (100, 200, 255))
            screen.blit(text, (50, y_pos))
            y_pos += line_height
            text = font_small.render(
                f"  Throttle: {snap['motor']['throttle']:.2f}  |  Velocity: {snap['motor']['velocity']:.2f}",
                True, (255, 255, 255)
            )
            screen.blit(text, (70, y_pos))
            y_pos += line_height
            
            # Display front RPM
            text = font.render("RPM Front:", True, (100, 200, 255))
            screen.blit(text, (50, y_pos))
            y_pos += line_height
            text = font_small.render(
                f"  Left: {snap['rpm_front']['rpm_left']:.1f}  |  Right: {snap['rpm_front']['rpm_right']:.1f}",
                True, (255, 255, 255)
            )
            screen.blit(text, (70, y_pos))
            y_pos += line_height
            
            # Display back RPM
            text = font.render("RPM Back:", True, (100, 200, 255))
            screen.blit(text, (50, y_pos))
            y_pos += line_height
            text = font_small.render(
                f"  Left: {snap['rpm_back']['rpm_left']:.1f}  |  Right: {snap['rpm_back']['rpm_right']:.1f}",
                True, (255, 255, 255)
            )
            screen.blit(text, (70, y_pos))
            y_pos += line_height
            screen.blit(map_icon, (50, y_pos))
            # Display GPS data
            text = font.render("GPS:", True, (100, 200, 255))
            screen.blit(text, (80, y_pos))
            y_pos += line_height
            text = font_small.render(
                f"  Lat: {snap['gps']['gps_lat']:.6f}  |  Long: {snap['gps']['gps_long']:.6f}",
                True, (255, 255, 255)
            )
            screen.blit(text, (70, y_pos))
            y_pos += line_height
            
        else:
            text = font.render("Waiting for data...", True, (255, 100, 100))
            screen.blit(text, (50, 50))
    else:
        text = font.render("Shared memory not available", True, (255, 100, 100))
        screen.blit(text, (50, 50))
        text = font_small.render("Run the C++ writer script first", True, (255, 255, 255))
        screen.blit(text, (50, 90))
    
    pygame.display.flip()
    clock.tick(200)  # 200 Hz refresh rate

# Cleanup
reader.close()
pygame.quit()
sys.exit()