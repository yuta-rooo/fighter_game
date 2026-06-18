from __future__ import annotations


import socket

import subprocess

import sys

import time

from pathlib import Path


import pygame


WIDTH, HEIGHT = 760, 610

FPS = 60

ONLINE_PORT = 5000

ROOT = Path(__file__).resolve().parent


pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption("Fighting Game Arcade - Mode Select")

clock = pygame.time.Clock()

font_big = pygame.font.SysFont(None, 64)

font_mid = pygame.font.SysFont(None, 36)

font_small = pygame.font.SysFont(None, 25)


WHITE = (245, 245, 245)

BLACK = (20, 20, 25)

DARK = (32, 36, 52)

PANEL = (54, 61, 84)

CYAN = (90, 220, 255)

YELLOW = (245, 218, 90)

RED = (235, 95, 95)

GREEN = (100, 225, 140)


class Button:

    def __init__(self, y: int, text: str, action: str) -> None:

        self.rect = pygame.Rect(160, y, 440, 54)

        self.text = text

        self.action = action


    def draw(self, mouse_pos: tuple[int, int]) -> None:

        color = CYAN if self.rect.collidepoint(mouse_pos) else PANEL

        pygame.draw.rect(screen, color, self.rect, border_radius=12)

        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=12)

        image = font_mid.render(self.text, True, BLACK if color == CYAN else WHITE)

        screen.blit(image, image.get_rect(center=self.rect.center))


BUTTONS = [

    Button(170, "1  CPU BATTLE - EASY", "cpu_easy"),

    Button(236, "2  CPU BATTLE - NORMAL", "cpu_normal"),

    Button(302, "3  CPU BATTLE - HARD", "cpu_hard"),

    Button(390, "4  ONLINE BATTLE - HOST", "online_host"),

    Button(456, "5  ONLINE BATTLE - JOIN", "online_join"),

]


def draw_text(text: str, x: int, y: int, font: pygame.font.Font, color: tuple[int, int, int] = WHITE) -> None:

    image = font.render(text, True, color)

    screen.blit(image, image.get_rect(center=(x, y)))


def free_local_port() -> int:

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:

        probe.bind(("127.0.0.1", 0))

        return int(probe.getsockname()[1])


def server_command(*, cpu: bool, port: int, difficulty: str = "normal") -> list[str]:

    command = [sys.executable, str(ROOT / "server.py"), "--host", "0.0.0.0", "--port", str(port)]

    if cpu:

        command += ["--cpu", "--difficulty", difficulty]

    return command


def client_command(server_ip: str, port: int, mode_label: str) -> list[str]:

    return [

        sys.executable,

        str(ROOT / "client.py"),

        "--server-ip",

        server_ip,

        "--port",

        str(port),

        "--mode-label",

        mode_label,

    ]


def stop_process(process: subprocess.Popen[bytes] | None) -> None:

    if process is None or process.poll() is not None:

        return

    process.terminate()

    try:

        process.wait(timeout=2)

    except subprocess.TimeoutExpired:

        process.kill()


def run_cpu_battle(difficulty: str) -> str:

    port = free_local_port()

    server = subprocess.Popen(server_command(cpu=True, port=port, difficulty=difficulty), cwd=ROOT)

    try:

        time.sleep(0.45)

        result = subprocess.run(client_command("127.0.0.1", port, f"CPU {difficulty.upper()}"), cwd=ROOT)

        if result.returncode != 0:

            return "CPU battle client closed with an error."

        return "CPU battle finished. Select another mode."

    finally:

        stop_process(server)


def run_online_host() -> str:

    server = subprocess.Popen(server_command(cpu=False, port=ONLINE_PORT), cwd=ROOT)

    try:

        print("\nONLINE HOST STARTED")

        print("Open another PC on the same LAN and select ONLINE JOIN.")

        print("Enter this host PC's IPv4 address. Check it with: ipconfig\n")

        time.sleep(0.45)

        result = subprocess.run(client_command("127.0.0.1", ONLINE_PORT, "ONLINE HOST"), cwd=ROOT)

        if result.returncode != 0:

            return "Online host client closed with an error."

        return "Online host session finished."

    finally:

        stop_process(server)


