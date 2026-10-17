from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
from scrapling.fetchers import StealthySession, ProxyRotator
from commonlib.observability import get_logger
from commonlib.terminalColor import yellow

logger = get_logger("scrapper.scraplingService")


class ScraplingService:
    def __init__(self, proxies: Optional[List[str]] = None, debug: bool = False):
        self.debug = debug
        self.proxies = proxies
        self.session: Optional[StealthySession] = None
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        self._init_session()

    def _is_thread_pool_alive(self) -> bool:
        return self._thread_pool is not None and not self._thread_pool._shutdown

    def _run_in_thread(self, fn, *args, **kwargs):
        if not self._is_thread_pool_alive():
            self._thread_pool = ThreadPoolExecutor(max_workers=1)
        return self._thread_pool.submit(fn, *args, **kwargs).result()

    def _window_setup(self, page):
        """Match the window size/position used by the Selenium scrappers (driverUtil._set_window_size_and_position)."""
        try:
            avail_width, avail_height = page.evaluate("() => [screen.availWidth, screen.availHeight]")
            cdp = page.context.new_cdp_session(page)
            window_id = cdp.send("Browser.getWindowForTarget")["windowId"]
            cdp.send("Browser.setWindowBounds", {"windowId": window_id, "bounds": {"width": 1200, "height": avail_height - 90, "left": avail_width - 1200, "top": 0}})
            cdp.detach()
        except Exception as e:
            logger.warning("scrapling.window_setup_failed", error=str(e), console=yellow(f"Could not resize browser window: {e}"))

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
            "new_context": False,
            "page_setup": self._window_setup
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
            logger.warning("scrapling.fetch_failed", error_type=type(e).__name__, console=yellow(f"Fetch failed: {e}, resetting session..."))
            self.reset_session()
            return self.fetch(url, **kwargs)

    def reset_session(self):
        if self.session:
            logger.info("scrapling.session_resetting", console=yellow("Resetting scrapling session..."))
            self.close()
            self._init_session()

    def close(self):
        if self.session:
            self._run_in_thread(self.session.close)
            self.session = None
