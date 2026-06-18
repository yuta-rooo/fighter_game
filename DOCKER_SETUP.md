# Dockerでオンライン対戦サーバーを起動する方法

このDocker設定は、**オンライン対戦用のサーバーだけ**をコンテナで起動します。

重要：`client.py` は pygame の画面を開くデスクトップアプリなので、Docker内ではなく、各プレイヤーのPCで直接起動します。

---

## 使い方の全体像

```text
ホストPC
├ Dockerで server.py を起動
└ 自分も client.py で接続

参加側PC
└ client.py でホストPCのIPv4アドレスに接続
```

---

## 1. 必要なもの

ホスト側PCに Docker Desktop を入れてください。

確認：

```powershell
docker --version
docker compose version
```

---

## 2. オンライン対戦サーバーを起動

プロジェクトフォルダで実行します。

```powershell
docker compose up --build
```

成功すると、だいたい次のように表示されます。

```text
Server listening on 0.0.0.0:5000 | mode=ONLINE
```

または、Windowsなら次をダブルクリックしてもOKです。

```text
start_server_docker.bat
```

---

## 3. ホスト側のプレイヤーが接続

別のPowerShellで、ホストPC自身のクライアントを起動します。

```powershell
py client.py --server-ip 127.0.0.1 --port 5000 --mode-label "ONLINE HOST"
```

---

## 4. 参加側のプレイヤーが接続

参加側PCでは、ホストPCのIPv4アドレスを指定します。

ホストPCでIPv4を確認：

```powershell
ipconfig
```

例：

```text
IPv4 アドレス . . . . . . . . . . . .: 192.168.1.23
```

参加側PCで：

```powershell
py client.py --server-ip 192.168.1.23 --port 5000 --mode-label "ONLINE JOIN"
```

---

## 5. サーバーを止める

起動中のPowerShellで：

```powershell
Ctrl + C
```

または別PowerShellで：

```powershell
docker compose down
```

Windowsなら次をダブルクリックしてもOKです。

```text
stop_server_docker.bat
```

---

## CPU戦サーバーをDockerで起動する場合

通常はCPU戦はDocker不要ですが、確認用としてDockerでも起動できます。

```powershell
$env:GAME_MODE="cpu"
$env:CPU_DIFFICULTY="normal"
docker compose up --build
```

難易度：

```text
easy
normal
hard
```

接続：

```powershell
py client.py --server-ip 127.0.0.1 --port 5000 --mode-label "CPU NORMAL"
```

Windowsなら次をダブルクリックしてもOKです。

```text
start_cpu_server_docker.bat
```

---

## ポート番号を変える場合

外側のポートだけ変える場合：

```powershell
$env:FIGHTER_PORT="6000"
docker compose up --build
```

この場合、クライアントも `--port 6000` にします。

```powershell
py client.py --server-ip 127.0.0.1 --port 6000 --mode-label "ONLINE HOST"
```

参加側も同じです。

```powershell
py client.py --server-ip 192.168.1.23 --port 6000 --mode-label "ONLINE JOIN"
```

---

## アドレスの意味

| アドレス | 使う場所 | 意味 |
|---|---|---|
| `0.0.0.0` | サーバー側 | 全ネットワークから受け付ける |
| `127.0.0.1` | ホストPC自身のclient.py | 自分自身のPC |
| `192.168.x.x` | 参加側PCのclient.py | ホストPCのLAN内アドレス |

参加側に `0.0.0.0` や `127.0.0.1` を入力してはいけません。参加側はホストPCの `192.168.x.x` を使います。

---

## GitHubに載せるときの推奨構成

```text
fighter_game/
├ server.py
├ client.py
├ animation.py
├ cpu_controller.py
├ launcher.py
├ Dockerfile
├ docker-compose.yml
├ docker_entrypoint.py
├ .dockerignore
├ .gitignore
├ start_server_docker.bat
├ start_cpu_server_docker.bat
├ stop_server_docker.bat
├ README.md
└ assets/
```

`__pycache__`、`.venv`、`.zip` はGitに載せないでください。
