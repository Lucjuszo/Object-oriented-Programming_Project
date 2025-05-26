from vpython import *
import math

scene.title = "Robot cylindryczny"
scene.caption = """Sterowanie:
← / → : obrót
↑ / ↓ : góra/dół
W / S : promień ramienia
Spacja: chwyć / puść
"""
scene.width = 800
scene.height = 600
scene.background = color.white
scene.range = 5


class TargetObject:
    def __init__(self):
        self.body = box(pos=vector(3, 0.2, 0), size=vector(0.4, 0.4, 0.4), color=color.green)

    def set_position(self, pos):
        self.body.pos = pos

    def get_position(self):
        return self.body.pos


class CylindricalRobot:
    def __init__(self, target):
        self.theta = 0
        self.z_pos = 0.1
        self.r = 2
        self.jaw_gap = 0.3
        self.grabbing = False
        self.target = target

        # Części robota
        self.base = cylinder(pos=vector(0, 0, 0), axis=vector(0, 0.1, 0), radius=1.5, color=color.gray(0.5))
        self.stem = cylinder(pos=vector(0, 0, 0), axis=vector(0, 5, 0), radius=1, color=color.blue)
        self.rotating_plate = box(pos=vector(0, self.z_pos + 0.5, 0), size=vector(0.5, 2.5, 2.5), color=color.yellow)
        self.arm = box(pos=vector(self.r, self.z_pos + 0.5, 0), size=vector(2, 0.2, 0.2), color=color.orange)

        # Chwytak
        self.gripper_base = box(pos=vector(0, 0, 0), size=vector(0.1, 0.1, 1), color=color.green)
        self.jaw_size = vector(0.2, 0.5, 0.01)
        self.jaw_left = box(pos=vector(0, 0, 0), size=self.jaw_size, color=color.red)
        self.jaw_right = box(pos=vector(0, 0, 0), size=self.jaw_size, color=color.red)

    def update(self):
        self.arm.pos = vector(self.r * math.cos(self.theta), self.z_pos + 0.5, self.r * math.sin(self.theta))
        self.arm.axis = vector(math.cos(self.theta), 0, math.sin(self.theta)) * 2

        self.rotating_plate.pos = vector(0, self.z_pos + 0.5, 0)
        self.rotating_plate.up = vector(math.cos(self.theta), 0, math.sin(self.theta))

        end_pos = self.arm.pos + norm(self.arm.axis)
        side = cross(self.arm.axis, vector(0, 1, 0))
        side_norm = norm(side)

        grip_center = end_pos

        self.gripper_base.pos = grip_center
        self.gripper_base.axis = vector(math.cos(self.theta), 0, math.sin(self.theta)) / 10

        self.jaw_left.pos = grip_center + side_norm * (self.jaw_gap / 2)
        self.jaw_right.pos = grip_center - side_norm * (self.jaw_gap / 2)
        self.jaw_left.axis = norm(self.arm.axis)
        self.jaw_right.axis = norm(self.arm.axis)

        if self.grabbing:
            self.target.set_position((self.jaw_left.pos + self.jaw_right.pos) / 2)

    def animate_grip(self, target_gap, step=0.01):
        while abs(self.jaw_gap - target_gap) > 0.01:
            self.jaw_gap += step if self.jaw_gap < target_gap else -step
            self.update()
            rate(60)

    def grab_or_release(self):
        jaw_vec = self.jaw_right.pos - self.jaw_left.pos
        jaw_dir = norm(jaw_vec)
        jaw_len = mag(jaw_vec)

        obj_vec = self.target.get_position() - self.jaw_left.pos
        proj_len = dot(obj_vec, jaw_dir)
        perp_dist = mag(obj_vec - proj_len * jaw_dir)

        if not self.grabbing and 0 < proj_len < jaw_len and perp_dist < 0.2:
            self.grabbing = True
            self.animate_grip(0.05)
        else:
            self.grabbing = False
            self.animate_grip(0.2)

    def handle_input(self, key):
        if key == 'left': self.theta -= 0.1
        elif key == 'right': self.theta += 0.1
        elif key == 'up': self.z_pos += 0.1
        elif key == 'down': self.z_pos -= 0.1
        elif key == 'w': self.r += 0.1
        elif key == 's': self.r -= 0.1
        elif key == ' ': self.grab_or_release()

        # Ograniczenia
        self.z_pos = max(0, min(self.z_pos, 4))
        self.r = max(0.5, min(self.r, 4))
        if self.theta > 2 * math.pi: self.theta -= 2 * math.pi
        if self.theta < 0: self.theta += 2 * math.pi


# Inicjalizacja
target = TargetObject()
robot = CylindricalRobot(target)

# Podłoga
floor = box(pos=vector(0, -1.5, 0), size=vector(100, 3, 100), color=color.gray(0.9))


def on_key(evt):
    robot.handle_input(evt.key)


scene.bind('keydown', on_key)

# Pętla główna
while True:
    rate(60)
    robot.update()
