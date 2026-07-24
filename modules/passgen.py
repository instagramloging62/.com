import itertools
from rich.console import Console

console = Console()


class PassGen:
    SUFFIXES = [
        "", "1", "12", "123", "1234", "12345", "123456", "123456789",
        "!", "@", "#", "$", "!!", "@@",
        "2020", "2021", "2022", "2023", "2024", "2025", "2026",
        "00", "01", "07", "10", "11", "99",
        "Insta", "instagram", "ig",
    ]
    PREFIXES = ["", "!", "@", "#", "1", "12"]
    LEET = str.maketrans({
        "a": "@", "A": "4", "e": "3", "E": "3",
        "i": "1", "I": "1", "o": "0", "O": "0",
        "s": "$", "S": "5", "t": "7", "T": "7",
    })

    def ask_personal_info(self) -> dict:
        console.print("\n[bold yellow]═══ معلومات الهدف (لإخراج كلمات سر واقعية) ═══[/bold yellow]")
        console.print("[dim]Enter للتخطي[/dim]\n")
        keys = [
            ("first_name", "الاسم الشخصي"),
            ("last_name", "اسم العائلة"),
            ("nickname", "الكنية / username"),
            ("birth_day", "يوم الميلاد (1-31)"),
            ("birth_month", "شهر الميلاد (1-12)"),
            ("birth_year", "سنة الميلاد (مثال 1998)"),
            ("phone_last4", "آخر 4 أرقام هاتف"),
            ("city", "المدينة"),
            ("pet", "اسم حيوان أليف"),
            ("partner", "اسم الشريك"),
            ("extra", "كلمات إضافية (مفصولة بفاصلة)"),
        ]
        info = {}
        for k, label in keys:
            info[k] = input(f"  {label}: ").strip()
        return info

    def generate(self, info: dict, username: str = "", target: int = 18000) -> list:
        console.print("\n[cyan]🧠 توليد قاموس كلمات المرور...[/cyan]")
        bases = set()

        def add(*vals):
            for v in vals:
                v = (v or "").strip()
                if len(v) >= 2:
                    bases.add(v)
                    bases.add(v.lower())
                    bases.add(v.upper())
                    bases.add(v.capitalize())
                    bases.add(v.translate(self.LEET))

        first = info.get("first_name", "")
        last = info.get("last_name", "")
        nick = info.get("nickname", "") or username
        add(first, last, nick, username, info.get("city"), info.get("pet"), info.get("partner"))

        if first and last:
            add(f"{first}{last}", f"{first}_{last}", f"{first}.{last}",
                f"{first[0]}{last}", f"{last}{first}")

        try:
            d = int(info.get("birth_day") or 0)
            m = int(info.get("birth_month") or 0)
            y = int(info.get("birth_year") or 0)
        except ValueError:
            d = m = y = 0

        if y:
            add(str(y), str(y)[2:])
        if d and m:
            add(f"{d:02d}{m:02d}", f"{m:02d}{d:02d}")
        if d and m and y:
            add(
                f"{d:02d}{m:02d}{str(y)[2:]}", f"{d:02d}{m:02d}{y}",
                f"{first}{y}", f"{nick}{y}", f"{first}{d:02d}{m:02d}",
                f"{nick}{d:02d}{m:02d}", f"{first}{str(y)[2:]}",
            )

        phone = info.get("phone_last4", "")
        if phone:
            add(phone)

        for x in (info.get("extra") or "").split(","):
            add(x.strip())

        # common weak base
        add("password", "qwerty", "iloveyou", "instagram", "admin", "123456", "camorro")

        out = set()
        for b in list(bases):
            for pre, suf in itertools.product(self.PREFIXES, self.SUFFIXES):
                out.add(f"{pre}{b}{suf}")
                if len(out) >= target * 2:
                    break
            if len(out) >= target * 2:
                break

        # rank short/realistic first
        ranked = sorted(out, key=lambda p: (len(p), p))
        result = ranked[:target]
        console.print(f"[green][✓] Generated {len(result)} passwords[/green]")
        return result

    def save(self, passwords: list, username: str) -> str:
        path = f"wordlist_{username}.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(passwords))
        console.print(f"[green][✓] Wordlist: {path}[/green]")
        return path
