from __future__ import annotations

import argparse
import json
import math
import random
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Any

import pygame

from animation import AnimationPlayer

WIDTH, HEIGHT = 960, 540
FPS = 60
GROUND_Y = 440
DEFAULT_SERVER_IP = "127.0.0.1"
DEFAULT_PORT = 5000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="pygame fighting game client")
    parser.add_argument(
        "--server-ip",
        default=DEFAULT_SERVER_IP,
        help="Server IPv4 address",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Server TCP port",
    )
    parser.add_argument(
        "--mode-label",
        default="ONLINE",
        help="Text displayed in the game UI",
    )
    return parser.parse_args()


ARGS = parse_args()
SERVER_IP = ARGS.server_ip
PORT = ARGS.port
MODE_LABEL = ARGS.mode_label.upper()
ASSETS_ROOT = Path(__file__).resolve().parent / "assets" / "sprites"

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f"Fighting Game v5.3 - {MODE_LABEL}")
clock = pygame.time.Clock()

font_big = pygame.font.SysFont(None, 64)
font_mid = pygame.font.SysFont(None, 40)
font_small = pygame.font.SysFont(None, 26)

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
RED = (220, 60, 60)
BLUE = (60, 120, 220)
YELLOW = (240, 220, 80)
ORANGE = (255, 140, 60)
PURPLE = (180, 80, 255)
GRAY = (120, 120, 120)
CYAN = (80, 220, 255)
GREEN = (80, 240, 120)

ATTACK_COLORS = {
    "LIGHT": YELLOW,
    "HEAVY": ORANGE,
    "SPECIAL": PURPLE,
}


