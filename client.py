from __future__ import annotations
import argparse
import json
import random
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Any
import pygame
from animation import AnimationPlayer
from arcade_effects import ArcadeEffects, draw_arcade_bar, draw_arcade_text
WIDTH, HEIGHT = (960, 540)
FPS = 60
GROUND_Y = 440
DEFAULT_SERVER_IP = '127.0.0.1'
DEFAULT_PORT = 5000

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='pygame fighting game client')
    parser.add_argument('--server-ip', default=DEFAULT_SERVER_IP, help='Server IPv4 address')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Server TCP port')
    parser.add_argument('--mode-label', default='ONLINE', help='Text displayed in the game UI')
    return parser.parse_args()
ARGS = parse_args()
SERVER_IP = ARGS.server_ip
PORT = ARGS.port
MODE_LABEL = ARGS.mode_label.upper()
ASSETS_ROOT = Path(__file__).resolve().parent / 'assets' / 'sprites'
SOUNDS_ROOT = Path(__file__).resolve().parent / 'assets' / 'sounds'
pygame.init()
try:
    pygame.mixer.init()
    MIXER_READY = True
except pygame.error:
    MIXER_READY = False
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f'Fighting Game Arcade - {MODE_LABEL}')
clock = pygame.time.Clock()
font_big = pygame.font.SysFont(None, 72, bold=True)
font_mid = pygame.font.SysFont(None, 44, bold=True)
font_small = pygame.font.SysFont(None, 26, bold=True)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
RED = (220, 60, 60)
BLUE = (60, 120, 220)
YELLOW = (255, 225, 75)
ORANGE = (255, 140, 60)
PURPLE = (180, 80, 255)
GRAY = (120, 120, 120)
CYAN = (80, 220, 255)
GREEN = (80, 240, 120)
DARK_BLUE = (16, 20, 36)
ATTACK_COLORS = {'LIGHT': YELLOW, 'HEAVY': ORANGE, 'SPECIAL': PURPLE}
sounds: dict[str, pygame.mixer.Sound] = {}
last_special_flags = [False, False]
last_phase = ''

def load_sound(name: str, filename: str, volume: float) -> None:
    if not MIXER_READY:
        return
    path = SOUNDS_ROOT / filename
    if not path.exists():
        return
    try:
        item = pygame.mixer.Sound(str(path))
        item.set_volume(volume)
        sounds[name] = item
    except pygame.error:
        pass

def play_sound(name: str) -> None:
    item = sounds.get(name)
    if item is not None:
        item.play()

def start_bgm() -> None:
    if not MIXER_READY:
        return
    path = SOUNDS_ROOT / 'bgm.wav'
    if not path.exists():
        return
    try:
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.set_volume(0.22)
        pygame.mixer.music.play(-1)
    except pygame.error:
        pass

def load_sounds() -> None:
    load_sound('hit', 'hit.wav', 0.55)
    load_sound('guard', 'guard.wav', 0.5)
    load_sound('special', 'special.wav', 0.62)
    load_sound('ko', 'ko.wav', 0.7)
    load_sound('round', 'round.wav', 0.58)
    start_bgm()

def process_snapshot_sounds(state: dict[str, Any]) -> None:
    global last_phase
    players = state.get('players', [])
    if len(players) >= 2:
        for i, player in enumerate(players[:2]):
            active = str(player.get('state')) == 'ATTACK' and str(player.get('attack_type')) == 'SPECIAL'
            if active and not last_special_flags[i]:
                play_sound('special')
            last_special_flags[i] = active
    phase = str(state.get('phase', ''))
    if phase != last_phase:
        if phase == 'ROUND_START':
            play_sound('round')
        elif phase in ('ROUND_OVER', 'MATCH_OVER'):
            play_sound('ko')
        last_phase = phase

