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