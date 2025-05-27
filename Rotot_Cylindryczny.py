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
        self.body = box(pos=vector(0, 0.2, 2), size=vector(0.4, 0.4, 0.4), color=color.red)

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
        self.base = cylinder(pos=vector(0, 0, 0), axis=vector(0, 0.1, 0), radius=1.5, color=color.blue)
        self.stem = cylinder(pos=vector(0, 0, 0), axis=vector(0, 5, 0), radius=0.7, color=color.gray(0.8))
        self.rotating_plate = box(pos=vector(0, self.z_pos + 0.5, 0), size=vector(0.5, 2.5, 2.5), color=color.gray(0.3))
        self.arm = box(pos=vector(self.r, self.z_pos + 0.5, 0), size=vector(0.2, 2.5, 0.2), color=color.white)

        # Chwytak
        self.gripper_base = box(pos=vector(0, 0, 0), size=vector(0.1, 0.1, 1), color=color.black)
        self.jaw_left = box(pos=vector(0, 0, 0), size=vector(0.35, 0.5, 0.02), color=color.black)
        self.jaw_right = box(pos=vector(0, 0, 0), size=vector(0.35, 0.5, 0.02), color=color.black)

    def update(self):
        self.arm.pos = vector(self.r * math.cos(self.theta), self.z_pos + 0.5, self.r * math.sin(self.theta))
        self.arm.up = vector(math.cos(self.theta), 0, math.sin(self.theta))
        #self.arm.axis = vector(math.cos(self.theta), 0, math.sin(self.theta)) * 2.5

        self.rotating_plate.pos = vector(0, self.z_pos + 0.5, 0)
        self.rotating_plate.up = vector(math.cos(self.theta), 0, math.sin(self.theta))

        grip_center = self.arm.pos + self.arm.up * (self.arm.size.y - self.gripper_base.size.y) / 2
        side = cross(self.arm.up, vector(0, 1, 0))
        side_norm = norm(side)

        self.gripper_base.pos = grip_center
        self.gripper_base.up = vector(math.cos(self.theta), 0, math.sin(self.theta)) 

        self.jaw_left.pos = self.arm.pos + self.arm.up * (self.arm.size.y / 2 - self.gripper_base.size.y + self.jaw_left.size.y / 2) + side_norm * (self.jaw_gap / 2)
        self.jaw_right.pos = self.arm.pos + self.arm.up * (self.arm.size.y / 2 - self.gripper_base.size.y + self.jaw_left.size.y / 2) - side_norm * (self.jaw_gap / 2)
        self.jaw_left.up = norm(self.arm.up)
        self.jaw_right.up = norm(self.arm.up)

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
        self.r = max(0.5, min(self.r, 2.5))
        self.theta = max(0, min(self.theta, 1.8 * math.pi))



# Inicjalizacja
target = TargetObject()
robot = CylindricalRobot(target)

# Podłoga
floor = box(pos=vector(0, -1.5, 0), size=vector(100, 3, 100), color=color.green)


def on_key(evt):
    robot.handle_input(evt.key)


scene.bind('keydown', on_key)

# Pętla główna
while True:
    rate(60)
    robot.update()
