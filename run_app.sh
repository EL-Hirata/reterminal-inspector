#!/bin/bash
cd /home/pi/work/reterminal_inspector || exit 1
source /home/pi/work/reterminal_inspector/.venv/bin/activate
export DISPLAY=:0
export XDG_RUNTIME_DIR=/run/user/1000
exec python -m app.main