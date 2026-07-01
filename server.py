from __future__ import annotations


import argparse

import json

import socket

import threading

import time

from dataclasses import dataclass, field

from typing import Any


from cpu_controller import CPUController


HOST = "0.0.0.0"

PORT = 5000

FPS = 60

CPU_MODE = False

CPU_DIFFICULTY = "normal"

WIDTH, HEIGHT = 960, 540

GROUND_Y = 440

PLAYER_W, PLAYER_H = 50, 100

ROUND_START_FRAMES = 90

ROUND_END_FRAMES = 120

ROUNDS_TO_WIN = 2


ATTACKS: dict[str, dict[str, int]] = {

    "LIGHT": {

        "damage": 8,

        "startup": 5,

        "active": 4,

        "recovery": 10,

        "knockback": 6,

        "width": 45,

        "height": 25,

        "y_offset": 35,

        "hitstop": 4,

        "meter_gain": 10,

    },

    "HEAVY": {

        "damage": 18,

        "startup": 12,

        "active": 6,

        "recovery": 18,

        "knockback": 12,

        "width": 70,

        "height": 35,

        "y_offset": 25,

        "hitstop": 8,

        "meter_gain": 14,

    },

    "SPECIAL": {

        "damage": 25,

        "startup": 18,

        "active": 8,

        "recovery": 26,

        "knockback": 18,

        "width": 110,

        "height": 45,

        "y_offset": 20,

        "hitstop": 10,

        "meter_gain": 0,

        "meter_cost": 30,

    },

}


EMPTY_INPUT = {

    "left": False,

    "right": False,

    "jump": False,

    "crouch": False,

    "guard": False,

    "light": False,

    "heavy": False,

    "special": False,

}


def rects_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:

    ax, ay, aw, ah = a

    bx, by, bw, bh = b

    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


@dataclass

