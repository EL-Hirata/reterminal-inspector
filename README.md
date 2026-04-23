# reTerminal Inspector

reTerminal 上で動作する、Python / Tkinter ベースの GUI 検査アプリです。  
Wio Terminal と BLE 接続し、ボタンイベントやセンサー値を受信しながら、reTerminal 側の物理ボタンと LED を使って操作・確認できます。

## 概要

このアプリは、Seeed Studio reTerminal を表示・操作端末として使い、Wio Terminal から送られてくる BLE 通信内容をグラフィカルに表示するためのツールです。

現在の構成では、画面描画を担当する `gui.py` と、BLE 通信・LED 制御・物理ボタン処理を担当する `controller.py` に役割を分離しています。  
BLE 接続先は Wio Terminal 側の `WioTerminal-GUI` アプリを前提にしています。Wio 側コードでは、デバイス名 `WioTerminal-GUI`、Service UUID `12345678-1234-1234-1234-1234567890ab`、reTerminal→Wio の書き込み UUID `...90ac`、Wio→reTerminal の通知 UUID `...90ad` が使われています。 :contentReference[oaicite:0]{index=0}

## 主な機能

- reTerminal 上でのフルスクリーン GUI 表示
- BLE スキャン / 接続 / 切断
- Wio Terminal からの通知受信
- Wio Terminal のボタン状態をグラフィカル表示
- Wio Terminal のセンサー値表示
  - LIGHT
  - ACC X / Y / Z
- reTerminal 前面ボタンによる操作
- reTerminal LED による状態表示
- ○ ボタン長押しによるシャットダウン確認

## 現在の BLE 接続先

Wio Terminal 側コードの前提は以下です。  
BLE 名は `WioTerminal-GUI`、Service UUID は `12345678-1234-1234-1234-1234567890ab`、Characteristic は `RX=...90ac`、`TX=...90ad` です。通知内容には `EVT,BTN,...`、`SENSOR,...`、`STATE,LED,...`、`*IDN?` 応答が含まれます。 

### BLE 設定

- Device Name: `WioTerminal-GUI`
- Service UUID: `12345678-1234-1234-1234-1234567890ab`
- Write Characteristic: `12345678-1234-1234-1234-1234567890ac`
- Notify Characteristic: `12345678-1234-1234-1234-1234567890ad`

### 受信データ例

- `Seeed,WioTerminal,BLE_GUI,1.0.0`
- `EVT,BTN,A,1`
- `EVT,BTN,UP,0`
- `SENSOR,LIGHT,1234`
- `SENSOR,ACC,0.12,0.34,0.56`
- `STATE,LED,ON`

## 画面構成

reTerminal 側 GUI は Canvas ベースのダッシュボード画面です。

- **SYSTEM**
  - BLE 接続状態
  - Wio LED 状態
  - IDN
- **SENSOR**
  - LIGHT
  - AX / AY / AZ
- **WIO BUTTONS**
  - UP / DOWN / LEFT / RIGHT / PRESS
  - C / B / A
- **reTerminal BUTTONS**
  - F1 / F2 / F3 / ○
- **COMM / LOG**
  - 最新送受信
  - 状態
  - ログ表示

## reTerminal 側ボタン割り当て

現在の割り当ては以下です。

- **F1**: `GET SENSOR` 送信
- **F2**: `LED TOGGLE` 送信
- **F3**: `*IDN?` 送信
- **○ 短押し**: BLE 接続 / 切断
- **○ 長押し 3 秒**: シャットダウン確認ダイアログ
- **上部ボタン**: アプリ上では未使用

## LED の役割

reTerminal のユーザープログラマブル LED は次の用途で使います。

- `usr_led1`: BLE 未接続表示
- `usr_led2`: BLE 接続中表示
- `usr_led0`: Wio から受信したときの通信インジケータ

## プロジェクト構成

```text
reterminal_inspector/
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ gui.py
│  ├─ controller.py
│  ├─ config.py
│  ├─ ble_client.py
│  ├─ leds.py
│  └─ special_buttons.py
├─ .vscode/
│  ├─ sample_launch.json
│  └─ sample_tasks.json
├─ .venv/
├─ requirements.txt
├─ README.md
├─ run_app.sh
├─ run_autostart.sh
├─ autostart.log
└─ app_launch.log