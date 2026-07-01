# pygame Fighting Game Arcade

pygameで作った2D格闘ゲームです。
1人で遊べるCPU戦と、同じPCまたは同じWi-Fi内で遊べるオンライン対戦を選べます。

アーケード格闘ゲーム風のスプライト、ヒットエフェクト、HPバー、必殺技演出を入れています。

---

## 主な機能

* CPU戦：EASY / NORMAL / HARD
* オンライン対戦：HOST / JOIN
* pygameによる画面描画
* スプライト画像アニメーション
* アーケード風ヒットエフェクト
* 移動、ジャンプ、しゃがみ、ガード
* 弱攻撃、強攻撃、必殺技
* HPバー、必殺技ゲージ、コンボ表示
* ヒットストップ、ノックバック
* ラウンド制、2本先取
* `B`キーで当たり判定表示
* サーバー側で攻撃判定・HP・ラウンドを管理
* Dockerによるオンライン対戦サーバー起動

---

## ファイル構成

```text
fighter_game/
├ server.py
├ client.py
├ animation.py
├ arcade_effects.py
├ cpu_controller.py
├ launcher.py
├ docker_entrypoint.py
├ generate_arcade_sprites.py
├ run_game.bat
├ Dockerfile
├ docker-compose.yml
├ .dockerignore
├ .gitignore
├ README.md
├ DOCKER_SETUP.md
└ assets/
    └ sprites/
        ├ player1/
        │   ├ idle/
        │   ├ walk/
        │   ├ jump/
        │   ├ crouch/
        │   ├ guard/
        │   ├ hit/
        │   ├ ko/
        │   ├ light/
        │   ├ heavy/
        │   └ special/
        └ player2/
            ├ idle/
            ├ walk/
            ├ jump/
            ├ crouch/
            ├ guard/
            ├ hit/
            ├ ko/
            ├ light/
            ├ heavy/
            └ special/
```

---

## インストール

PowerShellでプロジェクトフォルダに移動します。

```powershell
cd C:\Users\...\fighter_game
```

pygameをインストールします。

```powershell
py -m pip install pygame
```

アーケード風スプライトを再生成する場合だけ、Pillowも必要です。

```powershell
py -m pip install pillow
```

---

## 起動方法1：ランチャーから起動

通常はこれで起動します。

```powershell
py launcher.py
```

または、Windowsなら次をダブルクリックします。

```text
run_game.bat
```

ランチャーでは次を選べます。

```text
1  CPU BATTLE - EASY
2  CPU BATTLE - NORMAL
3  CPU BATTLE - HARD
4  ONLINE BATTLE - HOST
5  ONLINE BATTLE - JOIN
```

環境によっては、ランチャーが子プロセスを待っている間に「応答なし」に見えることがあります。
その場合は、次の手動起動を使ってください。

---

## 起動方法2：CPU戦を手動で起動する方法

PowerShellを2つ開きます。

### 1つ目：サーバー起動

```powershell
py server.py --host 127.0.0.1 --port 5000 --cpu --difficulty easy
```

難易度は次から選べます。

```text
easy
normal
hard
```

NORMALの場合は次のようにします。

```powershell
py server.py --host 127.0.0.1 --port 5000 --cpu --difficulty normal
```

サーバー側に次のように表示されればOKです。

```text
Server listening on 127.0.0.1:5000 | mode=CPU (easy)
```

### 2つ目：クライアント起動

```powershell
py client.py --server-ip 127.0.0.1 --port 5000 --mode-label "CPU EASY"
```

NORMALの場合は次のようにします。

```powershell
py client.py --server-ip 127.0.0.1 --port 5000 --mode-label "CPU NORMAL"
```

---

## 起動方法3：同じPCでオンライン対戦を確認する方法

同じPCでオンライン対戦を確認する場合は、PowerShellを3つ開きます。

### 1つ目：サーバー

```powershell
py server.py --host 127.0.0.1 --port 5000
```

### 2つ目：1Pクライアント

```powershell
py client.py --server-ip 127.0.0.1 --port 5000 --mode-label "ONLINE 1P"
```

### 3つ目：2Pクライアント

```powershell
py client.py --server-ip 127.0.0.1 --port 5000 --mode-label "ONLINE 2P"
```

サーバー側に次のように表示されればOKです。

```text
Player 1 connected
Player 2 connected
Online match start
```

同じPCで2つのクライアントを開いた場合、キーボード入力は選択中のウィンドウにしか入りません。
同時に2人で操作したい場合は、別PCで確認する方が適しています。

---

## 起動方法4：同じWi-Fi内でオンライン対戦する方法

同じWi-Fi内の2台のPCで遊ぶ場合の方法です。

### ホスト側PC

PowerShellを2つ開きます。

1つ目：サーバー

```powershell
py server.py --host 0.0.0.0 --port 5000
```

2つ目：ホスト側のクライアント

```powershell
py client.py --server-ip 127.0.0.1 --port 5000 --mode-label "ONLINE HOST"
```

### 参加側PC

ホストPCのIPv4アドレスを入力して接続します。

