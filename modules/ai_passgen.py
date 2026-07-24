"""AI-powered password dictionary generator — مولد القاموس الذكي.

يأخذ معلومات شخصية عن الهدف (اسم، تاريخ ميلاد، هوايات، كلمات مفتاحية...)
وينتج قاموس كلمات مرور محتملة بناءً على أنماط بشرية شائعة.
"""

from typing import List, Set, Optional
from modules.mutator import PasswordMutator
from rich.console import Console

console = Console()

class AIPasswordGenerator:
    """Smart password dictionary generator using personal data."""

    def __init__(self):
        self.base_words: Set[str] = set()
        self.passwords: Set[str] = set()

    def collect_personal_info_interactive(self) -> dict:
        """Interactive mode: ask user for target personal info."""
        console.print("\n[bold yellow]═══ Target Personal Information ═══[/bold yellow]")
        console.print("[dim](Press Enter to skip any field)[/dim]\n")

        info = {}
        info["first_name"] = input("  First name: ").strip()
        info["last_name"] = input("  Last name: ").strip()
        info["nickname"] = input("  Nickname / alias: ").strip()
        info["birth_day"] = input("  Birth day (1-31): ").strip()
        info["birth_month"] = input("  Birth month (1-12): ").strip()
        info["birth_year"] = input("  Birth year (e.g. 1998): ").strip()
        info["pet_name"] = input("  Pet name: ").strip()
        info["partner_name"] = input("  Partner / spouse name: ").strip()
        info["child_name"] = input("  Child name: ").strip()
        info["favorite_team"] = input("  Favorite sports team: ").strip()
        info["favorite_artist"] = input("  Favorite artist/band: ").strip()
        info["favorite_city"] = input("  Favorite city / hometown: ").strip()
        info["phone_last4"] = input("  Last 4 digits of phone: ").strip()
        info["extra_keywords"] = input("  Extra keywords (comma separated): ").strip()

        return info

    def generate_from_personal_info(self, info: dict, target_count: int = 18000) -> List[str]:
        """Generate password dictionary from personal info."""
        console.print("\n[bold cyan]🧠 AI Password Generator — Building dictionary...[/bold cyan]")

        # ── Step 1: Extract base tokens ──
        tokens = set()

        # Name components
        first = info.get("first_name", "")
        last = info.get("last_name", "")
        nick = info.get("nickname", "")

        for name in [first, last, nick]:
            if name and len(name) >= 2:
                tokens.add(name.lower())
                tokens.add(name)
                tokens.add(name.upper())

        # Combined names
        if first and last:
            for combo in [
                f"{first}{last}", f"{first}_{last}", f"{first}.{last}",
                f"{first[0]}{last}", f"{first}{last[0]}",
                f"{last}{first}", f"{last}_{first}",
            ]:
                tokens.add(combo)
                tokens.add(combo.lower())

        if nick and last:
            tokens.add(f"{nick}{last}")
            tokens.add(f"{nick}_{last}")

        # Dates
        try:
            day = int(info.get("birth_day", 0))
            month = int(info.get("birth_month", 0))
            year = int(info.get("birth_year", 0))
        except ValueError:
            day = month = year = 0

        date_tokens = PasswordMutator.date_formats(
            day if day > 0 else None,
            month if month > 0 else None,
            year if year > 0 else None,
        )
        tokens.update(date_tokens)

        # Year alone
        if year:
            tokens.update([str(year), str(year)[2:]])

        # Other personal info
        for key in ["pet_name", "partner_name", "child_name",
                     "favorite_team", "favorite_artist", "favorite_city"]:
            val = info.get(key, "")
            if val and len(val) >= 2:
                tokens.add(val)
                tokens.add(val.lower())
                tokens.add(val.upper())
                tokens.add(val.capitalize())

        # Phone digits
        phone = info.get("phone_last4", "")
        if phone and len(phone) >= 4:
            tokens.add(phone)

        # Extra keywords
        extra = info.get("extra_keywords", "")
        for kw in extra.split(","):
            kw = kw.strip()
            if kw and len(kw) >= 2:
                tokens.add(kw)
                tokens.add(kw.lower())

        # ── Step 2: Add common weak passwords ──
        common_weak = [
            "password", "Password", "PASSWORD", "passw0rd", "P@ssw0rd",
            "instagram", "Instagram", "INSTAGRAM", "insta", "Insta",
            "admin", "Admin", "ADMIN", "adm1n",
            "qwerty", "Qwerty", "QWERTY", "qwerty123",
            "iloveyou", "Iloveyou", "ILOVEYOU",
            "princess", "sunshine", "dragon", "monkey", "football",
            "baseball", "hockey", "soccer", "charlie", "michael",
            "ashley", "nicole", "jessica", "jennifer", "amanda",
            "andrew", "joshua", "daniel", "matthew", "anthony",
            "shadow", "master", "killer", "hunter", "ranger",
            "batman", "superman", "ironman", "spiderman",
            "123456", "12345678", "123456789", "1234567890",
            "111111", "000000", "121212", "131313",
            "abc123", "qwerty123", "asdfgh", "zxcvbn",
            "letmein", "trustno1", "welcome", "whatever",
        ]
        tokens.update(common_weak)

        # ── Step 3: Apply mutations to each token ──
        console.print(f"[dim]  Base tokens: {len(tokens)}[/dim]")

        all_passwords = set()

        # Custom suffix list with birth year + common combos
        suffixes = list(PasswordMutator.COMMON_SUFFIXES)
        if year:
            suffixes.extend([str(year), str(year)[2:], f"@{str(year)[2:]}"])
        if day and month:
            suffixes.extend([
                f"{day:02d}{month:02d}", f"{month:02d}{day:02d}"
            ])

        for token in tokens:
            if len(token) < 2:
                continue
            mutated = PasswordMutator.mutate(token, suffixes=suffixes)
            all_passwords.update(mutated)

            # If not enough, also try combining tokens
            if len(all_passwords) < target_count:
                for token2 in list(tokens)[:30]:
                    combined = f"{token}{token2}"
                    all_passwords.update(PasswordMutator.mutate(combined[:20], suffixes=suffixes[:15]))

        # ── Step 4: Combine name+date patterns ──
        if first and year:
            patterns = [
                f"{first}{year}", f"{first}_{year}", f"{first}@{year}",
                f"{first.capitalize()}{year}", f"{first.upper()}{year}",
                f"{first}{str(year)[2:]}", f"{first.capitalize()}{str(year)[2:]}",
            ]
            for p in patterns:
                all_passwords.update(PasswordMutator.mutate(p, suffixes=PasswordMutator.COMMON_SUFFIXES[:10]))

        if first and day and month:
            dm = f"{day:02d}{month:02d}"
            patterns = [f"{first}{dm}", f"{first.capitalize()}{dm}"]
            for p in patterns:
                all_passwords.update(PasswordMutator.mutate(p, suffixes=PasswordMutator.COMMON_SUFFIXES[:10]))

        # ── Step 5: Trim to target ──
        passwords_list = list(all_passwords)
        passwords_list.sort(key=lambda x: (len(x), x))

        if len(passwords_list) > target_count:
            # Prioritize shorter passwords + those with special chars
            scored = [(p, len(p) - (5 if any(c in "!@#$%&*" for c in p) else 0)) for p in passwords_list]
            scored.sort(key=lambda x: x[1])
            passwords_list = [p for p, _ in scored[:target_count]]

        console.print(f"[green][✓] Generated {len(passwords_list)} passwords[/green]")
        return passwords_list

    def save_wordlist(self, passwords: List[str], filename: str = None, username: str = None) -> str:
        """Save generated passwords to file."""
        if filename is None:
            filename = f"wordlist_{username or 'target'}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for p in passwords:
                f.write(p + "\n")
        console.print(f"[green][✓] Wordlist saved: {filename} ({len(passwords)} passwords)[/green]")
        return filename
