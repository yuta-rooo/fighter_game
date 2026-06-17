from __future__ import annotations

from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent / "assets" / "sprites"
SIZE = (144, 144)
FEET_Y = 136

ANIMATIONS: dict[str, int] = {
    "idle": 4,
    "walk": 6,
    "jump": 3,
    "crouch": 2,
    "guard": 2,
    "hit": 3,
    "ko": 3,
    "light": 4,
    "heavy": 5,
    "special": 6,
}

CHARACTERS = {
    "player1": {"body": (220, 60, 60, 255), "accent": (255, 205, 80, 255)},
    "player2": {"body": (60, 120, 220, 255), "accent": (90, 240, 255, 255)},
}


def line(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], fill: tuple[int, int, int, int], width: int) -> None:
    draw.line(points, fill=fill, width=width, joint="curve")


def draw_fighter(character: str, animation: str, frame: int, count: int) -> Image.Image:
    colors = CHARACTERS[character]
    body = colors["body"]
    accent = colors["accent"]
    white = (248, 248, 248, 255)
    dark = (30, 30, 42, 255)

    image = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    phase = frame / max(1, count - 1)
    bob = 0
    torso_x = 72
    torso_y = 66
    head_y = 43
    left_foot = (57, FEET_Y)
    right_foot = (87, FEET_Y)
    left_hand = (43, 91)
    right_hand = (101, 91)
    pose = animation

    if pose == "idle":
        bob = (0, -2, 0, 2)[frame % 4]
    elif pose == "walk":
        swing = (-16, -9, 0, 16, 9, 0)[frame % 6]
        left_foot = (57 + swing, FEET_Y)
        right_foot = (87 - swing, FEET_Y)
        left_hand = (43 - swing // 2, 91)
        right_hand = (101 + swing // 2, 91)
        bob = -abs(swing) // 8
    elif pose == "jump":
        bob = (-8, -14, -8)[frame % 3]
        left_foot = (55, FEET_Y - 16)
        right_foot = (92, FEET_Y - 25)
        left_hand = (42, 77)
        right_hand = (104, 76)
    elif pose == "crouch":
        torso_y += 20
        head_y += 20
        left_foot = (52, FEET_Y)
        right_foot = (97, FEET_Y)
        left_hand = (42, 108)
        right_hand = (96, 104)
    elif pose == "guard":
        left_hand = (96, 58)
        right_hand = (107, 78)
    elif pose == "hit":
        torso_x -= 5 + frame * 4
        head_y += frame * 3
        left_hand = (36 - frame * 3, 82)
        right_hand = (86 - frame * 5, 100)
    elif pose == "ko":
        if frame >= 1:
            draw.ellipse((23, 117, 120, 137), fill=(0, 0, 0, 75))
            line(draw, [(35, 112), (78, 113), (113, 126)], body, 17)
            draw.ellipse((19, 98, 49, 128), fill=body)
            line(draw, [(76, 112), (102, 94)], body, 10)
            line(draw, [(84, 116), (113, 104)], body, 10)
            draw.ellipse((25, 106, 31, 112), fill=white)
            return image
    elif pose == "light":
        right_hand = (101 + int(31 * phase), 82)
    elif pose == "heavy":
        right_hand = (97 + int(39 * phase), 83 - int(13 * (1 - abs(phase - 0.5) * 2)))
        torso_x += int(7 * phase)
    elif pose == "special":
        right_hand = (100 + int(29 * phase), 82)
        radius = 8 + frame * 5
        cx, cy = right_hand[0] + 12, right_hand[1]
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=accent, width=4)
        if frame >= 3:
            draw.ellipse((cx - radius // 2, cy - radius // 2, cx + radius // 2, cy + radius // 2), fill=(*accent[:3], 110))

    torso_y += bob
    head_y += bob
    left_hand = (left_hand[0], left_hand[1] + bob)
    right_hand = (right_hand[0], right_hand[1] + bob)
    left_foot = (left_foot[0], left_foot[1] + bob)
    right_foot = (right_foot[0], right_foot[1] + bob)

    draw.ellipse((45, 129, 102, 140), fill=(0, 0, 0, 65))
    line(draw, [(torso_x - 9, torso_y + 36), left_foot], body, 11)
    line(draw, [(torso_x + 9, torso_y + 36), right_foot], body, 11)
    line(draw, [(torso_x - 15, torso_y + 6), left_hand], body, 10)
    line(draw, [(torso_x + 15, torso_y + 6), right_hand], body, 10)
    draw.rounded_rectangle((torso_x - 20, torso_y - 8, torso_x + 20, torso_y + 45), radius=10, fill=body)
    draw.ellipse((torso_x - 17, head_y - 17, torso_x + 17, head_y + 17), fill=body)
    draw.ellipse((torso_x + 4, head_y - 5, torso_x + 10, head_y + 1), fill=white)
    draw.rectangle((torso_x - 19, torso_y + 16, torso_x + 19, torso_y + 23), fill=accent)

    if pose == "guard":
        draw.arc((86, 46, 127, 105), start=250, end=110, fill=accent, width=4)
    if pose == "light" and frame >= 2:
        line(draw, [(116, 72), (139, 67)], accent, 3)
        line(draw, [(116, 82), (142, 82)], accent, 3)
    if pose == "heavy" and frame >= 2:
        line(draw, [(119, 66), (141, 52)], accent, 4)
        line(draw, [(121, 78), (143, 75)], accent, 4)

    return image


def main() -> None:
    for character in CHARACTERS:
        for animation, count in ANIMATIONS.items():
            folder = ROOT / character / animation
            folder.mkdir(parents=True, exist_ok=True)
            for frame in range(count):
                image = draw_fighter(character, animation, frame, count)
                image.save(folder / f"{frame:03d}.png")
    print(f"Generated sample sprites under: {ROOT}")


if __name__ == "__main__":
    main()
