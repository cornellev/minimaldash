from kivy.app import App
from kivy.core.window import Window
Window.fullscreen = 'auto'
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
import math
from uc26_sensor_reader.read_shm import SensorShmReader
TIMESTAMP_WRAP= 70 * 60# seconds before timestamp rolls over
METER_TO_MILE= 1 / 1609.344
MPS_TO_MPH = 2.23694
MAX_SPEED=40
MAX_EFFECIENCY=500
IDEAL_SPEED=20
class TelemetryState:
    def __init__(self):
        self.last_ts   = None
        self.miles_per_kwh = 0.0
        self.speed_mph = 0.0

    def update(self, snap):
        ts = snap["global_ts"]
        if self.last_ts is None:
            self.last_ts = ts
            return
        dt = ts - self.last_ts
        if dt < 0:
            dt = (TIMESTAMP_WRAP - self.last_ts) + ts
        if dt <= 0:
            return
        self.last_ts = ts
        speed_mps = snap["filtered"]["speed"]# m/s from sensor
        self.speed_mph = speed_mps * MPS_TO_MPH
        current = snap["power"]["current"]
        voltage = snap["power"]["voltage"]
        kilowatts = (current * voltage) / 1000.0
        if kilowatts > 0 and self.speed_mph/kilowatts<=1000:
            self.miles_per_kwh = self.speed_mph / kilowatts
        else:
            self.miles_per_kwh = 0.0

class CircularGauge(Widget):
    value= NumericProperty(0)
    max_value = NumericProperty(40)

    def __init__(self, unit="", show_dot=True, title="", **kwargs):
        self.unit     = unit
        self.show_dot = show_dot
        self.title    = title
        super().__init__(**kwargs)

        self.title_label = Label(
            text=title, bold=True,
            size_hint=(None, None)
        )
        self.add_widget(self.title_label)

        self.label = Label(
            text="0", bold=True,
            font_name="DSEG7Classic-Bold.ttf",
            size_hint=(None, None)
        )
        self.add_widget(self.label)

        self.unit_label = Label(text=unit, size_hint=(None, None))
        self.add_widget(self.unit_label)
        
        Clock.schedule_interval(self.update_gauge, 1 / 10)

    def update_gauge(self, dt):
        self.canvas.before.clear()

        cx, cy = self.center
        radius = min(self.width, self.height) * 0.45

        arc_start= -90
        arc_end= 90
        progress_angle = (min(self.value, self.max_value) / self.max_value) * 180
        end_angle= arc_start + progress_angle

        with self.canvas.before:
            Color(0.25, 0.25, 0.3)
            Line(circle=(cx, cy, radius, arc_start, arc_end),
                 width=max(2, radius * 0.08))

            Color(0.702, 0.106, 0.106)
            Line(circle=(cx, cy, radius, arc_start, end_angle),
                 width=max(2, radius * 0.1))

            if self.show_dot:
                marker_angle = 180-(IDEAL_SPEED / MAX_SPEED) * 180
                mx = cx + radius * math.cos(math.radians(marker_angle))
                my = cy + radius * math.sin(math.radians(marker_angle))
                Color(0.12, 0.78, 0.35)
                dot = radius * 0.12
                Ellipse(pos=(mx - dot / 2, my - dot / 2), size=(dot, dot))

        self.label.center= (self.center[0], self.center[1] + radius * 0.12)
        self.label.font_size = radius * 0.5
        self.label.text = f"{self.value:.1f}"

        self.unit_label.center= (self.center[0], self.center[1] - radius * 0.25)
        self.unit_label.font_size = radius * 0.22
        self.unit_label.text = self.unit

        self.title_label.center= (self.center[0], self.center[1] + radius * 1.3)
        self.title_label.font_size = radius * 0.28
        self.title_label.text = self.title

class Dashboard(FloatLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # max_value: set to expected max speed / efficiency ceiling
        self.left_gauge = CircularGauge(
            title="Efficiency", unit="mi/kWh",
            show_dot=False, max_value=MAX_EFFECIENCY,
            size_hint=(0.42, 0.7),
            pos_hint={"x": 0.02, "center_y": 0.5}
        )
        self.right_gauge = CircularGauge(
            title="Speed", unit="mph",
            show_dot=True, max_value=MAX_SPEED,
            size_hint=(0.42, 0.7),
            pos_hint={"right": 0.98, "center_y": 0.5}
        )
        self.add_widget(self.left_gauge)
        self.add_widget(self.right_gauge)

        self.light_image = Image(
            source="fulllight.png",
            size_hint=(None, None),
            size=(80, 80),
            pos_hint={"x": 0.01, "y": 0.01}
        )
        self.add_widget(self.light_image)

        self.reader = SensorShmReader()
        self.state  = TelemetryState()

        Clock.schedule_interval(self.poll_sensors, 1 / 30)

    def poll_sensors(self, dt):
        if not self.reader.available:
            return

        snap = self.reader.read_snapshot_dict()
        if not snap:
            return

        self.state.update(snap)

        self.left_gauge.value  = max(0, self.state.miles_per_kwh)
        self.right_gauge.value = max(0, self.state.speed_mph)

    def on_stop(self):
        self.reader.close()


class DashboardApp(App):
    def build(self):
        return Dashboard()

    def on_stop(self):
        self.root.on_stop()


DashboardApp().run()