def draw_boot_message(message: str) -> None:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((26, 30, 46))
    image = font_mid.render(message, True, WHITE)
    screen.blit(image, image.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
    pygame.display.flip()
    pygame.event.pump()


def create_socket() -> socket.socket:
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    return connection


sock = create_socket()

player_id: int | None = None
game_state: dict[str, Any] | None = None
connection_error = ""
state_lock = threading.Lock()

particles: list[dict[str, Any]] = []
hit_effects: list[dict[str, Any]] = []
camera_shake = 0
last_event_id = 0
draw_hitboxes = False


draw_boot_message("Loading sprites...")

animators = {
    0: AnimationPlayer("player1", RED, ASSETS_ROOT),
    1: AnimationPlayer("player2", BLUE, ASSETS_ROOT),
}

draw_boot_message("Sprites loaded")


def send_json(payload: dict[str, Any]) -> None:
    msg = json.dumps(payload, separators=(",", ":")) + "\n"
    sock.sendall(msg.encode("utf-8"))


def receive_loop() -> None:
    global player_id, game_state, connection_error

    buffer = ""

    try:
        while True:
            data = sock.recv(4096)

            if not data:
                connection_error = "Disconnected from server"
                return

            buffer += data.decode("utf-8")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)

                if not line.strip():
                    continue

                msg = json.loads(line)

                if msg.get("type") == "welcome":
                    player_id = int(msg["player_id"])

                elif msg.get("type") == "snapshot":
                    with state_lock:
                        game_state = msg

                elif msg.get("type") == "error":
                    connection_error = str(msg.get("message", "Server error"))
                    return

    except (
        ConnectionError,
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        connection_error = f"Connection error: {exc}"


def connect(retries: int = 20, delay: float = 0.15) -> bool:
    global connection_error, sock

    last_error: OSError | None = None

    for attempt in range(1, retries + 1):
        draw_boot_message(
            f"Connecting to {SERVER_IP}:{PORT} ... ({attempt}/{retries})"
        )

        try:
            sock.settimeout(0.8)
            sock.connect((SERVER_IP, PORT))
            sock.settimeout(None)
            connection_error = ""

            threading.Thread(
                target=receive_loop,
                daemon=True,
            ).start()

            return True

        except OSError as exc:
            last_error = exc

            try:
                sock.close()
            except OSError:
                pass

            sock = create_socket()
            time.sleep(delay)

    connection_error = f"Could not connect to {SERVER_IP}:{PORT} ({last_error})"
    return False


def current_input(keys: pygame.key.ScancodeWrapper) -> dict[str, Any]:
    return {
        "type": "input",
        "left": keys[pygame.K_a],
        "right": keys[pygame.K_d],
        "jump": keys[pygame.K_w],
        "crouch": keys[pygame.K_s],
        "guard": keys[pygame.K_q],
        "light": keys[pygame.K_f],
        "heavy": keys[pygame.K_g],
        "special": keys[pygame.K_h],
    }


def add_particles(
    x: float,
    y: float,
    color: tuple[int, int, int],
    count: int = 12,
) -> None:
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(2, 7)

        particles.append(
            {
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": random.randint(18, 32),
                "color": color,
                "size": random.randint(3, 7),
            }
        )


def add_hit_effect(
    x: float,
    y: float,
    color: tuple[int, int, int],
) -> None:
    hit_effects.append(
        {
            "x": x,
            "y": y,
            "radius": 10,
            "life": 12,
            "color": color,
        }
    )


def process_server_events(state: dict[str, Any]) -> None:
    global last_event_id, camera_shake

    for event in state.get("events", []):
        event_id = int(event["id"])

        if event_id <= last_event_id:
            continue

        last_event_id = event_id

        if event.get("type") == "HIT":
            attack_type = str(event["attack_type"])
            guarded = bool(event["guarded"])
            color = CYAN if guarded else ATTACK_COLORS.get(attack_type, WHITE)

            add_particles(
                float(event["x"]),
                float(event["y"]),
                color,
                8 if guarded else 18,
            )

            add_hit_effect(
                float(event["x"]),
                float(event["y"]),
                color,
            )

            camera_shake = max(
                camera_shake,
                4 if guarded else int(event["hitstop"]) + 4,
            )


def update_effects() -> None:
    for particle in particles[:]:
        particle["x"] += particle["vx"]
        particle["y"] += particle["vy"]
        particle["vy"] += 0.25
        particle["life"] -= 1

        if particle["life"] <= 0:
            particles.remove(particle)

    for effect in hit_effects[:]:
        effect["radius"] += 5
        effect["life"] -= 1

        if effect["life"] <= 0:
            hit_effects.remove(effect)


def draw_text(
    text: str,
    x: int,
    y: int,
    font: pygame.font.Font,
    color: tuple[int, int, int] = WHITE,
) -> None:
    image = font.render(text, True, color)
    screen.blit(image, image.get_rect(center=(x, y)))


def draw_bar(
    x: int,
    y: int,
    value: int,
    max_value: int,
    color: tuple[int, int, int],
    width: int = 300,
    height: int = 28,
) -> None:
    pygame.draw.rect(screen, BLACK, (x, y, width, height))

    value = max(0, min(value, max_value))

    pygame.draw.rect(
        screen,
        color,
        (x, y, width * value / max_value, height),
    )

    pygame.draw.rect(screen, WHITE, (x, y, width, height), 3)


def draw_background(ox: int, oy: int) -> None:
    screen.fill((26, 30, 46))

    pygame.draw.circle(
        screen,
        (230, 230, 200),
        (780 + ox // 4, 90 + oy // 4),
        42,
    )

    for i in range(8):
        x = i * 130 - 40 + ox // 3
        h = 120 + (i % 3) * 35

        pygame.draw.rect(
            screen,
            (45, 50, 70),
            (x, GROUND_Y - h + oy, 90, h),
        )

        for wy in range(GROUND_Y - h + 20, GROUND_Y - 10, 28):
            pygame.draw.rect(
                screen,
                (240, 220, 90),
                (x + 20, wy + oy, 10, 12),
            )
            pygame.draw.rect(
                screen,
                (240, 220, 90),
                (x + 55, wy + oy, 10, 12),
            )

    pygame.draw.rect(
        screen,
        GRAY,
        (0, GROUND_Y + oy, WIDTH, HEIGHT - GROUND_Y),
    )

    for x in range(0, WIDTH, 80):
        pygame.draw.line(
            screen,
            (90, 90, 90),
            (x + ox % 80, GROUND_Y + oy),
            (x - 40 + ox % 80, HEIGHT + oy),
            2,
        )

    pygame.draw.line(
        screen,
        WHITE,
        (0, GROUND_Y + oy),
        (WIDTH, GROUND_Y + oy),
        3,
    )


def body_rect(player: dict[str, Any]) -> pygame.Rect:
    x = int(float(player["x"]))
    y = int(float(player["y"]))

    if bool(player["crouch"]):
        return pygame.Rect(x, y + 40, 50, 60)

    return pygame.Rect(x, y, 50, 100)


def draw_debug_hitboxes(
    player: dict[str, Any],
    ox: int,
    oy: int,
) -> None:
    physics_rect = body_rect(player).move(ox, oy)
    pygame.draw.rect(screen, GREEN, physics_rect, 2)

    attack_rect = player.get("attack_rect")

    if attack_rect:
        attack_color = ATTACK_COLORS.get(
            str(player.get("attack_type")),
            WHITE,
        )

        pygame.draw.rect(
            screen,
            attack_color,
            pygame.Rect(*attack_rect).move(ox, oy),
            2,
        )


def draw_player(
    player: dict[str, Any],
    ox: int,
    oy: int,
) -> None:
    fighter_id = int(player["id"])
    x = int(float(player["x"]))

    pygame.draw.ellipse(
        screen,
        (10, 10, 10),
        (x - 10 + ox, GROUND_Y - 8 + oy, 70, 12),
    )

    animator = animators[fighter_id]
    animator.update(player)
    animator.draw(screen, player, ox, oy)

    if bool(player["guard"]):
        rect = body_rect(player).inflate(32, 22).move(ox, oy)
        pygame.draw.ellipse(screen, CYAN, rect, 3)

    if draw_hitboxes:
        draw_debug_hitboxes(player, ox, oy)


def draw_effects(ox: int, oy: int) -> None:
    for particle in particles:
        pygame.draw.circle(
            screen,
            particle["color"],
            (int(particle["x"] + ox), int(particle["y"] + oy)),
            particle["size"],
        )

    for effect in hit_effects:
        pygame.draw.circle(
            screen,
            effect["color"],
            (int(effect["x"] + ox), int(effect["y"] + oy)),
            effect["radius"],
            3,
        )


def draw_game(state: dict[str, Any] | None) -> None:
    global camera_shake

    ox = 0
    oy = 0

    if camera_shake > 0:
        ox = random.randint(-camera_shake, camera_shake)
        oy = random.randint(-camera_shake, camera_shake)
        camera_shake -= 1

    draw_background(ox, oy)

    if state is None:
        draw_text(
            "Waiting for server state...",
            WIDTH // 2,
            HEIGHT // 2,
            font_mid,
        )
        return

    process_server_events(state)

    players = state["players"]
    p1, p2 = players

    draw_bar(40, 30, int(p1["hp"]), 100, RED)
    draw_bar(WIDTH - 340, 30, int(p2["hp"]), 100, BLUE)

    draw_bar(40, 65, int(p1["meter"]), 100, PURPLE, 300, 16)
    draw_bar(WIDTH - 340, 65, int(p2["meter"]), 100, PURPLE, 300, 16)

    draw_player(p1, ox, oy)
    draw_player(p2, ox, oy)
    draw_effects(ox, oy)

    draw_text(str(p1["round_wins"]), 360, 42, font_mid)
    draw_text(str(p2["round_wins"]), 600, 42, font_mid)

    if player_id is not None:
        draw_text(
            f"YOU ARE {player_id + 1}P",
            WIDTH // 2,
            30,
            font_small,
        )

    mode = str(state.get("mode", MODE_LABEL)).upper()
    difficulty = state.get("cpu_difficulty")

    if mode == "CPU" and difficulty:
        draw_text(
            f"CPU BATTLE - {str(difficulty).upper()}",
            WIDTH // 2,
            82,
            font_small,
            CYAN,
        )
    else:
        draw_text(
            "ONLINE BATTLE",
            WIDTH // 2,
            82,
            font_small,
            CYAN,
        )

    screen.blit(
        font_small.render(
            "A/D move  W jump  S crouch  Q guard",
            True,
            WHITE,
        ),
        (40, 110),
    )

    screen.blit(
        font_small.render(
            "F light  G heavy  H special  R rematch  B hitboxes",
            True,
            WHITE,
        ),
        (40, 138),
    )

    if int(p1["combo_count"]) >= 2:
        draw_text(
            f"{p1['combo_count']} COMBO!",
            170,
            230,
            font_mid,
            YELLOW,
        )

    if int(p2["combo_count"]) >= 2:
        draw_text(
            f"{p2['combo_count']} COMBO!",
            WIDTH - 170,
            230,
            font_mid,
            YELLOW,
        )

    phase = str(state["phase"])
    timer = int(state["phase_timer"])

    if int(state["connected"]) < 2:
        draw_text(
            "WAITING FOR PLAYER 2",
            WIDTH // 2,
            HEIGHT // 2,
            font_mid,
        )

    elif phase == "ROUND_START":
        if timer > 30:
            draw_text(
                "READY",
                WIDTH // 2,
                HEIGHT // 2,
                font_big,
            )
        else:
            draw_text(
                "FIGHT!",
                WIDTH // 2,
                HEIGHT // 2,
                font_big,
                YELLOW,
            )

    elif phase == "ROUND_OVER":
        if int(p1["hp"]) <= 0 and int(p2["hp"]) <= 0:
            draw_text(
                "DRAW",
                WIDTH // 2,
                HEIGHT // 2,
                font_big,
            )

        elif int(p1["hp"]) <= 0:
            draw_text(
                "2P ROUND WIN!",
                WIDTH // 2,
                HEIGHT // 2,
                font_big,
            )

        else:
            draw_text(
                "1P ROUND WIN!",
                WIDTH // 2,
                HEIGHT // 2,
                font_big,
            )

    elif phase == "MATCH_OVER":
        winner = "1P" if int(p1["round_wins"]) >= 2 else "2P"

        draw_text(
            f"{winner} MATCH WIN!",
            WIDTH // 2,
            HEIGHT // 2,
            font_big,
        )

        draw_text(
            "Press R for Rematch",
            WIDTH // 2,
            HEIGHT // 2 + 55,
            font_mid,
        )


def main() -> None:
    global draw_hitboxes

    connected = connect()
    running = True
    caption_done = False

    while running:
        clock.tick(FPS)

        if player_id is not None and not caption_done:
            pygame.display.set_caption(
                f"Fighting Game v5.3 - {MODE_LABEL} - {player_id + 1}P"
            )
            caption_done = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and connected:
                    try:
                        send_json({"type": "reset"})
                    except OSError:
                        pass

                elif event.key == pygame.K_b:
                    draw_hitboxes = not draw_hitboxes

        if connected and not connection_error:
            try:
                send_json(current_input(pygame.key.get_pressed()))
            except OSError:
                pass

        with state_lock:
            state = game_state

        update_effects()
        draw_game(state)

        if draw_hitboxes:
            draw_text(
                "DEBUG HITBOXES ON",
                WIDTH // 2,
                172,
                font_small,
                GREEN,
            )

        if connection_error:
            draw_text(
                connection_error,
                WIDTH // 2,
                HEIGHT // 2 + 100,
                font_small,
                ORANGE,
            )

        pygame.display.flip()

    try:
        sock.close()
    except OSError:
        pass

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()