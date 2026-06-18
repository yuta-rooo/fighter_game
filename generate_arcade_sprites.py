from __future__ import annotations


from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent

SPRITE_ROOT = ROOT / "assets" / "sprites"

SIZE = 192

FEET_Y = 178


STATES = {

    "idle": 4,

    "walk": 6,

    "jump": 3,

    "crouch": 3,

    "guard": 3,

    "hit": 3,

    "ko": 4,

    "light": 4,

    "heavy": 5,

    "special": 6,

}


PLAYER_COLORS = {

    "player1": {

        "main": (220, 55, 55, 255),

        "dark": (120, 28, 38, 255),

        "accent": (245, 230, 190, 255),

        "glove": (245, 245, 245, 255),

        "energy": (255, 210, 80, 255),

    },

    "player2": {

        "main": (55, 115, 225, 255),

        "dark": (24, 48, 120, 255),

        "accent": (230, 238, 255, 255),

        "glove": (245, 245, 245, 255),

        "energy": (100, 220, 255, 255),

    },

}


def line(draw: ImageDraw.ImageDraw, a, b, fill, width: int) -> None:

    draw.line([a, b], fill=fill, width=width)

    r = width // 2

    draw.ellipse((a[0] - r, a[1] - r, a[0] + r, a[1] + r), fill=fill)

    draw.ellipse((b[0] - r, b[1] - r, b[0] + r, b[1] + r), fill=fill)


def circle(draw: ImageDraw.ImageDraw, c, r, fill, outline=None, width=1) -> None:

    box = (c[0] - r, c[1] - r, c[0] + r, c[1] + r)

    draw.ellipse(box, fill=fill, outline=outline, width=width)


