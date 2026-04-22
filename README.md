# reTerminal Inspector

reTerminal 上で動作する、Python / Tkinter ベースの検査用 GUI アプリです。  
物理ボタン入力、上部ボタン監視、ユーザー LED 制御、BLE デバイスとの通信を組み合わせて、簡易な検査装置・確認装置として利用できます。

## 概要

このアプリは、Seeed Studio reTerminal 上で動作する検査・操作用 GUI です。  
主な目的は、reTerminal 本体の物理入力と外部 BLE デバイスを組み合わせて、簡易な検査装置・確認装置として使うことです。

現在は以下の機能を実装しています。

- reTerminal 上でのフルスクリーン GUI 起動
- reTerminal 前面ボタン F1 / F2 / F3 / ○ の状態取得
- reTerminal 左上の上部ボタン（KEY_SLEEP）の取得
- reTerminal のユーザープログラマブル LED 制御
- BLE スキャン、接続、切断
- Wio Terminal 側の `WIO-SCPI` BLE デバイスとの接続
- `*IDN?` コマンド送信と応答確認
- Wio Terminal からの `WIO:BTN ...` 通知受信
- 上部ボタン長押し時のシャットダウン確認ダイアログ表示

## 主な用途

- reTerminal 単体の入出力確認
- BLE 接続先との通信テスト
- Wio Terminal とのボタン連携確認
- GUI ベースの簡易検査装置の土台

## 動作環境

- Seeed Studio reTerminal
- Raspberry Pi OS ベース環境
- Python 3.12 系想定
- GUI: Tkinter
- BLE: bleak
- 入力イベント監視: evdev

## プロジェクト構成

```text
reterminal_inspector/
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ gui.py
│  ├─ config.py
│  ├─ ble_client.py
│  ├─ leds.py
│  └─ special_buttons.py
├─ .venv/
├─ requirements.txt
├─ run_app.sh
├─ run_autostart.sh
├─ autostart.log
└─ app_launch.log
```

## 各ファイルの役割

- `app/main.py`  
  アプリの起動エントリです。

- `app/gui.py`  
  GUI 本体です。  
  画面表示、物理ボタン状態表示、BLE 操作、上部ボタン長押し時のシャットダウン確認などを担当します。

- `app/config.py`  
  BLE デバイス名、UUID、画面設定などの構成情報を管理します。

- `app/ble_client.py`  
  `bleak` を使った BLE 通信ラッパーです。

- `app/leds.py`  
  reTerminal の LED 制御を担当します。

- `app/special_buttons.py`  
  `gpio_keys` を `evdev` で監視し、前面ボタンと上部ボタンの入力を取得します。

- `run_app.sh`  
  手動起動・デスクトップショートカット用の起動スクリプトです。

- `run_autostart.sh`  
  自動起動用の起動スクリプトです。ログを残します。

## 必要パッケージ

### OS パッケージ
必要に応じて以下を導入してください。

```bash
sudo apt update
sudo apt install -y python3-tk bluetooth bluez
```

### Python パッケージ
`requirements.txt` 例:

```txt
bleak
gpiozero
evdev
```

インストール:

```bash
cd /home/pi/work/reterminal_inspector
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## BLE 接続先設定

現在の接続対象は、Wio Terminal 側の BLE Peripheral アプリです。

### Wio Terminal 側の想定情報

- Device Name: `WIO-SCPI`
- Service UUID: `12345678-1234-1234-1234-1234567890ab`
- Notify / Read Characteristic: `12345678-1234-1234-1234-1234567890ac`
- Write Characteristic: `12345678-1234-1234-1234-1234567890ad`

### 受信データ例

- `WIO,TERMINAL,BLE,0.1`
- `READY`
- `WIO:BTN 1,0,0`

## 実装済みの reTerminal 側機能

### 物理ボタン
前面ボタンの入力を取得し、GUI 上の状態表示を更新します。

- F1
- F2
- F3
- ○

### 上部ボタン
左上の上部ボタン（KEY_SLEEP）を取得します。  
長押し時にはシャットダウン確認ダイアログを表示し、確認後に OS シャットダウンを実行できます。

### LED
reTerminal のユーザープログラマブル LED を制御します。  
前面ボタン操作時の点灯、全消灯などに対応しています。

## 初期セットアップ

### 1. 仮想環境作成
```bash
cd /home/pi/work/reterminal_inspector
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### 2. LED 制御用 sudoers 設定
LED の brightness へ書き込むため、`tee` にパスワードなし sudo を許可します。

```bash
sudo visudo -f /etc/sudoers.d/reterminal-led
```

内容:

```text
pi ALL=(ALL) NOPASSWD: /usr/bin/tee /sys/class/leds/usr_led0/brightness
pi ALL=(ALL) NOPASSWD: /usr/bin/tee /sys/class/leds/usr_led1/brightness
pi ALL=(ALL) NOPASSWD: /usr/bin/tee /sys/class/leds/usr_led2/brightness
```

### 3. 上部ボタン長押しシャットダウン用 sudoers 設定
```bash
sudo visudo -f /etc/sudoers.d/reterminal-power
```

内容:

```text
pi ALL=(ALL) NOPASSWD: /usr/bin/systemctl poweroff
```