class Player:

    player_id: int

    spawn_x: float

    x: float = 0.0

    y: float = 0.0

    vx: float = 0.0

    vy: float = 0.0

    hp: int = 100

    meter: int = 0

    facing: int = 1

    on_ground: bool = True

    state: str = "IDLE"

    guard: bool = False

    crouch: bool = False

    attack_type: str | None = None

    attack_timer: int = 0

    attack_hit: bool = False

    hit_timer: int = 0

    combo_count: int = 0

    combo_timer: int = 0

    guard_meter: float = 100.0

    guard_break_timer: int = 0

    round_wins: int = 0


    speed: float = 5.0

    gravity: float = 0.8

    jump_power: float = -16.0


    def __post_init__(self) -> None:

        self.reset_round()


    def reset_round(self) -> None:

        self.x = self.spawn_x

        self.y = GROUND_Y - PLAYER_H

        self.vx = 0.0

        self.vy = 0.0

        self.hp = 100

        self.meter = 0

        self.facing = 1 if self.player_id == 0 else -1

        self.on_ground = True

        self.state = "IDLE"

        self.guard = False

        self.crouch = False

        self.attack_type = None

        self.attack_timer = 0

        self.attack_hit = False

        self.hit_timer = 0

        self.combo_count = 0

        self.combo_timer = 0

        self.guard_meter = 100.0

        self.guard_break_timer = 0


    def body_rect(self) -> tuple[float, float, float, float]:

        if self.crouch:

            return (self.x, self.y + 40, PLAYER_W, 60)

        return (self.x, self.y, PLAYER_W, PLAYER_H)


    def attack_rect(self) -> tuple[float, float, float, float] | None:

        if self.attack_type is None:

            return None

        data = ATTACKS[self.attack_type]

        width = data["width"]

        height = data["height"]

        y = self.y + data["y_offset"]

        if self.facing == 1:

            return (self.x + PLAYER_W, y, width, height)

        return (self.x - width, y, width, height)


    def attack_is_active(self) -> bool:

        if self.state != "ATTACK" or self.attack_type is None:

            return False

        data = ATTACKS[self.attack_type]

        first_active = data["startup"]

        last_active = data["startup"] + data["active"] - 1

        return first_active <= self.attack_timer <= last_active


    def start_attack(self, attack_type: str) -> None:

        self.state = "ATTACK"

        self.attack_type = attack_type

        self.attack_timer = 0

        self.attack_hit = False

        self.vx = 0.0


    def update_input(self, inp: dict[str, bool], pressed: dict[str, bool]) -> None:

        if self.hp <= 0 or self.state in {"ATTACK", "HIT", "KO", "GUARD_BREAK"}:

            return


        self.vx = 0.0

        self.guard = False

        self.crouch = False


        if inp["guard"] and self.on_ground and self.guard_break_timer <= 0 and self.guard_meter > 0:

            self.guard = True

            self.state = "GUARD"

            return


        if inp["crouch"] and self.on_ground:

            self.crouch = True

            self.state = "CROUCH"

        else:

            self.state = "IDLE" if self.on_ground else "JUMP"


        if not self.crouch:

            if inp["left"] and not inp["right"]:

                self.vx = -self.speed

                if self.on_ground:

                    self.state = "WALK"

            elif inp["right"] and not inp["left"]:

                self.vx = self.speed

                if self.on_ground:

                    self.state = "WALK"


        if pressed["jump"] and self.on_ground and not self.crouch:

            self.vy = self.jump_power

            self.on_ground = False

            self.state = "JUMP"


        if pressed["light"]:

            self.start_attack("LIGHT")

        elif pressed["heavy"]:

            self.start_attack("HEAVY")

        elif pressed["special"] and self.meter >= ATTACKS["SPECIAL"]["meter_cost"]:

            self.meter -= ATTACKS["SPECIAL"]["meter_cost"]

            self.start_attack("SPECIAL")


    def update_physics_and_state(self) -> None:

        if self.hp <= 0:

            self.state = "KO"

            self.guard = False

            self.crouch = False


        if self.combo_timer > 0:

            self.combo_timer -= 1

        else:

            self.combo_count = 0


        if self.state != "GUARD" and self.guard_break_timer <= 0 and self.hp > 0:

            self.guard_meter = min(100.0, self.guard_meter + 0.25)


        if self.state == "GUARD_BREAK":

            self.guard_break_timer -= 1

            self.guard = False

            self.crouch = False

            self.vx = 0.0

            if self.guard_break_timer <= 0:

                self.guard_break_timer = 0

                self.state = "IDLE" if self.on_ground else "JUMP"

        elif self.state == "HIT":

            self.hit_timer -= 1

            if self.hit_timer <= 0:

                self.state = "IDLE" if self.on_ground else "JUMP"

        elif self.state == "ATTACK" and self.attack_type is not None:

            self.attack_timer += 1

            data = ATTACKS[self.attack_type]

            total = data["startup"] + data["active"] + data["recovery"]

            if self.attack_timer >= total:

                self.state = "IDLE" if self.on_ground else "JUMP"

                self.attack_timer = 0

                self.attack_type = None

                self.attack_hit = False


        self.x += self.vx

        self.x = max(0.0, min(WIDTH - PLAYER_W, self.x))


        self.vy += self.gravity

        self.y += self.vy

        if self.y + PLAYER_H >= GROUND_Y:

            self.y = GROUND_Y - PLAYER_H

            self.vy = 0.0

            self.on_ground = True

            if self.state == "JUMP":

                self.state = "IDLE"

        else:

            self.on_ground = False


    def serialize(self) -> dict[str, Any]:

        attack_rect = self.attack_rect() if self.attack_is_active() else None

        return {

            "id": self.player_id,

            "x": round(self.x, 2),

            "y": round(self.y, 2),

            "hp": self.hp,

            "meter": self.meter,

            "guard_meter": round(self.guard_meter, 2),

            "guard_break_timer": self.guard_break_timer,

            "facing": self.facing,

            "state": self.state,

            "guard": self.guard,

            "crouch": self.crouch,

            "attack_type": self.attack_type,

            "attack_timer": self.attack_timer,

            "attack_active": self.attack_is_active(),

            "attack_rect": attack_rect,

            "combo_count": self.combo_count,

            "round_wins": self.round_wins,

        }


@dataclass