def rounded_rect(draw: ImageDraw.ImageDraw, xy, radius: int, fill, outline=None, width=1) -> None:

    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_fighter(state: str, frame: int, palette: dict[str, tuple[int, int, int, int]]) -> Image.Image:

    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    d = ImageDraw.Draw(img)


    main = palette["main"]

    dark = palette["dark"]

    accent = palette["accent"]

    glove = palette["glove"]

    energy = palette["energy"]


    cx = SIZE // 2

    bounce = 0

    lean = 0

    body_h = 62

    crouch = False


    if state == "idle":

        bounce = [-2, -1, 0, -1][frame % 4]

    elif state == "walk":

        bounce = [-2, 0, 2, 0, -2, 0][frame % 6]

        lean = [2, 5, 0, -2, -5, 0][frame % 6]

    elif state == "jump":

        bounce = [-24, -36, -28][frame % 3]

    elif state == "crouch":

        crouch = True

        body_h = 45

    elif state == "guard":

        lean = -4

    elif state == "hit":

        lean = -12

        bounce = [-2, 1, 0][frame % 3]

    elif state == "ko":


        y = FEET_Y - 16

        rounded_rect(d, (45, y - 28, 138, y + 4), 14, dark)

        rounded_rect(d, (50, y - 34, 143, y - 2), 14, main)

        circle(d, (142, y - 25), 17, main)

        line(d, (70, y - 24), (34, y - 42), glove, 14)

        line(d, (93, y - 10), (132, y + 12), dark, 16)

        line(d, (78, y - 7), (42, y + 8), dark, 16)

        return img

    elif state == "light":

        lean = 6 + frame * 2

    elif state == "heavy":

        lean = [0, 4, 14, 18, 8][frame % 5]

    elif state == "special":

        lean = [0, 6, 10, 14, 10, 4][frame % 6]

        bounce = -2


    feet_y = FEET_Y + bounce

    hip_y = feet_y - (42 if not crouch else 26)

    chest_y = hip_y - body_h

    head_y = chest_y - 24


    rounded_rect(d, (cx - 30 + lean + 4, chest_y + 4, cx + 30 + lean + 4, hip_y + 8), 14, dark)

    rounded_rect(d, (cx - 30 + lean, chest_y, cx + 30 + lean, hip_y + 4), 14, main)


    d.polygon([(cx - 26 + lean, chest_y + 4), (cx + lean, hip_y), (cx + 12 + lean, hip_y), (cx - 2 + lean, chest_y + 4)], fill=accent)


    circle(d, (cx + lean + 3, head_y + 3), 20, dark)

    circle(d, (cx + lean, head_y), 20, main)


    d.pieslice((cx - 22 + lean, head_y - 24, cx + 18 + lean, head_y + 4), 180, 360, fill=dark)

    circle(d, (cx + lean + 8, head_y - 2), 4, (255, 255, 255, 255))


    if state == "walk":

        leg_shift = [-14, -6, 10, 15, 6, -8][frame % 6]

    else:

        leg_shift = 0

    line(d, (cx - 16 + lean, hip_y), (cx - 36 - leg_shift, feet_y), dark, 17)

    line(d, (cx + 16 + lean, hip_y), (cx + 36 + leg_shift, feet_y), dark, 17)

    line(d, (cx - 16 + lean, hip_y), (cx - 38 - leg_shift, feet_y - 2), main, 13)

    line(d, (cx + 16 + lean, hip_y), (cx + 38 + leg_shift, feet_y - 2), main, 13)

    line(d, (cx - 42 - leg_shift, feet_y), (cx - 18 - leg_shift, feet_y), dark, 9)

    line(d, (cx + 28 + leg_shift, feet_y), (cx + 54 + leg_shift, feet_y), dark, 9)


    shoulder_l = (cx - 28 + lean, chest_y + 18)

    shoulder_r = (cx + 28 + lean, chest_y + 18)


    if state == "light":

        ext = [24, 48, 68, 42][frame % 4]

        line(d, shoulder_r, (cx + ext + lean, chest_y + 12), glove, 15)

        circle(d, (cx + ext + 10 + lean, chest_y + 10), 13, glove)

        line(d, shoulder_l, (cx - 54 + lean, chest_y + 36), glove, 13)

    elif state == "heavy":

        ext = [20, 38, 80, 92, 52][frame % 5]

        yoff = [5, -10, -22, -16, 0][frame % 5]

        line(d, shoulder_r, (cx + ext + lean, chest_y + yoff), glove, 19)

        circle(d, (cx + ext + 14 + lean, chest_y + yoff), 16, glove)

        line(d, shoulder_l, (cx - 52 + lean, chest_y + 38), glove, 14)

    elif state == "special":

        ext = [34, 55, 76, 92, 84, 64][frame % 6]

        line(d, shoulder_r, (cx + ext + lean, chest_y + 20), glove, 20)

        circle(d, (cx + ext + 24 + lean, chest_y + 20), 18, glove)


        radius = [12, 18, 25, 31, 25, 18][frame % 6]

        circle(d, (cx + ext + 48 + lean, chest_y + 20), radius + 8, (energy[0], energy[1], energy[2], 70))

        circle(d, (cx + ext + 48 + lean, chest_y + 20), radius, energy, outline=(255, 255, 255, 220), width=3)

        line(d, shoulder_l, (cx - 42 + lean, chest_y + 42), glove, 14)

    elif state == "guard":

        line(d, shoulder_r, (cx + 6 + lean, head_y + 8), glove, 17)

        line(d, shoulder_l, (cx - 8 + lean, head_y + 10), glove, 17)

        circle(d, (cx + 12 + lean, head_y + 6), 14, glove)

        circle(d, (cx - 12 + lean, head_y + 8), 14, glove)

    elif state == "hit":

        line(d, shoulder_r, (cx + 58 + lean, chest_y + 6), glove, 14)

        line(d, shoulder_l, (cx - 63 + lean, chest_y + 4), glove, 14)

    elif state == "crouch":

        line(d, shoulder_r, (cx + 52 + lean, chest_y + 34), glove, 14)

        line(d, shoulder_l, (cx - 48 + lean, chest_y + 36), glove, 14)

    else:

        arm_sway = [-6, -2, 4, 2, -4, 0][frame % 6] if state == "walk" else [-3, 1, 3, 1][frame % 4]

        line(d, shoulder_r, (cx + 55 + lean - arm_sway, chest_y + 40), glove, 14)

        line(d, shoulder_l, (cx - 55 + lean + arm_sway, chest_y + 42), glove, 14)


    return img


def generate() -> None:

    for player, palette in PLAYER_COLORS.items():

        for state, count in STATES.items():

            folder = SPRITE_ROOT / player / state

            folder.mkdir(parents=True, exist_ok=True)

            for old in folder.glob("*.png"):

                old.unlink()

            for i in range(count):

                draw_fighter(state, i, palette).save(folder / f"{i:03d}.png")

    print(f"Generated arcade sprites under: {SPRITE_ROOT}")


if __name__ == "__main__":

    generate()

