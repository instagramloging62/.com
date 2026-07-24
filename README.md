# CAMORRO v3

Instagram authorized testing toolkit:
- OSINT Recon + avatar download
- Smart password generator (18000+)
- Brute force with live progress
- Proxy rotation
- Resume attack
- Multi-target / combo
- HTML reports

## Install (Termux)
```bash
pkg update && pkg upgrade -y
pkg install python git -y
git clone https://github.com/camorro5/camorro.git
cd camorro
pip install -r requirements.txt
python camorro.py
