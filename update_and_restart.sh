git pull origin main
screen -S bot -X quit
cd /root/napcat_bot
source venv/bin/activate
screen -S bot python3 main.py
