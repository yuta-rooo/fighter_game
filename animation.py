from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import pygame

ANIMATION_CONFIG: dict[str, dict[str, int | bool | tuple[int, int]]] = {
    "IDLE": {"frame_duration": 10, "loop": True, "offset": (0, 0)},
    "WALK": {"frame_duration": 4, "loop": True, "offset": (0, 0)},
    "JUMP": {"frame_duration": 6, "loop": False, "offset": (0, -8)},
    "CROUCH": {"frame_duration": 8, "loop": True, "offset": (0, 8)},
    "GUARD": {"frame_duration": 5, "loop": True, "offset": (0, 0)},
    "HIT": {"frame_duration": 4, "loop": False, "offset": (0, 0)},
    "KO": {"frame_duration": 9, "loop": False, "offset": (0, 12)},
    "LIGHT": {"frame_duration": 3, "loop": False, "offset": (8, 0)},
    "HEAVY": {"frame_duration": 4, "loop": False, "offset": (12, 0)},
    "SPECIAL": {"frame_duration": 4, "loop": False, "offset": (16, -2)},
}

SPRITE_SIZE = (192, 192)
SPRITE_FEET_OFFSET = 12

def animation_key(player: dict[str, Any]) -> str:
    state = str(player.get("state", "IDLE"))
    if state == "ATTACK":
        attack_type = str(player.get("attack_type") or "LIGHT")
        return attack_type if attack_type in {"LIGHT", "HEAVY", "SPECIAL"} else "LIGHT"
    return state if state in ANIMATION_CONFIG else "IDLE"

def _fallback_frame(label: str, color: tuple[int, int, int], frame_index: int) -> pygame.Surface:
    surface = pygame.Surface(SPRITE_SIZE, pygame.SRCALPHA)
    cx = SPRITE_SIZE[0] // 2
    feet_y = SPRITE_SIZE[1] - SPRITE_FEET_OFFSET
    bounce = -2 if frame_index % 2 == 0 else 2
    head = (cx, feet_y - 112 + bounce)
    torso = pygame.Rect(cx - 28, feet_y - 95 + bounce, 56, 62)
    dark = tuple(max(0, c - 65) for c in color)
    glove = (245, 245, 245)

    pygame.draw.circle(surface, dark, (head[0] + 4, head[1] + 4), 18)
    pygame.draw.circle(surface, color, head, 18)
    pygame.draw.rect(surface, dark, torso.move(5, 5), border_radius=12)
    pygame.draw.rect(surface, color, torso, border_radius=12)

    if label == "LIGHT":
        pygame.draw.line(surface, glove, (cx + 22, feet_y - 83), (cx + 75, feet_y - 92), 14)
        pygame.draw.circle(surface, glove, (cx + 82, feet_y - 93), 12)
        pygame.draw.line(surface, color, (cx - 20, feet_y - 82), (cx - 48, feet_y - 66), 13)

    elif label == "HEAVY":
        pygame.draw.line(surface, glove, (cx + 22, feet_y - 85), (cx + 95, feet_y - 110), 18)
        pygame.draw.circle(surface, glove, (cx + 104, feet_y - 113), 15)
        pygame.draw.line(surface, color, (cx - 20, feet_y - 84), (cx - 52, feet_y - 52), 14)

    elif label == "SPECIAL":
        pygame.draw.line(surface, (120, 230, 255), (cx + 20, feet_y - 82), (cx + 95, feet_y - 82), 20)
        pygame.draw.circle(surface, (150, 230, 255), (cx + 112, feet_y - 82), 26, 5)
        pygame.draw.circle(surface, (255, 255, 255), (cx + 112, feet_y - 82), 12)

    elif label == "GUARD":
        pygame.draw.line(surface, glove, (cx - 18, feet_y - 82), (cx + 8, feet_y - 112), 16)
        pygame.draw.line(surface, glove, (cx + 18, feet_y - 82), (cx - 8, feet_y - 112), 16)

    else:
        sway = -8 if frame_index % 2 == 0 else 8
        pygame.draw.line(surface, glove, (cx - 25, feet_y - 80), (cx - 55 + sway, feet_y - 55), 13)
        pygame.draw.line(surface, glove, (cx + 25, feet_y - 80), (cx + 55 - sway, feet_y - 55), 13)

    pygame.draw.line(surface, dark, (cx - 14, feet_y - 34), (cx - 35, feet_y - 2), 16)
    pygame.draw.line(surface, dark, (cx + 14, feet_y - 34), (cx + 35, feet_y - 2), 16)
    pygame.draw.line(surface, color, (cx - 16, feet_y - 35), (cx - 38, feet_y - 4), 14)
    pygame.draw.line(surface, color, (cx + 16, feet_y - 35), (cx + 38, feet_y - 4), 14)

    pygame.draw.circle(surface, (255, 255, 255), (cx + 7, head[1] - 3), 4)

    font = pygame.font.SysFont(None, 18, bold=True)
    text = font.render(label, True, (255, 255, 255))
    surface.blit(text, text.get_rect(center=(cx, 16)))

    return surface

