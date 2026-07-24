#!/usr/bin/env python3
import os
import random

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
WORDLIST_DIR = os.path.join(DATA_DIR, "wordlists")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "results")
PROXY_FILE = os.path.join(DATA_DIR, "proxies.txt")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(WORDLIST_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(PROXY_FILE):
    with open(PROXY_FILE, "w", encoding="utf-8") as f:
        f.write("# Put one proxy per line\n")
        f.write("# ip:port\n")
        f.write("# ip:port:user:pass\n")
        f.write("# http://ip:port\n")
        f.write("# socks5://ip:port\n")

INSTAGRAM_ENDPOINTS = {
    "login": "https://www.instagram.com/api/v1/web/accounts/login/ajax/",
    "profile_info": "https://www.instagram.com/{username}/?__a=1",
    "graphql": "https://www.instagram.com/graphql/query",
    "web_profile": "https://i.instagram.com/api/v1/users/web_profile_info/",
}

USER_AGENTS = [
    "Instagram 289.0.0.30.120 Android (30/11; 420dpi; 1080x2340; samsung; SM-G998B; star2qlte; qcom; en_US; 507584516)",
    "Instagram 275.0.0.27.98 Android (29/10; 480dpi; 1080x1920; Xiaomi; Redmi Note 9; merlin; mt6768; en_GB; 462859381)",
    "Instagram 280.0.0.18.111 Android (31/12; 320dpi; 720x1600; HUAWEI; LIO-L29; hwLIO; kirin990; en_US; 479234167)",
    "Instagram 270.0.0.21.115 Android (28/9; 560dpi; 1440x2960; samsung; SM-N975F; d2s; exynos9820; en_US; 441762849)",
    "Instagram 288.0.0.30.118 (iPhone14,3; iOS 16.5; en_US; en; scale=3.00; 1284x2778; 509625743)",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "*/*",
        "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8", "ar;q=0.9,en;q=0.7"]),
        "Accept-Encoding": "gzip, deflate, br",
        "X-IG-App-ID": "936619743392459",
        "X-IG-Connection-Type": random.choice(["WIFI", "4G", "5G"]),
        "X-IG-Capabilities": "3brTvwE=",
        "X-IG-App-Locale": random.choice(["en_US", "en_GB", "ar_SA"]),
        "X-Device-ID": "android-{}".format(random.randint(1000000000, 9999999999)),
        "X-IG-Connection-Speed": "{}kbps".format(random.randint(1000, 15000)),
        "Origin": "https://www.instagram.com",
        "Referer": "https://www.instagram.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }

MUTATION_PATTERNS = {
    "basic": [
        "{word}",
        "{word}{year}",
        "{word}{num}",
        "{word}@{num}",
        "{word}#{num}",
        "{word}!",
        "{word}.",
    ],
    "advanced": [
        "{word}{year}{special}",
        "{word}_{num}",
        "{word}{month}{day}",
        "{capitalize}{num}",
        "{leet}",
        "{word}{day}{month}",
    ],
    "complex": [
        "{word1}{word2}{num}",
        "{word1}_{word2}",
        "{word1}{word2}{year}",
        "{word1}{special}{word2}{num}",
        "{leet}{year}",
    ],
}

LEET_MAP = str.maketrans({
    "a": "4", "A": "4",
    "e": "3", "E": "3",
    "i": "1", "I": "1",
    "o": "0", "O": "0",
    "s": "5", "S": "5",
    "t": "7", "T": "7",
    "b": "8", "B": "8",
    "g": "9", "G": "9",
    "l": "1", "L": "1",
})

# --- required by password_engine.py ---
SPECIAL_CHARS = ["!", "@", "#", "$", "%", "*", ".", "_", "?", "&"]

MIN_DELAY = 2
MAX_DELAY = 8
MAX_ATTEMPTS_PER_IP = 15
COOLDOWN_PERIOD = 120
TARGET_PASSWORD_COUNT = 18000
MAX_COMBINATIONS = 50000
