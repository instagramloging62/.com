#!/usr/bin/env python3
import json
import os
import random
import re
import time

import requests
from bs4 import BeautifulSoup

from .banner import C, G, R, RE, Y
from .config import (
    IG_APP_ID,
    PROFILES_DIR,
    REQUEST_TIMEOUT,
    USER_AGENTS,
    get_random_headers,
)


def format_proxy(proxy_string):
    if not proxy_string:
        return None
    s = str(proxy_string).strip()
    if "://" in s:
        return {"http": s, "https": s}
    parts = s.split(":")
    if len(parts) == 2:
        url = f"http://{s}"
        return {"http": url, "https": url}
    if len(parts) == 4:
        ip, port, user, pwd = parts
        url = f"http://{user}:{pwd}@{ip}:{port}"
        return {"http": url, "https": url}
    return None


class InstagramInfoGatherer:
    def __init__(self, proxy=None, proxy_list=None):
        self.proxy = proxy
        self.proxy_list = list(proxy_list or [])
        if proxy and proxy not in self.proxy_list:
            self.proxy_list.insert(0, proxy)
        self.session = requests.Session()
        self._apply_proxy(self.proxy)
        self.last_error = ""

    def _apply_proxy(self, proxy):
        self.proxy = proxy
        px = format_proxy(proxy)
        self.session.proxies.clear()
        if px:
            self.session.proxies.update(px)

    def _empty_data(self, username):
        return {
            "username": username,
            "full_name": "",
            "biography": "",
            "followers": 0,
            "following": 0,
            "posts": 0,
            "verified": False,
            "is_business": False,
            "is_private": False,
            "profile_pic_url": "",
            "external_url": "",
            "category": "",
            "user_id": "",
            "extracted_names": [],
            "extracted_dates": [],
            "extracted_keywords": [],
            "source": "none",
            "error": "",
        }

    def _parse_count(self, count_str):
        if count_str is None:
            return 0
        if isinstance(count_str, (int, float)):
            return int(count_str)
        s = str(count_str).replace(",", "").strip().upper()
        mult = 1
        if s.endswith("K"):
            mult, s = 1000, s[:-1]
        elif s.endswith("M"):
            mult, s = 1000000, s[:-1]
        elif s.endswith("B"):
            mult, s = 1000000000, s[:-1]
        try:
            return int(float(s) * mult)
        except ValueError:
            return 0

    def _browser_headers(self, username=None):
        h = get_random_headers(username)
        h["User-Agent"] = random.choice(USER_AGENTS)
        return h

    def _warmup(self, username):
        try:
            self.session.get(
                "https://www.instagram.com/",
                headers=self._browser_headers(),
                timeout=REQUEST_TIMEOUT,
            )
            time.sleep(random.uniform(0.4, 1.0))
            self.session.get(
                f"https://www.instagram.com/{username}/",
                headers=self._browser_headers(username),
                timeout=REQUEST_TIMEOUT,
            )
            time.sleep(random.uniform(0.3, 0.8))
        except requests.RequestException:
            pass

    def extract_profile_data(self, username):
        username = (username or "").strip().lstrip("@")
        print(f"\n{C}[*] Gathering intelligence on @{username}...{RE}")
        data = self._empty_data(username)

        proxies_try = [None]
        if self.proxy_list:
            proxies_try = list(self.proxy_list) + [None]
        elif self.proxy:
            proxies_try = [self.proxy, None]

        ok = False
        for px in proxies_try[:8]:
            self.session = requests.Session()
            self._apply_proxy(px)
            tag = px if px else "direct"
            print(f"{Y}[*] Trying proxy: {tag}{RE}")

            self._warmup(username)

            if self._method_web_profile_info(username, data):
                print(f"{G}[+] Profile via web_profile_info{RE}")
                ok = True
                break

            if self._method_html(username, data):
                print(f"{G}[+] Profile via HTML{RE}")
                ok = True
                break

            if self._method_oembed(username, data):
                print(f"{G}[+] Profile via oEmbed (limited){RE}")
                ok = True
                break

        if not ok:
            print(f"{R}[!] Could not fetch profile data{RE}")
            if self.last_error:
                print(f"{Y}[!] Last error: {self.last_error}{RE}")
            print(
                f"{Y}[!] Instagram may be blocking this IP, account private/invalid, or needs residential proxies{RE}"
            )
            print(f"{Y}[!] Tip: add proxies in data/proxies.txt then retry{RE}")
            data = self._manual_fill(username, data)

        data = self._extract_intelligence(data)
        if data.get("full_name") or data.get("followers") or data.get("biography"):
            print(
                f"{G}[+] @{username}: {data.get('followers', 0)} followers | "
                f"{data.get('following', 0)} following | {data.get('posts', 0)} posts | "
                f"source={data.get('source')}{RE}"
            )

        self._save_profile(username, data)
        return data

    def _manual_fill(self, username, data):
        print(f"\n{M if False else Y}[*] Manual fill (press Enter to skip){RE}")
        try:
            fn = input(f"{C}[?] Full name: {RE}").strip()
            bio = input(f"{C}[?] Bio: {RE}").strip()
            fl = input(f"{C}[?] Followers number: {RE}").strip()
            fg = input(f"{C}[?] Following number: {RE}").strip()
            po = input(f"{C}[?] Posts number: {RE}").strip()
            if fn:
                data["full_name"] = fn
            if bio:
                data["biography"] = bio
            if fl.isdigit():
                data["followers"] = int(fl)
            if fg.isdigit():
                data["following"] = int(fg)
            if po.isdigit():
                data["posts"] = int(po)
            if any([fn, bio, fl, fg, po]):
                data["source"] = "manual"
                print(f"{G}[+] Manual data accepted{RE}")
        except Exception:
            pass
        data["username"] = username
        return data

    def _save_profile(self, username, data):
        try:
            os.makedirs(PROFILES_DIR, exist_ok=True)
            path = os.path.join(PROFILES_DIR, f"{username}_profile.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"{G}[+] Profile saved to: {path}{RE}")
        except OSError as e:
            print(f"{R}[!] Save error: {e}{RE}")

    def _method_web_profile_info(self, username, data):
        url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "X-IG-App-ID": IG_APP_ID,
            "X-ASBD-ID": "129477",
            "X-IG-WWW-Claim": "0",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.instagram.com",
            "Referer": f"https://www.instagram.com/{username}/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }
        try:
            resp = self.session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                self.last_error = f"web_profile_info HTTP {resp.status_code}"
                print(f"    {Y}[!] {self.last_error}{RE}")
                return False
            payload = resp.json()
            user = (payload.get("data") or {}).get("user") or {}
            if not user:
                self.last_error = "web_profile_info empty user"
                return False
            data["username"] = user.get("username") or username
            data["full_name"] = user.get("full_name") or ""
            data["biography"] = user.get("biography") or ""
            data["followers"] = int((user.get("edge_followed_by") or {}).get("count") or 0)
            data["following"] = int((user.get("edge_follow") or {}).get("count") or 0)
            data["posts"] = int(
                (user.get("edge_owner_to_timeline_media") or {}).get("count") or 0
            )
            data["verified"] = bool(user.get("is_verified", False))
            data["is_business"] = bool(user.get("is_business_account", False))
            data["is_private"] = bool(user.get("is_private", False))
            data["profile_pic_url"] = (
                user.get("profile_pic_url_hd") or user.get("profile_pic_url") or ""
            )
            data["external_url"] = user.get("external_url") or ""
            data["category"] = user.get("category_name") or ""
            data["user_id"] = str(user.get("id") or "")
            data["source"] = "web_profile_info"
            return True
        except Exception as e:
            self.last_error = f"web_profile_info: {e}"
            print(f"    {R}[!] {self.last_error}{RE}")
            return False

    def _method_html(self, username, data):
        try:
            headers = self._browser_headers(username)
            headers["Accept"] = (
                "✅ text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8".replace(
                    "✅ ", ""
                )
            )
            resp = self.session.get(
                f"https://www.instagram.com/{username}/",
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code != 200 or not resp.text:
                self.last_error = f"HTML HTTP {getattr(resp, 'status_code', '?')}"
                print(f"    {Y}[!] {self.last_error}{RE}")
                return False

            html = resp.text
            low = html.lower()
            if "login" in low and "edge_followed_by" not in html and "og:description" not in low:
                self.last_error = "HTML login wall / blocked"
                print(f"    {Y}[!] {self.last_error}{RE}")

            found = False
            patterns = [
                r"window\._sharedData\s*=\s*(\{.+?\});</script>",
                r"window\.__additionalDataLoaded\([^,]+,\s*(\{.+?\})\);</script>",
            ]
            for pat in patterns:
                m = re.search(pat, html, re.DOTALL)
                if not m:
                    continue
                try:
                    blob = json.loads(m.group(1))
                    user = None
                    if "entry_data" in blob:
                        pages = blob.get("entry_data", {}).get("ProfilePage") or []
                        if pages:
                            user = ((pages[0] or {}).get("graphql") or {}).get("user")
                    elif "graphql" in blob:
                        user = (blob.get("graphql") or {}).get("user")
                    elif "data" in blob:
                        user = (blob.get("data") or {}).get("user")
                    if user:
                        self._fill_from_user(data, user)
                        data["source"] = "html_json"
                        found = True
                        break
                except Exception:
                    continue

            soup = BeautifulSoup(html, "html.parser")
            for tag in soup.find_all("meta"):
                prop = (tag.get("property") or tag.get("name") or "").lower()
                content = tag.get("content") or ""
                if not content:
                    continue
                if prop == "og:title" and not data.get("full_name"):
                    name = content.split("(@")[0].strip()
                    name = re.sub(r"\s*[•|].*$", "", name).strip()
                    if name and name.lower() not in ("instagram", "login"):
                        data["full_name"] = name
                        found = True
                elif prop in ("og:description", "description"):
                    fm = re.search(r"([\d,.]+[KMB]?)\s*Followers", content, re.I)
                    gm = re.search(r"([\d,.]+[KMB]?)\s*Following", content, re.I)
                    pm = re.search(r"([\d,.]+[KMB]?)\s*Posts", content, re.I)
                    if fm:
                        data["followers"] = self._parse_count(fm.group(1))
                        found = True
                    if gm:
                        data["following"] = self._parse_count(gm.group(1))
                        found = True
                    if pm:
                        data["posts"] = self._parse_count(pm.group(1))
                        found = True
                    if " - " in content and not data.get("biography"):
                        bio = content.split(" - ", 1)[-1].strip()
                        bio = re.sub(
                            r"\s*See Instagram photos and videos.*$",
                            "",
                            bio,
                            flags=re.I,
                        ).strip()
                        if bio and "instagram" not in bio.lower()[:20]:
                            data["biography"] = bio
                            found = True
                elif prop == "og:image" and not data.get("profile_pic_url"):
                    data["profile_pic_url"] = content
                    found = True

            if not data.get("followers"):
                m = re.search(r'"edge_followed_by"\s*:\s*\{\s*"count"\s*:\s*(\d+)', html)
                if m:
                    data["followers"] = int(m.group(1))
                    found = True
            if not data.get("following"):
                m = re.search(r'"edge_follow"\s*:\s*\{\s*"count"\s*:\s*(\d+)', html)
                if m:
                    data["following"] = int(m.group(1))
                    found = True
            if not data.get("posts"):
                m = re.search(
                    r'"edge_owner_to_timeline_media"\s*:\s*\{\s*"count"\s*:\s*(\d+)',
                    html,
                )
                if m:
                    data["posts"] = int(m.group(1)
                    )
                    found = True
            if not data.get("full_name"):
                m = re.search(r'"full_name"\s*:\s*"([^"]*)"', html)
                if m:
                    val = m.group(1)
                    try:
                        data["full_name"] = (
                            val.encode().decode("unicode_escape")
                            if "\\" in val
                            else val
                        )
                    except Exception:
                        data["full_name"] = val
                    found = True
            if not data.get("biography"):
                m = re.search(r'"biography"\s*:\s*"((?:\\.|[^"\\])*)"', html)
                if m:
                    try:
                        data["biography"] = bytes(m.group(1), "utf-8").decode(
                            "unicode_escape"
                        )
                    except Exception:
                        data["biography"] = m.group(1)
                    found = True

            if found and data.get("source") == "none":
                data["source"] = "html_meta"
            return found
        except Exception as e:
            self.last_error = f"HTML: {e}"
            print(f"    {R}[!] {self.last_error}{RE}")
            return False

    def _fill_from_user(self, data, user):
        data["full_name"] = user.get("full_name") or data.get("full_name") or ""
        data["biography"] = user.get("biography") or data.get("biography") or ""
        data["followers"] = int(
            (user.get("edge_followed_by") or {}).get("count")
            or data.get("followers")
            or 0
        )
        data["following"] = int(
            (user.get("edge_follow") or {}).get("count") or data.get("following") or 0
        )
        data["posts"] = int(
            (user.get("edge_owner_to_timeline_media") or {}).get("count")
            or data.get("posts")
            or 0
        )
        data["verified"] = bool(user.get("is_verified", data.get("verified")))
        data["is_business"] = bool(
            user.get("is_business_account", data.get("is_business"))
        )
        data["is_private"] = bool(user.get("is_private", data.get("is_private")))
        data["external_url"] = user.get("external_url") or data.get("external_url") or ""
        data["user_id"] = str(user.get("id") or data.get("user_id") or "")

    def _method_oembed(self, username, data):
        try:
            url = (
                "https://www.instagram.com/api/v1/oembed/"
                f"?url=https://www.instagram.com/{username}/"
            )
            resp = self.session.get(
                url, headers=self._browser_headers(username), timeout=15
            )
            if resp.status_code != 200:
                self.last_error = f"oEmbed HTTP {resp.status_code}"
                return False
            j = resp.json()
            title = j.get("title") or j.get("author_name") or ""
            if title:
                data["full_name"] = title
                data["source"] = "oembed"
                return True
            return False
        except Exception as e:
            self.last_error = f"oEmbed: {e}"
            return False

    def _extract_intelligence(self, data):
        full_name = data.get("full_name", "") or ""
        if full_name:
            names = full_name.split()
            data["extracted_names"] = [n.lower() for n in names if len(n) > 1]
            data["extracted_names"].append(full_name.lower().replace(" ", ""))
            data["extracted_names"].append(full_name.lower().replace(" ", "_"))

        bio = data.get("biography", "") or ""
        if bio:
            data["extracted_dates"] = list(
                set(
                    (data.get("extracted_dates") or [])
                    + re.findall(r"\b(?:19|20)\d{2}\b", bio)
                )
            )
            for d in re.findall(r"\b(\d{1,2})[/\-.](\d{1,2})\b", bio):
                data["extracted_dates"].extend(list(d))
            kws = [k.replace("#", "") for k in re.findall(r"#[a-zA-Z0-9_]+", bio)]
            kws.extend(re.findall(r"@(\w+)", bio))
            data["extracted_keywords"] = list(
                set((data.get("extracted_keywords") or []) + kws)
            )

        username = data.get("username", "") or ""
        if username:
            data["extracted_keywords"] = list(
                set(
                    (data.get("extracted_keywords") or [])
                    + [re.sub(r"[._\-]", "", username).lower()]
                    + [
                        w.lower()
                        for w in re.findall(r"[A-Z]?[a-z]+|[a-z]+", username)
                        if len(w) > 1
                    ]
                )
            )

        external_url = data.get("external_url", "") or ""
        if external_url:
            domain = re.sub(r"https?://(www\.)?", "", external_url).split("/")[0]
            if domain:
                data["extracted_keywords"] = list(
                    set(
                        (data.get("extracted_keywords") or [])
                        + [domain.split(".")[0]]
                    )
                )

        data["extracted_names"] = list(
            set([x for x in (data.get("extracted_names") or []) if x])
        )
        data["extracted_dates"] = list(
            set([x for x in (data.get("extracted_dates") or []) if x])
        )
        data["extracted_keywords"] = list(
            set([x for x in (data.get("extracted_keywords") or []) if x])
        )
        return data
