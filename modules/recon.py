"""OSINT reconnaissance module — جمع معلومات الحساب."""

import json
import instaloader
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Optional

console = Console()

class InstaRecon:
    """Instagram account intelligence gathering."""

    def __init__(self, username: str):
        self.username = username
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            save_metadata=False,
            compress_json=False,
        )
        self.profile: Optional[instaloader.Profile] = None
        self.data: dict = {}

    def gather(self) -> dict:
        """Run full recon on target account."""
        console.print(Panel.fit(f"[bold cyan]🔍 Recon: @{self.username}[/bold cyan]", border_style="cyan"))

        try:
            self.profile = instaloader.Profile.from_username(self.loader.context, self.username)
        except instaloader.exceptions.ProfileNotExistsException:
            console.print(f"[red][✗] Account @{self.username} does not exist.[/red]")
            return {}
        except instaloader.exceptions.PrivateProfileNotFollowedException:
            console.print(f"[yellow][!] @{self.username} is PRIVATE — limited data available.[/yellow]")
            # Still gather public data
        except Exception as e:
            console.print(f"[red][✗] Error: {e}[/red]")
            return {}

        p = self.profile

        self.data = {
            "username": p.username,
            "full_name": p.full_name,
            "userid": str(p.userid),
            "followers": p.followers,
            "followees": p.followees,
            "posts_count": p.mediacount,
            "biography": p.biography,
            "external_url": p.external_url,
            "is_private": p.is_private,
            "is_verified": p.is_verified,
            "is_business": p.is_business_account,
            "business_category": p.business_category_name,
            "profile_pic_url": str(p.profile_pic_url) if p.profile_pic_url else "",
            "igtv_count": p.igtvcount,
            "has_guides": p.has_guides,
            "has_highlight_reels": p.has_highlight_reels,
        }

        # ── Extract keywords from bio ──
        if p.biography:
            self.data["bio_keywords"] = self._extract_keywords(p.biography)
            self.data["bio_emails"] = self._extract_emails(p.biography)
            self.data["bio_phones"] = self._extract_phones(p.biography)

        # ── Recent posts analysis ──
        try:
            posts = list(p.get_posts())[:20]
            captions = []
            hashtags = set()
            mentions = set()
            total_likes = 0
            total_comments = 0

            for post in posts:
                if post.caption:
                    captions.append(post.caption)
                    for word in post.caption.split():
                        if word.startswith("#"):
                            hashtags.add(word[1:])
                        if word.startswith("@"):
                            mentions.add(word[1:])
                total_likes += post.likes if post.likes else 0
                total_comments += post.comments if post.comments else 0

            n = len(posts)
            self.data["recent_hashtags"] = list(hashtags)
            self.data["recent_mentions"] = list(mentions)
            self.data["avg_likes"] = total_likes // n if n else 0
            self.data["avg_comments"] = total_comments // n if n else 0
            self.data["engagement_rate"] = (
                round(((total_likes + total_comments) / n / max(p.followers, 1)) * 100, 2)
                if n else 0
            )
            if captions:
                self.data["caption_keywords"] = self._extract_keywords(" ".join(captions))
        except Exception:
            pass  # limited posts available

        return self.data

    def _extract_keywords(self, text: str) -> list:
        """Extract meaningful keywords from text."""
        import re
        words = re.findall(r"[a-zA-Z0-9\u0600-\u06FF]{3,}", text)
        stopwords = {"the","and","for","that","this","with","you","have","are","not",
                     "but","all","can","was","has","had","from","they","will","been",
                     "من","على","في","الى","ان","هذا","التي","كان","هو","هي","لم","لن",
                     "حيث","كما","اذا","هذه","ذلك","عند","بعض","كل","قد","لا","ما",
                     "The","And","For","That","This","With","You","Have","Are","Not"}
        return list(set(w for w in words if w.lower() not in stopwords))

    def _extract_emails(self, text: str) -> list:
        import re
        return re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)

    def _extract_phones(self, text: str) -> list:
        import re
        return re.findall(r"[\+]?[0-9]{7,15}", text)

    def display(self):
        """Pretty-print gathered data."""
        if not self.data:
            return
        table = Table(title=f"🎯 @{self.data.get('username','?')}", show_header=True)
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        for k, v in self.data.items():
            if k in ("bio_keywords", "recent_hashtags", "recent_mentions", "caption_keywords"):
                v = ", ".join(v) if isinstance(v, list) else v
            if v is not None and v != "" and v != []:
                table.add_row(k.replace("_", " ").title(), str(v))

        console.print(table)

    def export(self, fmt: str = "json") -> str:
        """Export recon data to file."""
        fname = f"recon_{self.username}.{fmt}"
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        console.print(f"[green][✓] Saved: {fname}[/green]")
        return fname
