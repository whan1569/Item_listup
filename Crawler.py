"""
Crawler.py

Purpose:
- Crawl raw search phrases from public pages.
- Keep the phrase as a whole search form.
- Lowercase only.
- Normalize whitespace only.
- Do NOT split words.
- Do NOT filter by product relevance.
- Do NOT remove prices, units, stopwords, or short phrases.
- Do NOT score, summarize, or combine phrases.
- Do NOT use Google Trends seed expansion.

Output:
    data/raw_search_phrases.csv

Install:
    pip install playwright beautifulsoup4 lxml
    playwright install chromium

Run:
    python Crawler.py
"""

from __future__ import annotations

import csv
import random
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


OUTPUT_DIR = Path("data")
OUTPUT_CSV = OUTPUT_DIR / "raw_search_phrases.csv"

HEADLESS = True
PAGE_TIMEOUT_MS = 45_000
MIN_SLEEP_SEC = 1.5
MAX_SLEEP_SEC = 3.5

SOURCES = [
    {
        "source": "amazon_au_movers",
        "url": "https://www.amazon.com.au/gp/movers-and-shakers",
        "base_url": "https://www.amazon.com.au",
        "type": "amazon",
    },
    {
        "source": "amazon_au_new_releases",
        "url": "https://www.amazon.com.au/gp/new-releases",
        "base_url": "https://www.amazon.com.au",
        "type": "amazon",
    },
    {
        "source": "tiktok_creative_center_products",
        "url": "https://ads.tiktok.com/business/creativecenter/inspiration/popular/products/pc/en",
        "base_url": "https://ads.tiktok.com",
        "type": "generic",
    },
    {
        "source": "yesstyle_bestsellers",
        "url": "https://www.yesstyle.com/en/best-sellers.html",
        "base_url": "https://www.yesstyle.com",
        "type": "generic",
    },
    {
        "source": "oliveyoung_global_best",
        "url": "https://global.oliveyoung.com/display/page/best-seller",
        "base_url": "https://global.oliveyoung.com",
        "type": "generic",
    },
    {
        "source": "reddit_skincareaddiction",
        "url": "https://www.reddit.com/r/SkincareAddiction/",
        "base_url": "https://www.reddit.com",
        "type": "generic",
    },
    {
        "source": "reddit_beauty",
        "url": "https://www.reddit.com/r/Beauty/",
        "base_url": "https://www.reddit.com",
        "type": "generic",
    },
]


@dataclass
class RawSearchPhrase:
    collected_at: str
    source: str
    page_url: str
    item_type: str
    raw_phrase: str
    item_id: Optional[str]
    item_url: Optional[str]
    extractor: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sleep_jitter() -> None:
    time.sleep(random.uniform(MIN_SLEEP_SEC, MAX_SLEEP_SEC))


def normalize_raw_phrase(value: Optional[str]) -> str:
    """
    Minimal normalization only.

    Allowed:
    - lowercase
    - whitespace normalization
    - strip edges

    Not allowed:
    - word splitting
    - stopword removal
    - product relevance filtering
    - price/unit removal
    - phrase recombination
    """
    if not value:
        return ""

    value = value.lower()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def fetch_page_html(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            locale="en-AU",
            timezone_id="Australia/Sydney",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1365, "height": 900},
        )
        page = context.new_page()
        page.set_default_timeout(PAGE_TIMEOUT_MS)

        try:
            page.goto(url, wait_until="domcontentloaded")
            sleep_jitter()

            for _ in range(4):
                page.mouse.wheel(0, 1800)
                sleep_jitter()

            return page.content()

        except PlaywrightTimeoutError:
            print(f"TIMEOUT: {url}")
            return ""

        except Exception as exc:
            print(f"FETCH FAILED: {url} | {exc}")
            return ""

        finally:
            context.close()
            browser.close()


def extract_asin(url: str) -> Optional[str]:
    parts = urlparse(url).path.split("/")

    for i, part in enumerate(parts):
        if part in {"dp", "product"} and i + 1 < len(parts):
            asin = parts[i + 1].strip()
            if len(asin) == 10:
                return asin

    return None


def amazon_slug_phrase(url: str) -> str:
    parts = urlparse(url).path.split("/")

    if "dp" in parts:
        idx = parts.index("dp")
        if idx > 0:
            return normalize_raw_phrase(
                parts[idx - 1]
                .replace("-", " ")
                .replace("_", " ")
            )

    return ""


def add_row(
    rows: list[RawSearchPhrase],
    seen: set[tuple],
    *,
    collected_at: str,
    source: str,
    page_url: str,
    item_type: str,
    raw_phrase: Optional[str],
    item_id: Optional[str],
    item_url: Optional[str],
    extractor: str,
) -> None:
    phrase = normalize_raw_phrase(raw_phrase)

    if not phrase:
        return

    key = (source, item_type, phrase, item_id, item_url, extractor)
    if key in seen:
        return

    seen.add(key)
    rows.append(
        RawSearchPhrase(
            collected_at=collected_at,
            source=source,
            page_url=page_url,
            item_type=item_type,
            raw_phrase=phrase,
            item_id=item_id,
            item_url=item_url,
            extractor=extractor,
        )
    )


