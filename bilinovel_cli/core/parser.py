"""HTML parsing with lxml."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from lxml import html


def _load_rubbish_map():
    path = Path(__file__).parent / "rubbish_map.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["rubbish_secret_map"]


rubbish_secret_map = _load_rubbish_map()


chinese_punctuation = "，。！？、；：\u201c\u201d\u2018\u2019\uff08\uff09\u300a\u300b\u3008\u3009\u3010\u3011\u300e\u300f\u300c\u300d\u3016\u3017\u2026\u2014\u300c\u300d\u300e\u300f\u300a\u300b\u3008\u3009\u300e\u300f\u300c\u300d\u3010\u3011\uff08\uff09\u300a\u300b\u3008\u3009\u300c\u300d\u300e\u300f\u3016\u3017\uff08\uff09"


@dataclass
class ChapterData:
    title: str
    num: int
    url: str
    content: str = ""


@dataclass
class VolumeData:
    title: str
    chapters: List[ChapterData] = field(default_factory=list)


@dataclass
class NovelData:
    title: str
    author: str
    description: str
    cover: str = ""
    tags: List[str] = field(default_factory=list)
    volumes: List[VolumeData] = field(default_factory=list)


class Parser:
    def parse_novel_info(self, page_content: str) -> NovelData:
        tree = html.fromstring(page_content)
        title = tree.xpath("string(//h1)").strip()
        author = tree.xpath(
            "string(//meta[@property='og:novel:author']/@content)"
        ).strip()
        description = tree.xpath("string(//meta[@name='description']/@content)").strip()
        cover = tree.xpath("string(//meta[@property='og:image']/@content)").strip()
        tags_str = tree.xpath("string(//meta[@name='keywords']/@content)").strip()
        tags = tags_str.split(",") if tags_str else []
        return NovelData(
            title=title, author=author, description=description, cover=cover, tags=tags
        )

    def parse_catalog(self, page_content: str) -> List[VolumeData]:
        tree = html.fromstring(page_content)
        volumes = []
        for vol_elem in tree.xpath("//div[contains(@class, 'catalog-volume')]"):
            vol_text = vol_elem.text_content().strip()
            vol_title = vol_text.split("\n")[0].strip() if vol_text else ""
            chapters = self._extract_chapters(vol_elem)
            volumes.append(VolumeData(title=vol_title, chapters=chapters))
        return volumes

    def _extract_chapters(self, vol_elem) -> List[ChapterData]:
        chapters = []
        seen_urls = set()
        for a_elem in vol_elem.xpath(".//a"):
            href = a_elem.get("href", "").strip()
            if not self._is_valid_chapter_url(href, seen_urls):
                continue
            ch_title = a_elem.text_content().strip()
            ch_title = self._normalize_chapter_title(ch_title, href, len(chapters))
            seen_urls.add(href)
            chapters.append(
                ChapterData(title=ch_title, num=len(chapters) + 1, url=href)
            )
        return chapters

    def _is_valid_chapter_url(self, href: str, seen_urls: set) -> bool:
        return bool(
            href and "/novel/" in href and "vol_" not in href and href not in seen_urls
        )

    def _normalize_chapter_title(
        self, title: str, href: str, chapter_count: int
    ) -> str:
        default_title = f"Chapter {chapter_count + 1}"
        if not title or title == href.split("/")[-1].replace(".html", ""):
            return default_title
        return title

    def parse_chapter_content(self, page_content: str) -> str:
        tree = html.fromstring(page_content)
        content_div = tree.xpath("//div[@id='acontent']")
        if not content_div:
            return ""
        content_div = content_div[0]
        paragraphs = []
        seen = set()
        for p in content_div.xpath(".//p"):
            text = "".join(p.itertext()).strip()
            if text and text not in seen:
                seen.add(text)
                paragraphs.append(text)
        return "\n\n".join(paragraphs)

    def parse_novel(self, novel_page: str, catalog_page: str) -> NovelData:
        novel = self.parse_novel_info(novel_page)
        novel.volumes = self.parse_catalog(catalog_page)
        return novel

    def replace_rubbish_text(self, text: str) -> str:
        result = []
        for char in text:
            replacement = rubbish_secret_map.get(char)
            if replacement is not None:
                result.append(replacement)
            else:
                result.append(char)
        return "".join(result)

    def clean_content(self, content: str) -> str:
        anti_crawler_msg = (
            "【如需繼續閱讀請使用〔Chrome瀏覽器〕訪問 www.bilinovel.com】"
        )
        if anti_crawler_msg in content:
            content = content[: content.find(anti_crawler_msg)]
        content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
        content = re.sub(r"<p\d+>.*?</p>", "", content)
        content = re.sub(r"<br\s*/?>", "\n", content)
        content = re.sub(r"\n{3,}", "\n\n", content)
        content = content.strip()
        return content

    def parse_chapter_pages(self, pages: list[str]) -> str:
        full_content = "\n\n".join(pages)
        full_content = self.replace_rubbish_text(full_content)
        full_content = self.clean_content(full_content)
        return full_content
