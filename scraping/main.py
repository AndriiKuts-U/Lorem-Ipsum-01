from __future__ import annotations

import json
import argparse
import re
import time
from dataclasses import asdict, dataclass
from html import unescape
from collections.abc import Iterable

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


# Default categories (from README)
CATEGORY_URLS = [
    "https://www.ifresh.sk/donaskake/product-category/ovocie-a-zelenina/",
    "https://www.ifresh.sk/donaskake/product-category/pecivo/",
    "https://www.ifresh.sk/donaskake/product-category/chladene-a-mliecne-potraviny-vajcia-a-tuky/",
    "https://www.ifresh.sk/donaskake/product-category/maso-ryby-a-lahodky/",
    "https://www.ifresh.sk/donaskake/product-category/trvanlive-potraviny/",
    "https://www.ifresh.sk/donaskake/product-category/mrazeny-sortiment/",
    "https://www.ifresh.sk/donaskake/product-category/napoje/",
]


@dataclass
class Product:
    id: str | None
    name: str | None
    price: float | None
    price_discounted: float | None
    discount_percentage: float | None
    amount: float | None
    unit: str | None
    description: str | None
    category: str | None
    url: str | None


def fetch(url: str) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200:
            return resp.text
    except requests.RequestException:
        return None
    return None


def parse_price(text: str | None) -> float | None:
    if not text:
        return None
    t = text.strip()
    # Remove currency and spaces
    t = re.sub(r"[€\s]", "", t)
    # Keep digits, comma, dot; capture first numeric token (handles ranges by taking first)
    m = re.search(r"([0-9][0-9\.,]*)", t)
    if not m:
        return None
    num = m.group(1)
    if "," in num and "." in num:
        # Decide decimal separator by last occurrence
        last_dot = num.rfind(".")
        last_comma = num.rfind(",")
        if last_dot < last_comma:
            # European style: 1.234,56 -> remove dots, comma becomes decimal point
            num = num.replace(".", "").replace(",", ".")
        else:
            # US style: 1,234.56 -> remove commas, keep dot
            num = num.replace(",", "")
    elif "," in num:
        # Only comma present: treat as decimal
        num = num.replace(",", ".")
    else:
        # Only digits and maybe dots: already OK
        pass
    try:
        return float(num)
    except ValueError:
        return None


UNIT_MAP = {
    "l": ("liters", 1.0),
    "ml": ("liters", 1 / 1000.0),
    "kg": ("kilograms", 1.0),
    "g": ("kilograms", 1 / 1000.0),
    "ks": ("pieces", 1.0),  # Slovak: pieces
    "pc": ("pieces", 1.0),
    "pcs": ("pieces", 1.0),
}


def parse_amount_and_unit(
    name: str | None, page_text: str | None
) -> tuple[float | None, str | None]:
    src = " ".join([s for s in [name, page_text] if s])
    src = unescape(src).lower()
    # Patterns like: 1 l, 1l, 0,5 l, 500 g, 12 ks
    for pattern in [
        r"(\d+[\.,]\d+)\s*(l|ml|kg|g)",
        r"(\d+)\s*(l|ml|kg|g|ks|pc|pcs)",
        r"(\d+[\.,]\d+)(l|ml|kg|g)",
        r"(\d+)(l|ml|kg|g|ks|pc|pcs)",
    ]:
        m = re.search(pattern, src)
        if m:
            raw_amount = m.group(1).replace(",", ".")
            unit = m.group(2)
            try:
                amount = float(raw_amount)
            except ValueError:
                continue
            pretty_unit, factor = UNIT_MAP.get(unit, (unit, 1.0))
            return round(amount * factor, 4), pretty_unit
    return None, None


def get_category_name_from_url(url: str) -> str:
    # Last non-empty path segment
    slug = [seg for seg in url.rstrip("/").split("/") if seg][-1]
    return slug.replace("-", " ")


def get_category_slug_from_url(url: str) -> str:
    # Use last path segment as slug
    return [seg for seg in url.rstrip("/").split("/") if seg][-1]


def extract_product_links(category_html: str) -> Iterable[str]:
    soup = BeautifulSoup(category_html, "html.parser")
    links: set[str] = set()
    # WooCommerce usual structure
    for a in soup.select(
        "ul.products li.product a.woocommerce-LoopProduct-link, a.woocommerce-LoopProduct-link"
    ):
        href = a.get("href")
        if isinstance(href, str) and href:
            links.add(href)
    # Fallback: any product link under products list
    if not links:
        for a in soup.select("ul.products li.product a"):
            href = a.get("href")
            if isinstance(href, str) and href:
                links.add(href)
    # Final fallback: theme outputs product cards linking to /shop/... detail pages
    if not links:
        for a in soup.select("a[href*='/donaskake/shop/']"):
            href = a.get("href")
            if not (isinstance(href, str) and href):
                continue
            if "add-to-cart" in href or "#" in href:
                continue
            # Only include product detail pages like /donaskake/shop/<slug>/
            m = re.search(r"/donaskake/shop/([^/?#]+)/?$", href)
            if not m:
                continue
            links.add(href)
    return links


def canonicalize_url(u: str) -> str:
    try:
        p = urlparse(u)
        # Drop query/fragment and normalize trailing slash
        path = p.path.rstrip("/")
        return urlunparse((p.scheme, p.netloc, path, "", "", ""))
    except Exception:
        return u


def extract_next_page_url(category_html: str) -> str | None:
    soup = BeautifulSoup(category_html, "html.parser")
    # rel=next first
    a = soup.select_one("a[rel='next']")
    if a:
        href = a.get("href")
        if isinstance(href, str):
            return href
    # WooCommerce pagination next
    a = soup.select_one(".woocommerce-pagination a.next, nav.pagination a.next")
    if a:
        href = a.get("href")
        if isinstance(href, str):
            return href
    return None


