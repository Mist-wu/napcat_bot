#!/bin/bash
set -x
echo "进入工作目录"
cd /root/napcat_bot

echo "拉取最新代码"
git fetch --all
git reset --hard origin/main

echo "关闭旧的 bot screen 会话"
screen -S bot -X quit

echo "重启 bot"
screen -dmS bot bash -c "source venv/bin/activate && python3 main.py"