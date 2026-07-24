#!/usr/bin/env python3
import itertools
import random
from datetime import datetime
from .config import MUTATION_PATTERNS, LEET_MAP, TARGET_PASSWORD_COUNT
from .banner import C, Y, G, RE

class PasswordEngine:
    def __init__(self, target_data, personal_info):
        self.target_data = target_data or {}
        self.personal = personal_info or {}
        self.word_pool = []
        self._build_word_pool()

    def _build_word_pool(self):
        pool = set()
        pool.update(self.target_data.get("extracted_names", []) or [])
        pool.update(self.target_data.get("extracted_keywords", []) or [])

        username = (self.target_data.get("username", "") or "").lower()
        if username:
            pool.add(username)
            pool.add(username.replace("_", "").replace(".", ""))

        if self.personal.get("real_name"):
            parts = self.personal["real_name"].lower().split()
            pool.update(parts)
            pool.add(self.personal["real_name"].lower().replace(" ", ""))
            if parts:
                pool.add(parts[0])
                pool.add(parts[0].capitalize())

        for key in ("girlfriend_name", "pet_name", "nickname", "favorite_thing"):
            val = self.personal.get(key)
            if val:
                v = str(val).lower()
                pool.add(v)
                pool.add(v.capitalize())
                pool.update(v.split())

        phone = str(self.personal.get("phone_number", "") or "")
        if phone:
            pool.add(phone)
            if len(phone) >= 4:
                pool.add(phone[-4:])
            if len(phone) >= 6:
                pool.add(phone[-6:])

        for w in self.personal.get("additional_words", []) or []:
            if w:
                pool.add(str(w).lower())

        self.word_pool = list(dict.fromkeys([w for w in pool if w and len(str(w)) > 1]))
        self.word_pool.sort(key=len, reverse=True)

    def _get_date_components(self):
        components = {
            "day": "", "month": "", "year": "", "short_year": "",
            "day_month": "", "month_day": "", "day_month_year": "",
            "month_day_year": "", "full_date": "", "reverse_date": "",
            "short_date": "", "month_name": "",
        }
        birth = self.personal.get("birth_date", "") or ""
        day = self.personal.get("birth_day", "") or ""
        month = self.personal.get("birth_month", "") or ""
        year = self.personal.get("birth_year", "") or ""

        if birth:
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y", "%m/%d/%Y"):
                try:
                    dt = datetime.strptime(birth, fmt)
                    day, month, year = str(dt.day).zfill(2), str(dt.month).zfill(2), str(dt.year)
                    break
                except ValueError:
                    continue

        if day:
            components["day"] = str(day).zfill(2)
        if month:
            components["month"] = str(month).zfill(2)
            try:
                names = ["january","february","march","april","may","june","july","august","september","october","november","december"]
                idx = int(month) - 1
                if 0 <= idx < 12:
                    components["month_name"] = names[idx]
            except ValueError:
                pass
        if year:
            components["year"] = str(year)
            components["short_year"] = str(year)[-2:]

        if components["day"] and components["month"] and components["year"]:
            d, m, y = components["day"], components["month"], components["year"]
            components["day_month"] = f"{d}{m}"
            components["month_day"] = f"{m}{d}"
            components["day_month_year"] = f"{d}{m}{y}"
            components["month_day_year"] = f"{m}{d}{y}"
            components["full_date"] = f"{d}{m}{y}"
            components["reverse_date"] = f"{y}{m}{d}"
            components["short_date"] = f"{d}{m}{y[-2:]}"
        elif components["day"] and components["month"]:
            d, m = components["day"], components["month"]
            components["day_month"] = f"{d}{m}"
            components["month_day"] = f"{m}{d}"
        return components

    def _apply_mutations(self, word, mutation_pattern, date_comps, num_range):
        result = mutation_pattern
        result = result.replace("{word}", word)
        result = result.replace("{capitalize}", word.capitalize())
        result = result.replace("{upper}", word.upper())
        result = result.replace("{leet}", word.translate(LEET_MAP))
        result = result.replace("{reverse}", word[::-1])
        for key, val in date_comps.items():
            if val:
                result = result.replace("{" + key + "}", str(val))
        if "{num}" in result:
            for _ in range(3):
                yield result.replace("{num}", str(random.randint(0, num_range)), 1)
        else:
            yield result
        if "{special}" in result:
            for sp in ["!", "@", "#", "$", "%", "&", "*"]:
                yield result.replace("{special}", sp)

    def generate_passwords(self, target_count=TARGET_PASSWORD_COUNT):
        print(f"\n{C}[*] Password Engine Initializing...{RE}")
        print(f"{Y}[*] Word pool size: {len(self.word_pool)} unique words{RE}")

        if not self.word_pool:
            username = (self.target_data.get("username", "") or "user").lower()
            self.word_pool = [username, username.replace("_", ""), username.replace(".", "")]

        date_comps = self._get_date_components()
        basic_passwords = set()
        for word in self.word_pool[:30]:
            word = str(word)
            for variant in set([word, word.capitalize(), word.upper(), word.lower(), word.translate(LEET_MAP)]):
                if len(variant) >= 2:
                    for num in range(0, 100):
                        basic_passwords.add(f"{variant}{num}")
                        basic_passwords.add(f"{variant}{num:02d}")
                        basic_passwords.add(f"{num}{variant}")
                    for year in range(1970, 2027):
                        if len(basic_passwords) > target_count * 0.35:
                            break
                        basic_passwords.add(f"{variant}{year}")
        print(f"{G}[+] Phase 1 (Basic): {len(basic_passwords):,} passwords{RE}")

        date_passwords = set()
        for word in self.word_pool[:20]:
            word = str(word)
            for date_val in [v for v in date_comps.values() if v]:
                date_val = str(date_val)
                if len(date_val) >= 2:
                    date_passwords.update([
                        f"{word}{date_val}", f"{date_val}{word}", f"{word}_{date_val}",
                        f"{word}{date_val}!", f"{word.capitalize()}{date_val}",
                    ])
                    if len(date_val) == 4 and date_val.isdigit():
                        date_passwords.add(f"{word}{date_val[-2:]}")
                        date_passwords.add(f"{date_val[-2:]}{word}")
        print(f"{G}[+] Phase 2 (Date-based): {len(date_passwords):,} passwords{RE}")

        combo_passwords = set()
        top_words = [str(w) for w in self.word_pool[:15]]
        for w1, w2 in itertools.combinations(top_words, 2):
            if len(combo_passwords) > target_count * 0.2:
                break
            for n in [0, 1, 12, 123, 1234, 2023, 2024, 2025, 2026]:
                combo_passwords.update([
                    f"{w1}{w2}", f"{w1}_{w2}", f"{w1}{w2}{n}",
                    f"{w1.capitalize()}{w2}", f"{w1}{w2.capitalize()}",
                ])
        print(f"{G}[+] Phase 3 (Combinations): {len(combo_passwords):,} passwords{RE}")

        leet_passwords = set()
        for word in self.word_pool[:25]:
            word = str(word)
            leet_word = word.translate(LEET_MAP)
            if leet_word != word:
                for suffix in ["", "!", "@", "#", "123", "007"]:
                    leet_passwords.add(f"{leet_word}{suffix}")
                    leet_passwords.add(f"{leet_word.capitalize()}{suffix}")
        print(f"{G}[+] Phase 4 (Leet): {len(leet_passwords):,} passwords{RE}")

        pattern_passwords = set()
        for word in self.word_pool[:10]:
            word = str(word)
            for patterns in MUTATION_PATTERNS.values():
                for pattern in patterns:
                    for result in self._apply_mutations(word, pattern, date_comps, 9999):
                        if len(result) >= 6 and "{" not in result:
                            pattern_passwords.add(result)
        print(f"{G}[+] Phase 5 (Patterns): {len(pattern_passwords):,} passwords{RE}")

        common_passwords = set()
        suffixes = ["123","1234","12345","123456","!","@","#","2024","2025","2026","007","007!","1","2","3","11","22","33"]
        for word in self.word_pool[:20]:
            word = str(word)
            for suffix in suffixes:
                common_passwords.add(f"{word}{suffix}")
                common_passwords.add(f"{word.capitalize()}{suffix}")
                common_passwords.add(f"{word.upper()}{suffix}")
        print(f"{G}[+] Phase 6 (Common patterns): {len(common_passwords):,} passwords{RE}")

        ai_passwords = self._ai_contextual_generation()
        print(f"{G}[+] Phase 7 (AI Contextual): {len(ai_passwords):,} passwords{RE}")

        all_passwords = set()
        for s in (basic_passwords, date_passwords, combo_passwords, leet_passwords, pattern_passwords, common_passwords, ai_passwords):
            all_passwords.update(s)

        all_passwords = {
            p for p in all_passwords
            if isinstance(p, str) and 6 <= len(p) <= 40 and not p.startswith(" ") and not p.endswith(" ") and "{" not in p
        }

        final_list = list(all_passwords)
        random.shuffle(final_list)
        final_list = final_list[:target_count]
        print(f"\n{G}[+] Generated {len(final_list):,} intelligent passwords{RE}")
        return final_list

    def _ai_contextual_generation(self):
        passwords = set()
        username = (self.target_data.get("username", "") or "").lower()
        real_name = (self.personal.get("real_name", "") or "").lower()
        birth_year = str(self.personal.get("birth_year", "") or "")
        gf = (self.personal.get("girlfriend_name", "") or "").lower()
        pet = (self.personal.get("pet_name", "") or "").lower()
        nickname = (self.personal.get("nickname", "") or "").lower()
        fav = (self.personal.get("favorite_thing", "") or "").lower()
        phone = str(self.personal.get("phone_number", "") or "")

        if not birth_year and self.personal.get("birth_date"):
            birth_year = self._get_date_components().get("year", "")

        for year in range(1980, 2027):
            if username:
                passwords.update([f"{username}{year}", f"{username}_{year}", f"{year}{username}"])

        if username and birth_year:
            passwords.update([f"{username}{birth_year}", f"{username}_{birth_year}", f"{username}{birth_year[-2:]}"])

        if real_name and " " in real_name:
            parts = real_name.split()
            first, last = parts[0], parts[-1]
            passwords.update([f"{first}{last}", f"{first[0]}{last}", f"{first}.{last}", f"{first}_{last}"])
            passwords.add(f"{first}{last}{birth_year}" if birth_year else f"{first}{last}123")

        if gf and real_name:
            first_name = real_name.split()[0]
            passwords.update([
                f"{first_name}+{gf}", f"{first_name}love{gf}", f"{gf}love{first_name}",
                f"{first_name}&{gf}", f"{first_name}and{gf}", f"{gf}and{first_name}",
            ])

        if pet:
            for num in ["", "1", "123", "007", "2024", "2025"]:
                passwords.update([f"{pet}{num}", f"{pet.capitalize()}{num}", f"my{pet}{num}", f"ilove{pet}{num}"])

        if phone and len(phone) >= 4:
            base_words = [username, pet, gf]
            if real_name:
                base_words.append(real_name.split()[0])
            for word in base_words:
                if word:
                    passwords.add(f"{word}{phone[-4:]}")
                    passwords.add(f"{word}@{phone[-4:]}")
                    if len(phone) >= 6:
                        passwords.add(f"{word}{phone[-6:]}")

        keywords = self.target_data.get("extracted_keywords", []) or []
        for kw1, kw2 in itertools.combinations(keywords[:5], 2):
            if len(kw1) > 2 and len(kw2) > 2:
                passwords.update([f"{kw1}{kw2}", f"{kw1}_{kw2}"])

        if nickname:
            for year in range(2000, 2027):
                passwords.add(f"{nickname}{year}")
            passwords.update([f"{nickname}007", f"{nickname}123"])

        if fav:
            for num in ["123", "007", "2024", "2025", "1", "99", "00"]:
                passwords.update([f"{fav}{num}", f"{fav.capitalize()}{num}"])

        return passwords
