#!/usr/bin/env python3
"""
Camoro Information Gathering Module
Fetches Instagram profile data and extracts intelligence for password generation.
"""

import re
import json
import time
import random
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from .config import (
    INSTAGRAM_ENDPOINTS, 
    get_random_headers
)

class InstagramInfoGatherer:
    """Gather intelligence from Instagram profiles."""
    
    def __init__(self, proxy=None):
        self.session = requests.Session()
        self.proxy = proxy
        if proxy:
            self.session.proxies = {
                "http": proxy,
                "https": proxy,
            }
    
    def _make_request(self, url, method="GET", data=None, timeout=15):
        """Make HTTP request with rotation headers and error handling."""
        headers = get_random_headers()
        
        try:
            if method == "GET":
                response = self.session.get(url, headers=headers, timeout=timeout)
            else:
                response = self.session.post(url, headers=headers, data=data, timeout=timeout)
            return response
        except requests.RequestException as e:
            print(f"    [!] Request failed: {e}")
            return None
    
    def fetch_profile_html(self, username):
        """Fetch Instagram profile page via web scraping."""
        url = f"https://www.instagram.com/{username}/"
        response = self._make_request(url)
        
        if not response or response.status_code != 200:
            return None
        
        return response.text
    
    def fetch_profile_json(self, username):
        """Fetch profile data via Instagram's JSON endpoint."""
        url = f"https://www.instagram.com/{username}/?__a=1&__d=1"
        response = self._make_request(url)
        
        if not response or response.status_code != 200:
            return None
        
        try:
            return response.json()
        except json.JSONDecodeError:
            return None
    
    def extract_profile_data(self, username):
        """Extract comprehensive profile information."""
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
        
        # Method 1: Try JSON endpoint
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
        
        # Method 2: Fallback to HTML scraping
        if not data.get("full_name"):
            html = self.fetch_profile_html(username)
            if html:
                data = self._parse_html_profile(html, username, data)
        
        # Extract intelligence from profile
        data = self._extract_intelligence(data)
        
        return data
    
    def _parse_html_profile(self, html, username, data):
        """Parse profile from HTML using BeautifulSoup."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract meta tags
        meta_tags = soup.find_all("meta")
        for tag in meta_tags:
            prop = tag.get("property", "")
            content = tag.get("content", "")
            
            if prop == "og:title" and "(@" in content:
                name_part = content.split("(@")[0].strip()
                data["full_name"] = name_part
            elif prop == "og:description":
                # Parse follower/post counts from description
                desc = content
                follower_match = re.search(r"([\d,.]+[KMB]?)\s*Followers", desc)
                post_match = re.search(r"([\d,.]+[KMB]?)\s*Posts", desc)
                
                if follower_match:
                    data["followers"] = self._parse_count(follower_match.group(1))
                if post_match:
                    data["posts"] = self._parse_count(post_match.group(1))
        
        # Try to find bio in script tags
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                ld_json = json.loads(script.string)
                if "description" in ld_json:
                    data["biography"] = ld_json.get("description", "")
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return data
    
    def _parse_count(self, count_str):
        """Parse follower/post count strings like '1.2K', '5M'."""
        count_str = count_str.replace(",", "").strip()
        
        multipliers = {"K": 1000, "M": 1000000, "B": 1000000000}
        
        for suffix, multiplier in multipliers.items():
            if suffix in count_str:
                num = float(count_str.replace(suffix, ""))
                return int(num * multiplier)
        
        try:
            return int(float(count_str))
        except ValueError:
            return 0
    
    def _extract_intelligence(self, data):
        """Extract password-relevant intelligence from profile data."""
        
        # Extract names from full name
        full_name = data.get("full_name", "")
        if full_name:
            # Split into individual names
            names = full_name.split()
            data["extracted_names"] = [n.lower() for n in names if len(n) > 1]
            # Add full name variants
            data["extracted_names"].append(full_name.lower().replace(" ", ""))
            data["extracted_names"].append(full_name.lower().replace(" ", "_"))
        
        # Extract dates from bio
        bio = data.get("biography", "")
        if bio:
            # Find year patterns (19xx-20xx)
            years = re.findall(r'\b(19|20)\d{2}\b', bio)
            for y in years:
                data["extracted_dates"].append(y)
            
            # Find date patterns like DD/MM or MM/DD
            date_patterns = re.findall(r'\b(\d{1,2})[/\-.](\d{1,2})\b', bio)
            for d in date_patterns:
                data["extracted_dates"].extend(d)
            
            # Extract keywords
            keywords = re.findall(r'#[a-zA-Z0-9_]+', bio)
            data["extracted_keywords"] = [k.replace("#", "") for k in keywords]
            
            # Extract possible names from bio mentions
            mentions = re.findall(r'@(\w+)', bio)
            data["extracted_keywords"].extend(mentions)
        
        # Extract from username itself
        username = data.get("username", "")
        if username:
            # Remove common separators
            clean_username = re.sub(r'[._\-]', '', username)
            data["extracted_keywords"].append(clean_username.lower())
            
            # Try to split camelCase
            words = re.findall(r'[A-Z]?[a-z]+', username)
            data["extracted_keywords"].extend([w.lower() for w in words if len(w) > 1])
        
        # Extract from external URL
        external_url = data.get("external_url", "")
        if external_url:
            domain = re.sub(r'https?://(www\.)?', '', external_url).split('/')[0]
            data["extracted_keywords"].append(domain.split('.')[0])
        
        # Remove duplicates
        data["extracted_names"] = list(set(data["extracted_names"]))
        data["extracted_dates"] = list(set(data["extracted_dates"]))
        data["extracted_keywords"] = list(set(data["extracted_keywords"]))
        
        return data