def draw_boot_message(message: str) -> None:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    screen.fill(DARK_BLUE)
    draw_arcade_text(screen, message, (WIDTH // 2, HEIGHT // 2), font_mid, CYAN)
    pygame.display.flip()
    pygame.event.pump()

def create_socket() -> socket.socket:
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    return connection
sock = create_socket()
player_id: int | None = None
game_state: dict[str, Any] | None = None
connection_error = ''
state_lock = threading.Lock()
camera_shake = 0
last_event_id = 0
draw_hitboxes = False
caption_done = False
load_sounds()
draw_boot_message('LOADING SPRITES')
animators = {0: AnimationPlayer('player1', RED, ASSETS_ROOT), 1: AnimationPlayer('player2', BLUE, ASSETS_ROOT)}
effects = ArcadeEffects(WIDTH, HEIGHT, GROUND_Y)
draw_boot_message('READY')

def send_json(payload: dict[str, Any]) -> None:
    sock.sendall((json.dumps(payload, separators=(',', ':')) + '\n').encode('utf-8'))

def receive_loop() -> None:
    global player_id, game_state, connection_error
    buffer = ''
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                connection_error = 'Disconnected from server'
                return
            buffer += data.decode('utf-8')
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if not line.strip():
                    continue
                msg = json.loads(line)
                if msg.get('type') == 'welcome':
                    player_id = int(msg['player_id'])
                elif msg.get('type') == 'snapshot':
                    with state_lock:
                        game_state = msg
                elif msg.get('type') == 'error':
                    connection_error = str(msg.get('message', 'Server error'))
                    return
    except (ConnectionError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        connection_error = f'Connection error: {exc}'

def connect(retries: int=20, delay: float=0.15) -> bool:
    global connection_error, sock
    last_error: OSError | None = None
    for attempt in range(1, retries + 1):
        draw_boot_message(f'CONNECTING {SERVER_IP}:{PORT}  {attempt}/{retries}')
        try:
            sock.settimeout(0.8)
            sock.connect((SERVER_IP, PORT))
            sock.settimeout(None)
            connection_error = ''
            threading.Thread(target=receive_loop, daemon=True).start()
            return True
        except OSError as exc:
            last_error = exc
            try:
                sock.close()
            except OSError:
                pass
            sock = create_socket()
            time.sleep(delay)
    connection_error = f'Could not connect to {SERVER_IP}:{PORT} ({last_error})'
    return False

def current_input(keys: pygame.key.ScancodeWrapper) -> dict[str, Any]:
    return {'type': 'input', 'left': keys[pygame.K_a], 'right': keys[pygame.K_d], 'jump': keys[pygame.K_w], 'crouch': keys[pygame.K_s], 'guard': keys[pygame.K_q], 'light': keys[pygame.K_f], 'heavy': keys[pygame.K_g], 'special': keys[pygame.K_h]}

def process_server_events(state: dict[str, Any]) -> None:
    global last_event_id, camera_shake
    for event in state.get('events', []):
        event_id = int(event['id'])
        if event_id <= last_event_id:
            continue
        last_event_id = event_id
        if event.get('type') == 'HIT':
            attack_type = str(event['attack_type'])
            guarded = bool(event['guarded'])
            hitstop = int(event['hitstop'])
            x = float(event['x'])
            y = float(event['y'])
            facing = 1
            players = state.get('players', [])
            if len(players) >= 2:
                p1, p2 = (players[0], players[1])
                facing = 1 if float(p2['x']) > float(p1['x']) else -1
            effects.on_hit(x, y, attack_type, guarded, hitstop, facing)
            if guarded:
                play_sound('guard')
                camera_shake = max(camera_shake, 4)
            elif attack_type == 'LIGHT':
                play_sound('hit')
                camera_shake = max(camera_shake, 5)
            elif attack_type == 'HEAVY':
                play_sound('hit')
                camera_shake = max(camera_shake, 10)
            else:
                play_sound('hit')
                camera_shake = max(camera_shake, 15)

def update_effects() -> None:
    effects.update()

def draw_text(text: str, x: int, y: int, font: pygame.font.Font, color: tuple[int, int, int]=WHITE) -> None:
    image = font.render(text, True, color)
    screen.blit(image, image.get_rect(center=(x, y)))

def draw_guard_gauge(x: int, y: int, value: Any, reverse: bool=False) -> None:
    amount = max(0.0, min(100.0, float(value)))
    width = 280
    height = 10
    fill = int(width * amount / 100.0)
    pygame.draw.rect(screen, (20, 24, 36), (x, y, width, height), border_radius=4)
    if reverse:
        pygame.draw.rect(screen, CYAN, (x + width - fill, y, fill, height), border_radius=4)
    else:
        pygame.draw.rect(screen, CYAN, (x, y, fill, height), border_radius=4)
    pygame.draw.rect(screen, WHITE, (x, y, width, height), 1, border_radius=4)
    label = font_small.render('GUARD', True, WHITE)
    if reverse:
        screen.blit(label, (x + width - label.get_width(), y + 10))
    else:
        screen.blit(label, (x, y + 10))

def draw_background(ox: int, oy: int) -> None:
    screen.fill((16, 20, 36))
    pygame.draw.circle(screen, (235, 228, 180), (785 + ox // 5, 88 + oy // 5), 42)
    pygame.draw.circle(screen, (16, 20, 36), (770 + ox // 5, 78 + oy // 5), 42)
    for i in range(10):
        x = i * 105 - 45 + ox // 4
        h = 105 + i % 4 * 34
        color = (34 + i % 3 * 6, 40 + i % 2 * 6, 63)
        pygame.draw.rect(screen, color, (x, GROUND_Y - h + oy, 78, h))
        for wy in range(GROUND_Y - h + 18, GROUND_Y - 12, 27):
            light = (245, 205, 90) if (wy // 27 + i) % 2 == 0 else (70, 90, 130)
            pygame.draw.rect(screen, light, (x + 15, wy + oy, 10, 12))
            pygame.draw.rect(screen, light, (x + 46, wy + oy, 10, 12))
    pygame.draw.rect(screen, (90, 25, 35), (75 + ox // 2, 165 + oy // 2, 180, 54), border_radius=6)
    pygame.draw.rect(screen, (235, 200, 95), (75 + ox // 2, 165 + oy // 2, 180, 54), 3, border_radius=6)
    draw_arcade_text(screen, 'FIGHT', (165 + ox // 2, 193 + oy // 2), font_mid, YELLOW)
    pygame.draw.rect(screen, (86, 78, 72), (0, GROUND_Y + oy, WIDTH, HEIGHT - GROUND_Y))
    pygame.draw.rect(screen, (62, 56, 54), (0, GROUND_Y + oy, WIDTH, 26))
    for x in range(-120, WIDTH + 120, 80):
        pygame.draw.line(screen, (125, 112, 95), (x + ox % 80, GROUND_Y + oy), (x - 55 + ox % 80, HEIGHT + oy), 2)
    pygame.draw.line(screen, (250, 230, 170), (0, GROUND_Y + oy), (WIDTH, GROUND_Y + oy), 4)

def body_rect(player: dict[str, Any]) -> pygame.Rect:
    x, y = (int(float(player['x'])), int(float(player['y'])))
    if bool(player['crouch']):
        return pygame.Rect(x, y + 40, 50, 60)
    return pygame.Rect(x, y, 50, 100)

def draw_debug_hitboxes(player: dict[str, Any], ox: int, oy: int) -> None:
    pygame.draw.rect(screen, GREEN, body_rect(player).move(ox, oy), 2)
    attack_rect = player.get('attack_rect')
    if attack_rect:
        attack_color = ATTACK_COLORS.get(str(player.get('attack_type')), WHITE)
        pygame.draw.rect(screen, attack_color, pygame.Rect(*attack_rect).move(ox, oy), 2)

def draw_player(player: dict[str, Any], ox: int, oy: int) -> None:
    fighter_id = int(player['id'])
    x = int(float(player['x']))
    shadow_width = 90 if not bool(player.get('crouch')) else 70
    pygame.draw.ellipse(screen, (8, 8, 12), (x - 20 + ox, GROUND_Y - 10 + oy, shadow_width, 16))
    animator = animators[fighter_id]
    animator.update(player)
    if str(player.get('state')) == 'ATTACK' and str(player.get('attack_type')) == 'SPECIAL':
        if int(player.get('attack_timer', 0)) % 4 == 0:
            image = animator.image(player)
            pos = animator.draw_position(player, ox, oy)
            effects.add_afterimage(image, pos, int(player.get('facing', 1)))
    animator.draw(screen, player, ox, oy)
    if bool(player['guard']):
        rect = body_rect(player).inflate(52, 32).move(ox, oy)
        pygame.draw.ellipse(screen, CYAN, rect, 4)
        pygame.draw.ellipse(screen, WHITE, rect.inflate(-12, -8), 2)
    if str(player.get('state')) == 'GUARD_BREAK':
        draw_arcade_text(screen, 'GUARD BREAK', (x + 25 + ox, int(float(player['y'])) - 32 + oy), font_small, YELLOW)
    if draw_hitboxes:
        draw_debug_hitboxes(player, ox, oy)

def draw_ui(state: dict[str, Any]) -> None:
    players = state['players']
    p1, p2 = players
    draw_arcade_bar(screen, 34, 26, int(p1['hp']), 100, RED, '1P', 350, 30, reverse=False)
    draw_arcade_bar(screen, WIDTH - 384, 26, int(p2['hp']), 100, BLUE, '2P', 350, 30, reverse=True)
    draw_arcade_bar(screen, 34, 67, int(p1['meter']), 100, PURPLE, 'SUPER', 280, 16, reverse=False)
    draw_arcade_bar(screen, WIDTH - 314, 67, int(p2['meter']), 100, PURPLE, 'SUPER', 280, 16, reverse=True)
    draw_guard_gauge(34, 91, p1.get('guard_meter', 100), reverse=False)
    draw_guard_gauge(WIDTH - 314, 91, p2.get('guard_meter', 100), reverse=True)
    draw_arcade_text(screen, str(p1['round_wins']), (395, 42), font_mid, YELLOW)
    draw_arcade_text(screen, str(p2['round_wins']), (565, 42), font_mid, YELLOW)
    if player_id is not None:
        draw_text(f'YOU ARE {player_id + 1}P', WIDTH // 2, 28, font_small, WHITE)
    mode = str(state.get('mode', MODE_LABEL)).upper()
    difficulty = state.get('cpu_difficulty')
    if mode == 'CPU' and difficulty:
        draw_text(f'CPU BATTLE - {str(difficulty).upper()}', WIDTH // 2, 84, font_small, CYAN)
    else:
        draw_text('ONLINE BATTLE', WIDTH // 2, 84, font_small, CYAN)
    screen.blit(font_small.render('A/D move  W jump  S crouch  Q guard', True, WHITE), (32, 124))
    screen.blit(font_small.render('F light  G heavy  H special  R rematch  B hitboxes', True, WHITE), (32, 150))

def draw_game(state: dict[str, Any] | None) -> None:
    global camera_shake
    ox = oy = 0
    if camera_shake > 0:
        ox = random.randint(-camera_shake, camera_shake)
        oy = random.randint(-camera_shake, camera_shake)
        camera_shake -= 1
    draw_background(ox, oy)
    if state is None:
        draw_arcade_text(screen, 'WAITING FOR SERVER STATE', (WIDTH // 2, HEIGHT // 2), font_mid, CYAN)
        return
    process_server_events(state)
    process_snapshot_sounds(state)
    p1, p2 = state['players']
    if effects.super_timer > 0:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 4, 20, 70))
        screen.blit(overlay, (0, 0))
    draw_player(p1, ox, oy)
    draw_player(p2, ox, oy)
    effects.draw_world(screen, ox, oy)
    draw_ui(state)
    if int(p1['combo_count']) >= 2:
        draw_arcade_text(screen, f"{p1['combo_count']} COMBO!", (170, 230), font_mid, YELLOW)
    if int(p2['combo_count']) >= 2:
        draw_arcade_text(screen, f"{p2['combo_count']} COMBO!", (WIDTH - 170, 230), font_mid, YELLOW)
    phase = str(state['phase'])
    timer = int(state['phase_timer'])
    if int(state['connected']) < 2:
        draw_arcade_text(screen, 'WAITING FOR PLAYER 2', (WIDTH // 2, HEIGHT // 2), font_mid, CYAN)
    elif phase == 'ROUND_START':
        if timer > 30:
            draw_arcade_text(screen, 'READY', (WIDTH // 2, HEIGHT // 2), font_big, WHITE)
        else:
            draw_arcade_text(screen, 'FIGHT!', (WIDTH // 2, HEIGHT // 2), font_big, YELLOW)
    elif phase == 'ROUND_OVER':
        if int(p1['hp']) <= 0 and int(p2['hp']) <= 0:
            draw_arcade_text(screen, 'DRAW', (WIDTH // 2, HEIGHT // 2), font_big, WHITE)
        elif int(p1['hp']) <= 0:
            draw_arcade_text(screen, '2P ROUND WIN!', (WIDTH // 2, HEIGHT // 2), font_big, BLUE)
        else:
            draw_arcade_text(screen, '1P ROUND WIN!', (WIDTH // 2, HEIGHT // 2), font_big, RED)
    elif phase == 'MATCH_OVER':
        winner = '1P' if int(p1['round_wins']) >= 2 else '2P'
        draw_arcade_text(screen, f'{winner} MATCH WIN!', (WIDTH // 2, HEIGHT // 2), font_big, YELLOW)
        draw_arcade_text(screen, 'Press R for Rematch', (WIDTH // 2, HEIGHT // 2 + 62), font_mid, WHITE)
    effects.draw_screen_overlay(screen)

def main() -> None:
    global draw_hitboxes, caption_done
    connected = connect()
    running = True
    while running:
        clock.tick(FPS)
        if player_id is not None and (not caption_done):
            pygame.display.set_caption(f'Fighting Game Arcade - {MODE_LABEL} - {player_id + 1}P')
            caption_done = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and connected:
                    try:
                        send_json({'type': 'reset'})
                    except OSError:
                        pass
                elif event.key == pygame.K_b:
                    draw_hitboxes = not draw_hitboxes
        if connected and (not connection_error):
            try:
                send_json(current_input(pygame.key.get_pressed()))
            except OSError:
                pass
        with state_lock:
            state = game_state
        update_effects()
        draw_game(state)
        if draw_hitboxes:
            draw_text('DEBUG HITBOXES ON', WIDTH // 2, 172, font_small, GREEN)
        if connection_error:
            draw_text(connection_error, WIDTH // 2, HEIGHT // 2 + 100, font_small, ORANGE)
        pygame.display.flip()
    try:
        sock.close()
    except OSError:
        pass
    pygame.quit()
    sys.exit()
if __name__ == '__main__':
    main()