class Game:

    players: list[Player] = field(default_factory=lambda: [Player(0, 200), Player(1, 700)])

    hitstop: int = 0

    phase: str = "WAITING"

    phase_timer: int = 0

    event_id: int = 0

    events: list[dict[str, Any]] = field(default_factory=list)


    def emit(self, event_type: str, **payload: Any) -> None:

        self.event_id += 1

        self.events.append({"id": self.event_id, "type": event_type, **payload})

        self.events = self.events[-30:]


    def start_match(self) -> None:

        for player in self.players:

            player.round_wins = 0

        self.reset_round()


    def reset_round(self) -> None:

        for player in self.players:

            player.reset_round()

        self.hitstop = 0

        self.phase = "ROUND_START"

        self.phase_timer = ROUND_START_FRAMES

        self.emit("ROUND_START")


    def reset_match(self) -> None:

        self.start_match()


    def apply_hit(self, attacker: Player, defender: Player) -> None:

        if attacker.attack_type is None:

            return


        attack_type = attacker.attack_type

        data = ATTACKS[attack_type]

        damage = data["damage"]

        knockback = data["knockback"] * attacker.facing

        guarded = defender.guard and defender.guard_break_timer <= 0 and defender.guard_meter > 0


        if guarded:

            guard_cost = 8

            guard_damage = 0

            if attack_type == "HEAVY":

                guard_cost = 18

                guard_damage = 1

            elif attack_type == "SPECIAL":

                guard_cost = 30

                guard_damage = 4

            defender.guard_meter = max(0.0, defender.guard_meter - guard_cost)

            defender.hp = max(0, defender.hp - guard_damage)

            damage = guard_damage

            knockback = int(knockback / 2)

            if defender.guard_meter <= 0:

                defender.state = "GUARD_BREAK"

                defender.guard = False

                defender.crouch = False

                defender.guard_break_timer = 90

        else:

            defender.state = "HIT"

            defender.hit_timer = 16

            defender.vy = -4.0

            defender.hp = max(0, defender.hp - damage)

        defender.vx = knockback

        attacker.attack_hit = True

        attacker.combo_count += 1

        attacker.combo_timer = 70

        attacker.meter = min(100, attacker.meter + data["meter_gain"])

        self.hitstop = data["hitstop"]


        self.emit(

            "HIT",

            attacker=attacker.player_id,

            defender=defender.player_id,

            attack_type=attack_type,

            guarded=guarded,

            damage=damage,

            x=round(defender.x + PLAYER_W / 2, 2),

            y=round(defender.y + PLAYER_H / 2, 2),

            hitstop=self.hitstop,

        )


    def resolve_attacks(self) -> None:

        for attacker, defender in ((self.players[0], self.players[1]), (self.players[1], self.players[0])):

            if not attacker.attack_is_active() or attacker.attack_hit:

                continue

            attack_rect = attacker.attack_rect()

            if attack_rect is not None and rects_overlap(attack_rect, defender.body_rect()):

                self.apply_hit(attacker, defender)


    def check_round_end(self) -> None:

        p1, p2 = self.players

        if p1.hp > 0 and p2.hp > 0:

            return


        self.phase = "ROUND_OVER"

        self.phase_timer = ROUND_END_FRAMES


        if p1.hp <= 0 and p2.hp <= 0:

            self.emit("ROUND_DRAW")

            return


        winner = 1 if p1.hp <= 0 else 0

        self.players[winner].round_wins += 1

        self.emit("ROUND_WIN", winner=winner)


        if self.players[winner].round_wins >= ROUNDS_TO_WIN:

            self.phase = "MATCH_OVER"

            self.phase_timer = 0

            self.emit("MATCH_WIN", winner=winner)


    def update(self, current_inputs: list[dict[str, bool]], pressed_inputs: list[dict[str, bool]]) -> None:

        if self.phase == "WAITING":

            return


        if self.phase == "ROUND_START":

            self.phase_timer -= 1

            if self.phase_timer <= 0:

                self.phase = "FIGHT"

                self.emit("FIGHT")

            return


        if self.phase == "ROUND_OVER":

            self.phase_timer -= 1

            if self.phase_timer <= 0:

                self.reset_round()

            return


        if self.phase == "MATCH_OVER":

            return


        if self.hitstop > 0:

            self.hitstop -= 1

            return


        p1, p2 = self.players

        p1.facing = 1 if p2.x > p1.x else -1

        p2.facing = 1 if p1.x > p2.x else -1


        for idx, player in enumerate(self.players):

            player.update_input(current_inputs[idx], pressed_inputs[idx])


        for player in self.players:

            player.update_physics_and_state()


        self.resolve_attacks()

        self.check_round_end()


    def snapshot(self, connected_count: int, mode: str = "ONLINE", cpu_difficulty: str | None = None) -> dict[str, Any]:

        return {

            "type": "snapshot",

            "connected": connected_count,

            "mode": mode,

            "cpu_difficulty": cpu_difficulty,

            "phase": self.phase,

            "phase_timer": self.phase_timer,

            "hitstop": self.hitstop,

            "players": [player.serialize() for player in self.players],

            "events": self.events,

        }


clients: dict[int, socket.socket] = {}

inputs: list[dict[str, bool]] = [EMPTY_INPUT.copy(), EMPTY_INPUT.copy()]

previous_inputs: list[dict[str, bool]] = [EMPTY_INPUT.copy(), EMPTY_INPUT.copy()]

lock = threading.Lock()

game = Game()

cpu_controller: CPUController | None = None


def normalize_input(payload: dict[str, Any]) -> dict[str, bool]:

    return {key: bool(payload.get(key, False)) for key in EMPTY_INPUT}