```powershell
py client.py --server-ip ホストPCのIPv4アドレス --port 5000 --mode-label "ONLINE JOIN"
```

例：ホストPCのIPv4アドレスが `192.168.1.23` の場合

```powershell
py client.py --server-ip 192.168.1.23 --port 5000 --mode-label "ONLINE JOIN"
```

---

## アドレスの意味

| アドレス          | 意味                | 使う場面                   |
| ------------- | ----------------- | ---------------------- |
| `127.0.0.1`   | 自分自身のPC           | 同じPCでサーバーとクライアントを動かすとき |
| `0.0.0.0`     | このPCの全ネットワークで待ち受け | サーバー起動時                |
| `192.168.x.x` | LAN内のPCのアドレス      | 別PCからホストPCへ接続するとき      |

参加側のクライアントに `0.0.0.0` を入力してはいけません。
`0.0.0.0` はサーバー起動用です。

---

## ホストPCのIPv4アドレスを確認する方法

ホスト側PCでPowerShellを開きます。

```powershell
ipconfig
```

次のような表示を探します。

```text
IPv4 アドレス . . . . . . . . . . . .: 192.168.1.23
```

この場合、参加側PCが入力するアドレスは次です。

```text
192.168.1.23
```

---

## 操作方法

| キー        | 操作           |
| --------- | ------------ |
| `A` / `D` | 左右移動         |
| `W`       | ジャンプ         |
| `S`       | しゃがみ         |
| `Q`       | ガード          |
| `F`       | 弱攻撃          |
| `G`       | 強攻撃          |
| `H`       | 必殺技          |
| `R`       | 試合終了後に再戦     |
| `B`       | 当たり判定の表示・非表示 |

必殺技はゲージを30消費します。
攻撃を当てるとゲージが増えます。

---

## Dockerでオンライン対戦サーバーを起動する方法

このプロジェクトはDocker対応済みです。
ただし、Dockerで動かすのは主に `server.py` です。

`client.py` はpygameの画面を開くため、各プレイヤーのPCで直接起動します。

### ホスト側：Dockerでサーバー起動

```powershell
docker compose up --build
```

成功すると次のように表示されます。

```text
Server listening on 0.0.0.0:5000 | mode=ONLINE
```

### ホスト側：自分のクライアントを起動

```powershell
py client.py --server-ip 127.0.0.1 --port 5000 --mode-label "ONLINE HOST"
```

### 参加側：ホストPCに接続

ホストPCで `ipconfig` を実行し、IPv4アドレスを確認します。

```powershell
ipconfig
```

例：

```text
IPv4 アドレス . . . : 192.168.1.23
```

参加側PCでは次のように起動します。

```powershell
py client.py --server-ip 192.168.1.23 --port 5000 --mode-label "ONLINE JOIN"
```

### サーバー停止

```powershell
docker compose down
```

詳しくは `DOCKER_SETUP.md` を見てください。

---

## Windowsファイアウォールが出た場合

同じWi-Fiでオンライン対戦をする場合は、PythonまたはDockerの通信を許可してください。
少なくとも「プライベートネットワーク」にチェックを入れて許可します。

---

## 接続確認

サーバーが5000番で待ち受けているか確認するには、PowerShellで次を実行します。

```powershell
netstat -ano | findstr :5000
```

正常なら、次のような表示が出ます。

```text
TCP    127.0.0.1:5000    0.0.0.0:0    LISTENING
```

または、

```text
TCP    0.0.0.0:5000      0.0.0.0:0    LISTENING
```

古いプロセスが残っている場合は、PIDを確認して終了します。

```powershell
taskkill /PID 番号 /F
```

---

## 仕組み

このゲームは、サーバー側がゲームの正解状態を管理します。

### `server.py`

* プレイヤー位置
* ジャンプ、重力
* 攻撃の発生・持続・硬直
* 当たり判定
* HP
* ゲージ
* ガード軽減
* ヒットストップ
* ラウンド制
* CPU戦モード
* オンライン対戦モード

### `client.py`

* pygameで画面描画
* キー入力の取得
* サーバーへの入力送信
* スプライトアニメーション
* HPバー、ゲージ、エフェクト表示
* 当たり判定のデバッグ表示

### `cpu_controller.py`

* CPUの入力を自動生成
* 距離に応じて接近、攻撃、後退、ガードを選択
* EASY / NORMAL / HARDで反応速度と行動確率を変更

### `animation.py`

* 状態ごとのPNG画像を読み込み
* `idle`、`walk`、`jump`、`guard`、`light` などのアニメーションを切り替え
* 左右反転表示
* 画像がない場合のフォールバック表示

### `arcade_effects.py`

* ヒットスパーク
* 衝撃波
* 斬撃風エフェクト
* 必殺技時の暗転
* スピード線
* 画面フラッシュ
* アーケード風HPバー
* アーケード風テキスト描画

### `generate_arcade_sprites.py`

* アーケード風のサンプルスプライトを生成
* `assets/sprites/player1/`
* `assets/sprites/player2/`

---


### サウンドの構成を加え修正しました。（6/19以降）