def _load_frames(folder: Path, label: str, fallback_color: tuple[int, int, int]) -> list[pygame.Surface]:
    files = sorted(folder.glob("*.png")) if folder.exists() else []
    frames: list[pygame.Surface] = []
    for file_path in files:
        try:
            image = pygame.image.load(file_path).convert_alpha()
            
            if image.get_size() != SPRITE_SIZE:
                image = pygame.transform.smoothscale(image, SPRITE_SIZE)

            frames.append(image)

        except (pygame.error, OSError):
            continue

    if frames:
        return frames

    return [_fallback_frame(label, fallback_color, 0), _fallback_frame(label, fallback_color, 1)]

@dataclass
class AnimationPlayer:
    character_name: str
    fallback_color: tuple[int, int, int]
    assets_root: Path

    def __post_init__(self) -> None:
        self.frames: dict[str, list[pygame.Surface]] = {
            name: _load_frames(
                self.assets_root / self.character_name / name.lower(),
                name,
                self.fallback_color,
            )
            for name in ANIMATION_CONFIG
        }

        self.current_animation = "IDLE"
        self.elapsed_frames = 0
        self.last_draw_rect = pygame.Rect(0, 0, *SPRITE_SIZE)

    def update(self, player: dict[str, Any]) -> None:
        new_animation = animation_key(player)
        if new_animation != self.current_animation:
            self.current_animation = new_animation
            self.elapsed_frames = 0
        else:
            self.elapsed_frames += 1

    def _frame_index(self, player: dict[str, Any]) -> int:
        frames = self.frames[self.current_animation]
        config = ANIMATION_CONFIG[self.current_animation]
        duration = max(1, int(config["frame_duration"]))

        if self.current_animation in {"LIGHT", "HEAVY", "SPECIAL"}:
            timer = max(0, int(player.get("attack_timer", 0)))
        else:
            timer = self.elapsed_frames

        index = timer // duration

        if bool(config["loop"]):
            return index % len(frames)

        return min(index, len(frames) - 1)

    def image(self, player: dict[str, Any]) -> pygame.Surface:
        image = self.frames[self.current_animation][self._frame_index(player)]
        if int(player.get("facing", 1)) < 0:
            return pygame.transform.flip(image, True, False)
        return image

    def draw_position(self, player: dict[str, Any], ox: int = 0, oy: int = 0) -> tuple[int, int]:
        image = self.image(player)
        body_x = int(float(player["x"]))
        body_y = int(float(player["y"]))
        body_w, body_h = 50, 100
        facing = int(player.get("facing", 1))

        config = ANIMATION_CONFIG[self.current_animation]
        offset = config.get("offset", (0, 0))
        offset_x, offset_y = offset if isinstance(offset, tuple) else (0, 0)

        draw_x = body_x + body_w // 2 - image.get_width() // 2 + ox + offset_x * facing
        draw_y = body_y + body_h - image.get_height() + SPRITE_FEET_OFFSET + oy + offset_y

        return int(draw_x), int(draw_y)

    def draw(self, surface: pygame.Surface, player: dict[str, Any], ox: int = 0, oy: int = 0) -> None:
        image = self.image(player)
        pos = self.draw_position(player, ox, oy)
        self.last_draw_rect = pygame.Rect(pos[0], pos[1], image.get_width(), image.get_height())

        if self.current_animation == "SPECIAL":
            glow = image.copy()
            glow.fill((90, 190, 255, 120), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(glow, (pos[0] - 2, pos[1] - 2), special_flags=pygame.BLEND_RGBA_ADD)

        surface.blit(image, pos)

