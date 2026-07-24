#!/data/data/com.termux/files/usr/bin/bash
set +e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'
clear
echo -e "${CYAN}"
echo "========================================"
echo "   CAMORO SETUP - Termux & Linux"
echo "========================================"
echo -e "${NC}"
if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo -e "${RED}[!] Python not found${NC}"
    exit 1
fi
if [ -d "/data/data/com.termux" ]; then
    echo -e "${CYAN}[+] Termux detected${NC}"
    pkg update -y
    pkg install -y python git curl openssl libffi
    $PY -m pip install --upgrade pip setuptools wheel
else
    echo -e "${CYAN}[+] Linux detected${NC}"
    if command -v sudo >/dev/null 2>&1; then
        sudo apt-get update -y
        sudo apt-get install -y python3 python3-pip git curl
    fi
    $PY -m pip install --upgrade pip setuptools wheel
fi
echo ""
echo -e "${YELLOW}[*] Installing required packages...${NC}"
for pkg in requests beautifulsoup4 colorama urllib3 certifi tqdm; do
    echo -e "${CYAN}[+] Installing $pkg ...${NC}"
    if $PY -m pip install "$pkg" --no-cache-dir; then
        echo -e "${GREEN}    OK: $pkg${NC}"
    else
        echo -e "${RED}    FAIL: $pkg${NC}"
    fi
done
for pkg in pysocks; do
    $PY -m pip install "$pkg" --no-cache-dir 2>/dev/null || true
done
mkdir -p data/wordlists output/results output/profiles output/wordlists core
touch data/proxies.txt
if [ ! -f core/__init__.py ]; then
    printf '%s\n' '# Camoro core' > core/__init__.py
fi
echo ""
echo -e "${YELLOW}[*] Verifying...${NC}"
$PY - <<'EOF'
ok = True
for name, mod in [("requests", "requests"), ("bs4", "bs4"), ("colorama", "colorama")]:
    try:
        __import__(mod)
        print("  OK:", name)
    except Exception as e:
        print("  FAIL:", name, "->", e)
        ok = False
raise SystemExit(0 if ok else 1)
EOF
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}[+] Installation completed!${NC}"
    echo -e "${GREEN}[+] Run: python camoro.py${NC}"
else
    echo -e "${RED}[!] Failed. Run manually:${NC}"
    echo "    pip install requests beautifulsoup4 colorama"
fi
