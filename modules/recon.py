import json
import re
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13; SM-S908B) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Mobile Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "X-IG-App-ID": "936619743392459",
}


class Recon:
    def __init__(self, username: str):
        self.username = username.lstrip("@").strip()
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.data = {}

    def gather(self) -> dict:
        console.print(Panel.fit(
            f"[bold cyan]🔍 CAMORRO RECON → @{self.username}[/bold cyan]",
            border_style="cyan"
        ))

        # Method 1: web profile API
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={self.username}"
        try:
            r = self.session.get(url, timeout=20)
            if r.status_code == 200:
                user = r.json()["data"]["user"]
                self.data = self._parse_user(user)
                return self.data
        except Exception:
            pass

        # Method 2: public page JSON
        try:
            r = self.session.get(
                f"https://www.instagram.com/{self.username}/?__a=1&__d=dis",
                timeout=20
            )
            if r.status_code == 200 and "graphql" in r.text:
                user = r.json()["graphql"]["user"]
                self.data = self._parse_user(user)
                return self.data
        except Exception:
            pass

        # Method 3: scrape HTML meta
        try:
            r = self.session.get(f"https://www.instagram.com/{self.username}/", timeout=20)
            if r.status_code != 200:
                console.print(f"[red][✗] Account not found or blocked (HTTP {r.status_code})[/red]")
                return {}
            self.data = self._parse_html(r.text)
            return self.data
        except Exception as e:
            console.print(f"[red][✗] Recon failed: {e}[/red]")
            return {}

    def _parse_user(self, u: dict) -> dict:
        bio = u.get("biography") or u.get("bio") or ""
        return {
            "username": u.get("username", self.username),
            "full_name": u.get("full_name", ""),
            "userid": str(u.get("id") or u.get("pk") or ""),
            "followers": (u.get("edge_followed_by") or {}).get("count") or u.get("follower_count") or 0,
            "following": (u.get("edge_follow") or {}).get("count") or u.get("following_count") or 0,
            "posts": (u.get("edge_owner_to_timeline_media") or {}).get("count") or u.get("media_count") or 0,
            "biography": bio,
            "is_private": u.get("is_private", False),
            "is_verified": u.get("is_verified", False),
            "external_url": u.get("external_url") or "",
            "profile_pic": u.get("profile_pic_url_hd") or u.get("profile_pic_url") or "",
            "emails": re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", bio),
            "phones": re.findall(r"\+?\d{8,15}", bio),
            "keywords": self._keywords(bio),
        }

    def _parse_html(self, html: str) -> dict:
        def meta(prop):
            m = re.search(rf'property="{prop}" content="([^"]*)"', html)
            return m.group(1) if m else ""

        title = meta("og:title")
        desc = meta("og:description")
        # Example desc: "1,234 Followers, 56 Following, 78 Posts - See Instagram photos..."
        nums = re.findall(r"([\d,\.]+)\s*(Followers|Following|Posts)", desc, re.I)
        mapped = {k.lower(): int(v.replace(",", "").replace(".", "")) for v, k in nums}

        return {
            "username": self.username,
            "full_name": title.split("(")[0].strip() if title else "",
            "userid": "",
            "followers": mapped.get("followers", 0),
            "following": mapped.get("following", 0),
            "posts": mapped.get("posts", 0),
            "biography": desc,
            "is_private": "private" in html.lower(),
            "is_verified": False,
            "external_url": meta("og:url"),
            "profile_pic": meta("og:image"),
            "emails": re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", fixed := desc),
            "phones": re.findall(r"\+?\d{8,15}", desc),
            "keywords": self._keywords(desc),
        }

    def _keywords(self, text: str) -> list:
        words = re.findall(r"[A-Za-z0-9\u0600-\u06FF]{3,}", text or "")
        stop = {"the", "and", "for", "with", "from", "من", "على", "في", "الى", "هذا", "هذه", "كان"}
        return sorted({w for w in words if w.lower() not in stop})[:40]

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
        path = path or f"recon_{self.username}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        console.print(f"[green][✓] Saved: {path}[/green]")
        return path
