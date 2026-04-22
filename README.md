# reTerminal Inspector

reTerminal 上で動作する、Python/Tkinter ベースの検査用 GUI アプリです。  
物理ボタン入力、上部ボタン監視、ユーザー LED 制御、BLE デバイスとの通信を組み合わせて、スタンドアロンの操作・確認用ツールとして利用できます。

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