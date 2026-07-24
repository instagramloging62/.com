# CAMORRO

Instagram authorized security testing tool:
- OSINT recon
- Smart password wordlist generation
- Brute force login with live progress

## Install (Termux)

```bash
pkg update && pkg upgrade -y
pkg install python git -y
git clone https://github.com/camorro5/camorro.git
cd camorro
pip install -r requirements.txt
python camorro.py