def run_online_join(server_ip: str) -> str:

    result = subprocess.run(client_command(server_ip, ONLINE_PORT, "ONLINE JOIN"), cwd=ROOT)

    if result.returncode != 0:

        return "Could not finish the online join session normally."

    return "Online session finished."


def draw_main(message: str) -> None:

    screen.fill(DARK)

    draw_text("PIXEL FIGHTER", WIDTH // 2, 70, font_big, YELLOW)

    draw_text("Select a game mode", WIDTH // 2, 118, font_mid, WHITE)

    mouse_pos = pygame.mouse.get_pos()

    for button in BUTTONS:

        button.draw(mouse_pos)

    draw_text("ESC: quit", WIDTH // 2, 548, font_small, WHITE)

    if message:

        draw_text(message, WIDTH // 2, 580, font_small, GREEN)


def draw_join(ip_text: str, message: str) -> None:

    screen.fill(DARK)

    draw_text("ONLINE JOIN", WIDTH // 2, 110, font_big, YELLOW)

    draw_text("Enter the host PC IPv4 address", WIDTH // 2, 185, font_mid)

    entry = pygame.Rect(145, 245, 470, 60)

    pygame.draw.rect(screen, PANEL, entry, border_radius=10)

    pygame.draw.rect(screen, CYAN, entry, 3, border_radius=10)

    draw_text(ip_text or "_", WIDTH // 2, 275, font_mid, WHITE)

    draw_text("ENTER: connect    ESC: back", WIDTH // 2, 360, font_small)

    if message:

        draw_text(message, WIDTH // 2, 410, font_small, RED)


def action_for_key(key: int) -> str | None:

    mapping = {

        pygame.K_1: "cpu_easy",

        pygame.K_2: "cpu_normal",

        pygame.K_3: "cpu_hard",

        pygame.K_4: "online_host",

        pygame.K_5: "online_join",

    }

    return mapping.get(key)


def main() -> None:

    screen_mode = "main"

    message = ""

    join_message = ""

    ip_text = "127.0.0.1"

    running = True


    while running:

        clock.tick(FPS)

        selected_action: str | None = None

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    if screen_mode == "join":

                        screen_mode = "main"

                        join_message = ""

                    else:

                        running = False

                elif screen_mode == "main":

                    selected_action = action_for_key(event.key)

                elif screen_mode == "join":

                    if event.key == pygame.K_RETURN:

                        if ip_text.strip():

                            pygame.display.iconify()

                            message = run_online_join(ip_text.strip())

                            pygame.display.set_mode((WIDTH, HEIGHT))

                            screen_mode = "main"

                        else:

                            join_message = "Enter an IPv4 address."

                    elif event.key == pygame.K_BACKSPACE:

                        ip_text = ip_text[:-1]

                    elif event.unicode and event.unicode in "0123456789.":

                        if len(ip_text) < 15:

                            ip_text += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and screen_mode == "main":

                for button in BUTTONS:

                    if button.rect.collidepoint(event.pos):

                        selected_action = button.action

                        break


        if selected_action:

            if selected_action.startswith("cpu_"):

                difficulty = selected_action.removeprefix("cpu_")

                pygame.display.iconify()

                message = run_cpu_battle(difficulty)

                pygame.display.set_mode((WIDTH, HEIGHT))

            elif selected_action == "online_host":

                pygame.display.iconify()

                message = run_online_host()

                pygame.display.set_mode((WIDTH, HEIGHT))

            elif selected_action == "online_join":

                screen_mode = "join"

                join_message = ""


        if screen_mode == "main":

            draw_main(message)

        else:

            draw_join(ip_text, join_message)

        pygame.display.flip()


    pygame.quit()


if __name__ == "__main__":

    main()

