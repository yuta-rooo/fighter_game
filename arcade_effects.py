from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from typing import Any
import pygame
WHITE = (255, 255, 255)
YELLOW = (255, 230, 90)
ORANGE = (255, 145, 55)
PURPLE = (190, 90, 255)
CYAN = (80, 220, 255)
RED = (255, 80, 80)
BLACK = (10, 10, 16)
ATTACK_COLORS = {'LIGHT': YELLOW, 'HEAVY': ORANGE, 'SPECIAL': PURPLE}

@dataclass
class Spark:
    x: float
    y: float
    vx: float
    vy: float
    life: int
    max_life: int
    color: tuple[int, int, int]
    size: int
    kind: str = 'dot'

@dataclass
class Ring:
    x: float
    y: float
    radius: float
    speed: float
    life: int
    max_life: int
    color: tuple[int, int, int]
    width: int = 4

@dataclass
class Slash:
    x: float
    y: float
    facing: int
    life: int
    max_life: int
    color: tuple[int, int, int]
    length: int
    thickness: int

@dataclass
class AfterImage:
    image: pygame.Surface
    pos: tuple[int, int]
    life: int
    max_life: int

@dataclass
class ArcadeEffects:
    width: int
    height: int
    ground_y: int
    rng: random.Random = field(default_factory=random.Random)

    def __post_init__(self) -> None:
        self.sparks: list[Spark] = []
        self.rings: list[Ring] = []
        self.slashes: list[Slash] = []
        self.afterimages: list[AfterImage] = []
        self.flash_timer = 0
        self.flash_color = WHITE
        self.super_timer = 0
        self.speed_lines_timer = 0

    def on_hit(self, x: float, y: float, attack_type: str, guarded: bool, hitstop: int, facing: int=1) -> None:
        color = CYAN if guarded else ATTACK_COLORS.get(attack_type, WHITE)
        if guarded:
            self._guard_burst(x, y)
            self.flash_timer = max(self.flash_timer, 2)
            self.flash_color = CYAN
            return
        if attack_type == 'LIGHT':
            self._hit_spark(x, y, color, count=18, power=6, size=4)
            self.rings.append(Ring(x, y, 10, 4.2, 10, 10, color, 3))
            self.flash_timer = max(self.flash_timer, 2)
            self.flash_color = color
        elif attack_type == 'HEAVY':
            self._hit_spark(x, y, color, count=34, power=9, size=6)
            self.rings.append(Ring(x, y, 12, 6.0, 14, 14, color, 5))
            self.slashes.append(Slash(x, y, facing, 12, 12, color, 118, 16))
            self.flash_timer = max(self.flash_timer, 3)
            self.flash_color = WHITE
        elif attack_type == 'SPECIAL':
            self._hit_spark(x, y, color, count=55, power=12, size=7)
            self.rings.append(Ring(x, y, 14, 7.5, 18, 18, color, 6))
            self.rings.append(Ring(x, y, 38, 5.0, 16, 16, CYAN, 4))
            self.slashes.append(Slash(x, y, facing, 16, 16, color, 165, 22))
            self.flash_timer = max(self.flash_timer, 5)
            self.flash_color = WHITE
            self.super_timer = max(self.super_timer, 12 + hitstop)
            self.speed_lines_timer = max(self.speed_lines_timer, 18)

    def add_afterimage(self, image: pygame.Surface, pos: tuple[int, int], facing: int) -> None:
        ghost = image.copy()
        ghost.fill((130, 210, 255, 95), special_flags=pygame.BLEND_RGBA_MULT)
        if facing < 0:
            ghost = pygame.transform.flip(ghost, True, False)
        self.afterimages.append(AfterImage(ghost, pos, 12, 12))

    def _hit_spark(self, x: float, y: float, color: tuple[int, int, int], count: int, power: float, size: int) -> None:
        for i in range(count):
            base = 0 if i % 2 == 0 else math.pi
            angle = base + self.rng.uniform(-0.75, 0.75)
            if i % 5 == 0:
                angle = self.rng.uniform(0, math.tau)
            speed = self.rng.uniform(power * 0.35, power)
            kind = 'line' if i % 3 == 0 else 'dot'
            life = self.rng.randint(12, 24)
            self.sparks.append(Spark(x, y, math.cos(angle) * speed, math.sin(angle) * speed, life, life, color, self.rng.randint(max(2, size - 2), size + 3), kind))

    def _guard_burst(self, x: float, y: float) -> None:
        for i in range(22):
            angle = math.tau / 22 * i
            speed = self.rng.uniform(2.5, 6.0)
            life = self.rng.randint(10, 18)
            self.sparks.append(Spark(x, y, math.cos(angle) * speed, math.sin(angle) * speed, life, life, CYAN, self.rng.randint(3, 6), 'dot'))
        self.rings.append(Ring(x, y, 18, 5.5, 12, 12, CYAN, 4))

    def update(self) -> None:
        for spark in self.sparks[:]:
            spark.x += spark.vx
            spark.y += spark.vy
            spark.vy += 0.22
            spark.vx *= 0.96
            spark.life -= 1
            if spark.life <= 0:
                self.sparks.remove(spark)
        for ring in self.rings[:]:
            ring.radius += ring.speed
            ring.life -= 1
            if ring.life <= 0:
                self.rings.remove(ring)
        for slash in self.slashes[:]:
            slash.life -= 1
            if slash.life <= 0:
                self.slashes.remove(slash)
        for ghost in self.afterimages[:]:
            ghost.life -= 1
            if ghost.life <= 0:
                self.afterimages.remove(ghost)
        self.flash_timer = max(0, self.flash_timer - 1)
        self.super_timer = max(0, self.super_timer - 1)
        self.speed_lines_timer = max(0, self.speed_lines_timer - 1)

    def draw_world(self, surface: pygame.Surface, ox: int=0, oy: int=0) -> None:
        for ghost in self.afterimages:
            alpha = int(120 * ghost.life / ghost.max_life)
            image = ghost.image.copy()
            image.set_alpha(alpha)
            surface.blit(image, (ghost.pos[0] + ox, ghost.pos[1] + oy))
        for slash in self.slashes:
            alpha = int(220 * slash.life / slash.max_life)
            temp = pygame.Surface((slash.length + 40, 80), pygame.SRCALPHA)
            points = [(20, 42), (slash.length, 8), (slash.length + 25, 24), (45, 64)]
            pygame.draw.polygon(temp, (*slash.color, alpha), points)
            pygame.draw.polygon(temp, (255, 255, 255, alpha), points, 2)
            if slash.facing < 0:
                temp = pygame.transform.flip(temp, True, False)
            surface.blit(temp, (int(slash.x - temp.get_width() // 2 + ox), int(slash.y - 40 + oy)))
        for ring in self.rings:
            alpha = int(220 * ring.life / ring.max_life)
            color = (*ring.color, alpha)
            temp_size = int(ring.radius * 2 + ring.width * 4)
            temp = pygame.Surface((temp_size, temp_size), pygame.SRCALPHA)
            center = temp_size // 2
            pygame.draw.circle(temp, color, (center, center), int(ring.radius), ring.width)
            surface.blit(temp, (int(ring.x - center + ox), int(ring.y - center + oy)))
        for spark in self.sparks:
            alpha = int(255 * spark.life / spark.max_life)
            color = (*spark.color, alpha)
            if spark.kind == 'line':
                temp = pygame.Surface((80, 80), pygame.SRCALPHA)
                start = (40, 40)
                end = (40 - int(spark.vx * 4), 40 - int(spark.vy * 4))
                pygame.draw.line(temp, color, start, end, spark.size)
                surface.blit(temp, (int(spark.x - 40 + ox), int(spark.y - 40 + oy)))
            else:
                temp = pygame.Surface((spark.size * 4, spark.size * 4), pygame.SRCALPHA)
                pygame.draw.circle(temp, color, (spark.size * 2, spark.size * 2), spark.size)
                surface.blit(temp, (int(spark.x - spark.size * 2 + ox), int(spark.y - spark.size * 2 + oy)))

    def draw_screen_overlay(self, surface: pygame.Surface) -> None:
        if self.super_timer > 0:
            dark = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            dark.fill((10, 6, 24, min(120, 35 + self.super_timer * 5)))
            surface.blit(dark, (0, 0))
        if self.speed_lines_timer > 0:
            temp = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            alpha = int(130 * self.speed_lines_timer / 18)
            for y in range(40, self.height - 60, 34):
                x0 = self.rng.randint(-80, 40)
                pygame.draw.line(temp, (150, 220, 255, alpha), (x0, y), (x0 + self.width // 2, y - 45), 3)
            surface.blit(temp, (0, 0))
        if self.flash_timer > 0:
            flash = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            alpha = int(95 * self.flash_timer / 5)
            flash.fill((*self.flash_color, max(35, alpha)))
            surface.blit(flash, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

def draw_arcade_bar(surface: pygame.Surface, x: int, y: int, value: int, max_value: int, fill_color: tuple[int, int, int], label: str, width: int=330, height: int=30, reverse: bool=False) -> None:
    value = max(0, min(value, max_value))
    ratio = value / max_value
    border = pygame.Rect(x - 4, y - 4, width + 8, height + 8)
    inner = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, (15, 15, 22), border, border_radius=7)
    pygame.draw.rect(surface, (235, 205, 115), border, 3, border_radius=7)
    pygame.draw.rect(surface, (40, 40, 48), inner, border_radius=5)
    fill_w = int(width * ratio)
    if reverse:
        fill_rect = pygame.Rect(x + width - fill_w, y, fill_w, height)
    else:
        fill_rect = pygame.Rect(x, y, fill_w, height)
    pygame.draw.rect(surface, fill_color, fill_rect, border_radius=5)
    highlight_h = max(3, height // 4)
    pygame.draw.rect(surface, (255, 255, 255), (fill_rect.x, fill_rect.y + 2, fill_rect.w, highlight_h))
    font = pygame.font.SysFont(None, 24, bold=True)
    text = font.render(label, True, WHITE)
    tx = x + 10 if not reverse else x + width - text.get_width() - 10
    surface.blit(text, (tx, y + 5))

def draw_arcade_text(surface: pygame.Surface, text: str, center: tuple[int, int], font: pygame.font.Font, color: tuple[int, int, int]=YELLOW) -> None:
    shadow = font.render(text, True, BLACK)
    image = font.render(text, True, color)
    outline_positions = [(-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2)]
    rect = image.get_rect(center=center)
    for dx, dy in outline_positions:
        surface.blit(shadow, rect.move(dx, dy))
    surface.blit(image, rect)