### 4. 入力イベント読み取り権限
`gpio_keys` を読むため、`pi` ユーザーが `input` グループへ入っていることを確認します。

```bash
id
```

必要なら:

```bash
sudo usermod -aG input pi
```

その後、再ログインまたは再起動してください。

## 起動方法

### 手動起動
```bash
cd /home/pi/work/reterminal_inspector
source .venv/bin/activate
python -m app.main
```

### デスクトップショートカット起動
デスクトップ上の `reterminal-inspector.desktop` から起動します。

### 自動起動
`~/.config/autostart/reterminal-inspector.desktop` から起動します。

## 起動スクリプト

### `run_app.sh`
デスクトップショートカット用のシンプル起動スクリプトです。

```bash
#!/bin/bash
cd /home/pi/work/reterminal_inspector || exit 1
source /home/pi/work/reterminal_inspector/.venv/bin/activate
export DISPLAY=:0
export XDG_RUNTIME_DIR=/run/user/1000
exec python -m app.main
```

### `run_autostart.sh`
自動起動用スクリプトです。ログを残します。

```bash
#!/bin/bash
LOG=/home/pi/work/reterminal_inspector/autostart.log

{
  echo "===== $(date '+%F %T') ====="
  echo "USER=$(whoami)"
  echo "PWD=$(pwd)"
  echo "DISPLAY=$DISPLAY"
  echo "XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR"
  id
  ls -l /sys/class/leds/usr_led0/brightness
  sudo -n tee /sys/class/leds/usr_led0/brightness <<< 0 >/dev/null
  echo "sudo_led_exit=$?"
} >> "$LOG" 2>&1

cd /home/pi/work/reterminal_inspector || exit 1
source /home/pi/work/reterminal_inspector/.venv/bin/activate
export DISPLAY=:0
export XDG_RUNTIME_DIR=/run/user/1000
exec python -m app.main >> "$LOG" 2>&1
```

## 自動起動設定

### ファイル
`/home/pi/.config/autostart/reterminal-inspector.desktop`

### 内容
```ini
[Desktop Entry]
Type=Application
Name=reTerminal Inspector AutoStart
Exec=/home/pi/work/reterminal_inspector/run_autostart.sh
StartupNotify=false
Terminal=false
X-GNOME-Autostart-enabled=true
```

## デスクトップショートカット設定

### ファイル
`/home/pi/Desktop/reterminal-inspector.desktop`

### 内容
```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=reTerminal Inspector
Comment=Launch reTerminal inspector app
Exec=/home/pi/work/reterminal_inspector/run_app.sh
Path=/home/pi/work/reterminal_inspector
Terminal=false
Icon=utilities-terminal
Categories=Utility;
```

## VS Code での実行例

### `.vscode/launch.json`
Remote-SSH で reTerminal に接続した状態で、そのままデバッグ実行するための例です。

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: reTerminal Inspector",
      "type": "debugpy",
      "request": "launch",
      "module": "app.main",
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal",
      "justMyCode": true,
      "env": {
        "DISPLAY": ":0",
        "XDG_RUNTIME_DIR": "/run/user/1000"
      },
      "python": "${workspaceFolder}/.venv/bin/python"
    }
  ]
}
```

### `.vscode/tasks.json`
手動起動スクリプトを VS Code のタスクとして実行する例です。

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "run reTerminal Inspector",
      "type": "shell",
      "command": "${workspaceFolder}/run_app.sh",
      "options": {
        "cwd": "${workspaceFolder}"
      },
      "problemMatcher": []
    }
  ]
}
```

## 権限設定
```bash
chmod +x /home/pi/work/reterminal_inspector/run_app.sh
chmod +x /home/pi/work/reterminal_inspector/run_autostart.sh
chmod +x /home/pi/Desktop/reterminal-inspector.desktop
```

## ログファイル

- `autostart.log`  
  自動起動時の確認用ログ

- `app_launch.log`  
  必要に応じて手動起動側でも利用可能なログ

## トラブルシュート

### BLE デバイスが見つからない
- Wio Terminal 側が BLE 広告中か確認
- デバイス名が `WIO-SCPI` か確認
- UUID が `config.py` と一致しているか確認

### LED が点灯しない
- `sudoers` の `reterminal-led` が正しく設定されているか確認
- `sudo -n tee /sys/class/leds/usr_led0/brightness <<< 255 >/dev/null`
  が成功するか確認

### 上部ボタン長押しでシャットダウンできない
- `sudoers` の `reterminal-power` が正しく設定されているか確認
- `which systemctl` の結果と sudoers のパスが一致しているか確認

### ボタンが反応しない
- `gpio_keys` が `evdev` で検出できるか確認
- `pi` ユーザーが `input` グループに入っているか確認

## 今後の拡張候補

- Wio Terminal 側のセンサー値受信
- BLE 受信内容の GUI 専用表示欄追加
- 検査フローごとの状態遷移管理
- ログファイル保存の整理
- `config.ini` 化による設定外出し
- GitHub 公開向けの整理

## 備考

このプロジェクトは、reTerminal をベースにした小規模な検査・制御 GUI の土台として作成しています。  
今後は、Wio Terminal や M5Stack などの BLE 接続機器との連携を拡張し、実運用向けの確認・検査ツールへ発展させることを想定しています。
