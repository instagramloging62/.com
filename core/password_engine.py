#!/usr/bin/env python3
import itertools
import re
from datetime import datetime

from .config import (
    LEET_MAP,
    MUTATION_PATTERNS,
    SPECIAL_CHARS,
    TARGET_PASSWORD_COUNT,
)

class PasswordEngine:
    def __init__(self, target_data=None, personal_info=None):
        self.target_data = target_data or {}
        self.personal_info = personal_info or {}
        self.passwords = set()
        self.base_words = set()
        self.years = set()
        self.numbers = set()
        self._build_seeds()

    def _build_seeds(self):
        username = str(self.target_data.get("username", "") or "").strip()
        if username:
            self.base_words.add(username)
            self.base_words.add(username.lower())
            self.base_words.add(username.capitalize())
            parts = re.split(r"[._\-]+", username)
            for p in parts:
                p = p.strip()
                if len(p) >= 2:
                    self.base_words.add(p)
                    self.base_words.add(p.lower())
                    self.base_words.add(p.capitalize())

        full_name = str(self.target_data.get("full_name", "") or "").strip()
        if full_name:
            self._add_name_variants(full_name)

        for name in self.target_data.get("extracted_names", []) or []:
            self._add_name_variants(str(name))

        for kw in self.target_data.get("extracted_keywords", []) or []:
            kw = str(kw).strip()
            if len(kw) >= 2:
                self.base_words.add(kw)
                self.base_words.add(kw.lower())
                self.base_words.add(kw.capitalize())

        for d in self.target_data.get("extracted_dates", []) or []:
            self._add_date_parts(str(d))

        pi = self.personal_info
        for key in (
            "real_name",
            "girlfriend_name",
            "pet_name",
            "favorite_thing",
            "nickname",
        ):
            val = str(pi.get(key, "") or "").strip()
            if val:
                self._add_name_variants(val)

        for w in pi.get("additional_words", []) or []:
            w = str(w).strip()
            if len(w) >= 2:
                self.base_words.add(w)
                self.base_words.add(w.lower())
                self.base_words.add(w.capitalize())

        phone = str(pi.get("phone_number", "") or "").strip()
        if phone:
            digits = re.sub(r"\D", "", phone)
            if digits:
                self.numbers.add(digits)
                if len(digits) >= 4:
                    self.numbers.add(digits[-4:])
                if len(digits) >= 6:
                    self.numbers.add(digits[-6:])
                if len(digits) >= 8:
                    self.numbers.add(digits[-8:])

        bd = str(pi.get("birth_date", "") or "").strip()
        if bd:
            self._add_date_parts(bd)

        day = str(pi.get("birth_day", "") or "").strip()
        month = str(pi.get("birth_month", "") or "").strip()
        year = str(pi.get("birth_year", "") or "").strip()
        if day:
            self.numbers.add(day.zfill(2))
            self.numbers.add(str(int(day)) if day.isdigit() else day)
        if month:
            self.numbers.add(month.zfill(2))
            self.numbers.add(str(int(month)) if month.isdigit() else month)
        if year:
            self.years.add(year)
            if len(year) == 4:
                self.years.add(year[2:])
                self.numbers.add(year)
                self.numbers.add(year[2:])

        current_year = datetime.now().year
        for y in range(current_year - 40, current_year + 2):
            self.years.add(str(y))
            self.years.add(str(y)[2:])

        for n in list(range(0, 100)) + [100, 111, 123, 321, 555, 666, 777, 888, 999, 1234, 1111, 0000]:
            self.numbers.add(str(n))
            self.numbers.add(str(n).zfill(2))
            self.numbers.add(str(n).zfill(3))
            self.numbers.add(str(n).zfill(4))

        # Common weak seeds if little personal data
        if len(self.base_words) < 3 and username:
            self.base_words.update(
                {
                    username,
                    username + "1",
                    "password",
                    "instagram",
                    "love",
                    "admin",
                }
            )

        self.base_words = {w for w in self.base_words if w and len(w) >= 2}
        self.years = {y for y in self.years if y}
        self.numbers = {n for n in self.numbers if n is not None and str(n) != ""}

    def _add_name_variants(self, name):
        name = str(name).strip()
        if not name:
            return
        self.base_words.add(name)
        self.base_words.add(name.lower())
        self.base_words.add(name.upper())
        self.base_words.add(name.capitalize())
        self.base_words.add(name.title().replace(" ", ""))
        parts = re.split(r"[\s._\-]+", name)
        clean_parts = []
        for p in parts:
            p = p.strip()
            if len(p) >= 2:
                clean_parts.append(p)
                self.base_words.add(p)
                self.base_words.add(p.lower())
                self.base_words.add(p.capitalize())
                self.base_words.add(p.upper())
        if len(clean_parts) >= 2:
            a, b = clean_parts[0], clean_parts[1]
            self.base_words.add(a + b)
            self.base_words.add(a.lower() + b.lower())
            self.base_words.add(a.capitalize() + b.capitalize())
            self.base_words.add(a + "_" + b)
            self.base_words.add(a[0].lower() + b.lower())
            self.base_words.add(a.lower() + b[0].lower())

    def _add_date_parts(self, date_str):
        date_str = str(date_str).strip()
        if not date_str:
            return
        parts = re.findall(r"\d+", date_str)
        if not parts:
            return
        for p in parts:
            self.numbers.add(p)
            if len(p) == 1:
                self.numbers.add(p.zfill(2))
            if len(p) == 4:
                self.years.add(p)
                self.years.add(p[2:])
                self.numbers.add(p[2:])
        if len(parts) >= 3:
            d, m, y = parts[0], parts[1], parts[2]
            combos = [
                d + m + y,
                d + m + y[-2:] if len(y) == 4 else d + m + y,
                d + m,
                m + d,
                y + m + d if len(y) >= 2 else "",
                d + m + y[-2:] if len(y) >= 2 else "",
            ]
            for c in combos:
                if c:
                    self.numbers.add(c)

    def _leet(self, word):
        return str(word).translate(LEET_MAP)

    def _apply_mutations(self, word):
        word = str(word)
        if not word:
            return
        specials = SPECIAL_CHARS if SPECIAL_CHARS else ["!", "@", "#", ".", "_", "*"]
        years = list(self.years)[:30]
        nums = list(self.numbers)[:80]

        candidates = {
            word,
            word.lower(),
            word.upper(),
            word.capitalize(),
            word + word,
            self._leet(word),
            self._leet(word.lower()),
        }

        for y in years:
            candidates.add(f"{word}{y}")
            candidates.add(f"{word.lower()}{y}")
            candidates.add(f"{word.capitalize()}{y}")
            candidates.add(f"{y}{word}")
            candidates.add(f"{word}_{y}")
            candidates.add(f"{word}@{y}")

        for n in nums:
            candidates.add(f"{word}{n}")
            candidates.add(f"{word.lower()}{n}")
            candidates.add(f"{word.capitalize()}{n}")
            candidates.add(f"{word}@{n}")
            candidates.add(f"{word}#{n}")
            candidates.add(f"{word}_{n}")
            candidates.add(f"{word}.{n}")

        for s in specials:
            candidates.add(f"{word}{s}")
            candidates.add(f"{word.lower()}{s}")
            candidates.add(f"{s}{word}")
            for n in nums[:20]:
                candidates.add(f"{word}{s}{n}")
                candidates.add(f"{word}{n}{s}")
            for y in years[:10]:
                candidates.add(f"{word}{y}{s}")
                candidates.add(f"{word}{s}{y}")

        for pattern_group in MUTATION_PATTERNS.values():
            for pattern in pattern_group:
                try:
                    if "{word}" in pattern and "{year}" in pattern:
                        for y in years[:15]:
                            candidates.add(
                                pattern.replace("{word}", word)
                                .replace("{year}", y)
                                .replace("{special}", specials[0])
                                .replace("{num}", "1")
                                .replace("{capitalize}", word.capitalize())
                                .replace("{leet}", self._leet(word))
                            )
                    elif "{word}" in pattern and "{num}" in pattern:
                        for n in nums[:20]:
                            candidates.add(
                                pattern.replace("{word}", word)
                                .replace("{num}", str(n))
                                .replace("{year}", years[0] if years else "2024")
                                .replace("{special}", specials[0])
                                .replace("{capitalize}", word.capitalize())
                                .replace("{leet}", self._leet(word))
                            )
                    elif "{word}" in pattern:
                        candidates.add(
                            pattern.replace("{word}", word)
                            .replace("{capitalize}", word.capitalize())
                            .replace("{leet}", self._leet(word))
                            .replace("{num}", "1")
                            .replace("{year}", years[0] if years else "2024")
                            .replace("{special}", specials[0])
                            .replace("{day}", "01")
                            .replace("{month}", "01")
                        )
                    elif "{leet}" in pattern:
                        candidates.add(
                            pattern.replace("{leet}", self._leet(word)).replace(
                                "{year}", years[0] if years else "2024"
                            )
                        )
                except Exception:
                    continue

        for c in candidates:
            c = str(c).strip()
            if 4 <= len(c) <= 40:
                self.passwords.add(c)

    def _combine_words(self):
        words = list(self.base_words)
        if len(words) < 2:
            return
        specials = SPECIAL_CHARS if SPECIAL_CHARS else ["", "_", ".", "@"]
        nums = list(self.numbers)[:30]
        years = list(self.years)[:15]

        for a, b in itertools.islice(itertools.permutations(words, 2), 200):
            combos = [
                f"{a}{b}",
                f"{a}_{b}",
                f"{a}.{b}",
                f"{a}{b}".lower(),
                f"{a.capitalize()}{b.capitalize()}",
                f"{a.lower()}{b.lower()}",
            ]
            for c in combos:
                if 4 <= len(c) <= 40:
                    self.passwords.add(c)
                for n in nums[:10]:
                    p = f"{c}{n}"
                    if 4 <= len(p) <= 40:
                        self.passwords.add(p)
                for y in years[:8]:
                    p = f"{c}{y}"
                    if 4 <= len(p) <= 40:
                        self.passwords.add(p)
                for s in specials:
                    if not s:
                        continue
                    p = f"{c}{s}"
                    if 4 <= len(p) <= 40:
                        self.passwords.add(p)

    def generate_passwords(self, target_count=None):
        target = target_count or TARGET_PASSWORD_COUNT
        self.passwords = set()

        for word in list(self.base_words):
            self._apply_mutations(word)

        self._combine_words()

        # Extra common patterns
        commons = [
            "123456",
            "password",
            "12345678",
            "qwerty",
            "abc123",
            "111111",
            "123123",
            "admin",
            "letmein",
            "welcome",
            "monkey",
            "dragon",
            "master",
            "login",
            "princess",
            "football",
            "iloveyou",
            "instagram",
            "passw0rd",
            "pass123",
        ]
        username = str(self.target_data.get("username", "") or "")
        for c in commons:
            self.passwords.add(c)
            if username:
                self.passwords.add(username + c)
                self.passwords.add(c + username)

        # Pad / fill up to target with more numeric mutations
        words = list(self.base_words) or ["user", "pass"]
        i = 0
        while len(self.passwords) < target and i < target * 3:
            w = words[i % len(words)]
            n = i % 10000
            variants = [
                f"{w}{n}",
                f"{w.lower()}{n}",
                f"{w.capitalize()}{n}",
                f"{w}{n:04d}",
                f"{w}@{n}",
                f"{w}_{n}",
                f"{w}{n}!",
                f"{self._leet(w)}{n}",
                f"{w}{datetime.now().year - (i % 30)}",
            ]
            for v in variants:
                if 4 <= len(v) <= 40:
                    self.passwords.add(v)
                if len(self.passwords) >= target:
                    break
            i += 1

        result = sorted(self.passwords, key=lambda x: (len(x), x))
        if len(result) > target:
            result = result[:target]
        self.passwords = set(result)
        return result
