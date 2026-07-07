@echo off
echo =======================================
echo Context Compiler Auto-Updater
echo =======================================

echo 1. Pulling latest code from GitHub...
git pull origin master

echo 2. Installing requirements...
pip install -r requirements.txt
pip install pyinstaller

echo 3. Building AgentSmith.exe...
pyinstaller --noconfirm --onedir --windowed --name "AgentSmith" main.py

echo =======================================
echo Update and Build Complete!
echo Restarting AgentSmith...
echo =======================================

start "" "dist\AgentSmith\AgentSmith.exe"
exit
