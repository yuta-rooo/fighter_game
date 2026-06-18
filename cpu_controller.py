from __future__ import annotations


import random

from dataclasses import dataclass

from typing import Any


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


DIFFICULTY_SETTINGS: dict[str, dict[str, float | int]] = {

    "easy": {

        "reaction_frames": 16,

        "guard_chance": 0.25,

        "jump_chance": 0.025,

        "special_chance": 0.08,

        "heavy_chance": 0.16,

        "retreat_chance": 0.06,

    },

    "normal": {

        "reaction_frames": 10,

        "guard_chance": 0.52,

        "jump_chance": 0.045,

        "special_chance": 0.18,

        "heavy_chance": 0.28,

        "retreat_chance": 0.10,

    },

    "hard": {

        "reaction_frames": 6,

        "guard_chance": 0.78,

        "jump_chance": 0.065,

        "special_chance": 0.32,

        "heavy_chance": 0.38,

        "retreat_chance": 0.16,

    },

}


@dataclass

class CPUController:

    


    difficulty: str = "normal"

    seed: int | None = None


    def __post_init__(self) -> None:

        if self.difficulty not in DIFFICULTY_SETTINGS:

            raise ValueError(f"Unknown CPU difficulty: {self.difficulty}")

        self.settings = DIFFICULTY_SETTINGS[self.difficulty]

        self.rng = random.Random(self.seed)

        self.frame = 0

        self.hold_input = EMPTY_INPUT.copy()


    def reset(self) -> None:

        self.frame = 0

        self.hold_input = EMPTY_INPUT.copy()


    def _empty(self) -> dict[str, bool]:

        return EMPTY_INPUT.copy()


    def decide(self, game: Any) -> dict[str, bool]:

        

        self.frame += 1


        if getattr(game, "phase", "WAITING") != "FIGHT":

            self.hold_input = self._empty()

            return self._empty()


        human = game.players[0]

        cpu = game.players[1]


        if cpu.hp <= 0 or cpu.state in {"ATTACK", "HIT", "KO"}:

            self.hold_input = self._empty()

            return self._empty()


        reaction_frames = int(self.settings["reaction_frames"])

        if self.frame % reaction_frames != 0:


            persistent = self.hold_input.copy()

            persistent["jump"] = False

            persistent["light"] = False

            persistent["heavy"] = False

            persistent["special"] = False

            return persistent


        inp = self._empty()

        distance = abs((human.x + 25) - (cpu.x + 25))

        human_is_threatening = human.state == "ATTACK" and distance <= 155


        if human_is_threatening and cpu.on_ground:

            if self.rng.random() < float(self.settings["guard_chance"]):

                inp["guard"] = True

                self.hold_input = inp.copy()

                return inp

            if self.rng.random() < float(self.settings["jump_chance"]) * 2.0:

                inp["jump"] = True

                self.hold_input = inp.copy()

                return inp


        if distance > 118:

            if human.x < cpu.x:

                inp["left"] = True

            else:

                inp["right"] = True

            if cpu.on_ground and self.rng.random() < float(self.settings["jump_chance"]):

                inp["jump"] = True

            self.hold_input = inp.copy()

            return inp


        if distance < 58 and self.rng.random() < float(self.settings["retreat_chance"]):

            if human.x < cpu.x:

                inp["right"] = True

            else:

                inp["left"] = True

            self.hold_input = inp.copy()

            return inp


        roll = self.rng.random()

        if cpu.meter >= 30 and distance <= 145 and roll < float(self.settings["special_chance"]):

            inp["special"] = True

        elif distance <= 105 and roll < float(self.settings["special_chance"]) + float(self.settings["heavy_chance"]):

            inp["heavy"] = True

        else:

            inp["light"] = True


        self.hold_input = inp.copy()

        return inp