def extract_text_or_none(soup: BeautifulSoup, selector: str) -> str | None:
    el = soup.select_one(selector)
    return el.get_text(strip=True) if el else None


def extract_html_or_none(soup: BeautifulSoup, selector: str) -> str | None:
    el = soup.select_one(selector)
    return str(el) if el else None


def parse_product_page(url: str, category_label: str) -> Product:
    html = fetch(url)
    if not html:
        return Product(None, None, None, None, None, None, None, None, category_label, url)
    soup = BeautifulSoup(html, "html.parser")

    # Name
    name = extract_text_or_none(soup, "h1.product_title") or extract_text_or_none(
        soup, "h1.entry-title"
    )

    # Prices: WooCommerce uses <p class="price"><ins> for discounted, <del> for regular
    price_block = soup.select_one("p.price") or soup.select_one("span.price")
    regular_price = None
    discounted_price = None
    if price_block:
        ins = price_block.select_one("ins .amount, ins .woocommerce-Price-amount, ins")
        delp = price_block.select_one("del .amount, del .woocommerce-Price-amount, del")
        if ins and delp:
            discounted_price = parse_price(ins.get_text(" ", strip=True))
            regular_price = parse_price(delp.get_text(" ", strip=True))
        else:
            # Single price
            amt = price_block.select_one(".amount, .woocommerce-Price-amount") or price_block
            regular_price = parse_price(amt.get_text(" ", strip=True))

    # ID: try container id like product-12345 or post-12345
    prod_container = soup.select_one("div.product") or soup.select_one(
        "div[id^='product-'], div[id^='post-']"
    )
    pid = None
    if prod_container:
        pid_attr = prod_container.get("id")
        if isinstance(pid_attr, str):
            m = re.search(r"(?:product|post)-(\d+)", pid_attr)
            if m:
                pid = m.group(1)
    if not pid:
        # Try meta tag
        meta = soup.select_one("meta[property='og:url']")
        if meta:
            content = meta.get("content")
            if isinstance(content, str):
                m = re.search(r"/(\d+)/?$", content)
                if m:
                    pid = m.group(1)

    # Description
    description_html = (
        extract_html_or_none(soup, "div#tab-description")
        or extract_html_or_none(soup, "div.woocommerce-Tabs-panel--description")
        or extract_html_or_none(soup, "div.product-short-description")
    )

    # Amount + unit
    page_text_sample = " ".join(
        [
            extract_text_or_none(soup, "div.product-short-description") or "",
            extract_text_or_none(soup, "div.summary") or "",
        ]
    )
    amount, unit = parse_amount_and_unit(name, page_text_sample)

    discount_pct = None
    if regular_price and discounted_price and regular_price > 0:
        discount_pct = round((1 - discounted_price / regular_price) * 100, 2)

    return Product(
        id=pid,
        name=name,
        price=regular_price,
        price_discounted=discounted_price,
        discount_percentage=discount_pct,
        amount=amount,
        unit=unit,
        description=description_html,
        category=category_label,
        url=url,
    )


def scrape_category(
    category_url: str, delay_sec: float = 0.5, limit: int | None = None
) -> list[Product]:
    results: list[Product] = []
    to_visit = [category_url]
    seen_pages: set[str] = set()
    seen_products: set[str] = set()
    cat_label = get_category_name_from_url(category_url)
    while to_visit:
        page_url = to_visit.pop(0)
        if page_url in seen_pages:
            continue
        seen_pages.add(page_url)
        html = fetch(page_url)
        if not html:
            continue
        for link in extract_product_links(html):
            c = canonicalize_url(link)
            if c in seen_products:
                continue
            seen_products.add(c)
            product = parse_product_page(link, cat_label)
            results.append(product)
            time.sleep(delay_sec)
            if limit is not None and len(results) >= limit:
                return results
        next_url = extract_next_page_url(html)
        if next_url:
            to_visit.append(next_url)
        time.sleep(delay_sec)
    return results


def to_serializable(products: Iterable[Product]) -> list[dict]:
    return [asdict(p) for p in products]


def main():
    parser = argparse.ArgumentParser(description="Scrape ifresh.sk WooCommerce category")
    parser.add_argument(
        "--category",
        default="https://www.ifresh.sk/donaskake/product-category/ovocie-a-zelenina/",
        help="Category URL to scrape",
    )
    parser.add_argument("--all", action="store_true", help="Scrape all default categories")
    parser.add_argument("--out", default=None, help="Output file path (JSON)")
    parser.add_argument("--outdir", default="data", help="Directory for per-category JSON files")
    parser.add_argument(
        "--limit", type=int, default=None, help="Max products to fetch per category"
    )
    parser.add_argument(
        "--delay", type=float, default=0.5, help="Delay between requests in seconds"
    )
    args = parser.parse_args()

    import os

    # Ensure outdir exists if using --all or when writing per-category files
    if args.all or args.outdir:
        os.makedirs(args.outdir, exist_ok=True)

    if args.all:
        for url in CATEGORY_URLS:
            slug = get_category_slug_from_url(url)
            products = scrape_category(url, delay_sec=args.delay, limit=args.limit)
            data = json.dumps(to_serializable(products), ensure_ascii=False, indent=2)
            out_path = os.path.join(args.outdir, f"{slug}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(data)
        return

    # Single-category mode
    products = scrape_category(args.category, delay_sec=args.delay, limit=args.limit)
    data = json.dumps(to_serializable(products), ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(data)
    else:
        # Default: write to outdir/<slug>.json
        slug = get_category_slug_from_url(args.category)
        out_path = os.path.join(args.outdir, f"{slug}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(data)


if __name__ == "__main__":
    main()
