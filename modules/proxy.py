import itertools
import random
from pathlib import Path
from typing import Optional, List


class ProxyPool:
    def __init__(self, proxy_file: str = "proxies.txt"):
        self.proxies: List[str] = []
        self._cycle = None
        path = Path(proxy_file)
        if path.exists():
            with open(path, encoding="utf-8", errors="ignore") as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln or ln.startswith("#"):
                        continue
                    # support ip:port | http://ip:port | user:pass@ip:port
                    if "://" not in ln:
                        ln = "http://" + ln
                    self.proxies.append(ln)
        if self.proxies:
            random.shuffle(self.proxies)
            self._cycle = itertools.cycle(self.proxies)

    def __bool__(self):
        return bool(self.proxies)

    def __len__(self):
        return len(self.proxies)

    def next(self) -> Optional[str]:
        if not self._cycle:
            return None
        return next(self._cycle)

    def as_requests(self, proxy: Optional[str] = None) -> dict:
        p = proxy or self.next()
        if not p:
            return {}
        return {"http": p, "https": p}
