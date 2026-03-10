from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
from scrapling.fetchers import StealthySession, ProxyRotator
from commonlib.terminalColor import yellow


class ScraplingService:
    def __init__(self, proxies: Optional[List[str]] = None, debug: bool = False):
        self.debug = debug
        self.proxies = proxies
        self.session: Optional[StealthySession] = None
        self._thread_pool = ThreadPoolExecutor(max_workers=1)
        self._init_session()

    def _run_in_thread(self, fn, *args, **kwargs):
        return self._thread_pool.submit(fn, *args, **kwargs).result()

    def _build_kwargs(self) -> dict:
        kwargs = {
            "solve_cloudflare": True,
            "block_webrtc": True,
            "hide_canvas": True,
            "google_search": False,
            "real_chrome": True,
            "impersonate": "chrome",
            "wait": 8000,
            "timeout": 60000,
            "headless": False,
            "max_pages": 1,
            "new_context": False
        }
        if self.proxies:
            if len(self.proxies) == 1:
                kwargs["proxy"] = self.proxies[0]
            else:
                kwargs["proxy"] = ProxyRotator(self.proxies)
        return kwargs

    def _init_session(self):
        if not self.session:
            def _start():
                self.session = StealthySession(**self._build_kwargs())
                self.session.start()
            self._run_in_thread(_start)

    def _fetch_page(self, url: str, **kwargs):
        if not self.session:
            raise RuntimeError("Browser session not initialized")
        fetch_kwargs = {"google_search": False}
        fetch_kwargs.update(kwargs)
        response = self.session.fetch(url, **fetch_kwargs)
        if hasattr(self.session, 'page_pool') and self.session.page_pool:
            pages = self.session.page_pool.pages
            for extra_page in pages[1:]:
                try:
                    extra_page.close()
                except Exception:
                    pass
        return response

    def fetch(self, url: str, **kwargs):
        return self._run_in_thread(self._fetch_page, url, **kwargs)

    def fetch_with_retry(self, url: str, **kwargs):
        try:
            return self.fetch(url, **kwargs)
        except Exception as e:
            print(yellow(f"Fetch failed: {e}, resetting session..."))
            self.reset_session()
            return self.fetch(url, **kwargs)

    def reset_session(self):
        if self.session:
            print(yellow("Resetting scrapling session..."))
            self.close()
            self._init_session()

    def close(self):
        if self.session:
            self._run_in_thread(self.session.close)
            self.session = None
        self._thread_pool.shutdown(wait=False)
