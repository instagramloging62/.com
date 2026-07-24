import json
import os
import re
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DIRS = ["wordlists", "reports", "sessions", "found", "avatars"]


def ensure_dirs():
    for d in DIRS:
        (BASE / d).mkdir(exist_ok=True)


def load_config() -> dict:
    path = BASE / "config.json"
    defaults = {
        "delay_min": 3.0,
        "delay_max": 5.0,
        "default_wordlist_size": 18000,
        "proxy_file": "proxies.txt",
        "rotate_proxy_every": 10,
        "rate_limit_sleep": 60,
        "max_rate_hits": 20,
        "user_agent_rotate": True,
        "save_every": 25,
        "timeout": 20,
    }
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                defaults.update(json.load(f))
        except Exception:
            pass
    return defaults


def clean_username(u: str) -> str:
    return (u or "").strip().lstrip("@").split("?")[0].split("/")[-1]


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path, default=None):
    if not os.path.exists(path):
        return default if default is not None else {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def append_found(username: str, password: str, note: str = ""):
    ensure_dirs()
    line = f"{username}:{password}"
    if note:
        line += f"  # {note}"
    path = BASE / "found" / "FOUND_ALL.txt"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    solo = BASE / "found" / f"FOUND_{username}.txt"
    with open(solo, "w", encoding="utf-8") as f:
        f.write(f"{username}:{password}\n")
    return str(solo)


def parse_targets_file(path: str) -> list:
    """Supports: username OR user:pass OR @user"""
    out = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            if ":" in ln:
                u, p = ln.split(":", 1)
                out.append({"username": clean_username(u), "password": p})
            else:
                out.append({"username": clean_username(ln), "password": None})
    return out


def extract_ig_username(text: str) -> str:
    """Accepts username, @user, or full Instagram URL."""
    text = (text or "").strip()
    m = re.search(r"instagram\.com/([A-Za-z0-9._]+)", text)
    if m:
        return clean_username(m.group(1))
    return clean_username(text)
