from vpython import *
import math
import time

scene.title = "Robot cylindryczny"
scene.caption = """Sterowanie:
← / → : obrót
↑ / ↓ : góra/dół
W / S : promień ramienia
Z : chwyć
P : puść
"""
scene.width = 800
scene.height = 600
scene.background = color.white
scene.range = 5

velocity = 0.07

class TargetObject:
    def __init__(self):
        self.body = sphere(pos=vector(0, 0.2, 3), radius=0.2, color=color.red)

    def set_position(self, pos):
        self.body.pos = pos

    def get_position(self):
        return self.body.pos

class CylindricalRobot:
    def __init__(self, target):
        self.theta = 0
        self.z_pos = 0.1
        self.r = 2
        self.jaw_max_gap = 1
        self.jaw_gap = 1
        self.grabbing = False
        self.target = target
        self.input_field = None

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
            # Ustaw pozycję przedmiotu na środku między szczękami
            new_pos = (self.jaw_left.pos + self.jaw_right.pos) / 2
            self.target.set_position(new_pos)

    def animate_grip(self, target_gap, step=0.02):
        # Animate jaw_gap smoothly to target_gap without blocking event loop or using time.sleep
        while abs(self.jaw_gap - target_gap) > 0.005:
            rate(60)
            if self.jaw_gap < target_gap:
                self.jaw_gap = min(self.jaw_gap + step, target_gap)
            else:
                self.jaw_gap = max(self.jaw_gap - step, target_gap)
            self.update()

    def close_gripper(self):
        self.animate_grip(0.05)  # Close jaws tightly
        jaw_vec = self.jaw_right.pos - self.jaw_left.pos
        jaw_dir = norm(jaw_vec)
        jaw_len = mag(jaw_vec)
        obj_vec = self.target.get_position() - self.jaw_left.pos
        proj_len = dot(obj_vec, jaw_dir)
        perp_dist = mag(obj_vec - proj_len * jaw_dir)
        if 0 <= proj_len <= jaw_len and perp_dist < 0.15:
            self.grabbing = True
        else:
            self.grabbing = False
    def open_gripper(self):
        self.animate_grip(self.jaw_max_gap)
        self.grabbing = False

    def check_collision_with_sphere(self, position):
        # Sprawdź odległość punktu ramienia od kuli (targetu)
        sphere_pos = self.target.get_position()
        sphere_radius = self.target.body.radius

        dist = mag(position - sphere_pos)
        # Margines bezpieczeństwa (np. promień ramienia + chwytaka)
        safety_distance = sphere_radius + 0.105  # dostosuj wartość 0.5 w razie potrzeby
        return dist < safety_distance

    def handle_input(self, key):
        # Zachowaj kopię bieżących parametrów
        new_theta = self.theta
        new_z_pos = self.z_pos
        new_r = self.r

        if key == 'left': new_theta -= 0.02
        elif key == 'right': new_theta += 0.02
        elif key == 'up': new_z_pos += 0.02
        elif key == 'down': new_z_pos -= 0.02
        elif key == 'w': new_r += 0.02
        elif key == 's': new_r -= 0.02
        elif key == 'z': self.close_gripper()  # zaciskaj szczęki
        elif key == 'p': self.open_gripper()   # otwieraj szczęki

        # Ograniczenia parametrów
        new_z_pos = max(0, min(new_z_pos, 4))
        new_r = max(0.5, min(new_r, 2.5))
        new_theta = max(-0.9 * math.pi, min(new_theta, 0.9 * math.pi))

        # Oblicz pozycję ramienia po zmianie
        new_arm_pos = vector(new_r * math.cos(new_theta), new_z_pos + 0.5, new_r * math.sin(new_theta))

        # Sprawdź kolizję, jeśli kolizji nie ma, zaakceptuj zmiany
        if not self.check_collision_with_sphere(new_arm_pos):
            self.theta = new_theta
            self.z_pos = new_z_pos
            self.r = new_r
        else:
            # Drukuj komunikat o kolizji lub ignoruj
            pass
            # print("Kolizja z kulą - ruch zablokowany")

    # okienko do wprowadzania danych
    def pos_input(self):
        if self.input_field is None:
            scene.append_to_caption("Wprowadź pozycję (np. 1.1 2.0 3.5):")
            self.input_field = winput(prompt='Podaj pozycję:', bind=self.get_position, type='string')

    # idź do pozycji po wpisaniu w okienko
    def get_position(self, text):
        try:
            x, y, new_z_pos = map(float, self.input_field.text.split())  # zamien string na 3 floaty
            new_theta = math.atan2(y, x)  # kąt theta
            new_r = sqrt(x ** 2 + y ** 2)  # promień
            if (0 < new_z_pos < 4) and (-0.9 * math.pi < new_theta < 0.9 * math.pi) and (0.5 < new_r < 2.5):
                ## Sprawdź kolizję na końcową pozycję
                #new_arm_pos = vector(new_r * math.cos(new_theta), new_z_pos + 0.5, new_r * math.sin(new_theta))
                #if self.check_collision_with_sphere(new_arm_pos):
                #    print("Pozycja w kolizji z kulą - ruch zablokowany")
                #    return

                while new_z_pos > self.z_pos:
                    self.z_pos += 0.02
                    self.update()
                    rate(60)
                    time.sleep(velocity)

                while new_z_pos < self.z_pos:
                    self.z_pos -= 0.02
                    self.update()
                    rate(60)
                    time.sleep(velocity)

                while new_theta > self.theta:
                    self.theta += 0.02
                    self.update()
                    rate(60)
                    time.sleep(velocity)

                while new_theta < self.theta:
                    self.theta -= 0.02
                    self.update()
                    rate(60)
                    time.sleep(velocity)

                while new_r > self.r:
                    self.r += 0.02
                    self.update()
                    rate(60)
                    time.sleep(velocity)

                while new_r < self.r:
                    self.r -= 0.02
                    self.update()
                    rate(60)
                    time.sleep(velocity)
            else:
                print("Współrzędne poza obszarem pracy")
        except:
            print("Błąd: podaj 3 liczby oddzielone spacjami.")


# Inicjalizacja
target = TargetObject()
robot = CylindricalRobot(target)

# Podłoga
floor = box(pos=vector(0, -1.5, 0), size=vector(100, 3, 100), color=color.green)

def on_key(evt):
    robot.handle_input(evt.key)

robot.pos_input()
scene.bind('keydown', on_key)

# Pętla główna
while True:
    rate(60)
    robot.update()

