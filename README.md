# pygame Fighting Game v5.3 — CPU Battle + Online Battle

v5.2 の pygame スプライト版を土台に、1人用CPU戦とモード選択画面を追加した版です。

## Features

- CPU battle: EASY / NORMAL / HARD
- Online battle: HOST / JOIN
- Sprite animation
- Movement, jump, crouch, guard
- Light, heavy and special attacks
- HP, meter, combo, hitstop, rounds and rematch
- Authoritative server logic shared by CPU and online modes

## Files

```text
fighter_game_v5_3/
├ server.py
├ client.py
├ animation.py
├ cpu_controller.py
├ launcher.py
├ generate_sample_sprites.py
├ run_game.bat
└ assets/
    └ sprites/
        ├ player1/
        └ player2/
```

## Install

```powershell
py -m pip install pygame
```

Pillow is needed only when regenerating the generated sample sprite images.

```powershell
py -m pip install pillow
```

## Recommended Run

```powershell
py launcher.py
```

or double-click:

```text
run_game.bat
```

The launcher shows:

```text
1  CPU BATTLE - EASY
2  CPU BATTLE - NORMAL
3  CPU BATTLE - HARD
4  ONLINE BATTLE - HOST
5  ONLINE BATTLE - JOIN
```

## Controls

- `A` / `D`: move
- `W`: jump
- `S`: crouch
- `Q`: guard
- `F`: light attack
- `G`: heavy attack
- `H`: special attack; costs 30 meter
- `R`: rematch after match end
- `B`: show / hide collision hitboxes

## Direct CPU Mode Run

The launcher automatically runs these commands, but you can execute them manually.

PowerShell window 1:

```powershell
py server.py --cpu --difficulty normal
```

PowerShell window 2:

```powershell
py client.py --mode-label "CPU NORMAL"
```

Available difficulty values:

```text
easy
normal
hard
```

## Direct Online Mode Run

Host PC, PowerShell window 1:

```powershell
py server.py --host 0.0.0.0 --port 5000
```

Host PC, PowerShell window 2:

```powershell
py client.py --server-ip 127.0.0.1 --port 5000
```

Joining PC:

```powershell
py client.py --server-ip <HOST_PC_IPV4_ADDRESS> --port 5000
```

## Architecture

- `server.py`: authoritative fighting-game rules, TCP communication, CPU option
- `cpu_controller.py`: generates Player 2 input dictionaries
- `client.py`: pygame drawing, animation, effects and Player 1 key input
- `animation.py`: state-based PNG animation loading
- `launcher.py`: mode-select UI and process startup

## 使用スプライトについて

この版では、`source_spritesheet.png` から切り出した透明PNGスプライトを `assets/sprites/` に配置しています。

1キャラあたりの内訳は次の通りです。

```text
idle      4枚
walk      6枚
jump      4枚
crouch    2枚
guard     2枚
hit       3枚
ko        4枚
light     4枚
heavy     5枚
special   4枚
```

player1、player2ともに同じ構成です。
player2は同じポーズをベースに、色を変えて区別しています。


## Specialフレーム更新

`player1/special/004.png`、`player1/special/005.png`、`player2/special/004.png`、`player2/special/005.png` をキャラクター本体入りの必殺技画像に差し替えています。

これにより、special は各プレイヤー6枚構成です。
