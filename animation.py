from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pygame

ANIMATION_CONFIG: dict[str, dict[str, int | bool]] = {
    "IDLE": {"frame_duration": 12, "loop": True},
    "WALK": {"frame_duration": 6, "loop": True},
    "JUMP": {"frame_duration": 8, "loop": False},
    "CROUCH": {"frame_duration": 10, "loop": True},
    "GUARD": {"frame_duration": 8, "loop": True},
    "HIT": {"frame_duration": 5, "loop": False},
    "KO": {"frame_duration": 10, "loop": False},
    "LIGHT": {"frame_duration": 4, "loop": False},
    "HEAVY": {"frame_duration": 5, "loop": False},
    "SPECIAL": {"frame_duration": 6, "loop": False},
}

SPRITE_SIZE = (144, 144)
SPRITE_FEET_OFFSET = 8


def animation_key(player: dict[str, Any]) -> str:
    state = str(player.get("state", "IDLE"))
    if state == "ATTACK":
        attack_type = str(player.get("attack_type") or "LIGHT")
        return attack_type if attack_type in {"LIGHT", "HEAVY", "SPECIAL"} else "LIGHT"
    return state if state in ANIMATION_CONFIG else "IDLE"


def _fallback_frame(label: str, color: tuple[int, int, int], frame_index: int) -> pygame.Surface:
    surface = pygame.Surface(SPRITE_SIZE, pygame.SRCALPHA)
    center_x = SPRITE_SIZE[0] // 2
    feet_y = SPRITE_SIZE[1] - SPRITE_FEET_OFFSET
    body_y = feet_y - 78

    pygame.draw.circle(surface, color, (center_x, body_y - 18), 15)
    pygame.draw.rect(surface, color, (center_x - 18, body_y - 4, 36, 54), border_radius=8)

    sway = -5 if frame_index % 2 == 0 else 5
    pygame.draw.line(surface, color, (center_x - 7, body_y + 48), (center_x - 13 + sway, feet_y), 9)
    pygame.draw.line(surface, color, (center_x + 7, body_y + 48), (center_x + 13 - sway, feet_y), 9)
    pygame.draw.line(surface, color, (center_x - 16, body_y + 8), (center_x - 36, body_y + 26), 8)
    pygame.draw.line(surface, color, (center_x + 16, body_y + 8), (center_x + 36, body_y + 26), 8)

    font = pygame.font.SysFont(None, 17)
    text = font.render(label, True, (255, 255, 255))
    surface.blit(text, text.get_rect(center=(center_x, 15)))
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
            # Continue loading other frames. Missing or invalid frames do not crash a match.
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
            name: _load_frames(self.assets_root / self.character_name / name.lower(), name, self.fallback_color)
            for name in ANIMATION_CONFIG
        }
        self.current_animation = "IDLE"
        self.elapsed_frames = 0

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

    def draw(self, surface: pygame.Surface, player: dict[str, Any], ox: int = 0, oy: int = 0) -> None:
        image = self.image(player)
        body_x = int(float(player["x"]))
        body_y = int(float(player["y"]))
        body_w, body_h = 50, 100
        draw_x = body_x + body_w // 2 - image.get_width() // 2 + ox
        draw_y = body_y + body_h - image.get_height() + SPRITE_FEET_OFFSET + oy
        surface.blit(image, (draw_x, draw_y))
