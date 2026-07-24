#!/usr/bin/env python3
import re
import json
import time
import hashlib
import uuid
import base64
import requests
from .config import INSTAGRAM_ENDPOINTS, get_random_headers

class InstagramSession:
    def __init__(self, proxy=None):
        self.session = requests.Session()
        self.csrf_token = None
        self.logged_in = False
        self.current_username = None
        self.proxy = proxy
        formatted = self._format_proxy(proxy)
        if formatted:
            self.session.proxies.update(formatted)
        self._initialize_session()

    def _format_proxy(self, proxy_string):
        if not proxy_string:
            return None
        if "://" in proxy_string:
            return {"http": proxy_string, "https": proxy_string}
        parts = str(proxy_string).split(":")
        if len(parts) == 2:
            return {"http": f"http://{proxy_string}", "https": f"http://{proxy_string}"}
        if len(parts) == 4:
            ip, port, user, pwd = parts
            url = f"http://{user}:{pwd}@{ip}:{port}"
            return {"http": url, "https": url}
        return None

    def _initialize_session(self):
        try:
            resp = self.session.get("https://www.instagram.com/", headers=get_random_headers(), timeout=15)
            self._extract_csrf(resp)
            self._set_device_fingerprint()
        except requests.RequestException:
            pass

    def _extract_csrf(self, response=None):
        csrf = self.session.cookies.get("csrftoken")
        if csrf:
            self.csrf_token = csrf
            return
        if response is not None and getattr(response, "text", None):
            match = re.search(r'"csrf_token"\s*:\s*"([^"]+)"', response.text)
            if match:
                self.csrf_token = match.group(1)
                return
        if not self.csrf_token:
            self.csrf_token = hashlib.md5(str(time.time()).encode()).hexdigest()[:32]

    def _set_device_fingerprint(self):
        device_id = str(uuid.uuid4()).upper()
        mid = "Z" + hashlib.md5(device_id.encode()).hexdigest()[:16]
        try:
            self.session.cookies.set("ig_did", device_id, domain=".instagram.com")
            self.session.cookies.set("mid", mid, domain=".instagram.com")
        except Exception:
            pass

    def _encode_password(self, password):
        return base64.b64encode(password.encode("utf-8")).decode("utf-8")

    def attempt_login(self, username, password):
        if not self.csrf_token:
            self._initialize_session()

        headers = get_random_headers()
        headers.update({
            "X-CSRFToken": self.csrf_token or "",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://www.instagram.com/accounts/login/",
        })

        ts = int(time.time())
        data = {
            "username": username,
            "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{ts}:{self._encode_password(password)}",
            "queryParams": "{}",
            "optIntoOneTap": "false",
            "stopDeletionNonce": "",
            "trustedDeviceRecords": "{}",
        }

        try:
            response = self.session.post(
                INSTAGRAM_ENDPOINTS["login"],
                headers=headers,
                data=data,
                timeout=20,
                allow_redirects=False,
            )
            self._extract_csrf(response)
            try:
                result = response.json()
            except json.JSONDecodeError:
                result = {"message": "unknown_error", "status": "fail"}

            if result.get("authenticated", False) or result.get("user", False):
                self.logged_in = True
                self.current_username = username
                return True, result

            message = str(result.get("message", "") or "").lower()
            if "checkpoint_required" in message or result.get("checkpoint_url"):
                return False, {"error": "checkpoint_required", "message": "2FA or challenge required"}
            if "rate" in message or "block" in message or "wait" in message:
                return False, {"error": "rate_limited", "message": "Rate limited - rotate proxy"}
            if "invalid" in message or "incorrect" in message or "password" in message:
                return False, {"error": "invalid_credentials", "message": "Invalid password"}
            if "unavailable" in message:
                return False, {"error": "account_unavailable", "message": "Account not available"}
            if response.status_code in (429, 403):
                return False, {"error": "rate_limited", "message": f"HTTP {response.status_code}"}
            return False, result
        except requests.RequestException as e:
            return False, {"error": "network_error", "message": str(e)}

    def reset_session(self):
        try:
            self.session.close()
        except Exception:
            pass
        self.session = requests.Session()
        formatted = self._format_proxy(self.proxy)
        if formatted:
            self.session.proxies.update(formatted)
        self.csrf_token = None
        self.logged_in = False
        self._initialize_session()
