from vpython import *
import math

# Scena
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

# Parametry
theta = 0         # obrót wokół osi Z
z_pos = 1         # pozycja góra/dół
r = 2             # promień ramienia
grabbing = False

# Podstawa
base = cylinder(pos=vector(0, 0, 0), axis=vector(0, 0.1, 0), radius=1.5, color=color.gray(0.5))

# Część poruszająca się w górę
vertical = cylinder(pos=vector(0, z_pos, 0), axis=vector(0, 5, 0), radius=1, color=color.blue)

# Ramię poziome
arm = box(pos=vector(r, z_pos + 0.5, 0), size=vector(2, 0.2, 0.2), color=color.orange)

# Końcówka
# Szczęki chwytaka
jaw_gap = 0.15  # odległość szczęk od osi
jaw_size = vector(0.2, 1, 0.004)

jaw_left = box(pos=vector(0, 0, 0), size=jaw_size, color=color.red)
jaw_right = box(pos=vector(0, 0, 0), size=jaw_size, color=color.red)


# Obiekt do złapania
target = box(pos=vector(3, 0.2, 0), size=vector(0.4, 0.4, 0.4), color=color.green)

# Podłoga
floor = box(pos=vector(0, -1.5, 0), size=vector(100, 3, 100), color=color.gray(0.9))

def update_robot():
    global arm, jaw_left, jaw_right

    # Pozycja pionowa
    vertical.pos = vector(0, z_pos, 0)

    # Pozycja i orientacja ramienia
    arm.pos = vector(r * math.cos(theta), z_pos + 0.5, r * math.sin(theta))
    arm.axis = vector(math.cos(theta), 0, math.sin(theta)) * 2

    # Pozycja końca ramienia (punkt wyjściowy dla chwytaka)
    end_pos = arm.pos + norm(arm.axis)

    # Wektor prostopadły do ramienia (dla szczęk)
    side = cross(arm.axis, vector(0, 1, 0))  # prostopadły wektor do ramienia

    # Środek między szczękami (punkt końca ramienia)
    grip_center = end_pos
    side_norm = norm(side)

    # Lewa i prawa szczęka po przeciwnych stronach środka
    jaw_left.pos = grip_center + side_norm * (jaw_gap / 2)
    jaw_right.pos = grip_center - side_norm * (jaw_gap / 2)

    # Ustawienie osi szczęk wzdłuż osi pionowej (ew. zmień wg potrzeby)
    jaw_left.axis = norm(arm.axis)
    jaw_right.axis = norm(arm.axis)

def animate_grip(target_gap, step=0.01):
    global jaw_gap
    while abs(jaw_gap - target_gap) > 0.01:
        jaw_gap += step if jaw_gap < target_gap else -step
        update_robot()
        rate(60)


def grab_release():
    global grabbing, jaw_gap

    # Wektor między szczękami
    jaw_vec = jaw_right.pos - jaw_left.pos
    jaw_dir = norm(jaw_vec)
    jaw_len = mag(jaw_vec)

    # Wektor od lewej szczęki do obiektu
    obj_vec = target.pos - jaw_left.pos

    # Projekcja wektora obiektu na linię szczęk
    proj_len = dot(obj_vec, jaw_dir)

    # Odległość od osi szczęk (czyli jak bardzo obiekt "odbiega" od tej linii)
    perp_dist = mag(obj_vec - proj_len * jaw_dir)

    # Warunki: obiekt mieści się między szczękami i jest blisko ich osi
    if not grabbing and 0 < proj_len < jaw_len and perp_dist < 0.2:
        grabbing = True
        jaw_gap = 0.05
    else:
        grabbing = False
        jaw_gap = 0.2





def move_target():
    if grabbing:
        # Umieszczamy obiekt między szczękami
        target.pos = (jaw_left.pos + jaw_right.pos) / 2


# Obsługa klawiatury
def key_input(evt):
    global theta, z_pos, r
    s = evt.key
    if s == 'left': theta -= 0.1
    elif s == 'right': theta += 0.1
    elif s == 'up': z_pos += 0.1
    elif s == 'down': z_pos -= 0.1
    elif s == 'w': r += 0.1
    elif s == 's': r -= 0.1
    elif s == ' ': grab_release()

    # Ograniczenia
    if z_pos < 0: z_pos = 0
    if r < 0.5: r = 0.5
    if r > 4: r = 4
    if z_pos > 4: z_pos = 4
    if theta > 2 * math.pi: theta -= 2 * math.pi
    if theta < 0: theta += 2 * math.pi

scene.bind('keydown', key_input)

# Pętla główna
while True:
    rate(60)
    update_robot()
    move_target()