def parse_amazon(html: str, source: str, page_url: str, base_url: str) -> list[RawSearchPhrase]:
    soup = BeautifulSoup(html, "lxml")
    collected_at = utc_now_iso()
    rows: list[RawSearchPhrase] = []
    seen: set[tuple] = set()

    links = soup.select("a[href*='/dp/'], a[href*='/gp/product/']")

    for link in links:
        href = link.get("href")
        if not href:
            continue

        full_url = urljoin(base_url, href)
        asin = extract_asin(full_url)
        if not asin:
            continue

        product_url = f"{base_url}/dp/{asin}"
        card = link.find_parent("div") or link

        # 1. Product/card image alt text as raw phrase.
        if hasattr(card, "select"):
            for img in card.select("img[alt]"):
                add_row(
                    rows,
                    seen,
                    collected_at=collected_at,
                    source=source,
                    page_url=page_url,
                    item_type="amazon_img_alt",
                    raw_phrase=img.get("alt"),
                    item_id=asin,
                    item_url=product_url,
                    extractor="img_alt",
                )

        # 2. Link visible text as raw phrase.
        add_row(
            rows,
            seen,
            collected_at=collected_at,
            source=source,
            page_url=page_url,
            item_type="amazon_link_text",
            raw_phrase=link.get_text(" "),
            item_id=asin,
            item_url=product_url,
            extractor="a_text",
        )

        # 3. URL slug phrase as raw phrase.
        add_row(
            rows,
            seen,
            collected_at=collected_at,
            source=source,
            page_url=page_url,
            item_type="amazon_url_slug",
            raw_phrase=amazon_slug_phrase(full_url),
            item_id=asin,
            item_url=product_url,
            extractor="url_slug",
        )

    return rows


def parse_generic(html: str, source: str, page_url: str, base_url: str) -> list[RawSearchPhrase]:
    soup = BeautifulSoup(html, "lxml")
    collected_at = utc_now_iso()
    rows: list[RawSearchPhrase] = []
    seen: set[tuple] = set()

    selectors = [
        ("img[alt]", "img_alt", "generic_img_alt"),
        ("a[title]", "a_title", "generic_a_title"),
        ("[aria-label]", "aria_label", "generic_aria_label"),
        ("[class*='product']", "text", "generic_class_product"),
        ("[class*='goods']", "text", "generic_class_goods"),
        ("[class*='item']", "text", "generic_class_item"),
        ("[class*='title']", "text", "generic_class_title"),
        ("[class*='name']", "text", "generic_class_name"),
        ("h1", "text", "generic_h1"),
        ("h2", "text", "generic_h2"),
        ("h3", "text", "generic_h3"),
        ("a", "text", "generic_a_text"),
        ("span", "text", "generic_span_text"),
    ]

    for selector, mode, item_type in selectors:
        for el in soup.select(selector):
            href = el.get("href") if hasattr(el, "get") else None
            item_url = urljoin(base_url, href) if href else None

            if mode == "img_alt":
                raw_values = [el.get("alt")]
            elif mode == "a_title":
                raw_values = [el.get("title")]
            elif mode == "aria_label":
                raw_values = [el.get("aria-label")]
            else:
                raw_values = [el.get_text(" ")]

            for raw_value in raw_values:
                add_row(
                    rows,
                    seen,
                    collected_at=collected_at,
                    source=source,
                    page_url=page_url,
                    item_type=item_type,
                    raw_phrase=raw_value,
                    item_id=None,
                    item_url=item_url,
                    extractor=mode,
                )

    return rows


def collect_source(config: dict) -> list[RawSearchPhrase]:
    source = config["source"]
    url = config["url"]
    base_url = config["base_url"]
    source_type = config["type"]

    print(f"Collecting: {source} | {url}")
    html = fetch_page_html(url)

    if not html:
        return []

    if source_type == "amazon":
        return parse_amazon(html, source, url, base_url)

    return parse_generic(html, source, url, base_url)


def write_csv(rows: list[RawSearchPhrase], path: Path) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8-sig") as f:
        if not rows:
            return

        writer = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()

        for row in rows:
            writer.writerow(asdict(row))


def main() -> None:
    all_rows: list[RawSearchPhrase] = []

    for config in SOURCES:
        rows = collect_source(config)
        all_rows.extend(rows)
        print(f"  collected raw phrases: {len(rows)}")

    write_csv(all_rows, OUTPUT_CSV)

    print()
    print("DONE")
    print(f"raw phrases: {len(all_rows)} -> {OUTPUT_CSV}")

    print()
    print("SAMPLE")
    for row in all_rows[:50]:
        print(f"{row.source} | {row.item_type} | {row.raw_phrase}")


if __name__ == "__main__":
    main()
