"""Page fetching via playwright with stealth mode and Cloudflare handling."""

import time
import re

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth


CLOUDFLARE_TITLE = "Access denied | www.bilinovelib.com used Cloudflare"
GOTO_TIMEOUT = 30000
CLOUDCARE_WAIT = 5
RETRY_WAIT = 2


class Fetcher:
    BASE_URL = "https://www.bilinovel.com"
    _instance = None

    def __init__(self, interval: float = 0):
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self.interval = float(interval)
        self._closed = False

    @classmethod
    def get_instance(cls, interval: float = 0):
        if cls._instance is None or cls._instance._closed:
            cls._instance = cls(interval)
        return cls._instance

    def _ensure_page(self):
        if self._page is None:
            self._playwright = sync_playwright().__enter__()
            browser_type = self._get_browser_type()
            browser_launcher = getattr(self._playwright, browser_type)
            self._browser = browser_launcher.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-web-security",
                ],
            )
            stealth = Stealth()
            stealth._reassign_new_page_new_context(self._browser)
            self._context = self._browser.new_context(
                extra_http_headers={
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                },
            )
            self._page = self._context.new_page()
            self._page.set_default_timeout(GOTO_TIMEOUT)
        return self._page

    def _get_browser_type(self) -> str:
        try:
            from bilinovel_cli.cli.config_manager import load_config

            return load_config().browser.type
        except Exception:
            return "chromium"

    def _prepare_novel_page(self, page, novel_id: str):
        main_page = f"{self.BASE_URL}/novel/{novel_id}.html"
        page.goto(main_page, wait_until="domcontentloaded", timeout=GOTO_TIMEOUT)
        time.sleep(0.5)
        page.reload(wait_until="domcontentloaded", timeout=GOTO_TIMEOUT)
        time.sleep(0.5)

    def _goto_with_retry(self, page, url: str) -> str:
        for attempt in range(3):
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=GOTO_TIMEOUT)
                return page.content()
            except Exception:
                if attempt < 2:
                    time.sleep(RETRY_WAIT)
                    continue
                raise

    def fetch(self, path: str) -> str:
        page = self._ensure_page()
        url = path if path.startswith("http") else f"{self.BASE_URL}{path}"
        novel_id = self._extract_novel_id(path)

        if novel_id and "/catalog" not in path:
            self._prepare_novel_page(page, novel_id)

        time.sleep(0.5)
        html = self._goto_with_retry(page, url)

        if CLOUDFLARE_TITLE in html:
            time.sleep(CLOUDCARE_WAIT)
            html = self._goto_with_retry(page, url)

        if self.interval > 0:
            time.sleep(self.interval)
        return html

    def _extract_novel_id(self, path: str) -> str:
        parts = path.split("/")
        if path.startswith("http"):
            return parts[4] if len(parts) >= 5 else None
        return parts[2] if len(parts) >= 3 else None

    def _safe_close(self, resource, name: str):
        if resource:
            try:
                resource.close()
            except Exception:
                pass

    def close(self):
        self._closed = True
        self._safe_close(self._page, "page")
        self._page = None
        self._safe_close(self._context, "context")
        self._context = None
        self._safe_close(self._browser, "browser")
        self._browser = None
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
        Fetcher._instance = None

    def fetch_novel(self, novel_id: int) -> str:
        return self.fetch(f"/novel/{novel_id}.html")

    def fetch_catalog(self, novel_id: int) -> str:
        return self.fetch(f"/novel/{novel_id}/catalog")

    def fetch_chapter(self, novel_id: int, chapter_id: int) -> str:
        return self.fetch(f"/novel/{novel_id}/{chapter_id}.html")

    def fetch_chapter_pages(self, url: str) -> list[str]:
        page = self._ensure_page()
        self.fetch(url)
        html = page.content()
        pages = [html]
        path = url[len(self.BASE_URL) :] if url.startswith(self.BASE_URL) else url
        page_no = 1

        while True:
            next_path = re.sub(r"\.html$", f"_{page_no + 1}.html", path)
            if next_path not in html:
                break
            page_no += 1
            self.fetch(f"{self.BASE_URL}{next_path}")
            html = page.content()
            pages.append(html)

        return pages

    @staticmethod
    def check_url(url: str) -> bool:
        return "javascript" in url or "cid" in url