def recv_client(conn: socket.socket, player_id: int) -> None:

    buffer = ""

    try:

        while True:

            data = conn.recv(4096)

            if not data:

                break

            buffer += data.decode("utf-8")

            while "\n" in buffer:

                line, buffer = buffer.split("\n", 1)

                if not line.strip():

                    continue

                payload = json.loads(line)

                if payload.get("type") == "input":

                    with lock:

                        inputs[player_id] = normalize_input(payload)

                elif payload.get("type") == "reset":

                    with lock:

                        if game.phase == "MATCH_OVER":

                            game.reset_match()

    except (ConnectionError, OSError, UnicodeDecodeError, json.JSONDecodeError):

        pass

    finally:

        with lock:

            clients.pop(player_id, None)

            inputs[player_id] = EMPTY_INPUT.copy()

            previous_inputs[player_id] = EMPTY_INPUT.copy()

            game.phase = "WAITING"

        try:

            conn.close()

        except OSError:

            pass

        print(f"Player {player_id + 1} disconnected")


def send_json(conn: socket.socket, payload: dict[str, Any]) -> None:

    conn.sendall((json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8"))


def accept_clients(server: socket.socket) -> None:

    while True:

        conn, addr = server.accept()

        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        with lock:

            allowed_ids = (0,) if CPU_MODE else (0, 1)

            free_ids = [player_id for player_id in allowed_ids if player_id not in clients]

            if not free_ids:

                try:

                    send_json(conn, {"type": "error", "message": "Server is full"})

                finally:

                    conn.close()

                continue


            player_id = free_ids[0]

            clients[player_id] = conn

            send_json(conn, {

                "type": "welcome",

                "player_id": player_id,

                "mode": "CPU" if CPU_MODE else "ONLINE",

                "cpu_difficulty": CPU_DIFFICULTY if CPU_MODE else None,

            })

            print(f"Player {player_id + 1} connected: {addr}")


            if CPU_MODE:

                game.start_match()

                if cpu_controller is not None:

                    cpu_controller.reset()

                print(f"CPU match start. Difficulty: {CPU_DIFFICULTY}")

            elif len(clients) == 2:

                game.start_match()

                print("Both players connected. Match start.")


        threading.Thread(target=recv_client, args=(conn, player_id), daemon=True).start()


def game_loop() -> None:

    frame_time = 1.0 / FPS

    while True:

        started = time.perf_counter()

        with lock:

            human_connected_count = len(clients)

            ready = human_connected_count == (1 if CPU_MODE else 2)

            if ready:

                if CPU_MODE and cpu_controller is not None:

                    inputs[1] = cpu_controller.decide(game)


                pressed_inputs = [

                    {key: inputs[idx][key] and not previous_inputs[idx][key] for key in EMPTY_INPUT}

                    for idx in (0, 1)

                ]

                game.update(inputs, pressed_inputs)

                for idx in (0, 1):

                    previous_inputs[idx] = inputs[idx].copy()


            visible_connected_count = 2 if CPU_MODE and ready else human_connected_count

            snapshot = game.snapshot(

                visible_connected_count,

                mode="CPU" if CPU_MODE else "ONLINE",

                cpu_difficulty=CPU_DIFFICULTY if CPU_MODE else None,

            )

            failed_ids: list[int] = []

            for player_id, conn in clients.items():

                try:

                    send_json(conn, snapshot)

                except OSError:

                    failed_ids.append(player_id)

            for player_id in failed_ids:

                clients.pop(player_id, None)

                inputs[player_id] = EMPTY_INPUT.copy()

                previous_inputs[player_id] = EMPTY_INPUT.copy()

                game.phase = "WAITING"


        elapsed = time.perf_counter() - started

        time.sleep(max(0.0, frame_time - elapsed))


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(description="pygame fighting game authoritative server")

    parser.add_argument("--host", default=HOST, help="Bind address")

    parser.add_argument("--port", type=int, default=PORT, help="TCP port")

    parser.add_argument("--cpu", action="store_true", help="Run a one-player match against the CPU")

    parser.add_argument("--difficulty", choices=("easy", "normal", "hard"), default="normal")

    return parser.parse_args()


def main() -> None:

    global CPU_MODE, CPU_DIFFICULTY, cpu_controller

    args = parse_args()

    CPU_MODE = bool(args.cpu)

    CPU_DIFFICULTY = str(args.difficulty)

    cpu_controller = CPUController(CPU_DIFFICULTY) if CPU_MODE else None


    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((args.host, args.port))

    server.listen()

    mode_text = f"CPU ({CPU_DIFFICULTY})" if CPU_MODE else "ONLINE"

    print(f"Server listening on {args.host}:{args.port} | mode={mode_text}")


    threading.Thread(target=accept_clients, args=(server,), daemon=True).start()

    try:

        game_loop()

    except KeyboardInterrupt:

        print("\nServer stopped")

    finally:

        server.close()


if __name__ == "__main__":

    main()

