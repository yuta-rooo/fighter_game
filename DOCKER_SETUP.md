# Dockerでオンライン対戦サーバーを起動する方法

このファイルでは、Dockerを使ってオンライン対戦用サーバーを起動する方法を説明します。

このプロジェクトでは、Dockerで動かすのは主に `server.py` です。
`client.py` はpygameの画面を開くため、各プレイヤーのPCで直接起動します。

---

## 全体構成

```text
ホストPC
├ Dockerで server.py を起動
└ client.py で自分も接続

参加側PC
└ client.py でホストPCのIPv4アドレスへ接続
```

---

## 1. 必要なもの

ホスト側PCにDocker Desktopをインストールしてください。

インストール後、PowerShellで次を確認します。

```powershell
docker --version
docker compose version
```

バージョンが表示されればOKです。

---

## 2. オンライン対戦サーバーを起動する

プロジェクトフォルダに移動します。

```powershell
cd C:\Users\...\fighter_game
```

Dockerでサーバーを起動します。

```powershell
docker compose up --build
```

成功すると、次のように表示されます。

```text
Server listening on 0.0.0.0:5000 | mode=ONLINE
```

このPowerShellは閉じずに、そのまま起動しておきます。

---

## 3. ホスト側のプレイヤーが接続する

別のPowerShellを開き、ホストPC自身のクライアントを起動します。

```powershell
py client.py --server-ip 127.0.0.1 --port 5000 --mode-label "ONLINE HOST"
```

`127.0.0.1` は自分自身のPCを表すアドレスです。

---

## 4. 参加側のプレイヤーが接続する

参加側PCでは、ホストPCのIPv4アドレスを指定して接続します。

ホストPCでIPv4アドレスを確認します。

```powershell
ipconfig
```

次のような表示を探します。

```text
IPv4 アドレス . . . . . . . . . . . .: 192.168.1.23
```

この場合、参加側PCでは次のように起動します。

```powershell
py client.py --server-ip 192.168.1.23 --port 5000 --mode-label "ONLINE JOIN"
```

---

## 5. サーバーを停止する

Dockerを起動しているPowerShellで次を押します。

```text
Ctrl + C
```

完全に停止する場合は、別のPowerShellで次を実行します。

```powershell
docker compose down
```

---

## 6. CPU戦サーバーをDockerで起動する場合

通常、CPU戦はDockerを使わずに起動できます。
ただし、確認用としてDockerでCPU戦サーバーを起動することもできます。

```powershell
$env:GAME_MODE="cpu"
$env:CPU_DIFFICULTY="normal"
docker compose up --build
```

難易度は次から選べます。

```text
easy
normal
hard
```

CPU戦に接続する場合は、別のPowerShellで次を実行します。

```powershell
py client.py --server-ip 127.0.0.1 --port 5000 --mode-label "CPU NORMAL"
```

---

## 7. ポート番号を変える場合

標準では `5000` 番ポートを使います。

別のポートを使いたい場合は、例えば `6000` 番なら次のようにします。

```powershell
$env:FIGHTER_PORT="6000"
docker compose up --build
```

この場合、クライアント側も `--port 6000` にします。

ホスト側：

```powershell
py client.py --server-ip 127.0.0.1 --port 6000 --mode-label "ONLINE HOST"
```

参加側：

```powershell
py client.py --server-ip 192.168.1.23 --port 6000 --mode-label "ONLINE JOIN"
```

---

## 8. アドレスの意味

| アドレス          | 使う場所           | 意味                   |
| ------------- | -------------- | -------------------- |
| `0.0.0.0`     | サーバー側          | すべてのネットワークから接続を受け付ける |
| `127.0.0.1`   | ホストPC自身のクライアント | 自分自身のPC              |
| `192.168.x.x` | 参加側PCのクライアント   | ホストPCのLAN内アドレス       |

参加側PCで `0.0.0.0` や `127.0.0.1` を入力してはいけません。
参加側PCは、ホストPCの `192.168.x.x` を使います。

---

## 9. Windowsファイアウォールが出た場合

初回起動時に、Windowsファイアウォールの許可画面が出ることがあります。

同じWi-Fiでオンライン対戦する場合は、少なくとも次を許可してください。

```text
プライベートネットワーク
```

許可しないと、参加側PCからホストPCへ接続できない場合があります。

---

## 10. 接続確認

サーバーが5000番で待ち受けているか確認するには、PowerShellで次を実行します。

```powershell
netstat -ano | findstr :5000
```

正常なら、次のような表示が出ます。

```text
TCP    0.0.0.0:5000      0.0.0.0:0      LISTENING
```

または、

```text
TCP    127.0.0.1:5000    0.0.0.0:0      LISTENING
```

古いプロセスが残っている場合は、PIDを確認して終了します。

```powershell
taskkill /PID 番号 /F
```

---


## 11. まとめ

オンライン対戦サーバーをDockerで起動する場合：

```powershell
docker compose up --build
```

ホスト側プレイヤー：

```powershell
py client.py --server-ip 127.0.0.1 --port 5000 --mode-label "ONLINE HOST"
```

参加側プレイヤー：

```powershell
py client.py --server-ip ホストPCのIPv4アドレス --port 5000 --mode-label "ONLINE JOIN"
```

サーバー停止：

```powershell
docker compose down
```
