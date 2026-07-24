#!/usr/bin/env python3
import re
import json
import requests
from bs4 import BeautifulSoup
from .config import get_random_headers
from .banner import C, RE, Y, G, R

class InstagramInfoGatherer:
    def __init__(self, proxy=None):
        self.session = requests.Session()
        self.proxy = proxy
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}

    def _make_request(self, url, method="GET", data=None, timeout=15):
        headers = get_random_headers()
        try:
            if method == "GET":
                return self.session.get(url, headers=headers, timeout=timeout)
            return self.session.post(url, headers=headers, data=data, timeout=timeout)
        except requests.RequestException as e:
            print(f"    {R}[!] Request failed: {e}{RE}")
            return None

    def fetch_profile_html(self, username):
        response = self._make_request(f"https://www.instagram.com/{username}/")
        if not response or response.status_code != 200:
            return None
        return response.text

    def fetch_profile_json(self, username):
        response = self._make_request(f"https://www.instagram.com/{username}/?__a=1&__d=1")
        if not response or response.status_code != 200:
            return None
        try:
            return response.json()
        except json.JSONDecodeError:
            return None

    def extract_profile_data(self, username):
        print(f"\n{C}[*] Gathering intelligence on @{username}...{RE}")
        data = {
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
            "extracted_names": [],
            "extracted_dates": [],
            "extracted_keywords": [],
        }

        json_data = self.fetch_profile_json(username)
        if json_data and "graphql" in json_data:
            user = json_data["graphql"].get("user", {})
            data["full_name"] = user.get("full_name", "")
            data["biography"] = user.get("biography", "")
            data["followers"] = user.get("edge_followed_by", {}).get("count", 0)
            data["following"] = user.get("edge_follow", {}).get("count", 0)
            data["posts"] = user.get("edge_owner_to_timeline_media", {}).get("count", 0)
            data["verified"] = user.get("is_verified", False)
            data["is_business"] = user.get("is_business_account", False)
            data["is_private"] = user.get("is_private", False)
            data["profile_pic_url"] = user.get("profile_pic_url_hd", "")
            data["external_url"] = user.get("external_url", "")
            data["category"] = user.get("category_name", "")
        elif json_data and "data" in json_data:
            user = json_data.get("data", {}).get("user", {})
            if user:
                data["full_name"] = user.get("full_name", "")
                data["biography"] = user.get("biography", "")
                data["followers"] = user.get("edge_followed_by", {}).get("count", 0)
                data["following"] = user.get("edge_follow", {}).get("count", 0)
                data["posts"] = user.get("edge_owner_to_timeline_media", {}).get("count", 0)
                data["verified"] = user.get("is_verified", False)
                data["is_business"] = user.get("is_business_account", False)
                data["is_private"] = user.get("is_private", False)
                data["external_url"] = user.get("external_url", "")

        if not data.get("full_name"):
            html = self.fetch_profile_html(username)
            if html:
                data = self._parse_html_profile(html, username, data)

        data = self._extract_intelligence(data)
        if data.get("full_name") or data.get("biography") or data.get("followers"):
            print(f"{G}[+] Profile data collected for @{username}{RE}")
        else:
            print(f"{Y}[!] Limited profile data for @{username}{RE}")
        return data

    def _parse_html_profile(self, html, username, data):
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all("meta"):
            prop = tag.get("property", "") or tag.get("name", "")
            content = tag.get("content", "") or ""
            if prop == "og:title":
                if "(@" in content:
                    data["full_name"] = content.split("(@")[0].strip()
                elif content:
                    data["full_name"] = content.replace(f"(@{username})", "").strip()
            elif prop in ("og:description", "description"):
                follower_match = re.search(r"([\d,.]+[KMB]?)\s*Followers", content, re.I)
                following_match = re.search(r"([\d,.]+[KMB]?)\s*Following", content, re.I)
                post_match = re.search(r"([\d,.]+[KMB]?)\s*Posts", content, re.I)
                if follower_match:
                    data["followers"] = self._parse_count(follower_match.group(1))
                if following_match:
                    data["following"] = self._parse_count(following_match.group(1))
                if post_match:
                    data["posts"] = self._parse_count(post_match.group(1))
                if " - " in content and not data.get("biography"):
                    data["biography"] = content.split(" - ", 1)[-1].strip()

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                ld_json = json.loads(script.string or "")
                if isinstance(ld_json, dict):
                    if ld_json.get("description") and not data.get("biography"):
                        data["biography"] = ld_json.get("description", "")
                    if ld_json.get("name") and not data.get("full_name"):
                        data["full_name"] = ld_json.get("name", "")
            except (json.JSONDecodeError, TypeError, AttributeError):
                continue
        return data

    def _parse_count(self, count_str):
        count_str = count_str.replace(",", "").strip().upper()
        for suffix, multiplier in {"K": 1000, "M": 1000000, "B": 1000000000}.items():
            if suffix in count_str:
                try:
                    return int(float(count_str.replace(suffix, "")) * multiplier)
                except ValueError:
                    return 0
        try:
            return int(float(count_str))
        except ValueError:
            return 0

    def _extract_intelligence(self, data):
        full_name = data.get("full_name", "") or ""
        if full_name:
            names = full_name.split()
            data["extracted_names"] = [n.lower() for n in names if len(n) > 1]
            data["extracted_names"].append(full_name.lower().replace(" ", ""))
            data["extracted_names"].append(full_name.lower().replace(" ", "_"))

        bio = data.get("biography", "") or ""
        if bio:
            data["extracted_dates"].extend(re.findall(r"\b(?:19|20)\d{2}\b", bio))
            for d in re.findall(r"\b(\d{1,2})[/\-.](\d{1,2})\b", bio):
                data["extracted_dates"].extend(list(d))
            data["extracted_keywords"] = [k.replace("#", "") for k in re.findall(r"#[a-zA-Z0-9_]+", bio)]
            data["extracted_keywords"].extend(re.findall(r"@(\w+)", bio))

        username = data.get("username", "") or ""
        if username:
            data["extracted_keywords"].append(re.sub(r"[._\-]", "", username).lower())
            data["extracted_keywords"].extend([w.lower() for w in re.findall(r"[A-Z]?[a-z]+|[a-z]+", username) if len(w) > 1])

        external_url = data.get("external_url", "") or ""
        if external_url:
            domain = re.sub(r"https?://(www\.)?", "", external_url).split("/")[0]
            if domain:
                data["extracted_keywords"].append(domain.split(".")[0])

        data["extracted_names"] = list(set([x for x in data["extracted_names"] if x]))
        data["extracted_dates"] = list(set([x for x in data["extracted_dates"] if x]))
        data["extracted_keywords"] = list(set([x for x in data["extracted_keywords"] if x]))
        return data
