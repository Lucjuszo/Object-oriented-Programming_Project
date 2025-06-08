from vpython import *
import math
import time

scene.title = "Robot cylindryczny"
scene.caption = """Sterowanie:
← / → : obrót   ↑ / ↓ : góra/dół    W / S : promień ramienia
Z / P : chwyć/puść
UCZENIE MASZYNOWE:
R / K: Rozpocznij / Koniec(Powtórz)
"""
scene.width = 800
scene.height = 600
scene.background = color.white
scene.range = 5

time_delay = 0.07

class TargetObject:
    def __init__(self):
        self.body = sphere(pos=vector(0, 0.4, 3), radius=0.4, color=color.red)
        self.velocity = vector(0, 0, 0)  # Prędkość opadania
        self.is_dropped = False  # Flaga informująca, czy obiekt został puszczony

    def set_position(self, pos):
        self.body.pos = pos

    def get_position(self):
        return self.body.pos

    def update(self):
        if self.is_dropped:
            # Dodaj grawitację
            self.velocity.y -= 0.02  # Przyspieszenie grawitacyjne
            self.body.pos += self.velocity  # Aktualizuj pozycję obiektu

            # Sprawdź kolizję z podłogą
            if self.body.pos.y <= 0.4:  # Zakładamy, że podłoga ma y = -1.5 i kula ma promień 0.4
                self.body.pos.y = 0.4  # Ustaw pozycję na poziomie podłogi
                self.velocity.y = 0  # Zatrzymaj obiekt

    def drop(self):
        self.is_dropped = True  # Ustaw flagę, aby obiekt opadł

    def reset(self):
        self.is_dropped = False  # Zresetuj flagę
        self.velocity = vector(0, 0, 0)  # Zresetuj prędkość
        self.body.pos.y = 0.4  # Ustaw pozycję na początkową


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

        #tablice do zapisania ruchów
        self.learn_z_pos = []
        self.learn_theta = []
        self.learn_r = []
        self.learn_gripped = []


        # Części robota
        self.base = cylinder(pos=vector(0, 0, 0), axis=vector(0, 0.1, 0), radius=1.5, color=color.blue)
        self.stem = cylinder(pos=vector(0, 0, 0), axis=vector(0, 5, 0), radius=0.7, color=color.gray(0.8))
        self.rotating_plate = box(pos=vector(0, self.z_pos + 0.5, 0), size=vector(0.5, 2.5, 2.5), color=color.gray(0.3))
        self.arm = box(pos=vector(self.r, self.z_pos + 0.5, 0), size=vector(0.2, 2.5, 0.2), color=color.white)

        # Chwytak
        self.gripper_base = box(pos=vector(0, 0, 0), size=vector(0.1, 0.1, 1), color=color.black)
        self.jaw_left = box(pos=vector(0, 0, 0), size=vector(0.35, 1, 0.02), color=color.black)
        self.jaw_right = box(pos=vector(0, 0, 0), size=vector(0.35, 1, 0.02), color=color.black)

        #flaga do nagrywania 
        self.recording = False
        #flaga do chwytania
        self.if_gripped = 0

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
            # Kluczowa zmiana: aktualizacja pozycji obiektu, aby podążał za szczękami
            new_pos = (self.jaw_left.pos + self.jaw_right.pos) / 2
            self.target.set_position(new_pos)

    def animate_grip(self, target_gap, step=0.02):
        # Animate jaw_gap smoothly to target_gap without blocking event loop or using time.sleep
        while abs(self.jaw_gap - target_gap) > 0.005:
            rate(60)
            time.sleep(time_delay)
            if self.jaw_gap < target_gap:
                self.jaw_gap = min(self.jaw_gap + step, target_gap)
            else:
                self.jaw_gap = max(self.jaw_gap - step, target_gap)
            self.update()

    def close_gripper(self):
        jaw_vec = self.jaw_right.pos - self.jaw_left.pos
        jaw_dir = norm(jaw_vec)
        jaw_len = mag(jaw_vec)
        obj_vec = self.target.get_position() - self.jaw_left.pos
        proj_len = dot(obj_vec, jaw_dir)
        perp_dist = mag(obj_vec - proj_len * jaw_dir)

        if 0 <= proj_len <= jaw_len and perp_dist < (self.target.body.radius + 0.05):
            self.animate_grip(2*self.target.body.radius) 
            self.grabbing = True
        else:
            self.animate_grip(0.2) 
            self.grabbing = False
            
    def open_gripper(self):
        self.animate_grip(self.jaw_max_gap)
        self.grabbing = False

    def check_collision_with_sphere(self, position):
        # Sprawdź odległość rdzenia ramienia od kuli (targetu)
        sphere_pos = self.target.get_position()
        sphere_radius = self.target.body.radius

        # Oblicz pozycję rdzenia ramienia
        arm_base_pos = position  
        dist = mag(arm_base_pos - sphere_pos)  
        safety_distance = sphere_radius + 0.48
        if dist <= safety_distance:
            return True

        #kolizja ramienia
        grip_center = position + self.arm.up * (self.arm.size.y - self.gripper_base.size.y) / 2
        dist_grip = mag(grip_center - sphere_pos)
        if  dist_grip <= sphere_radius:
            return True

        # Sprawdź kolizję dla gripper_base
        gripper_base_pos = self.gripper_base.pos
        dist_gripper_base = mag(gripper_base_pos - sphere_pos)
        if dist_gripper_base <= sphere_radius:
            return True

        # Sprawdź kolizję dla jaw_left
        jaw_left_pos = self.jaw_left.pos
        dist_jaw_left = mag(jaw_left_pos - sphere_pos)
        if dist_jaw_left <= sphere_radius + 0.1:
            return True

        # Sprawdź kolizję dla jaw_right
        jaw_right_pos = self.jaw_right.pos
        dist_jaw_right = mag(jaw_right_pos - sphere_pos)
        if dist_jaw_right <= sphere_radius + 0.1:
            return True

        return False



    def handle_input(self, key):
        # Zachowaj kopię bieżących parametrów
        new_theta = self.theta
        new_z_pos = self.z_pos
        new_r = self.r

        # Oblicz aktualną pozycję ramienia i odległość od kuli
        old_pos = vector(self.r * math.cos(self.theta), self.z_pos + 0.5, self.r * math.sin(self.theta))
        old_dist = mag(old_pos - self.target.get_position())

        if key == 'left': new_theta -= 0.02
        elif key == 'right': new_theta += 0.02
        elif key == 'up': new_z_pos += 0.02
        elif key == 'down': new_z_pos -= 0.02
        elif key == 'w': new_r += 0.02
        elif key == 's': new_r -= 0.02
        elif key == 'z': 
            self.close_gripper()  # zaciskaj szczęki
            self.if_gripped = 1
        elif key == 'p': 
            self.open_gripper()   # otwieraj szczęki
            self.target.drop()  # Zainicjuj opadanie obiektu
            self.if_gripped = 2

        # Ograniczenia parametrów
        new_z_pos = max(-0.09, min(new_z_pos, 4))
        new_r = max(0.5, min(new_r, 2.5))
        new_theta = max(-0.9 * math.pi, min(new_theta, 0.9 * math.pi))

        # Oblicz pozycję ramienia po zmianie i nową odległość od kuli
        new_arm_pos = vector(new_r * math.cos(new_theta), new_z_pos + 0.5, new_r * math.sin(new_theta))
        new_dist = mag(new_arm_pos - self.target.get_position())

        # Sprawdź kolizję nowej pozycji
        is_collision = self.check_collision_with_sphere(new_arm_pos)

        if not is_collision:
            # Brak kolizji - zaakceptuj ruch
            self.theta = new_theta
            self.z_pos = new_z_pos
            self.r = new_r
        else:
            # Kolizja - pozwól ruch tylko jeśli odległość zwiększa się (czyli ruch OD kuli)
            if new_dist > old_dist:
                self.theta = new_theta
                self.z_pos = new_z_pos
                self.r = new_r
            else:
                print("Ruch zablokowany z powodu kolizji w tej trajektorii.")




    def record_play(self, key):
        if key == 'r':
            self.clear_moves()
            self.recording = True
            print("Nagrywanie ruchów")
            return

        elif key == 'k':
            self.recording = False
            print("Nagrywanie zakończone")
            self.mache_play()
            return

        # wykonaj ruch
        self.handle_input(key)

        # jeśli nagrywasz, zapisz aktualną pozycję
        if self.recording:
            self.mache_learn()

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
            new_r = sqrt(x * 2 + y * 2)  # promień
            if (0 < new_z_pos < 4) and (-0.9 * math.pi < new_theta < 0.9 * math.pi) and (0.5 < new_r < 2.5):
                # # Sprawdź kolizję na końcową pozycję
                # new_arm_pos = vector(new_r * math.cos(new_theta), new_z_pos + 0.5, new_r * math.sin(new_theta))
                # if self.check_collision_with_sphere(new_arm_pos):
                #    print("Pozycja w kolizji z kulą - ruch zablokowany")
                #    return

                while new_z_pos > self.z_pos:
                    self.z_pos += 0.02
                    self.update()
                    rate(60)
                    time.sleep(time_delay)

                while new_z_pos < self.z_pos:
                    self.z_pos -= 0.02
                    self.update()
                    rate(60)
                    time.sleep(time_delay)

                while new_theta > self.theta:
                    self.theta += 0.02
                    self.update()
                    rate(60)
                    time.sleep(time_delay)

                while new_theta < self.theta:
                    self.theta -= 0.02
                    self.update()
                    rate(60)
                    time.sleep(time_delay)

                while new_r > self.r:
                    self.r += 0.02
                    self.update()
                    rate(60)
                    time.sleep(time_delay)

                while new_r < self.r:
                    self.r -= 0.02
                    self.update()
                    rate(60)
                    time.sleep(time_delay)
            else:
                print("Współrzędne poza obszarem pracy")
        except:
            print("Błąd: podaj 3 liczby oddzielone spacjami.")

    def move_to_pos(self, move_z_pos, move_theta, move_r):
        if (move_z_pos >= 0 and move_z_pos <= 4) and (move_theta >= -0.9 * math.pi and move_theta <= 0.9 * math.pi) and (move_r >= 0.5 and move_r <= 2.5):
                while(move_z_pos > self.z_pos):
                    self.z_pos += 0.04
                    time.sleep(time_delay)

                while(move_z_pos < self.z_pos):
                    self.z_pos -= 0.04
                    time.sleep(time_delay)

                while(move_theta > self.theta):
                    self.theta += 0.04
                    time.sleep(time_delay)

                while(move_theta < self.theta):
                    self.theta -= 0.04
                    time.sleep(time_delay)

                while(move_r > self.r):
                    self.r += 0.04
                    time.sleep(time_delay)

                while(move_r < self.r):
                    self.r -= 0.04
                    time.sleep(time_delay)
        else:
            print("Wspolrzedne poza obszarem pracy")

    def mache_learn(self):  
        #self.handle_input(key)

        self.learn_z_pos.append(self.z_pos)
        self.learn_theta.append(self.theta)
        self.learn_r.append(self.r)
        self.learn_gripped.append(self.if_gripped)

    def mache_play(self):
        print("Odtwarzanie zapisanych ruchów:")
        for i, (r, theta, z) in enumerate(zip(self.learn_r, self.learn_theta, self.learn_z_pos)):
            print(f"{i+1}: r = {r:.2f}, θ = {theta:.2f}, z = {z:.2f}, if = {self.if_gripped}")
        self.move_to_pos(self.learn_z_pos[0], self.learn_theta[0], self.learn_r[0])

        time.sleep(2 * time_delay)

        for i, (r, theta, z) in enumerate(zip(self.learn_r, self.learn_theta, self.learn_z_pos)):
            self.r = self.learn_r[i]
            self.theta = self.learn_theta[i]
            self.z_pos = self.learn_z_pos[i]
            if self.learn_gripped[i] == 1:
                self.close_gripper()
            elif self.learn_gripped[i] ==2:
                self.open_gripper()
            time.sleep(time_delay)
            

    #po zapisanie wyczyść tablicę z zapisanymi ruchami
    def clear_moves(self):
        self.learn_r.clear()
        self.learn_theta.clear()
        self.learn_z_pos.clear()
        self.learn_gripped.clear()


# Inicjalizacja
target = TargetObject()
robot = CylindricalRobot(target)

# Podłoga
floor = box(pos=vector(0, -1.5, 0), size=vector(100, 3, 100), color=color.green)

def on_key(evt):
    robot.record_play(evt.key)

robot.pos_input()
scene.bind('keydown', on_key)

# Pętla główna
while True:
    rate(60)
    robot.update()
    target.update()
