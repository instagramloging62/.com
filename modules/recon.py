import json
import re
import requests
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from modules.utils import ensure_dirs, BASE, clean_username

console = Console()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13; SM-S908B) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Mobile Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "X-IG-App-ID": "936619743392459",
    "X-ASBD-ID": "129477",
    "X-IG-WWW-Claim": "0",
}


class Recon:
    def __init__(self, username: str, proxies: dict = None, timeout: int = 20):
        self.username = clean_username(username)
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.proxies = proxies or {}
        self.timeout = timeout
        self.data = {}

    def exists(self) -> bool:
        """Feature: check if username exists."""
        try:
            r = self.session.get(
                f"https://www.instagram.com/{self.username}/",
                timeout=self.timeout,
                proxies=self.proxies,
                allow_redirects=True,
            )
            if r.status_code == 404:
                return False
            if "Sorry, this page isn't available" in r.text:
                return False
            return r.status_code == 200
        except Exception:
            return False

    def gather(self) -> dict:
        console.print(Panel.fit(
            f"[bold cyan]🔍 CAMORRO RECON → @{self.username}[/bold cyan]",
            border_style="cyan",
        ))

        if not self.exists():
            console.print(f"[red][✗] Account @{self.username} not found[/red]")
            return {}

        # warm-up homepage cookies
        try:
            self.session.get("https://www.instagram.com/", timeout=self.timeout, proxies=self.proxies)
        except Exception:
            pass

        # Method 1: web_profile_info
        try:
            url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={self.username}"
            r = self.session.get(url, timeout=self.timeout, proxies=self.proxies)
            if r.status_code == 200:
                user = r.json()["data"]["user"]
                self.data = self._parse_user(user)
                self._enrich_from_html()
                return self.data
        except Exception:
            pass

        # Method 2: HTML meta fallback
        try:
            r = self.session.get(
                f"https://www.instagram.com/{self.username}/",
                timeout=self.timeout,
                proxies=self.proxies,
            )
            if r.status_code != 200:
                console.print(f"[red][✗] HTTP {r.status_code}[/red]")
                return {}
            self.data = self._parse_html(r.text)
            return self.data
        except Exception as e:
            console.print(f"[red][✗] Recon failed: {e}[/red]")
            return {}

    def _enrich_from_html(self):
        """Try extract more keywords from public page."""
        try:
            r = self.session.get(
                f"https://www.instagram.com/{self.username}/",
                timeout=self.timeout,
                proxies=self.proxies,
            )
            # hashtags / mentions in embedded JSON-ish content
            tags = set(re.findall(r"#([A-Za-z0-9_\u0600-\u06FF]{2,})", r.text))
            ments = set(re.findall(r"@([A-Za-z0-9._]{2,})", r.text))
            self.data["page_hashtags"] = sorted(list(tags))[:30]
            self.data["page_mentions"] = sorted(
                [m for m in ments if m.lower() != self.username.lower()]
            )[:30]
            self.data["keywords"] = sorted(
                set(self.data.get("keywords", []) + self.data.get("page_hashtags", []))
            )[:50]
        except Exception:
            pass

    def _parse_user(self, u: dict) -> dict:
        bio = u.get("biography") or ""
        return {
            "username": u.get("username", self.username),
            "full_name": u.get("full_name", ""),
            "userid": str(u.get("id") or ""),
            "followers": (u.get("edge_followed_by") or {}).get("count", 0),
            "following": (u.get("edge_follow") or {}).get("count", 0),
            "posts": (u.get("edge_owner_to_timeline_media") or {}).get("count", 0),
            "biography": bio,
            "is_private": u.get("is_private", False),
            "is_verified": u.get("is_verified", False),
            "is_business": u.get("is_business_account", False),
            "category": u.get("category_name") or u.get("business_category_name") or "",
            "external_url": u.get("external_url") or "",
            "profile_pic": u.get("profile_pic_url_hd") or u.get("profile_pic_url") or "",
            "emails": re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", bio),
            "phones": re.findall(r"\+?\d{8,15}", bio),
            "keywords": self._keywords(bio + " " + (u.get("full_name") or "")),
        }

    def _parse_html(self, html: str) -> dict:
        def meta(prop):
            m = re.search(rf'property="{re.escape(prop)}" content="([^"]*)"', html)
            return m.group(1) if m else ""

        title = meta("og:title")
        desc = meta("og:description")
        nums = re.findall(r"([\d,.]+)\s*(Followers|Following|Posts)", desc, re.I)
        mapped = {}
        for v, k in nums:
            mapped[k.lower()] = int(v.replace(",", "").replace(".", ""))

        return {
            "username": self.username,
            "full_name": title.split("(")[0].strip() if title else "",
            "userid": "",
            "followers": mapped.get("followers", 0),
            "following": mapped.get("following", 0),
            "posts": mapped.get("posts", 0),
            "biography": desc,
            "is_private": "is_private\":true" in html or "This Account is Private" in html,
            "is_verified": False,
            "is_business": False,
            "category": "",
            "external_url": meta("og:url"),
            "profile_pic": meta("og:image"),
            "emails": re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", desc),
            "phones": re.findall(r"\+?\d{8,15}", desc),
            "keywords": self._keywords(desc + " " + title),
        }

    def _keywords(self, text: str) -> list:
        words = re.findall(r"[A-Za-z0-9\u0600-\u06FF]{3,}", text or "")
        stop = {
            "the", "and", "for", "with", "from", "instagram", "photos", "videos",
            "see", "followers", "following", "posts",
            "من", "على", "في", "الى", "هذا", "هذه", "كان", "التي",
        }
        return sorted({w for w in words if w.lower() not in stop})[:40]

    def download_avatar(self) -> str:
        """Feature: download profile picture."""
        ensure_dirs()
        url = (self.data or {}).get("profile_pic")
        if not url:
            console.print("[yellow][!] No profile pic URL[/yellow]")
            return ""
        try:
            r = self.session.get(url, timeout=self.timeout, proxies=self.proxies)
            path = BASE / "avatars" / f"{self.username}.jpg"
            path.write_bytes(r.content)
            console.print(f"[green][✓] Avatar saved: {path}[/green]")
            return str(path)
        except Exception as e:
            console.print(f"[red][✗] Avatar failed: {e}[/red]")
            return ""

    def display(self):
        if not self.data:
            return
        t = Table(title=f"🎯 @{self.data.get('username')}", show_header=True)
        t.add_column("Field", style="cyan")
        t.add_column("Value", style="green")
        for k, v in self.data.items():
            if v in ("", None, [], {}):
                continue
            if isinstance(v, list):
                v = ", ".join(map(str, v))
            t.add_row(k.replace("_", " ").title(), str(v))
        console.print(t)

    def export(self, path: str = None) -> str:
        ensure_dirs()
        path = path or str(BASE / "reports" / f"recon_{self.username}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        console.print(f"[green][✓] Saved: {path}[/green]")
        return path
