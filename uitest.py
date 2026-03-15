from kivy.app import App
from kivy.core.window import Window
Window.fullscreen = 'auto'
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse, Mesh
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
import math
import random
IDEAL_SPEED=20
MAX_SPEED=40

class CircularGauge(Widget):
    value = NumericProperty(0)
    max_value = NumericProperty(40)

    def __init__(self, unit="", show_dot=True, title="", **kwargs):
        self.unit = unit
        self.show_dot = show_dot
        self.title = title
        super().__init__(**kwargs)

        self.title_label = Label(
            text=title,
            bold=True,
            size_hint=(None, None)
        )
        self.add_widget(self.title_label)

        # Number inside the gauge
        self.label = Label(
            text="0",
            bold=True,
            font_name="DSEG7Classic-Bold.ttf",
            size_hint=(None, None)
        )
        self.add_widget(self.label)

        self.unit_label = Label(
            text=unit,
            size_hint=(None, None)
        )
        self.add_widget(self.unit_label)

        Clock.schedule_interval(self.update_gauge, 1 / 30)

    def update_gauge(self, dt):
        self.canvas.before.clear()

        cx, cy = self.center
        radius = min(self.width, self.height) * 0.45

        # 9 o'clock = 180°, 3 o'clock = 360° — bottom semicircle
        arc_start = -90
        arc_end   = 90  # full range = 180 degrees

        progress_angle = (self.value / self.max_value) * 180
        end_angle = arc_start + progress_angle

        with self.canvas.before:
            # Background ring — bottom semicircle only
            Color(0.25, 0.25, 0.3)
            Line(circle=(cx, cy, radius, arc_start, arc_end),
                 width=max(2, radius * 0.08))

            # Progress arc
            Color(0.702, 0.106, 0.106)
            Line(circle=(cx, cy, radius, arc_start, end_angle),
                 width=max(2, radius * 0.1))

            # Green dot marker at 3 o'clock (0° / max position)
            if self.show_dot:
                marker_angle = 180-(IDEAL_SPEED / MAX_SPEED) * 180
                mx = cx + radius * math.cos(math.radians(marker_angle))
                my = cy + radius * math.sin(math.radians(marker_angle))
                Color(0.12, 0.78, 0.35)
                dot = radius * 0.12
                Ellipse(pos=(mx - dot / 2, my - dot / 2),
                        size=(dot, dot))

        self.label.center = (self.center[0], self.center[1] + radius * 0.12)
        self.label.font_size = radius * 0.5
        self.label.text = str(int(self.value))

        self.unit_label.center = (self.center[0], self.center[1] - radius * 0.25)
        self.unit_label.font_size = radius * 0.22
        self.unit_label.text = self.unit

        self.title_label.center = (self.center[0], self.center[1] + radius * 1.3)
        self.title_label.font_size = radius * 0.28
        self.title_label.text = self.title


class DirectionArrow(Widget):
    angle = NumericProperty(90)  # degrees: 90=up, 0=right, 270=down

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.caption = Label(
            text="Best Path",
            size_hint=(None, None),
            color=(1, 1, 1, 0.7)
        )
        self.add_widget(self.caption)

        Clock.schedule_interval(self.update_arrow, 1 / 30)

    def update_arrow(self, dt):
        self.canvas.before.clear()

        cx, cy = self.center
        size = min(self.width, self.height) * 0.46

        a    = math.radians(self.angle)
        perp = a + math.pi / 2

        # GPS chevron: tip, left wing, back-center indent, right wing
        tip_x   = cx + size        * math.cos(a)
        tip_y   = cy + size        * math.sin(a)

        left_x  = cx - size * 0.45 * math.cos(a) + size * 0.55 * math.cos(perp)
        left_y  = cy - size * 0.45 * math.sin(a) + size * 0.55 * math.sin(perp)

        right_x = cx - size * 0.45 * math.cos(a) - size * 0.55 * math.cos(perp)
        right_y = cy - size * 0.45 * math.sin(a) - size * 0.55 * math.sin(perp)

        back_x  = cx - size * 0.12 * math.cos(a)
        back_y  = cy - size * 0.12 * math.sin(a)

        with self.canvas.before:
            Color(0.702, 0.106, 0.106, 1)
            Mesh(
                vertices=[
                    tip_x,   tip_y,   0, 0,
                    left_x,  left_y,  0, 0,
                    back_x,  back_y,  0, 0,
                    right_x, right_y, 0, 0,
                ],
                indices=[0, 1, 2, 0, 2, 3],
                mode='triangles'
            )

        self.caption.font_size = size * 0.40
        self.caption.center = (cx, cy - size * 1.2)


class Dashboard(FloatLayout):
    speed = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.left_gauge = CircularGauge(
            title="Efficiency",
            unit="mi/kWh",
            show_dot=False,
            size_hint=(0.42, 0.7),
            pos_hint={"x": 0.02, "center_y": 0.6}
        )

        self.right_gauge = CircularGauge(
            title="Speed",
            unit="mph",
            size_hint=(0.42, 0.7),
            pos_hint={"right": 0.98, "center_y": 0.6}
        )

        self.arrow = DirectionArrow(
            size_hint=(0.14, 0.35),
            pos_hint={"center_x": 0.5, "center_y": 0.55}
        )
        self.add_widget(self.left_gauge)
        self.add_widget(self.right_gauge)
        self.add_widget(self.arrow)

        self._t = 0.0
        Clock.schedule_interval(self.simulate_speed, 0.03)


    def simulate_speed(self, dt):
        self._t += dt
        # target ~100 so the bar hovers around the middle of the semicircle
        target = 15
        value = max(0, min(200,
            target
            + 15 * math.sin(self._t * 1.1)
            + 5  * math.sin(self._t * 3.7)
            + random.uniform(-1, 1)
        ))

        self.left_gauge.value = value
        self.right_gauge.value = value

        # Dummy best-path direction: pointing roughly northeast, drifting slowly
        self.arrow.angle = 20 + 18 * math.sin(self._t * 0.4)


class DashboardApp(App):
    def build(self):
        return Dashboard()


DashboardApp().run()