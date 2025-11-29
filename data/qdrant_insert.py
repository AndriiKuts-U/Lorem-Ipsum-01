import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).parent
DATASETS_DIR = BASE_DIR / "grocery_datasets"


def _compute_discount_percentage(
    price: Optional[float], old_price: Optional[float], explicit: Optional[float]
) -> Optional[float]:
    if explicit is not None:
        return explicit
    if price is not None and old_price is not None:
        try:
            if old_price > price and old_price > 0:
                return round((old_price - price) / old_price * 100, 2)
        except Exception:
            return None
    return None


_DESC_UNIT_REGEX = re.compile(r"(\b\d+[\d,.]*\s?(?:ml|l|g|kg|ks|pcs|pack|L|G|KG)\b)", re.IGNORECASE)


def _extract_units_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    match = _DESC_UNIT_REGEX.search(text.replace("&nbsp;", " "))
    if match:
        return match.group(1).strip()
    return None


def _parse_lidl_product(p: Dict[str, Any]) -> Dict[str, Any]:
    title = p.get("title")
    price_block = p.get("price", {}) or {}
    lidl_plus = p.get("lidlPlus", {}) or {}
    lp_price_block = lidl_plus.get("price", {}) or {}
    lp_discount_block = lp_price_block.get("discount", {}) or {}

    # Current price resolution order
    price: Optional[float] = price_block.get("current")
    if price is None:
        price = lp_price_block.get("price")

    # Old price resolution order
    old_price: Optional[float] = price_block.get("originalPrice")
    if old_price is None:
        old_price = lp_price_block.get("oldPrice")
    if old_price is None:
        old_price = lp_discount_block.get("deletedPrice")

    explicit_discount = price_block.get("discountPercentage")
    if explicit_discount is None:
        # Try highlight text like "-28 %" in lidlPlus.highlightText
        highlight = lidl_plus.get("highlightText") or lp_discount_block.get("discountText")
        if isinstance(highlight, str):
            m = re.search(r"(-?\d+[\d,.]*)\s?%", highlight)
            if m:
                try:
                    explicit_discount = float(m.group(1).replace(",", "."))
                except ValueError:
                    explicit_discount = None

    discount_percentage = _compute_discount_percentage(price, old_price, explicit_discount)

    description_html = p.get("description") or ""
    units = _extract_units_from_text(description_html)
    # Fallback: if title contains size info
    if units is None and isinstance(title, str):
        units = _extract_units_from_text(title)

    return {
        "name": title,
        "source": "lidl",
        "price": price,
        "old_price": old_price,
        "discount_percentage": discount_percentage,
        "units_of_measurement": units,
    }


def _parse_tesco_product(p: Dict[str, Any]) -> Dict[str, Any]:
    title = p.get("title")
    price_block = p.get("price", {}) or {}
    price: Optional[float] = price_block.get("actual")
    # Tesco sample doesn't show old price or discount; keep None
    old_price: Optional[float] = price_block.get("previous") or None
    discount_percentage: Optional[float] = None

    # Units: direct field or parse title
    units = price_block.get("unitOfMeasure")
    if units is None and isinstance(title, str):
        units = _extract_units_from_text(title)
    description_list = p.get("description") or []
    if units is None and isinstance(description_list, list):
        for d in description_list:
            if isinstance(d, str):
                units = _extract_units_from_text(d)
                if units:
                    break

    discount_percentage = _compute_discount_percentage(price, old_price, None)

    return {
        "name": title,
        "source": "tesco",
        "price": price,
        "old_price": old_price,
        "discount_percentage": discount_percentage,
        "units_of_measurement": units,
    }


def load_products(datasets_dir: Path = DATASETS_DIR) -> List[Dict[str, Any]]:
    products: List[Dict[str, Any]] = []
    if not datasets_dir.exists():
        return products
    for source_dir in datasets_dir.iterdir():
        if not source_dir.is_dir():
            continue
        source_name = source_dir.name.lower()
        parser = None
        if source_name == "lidl":
            parser = _parse_lidl_product
        elif source_name == "tesco":
            parser = _parse_tesco_product
        else:
            continue  # Skip unknown sources

        json_files = sorted(source_dir.glob("*.json"))
        for jf in json_files:
            try:
                with jf.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            prod = parser(item)
                            products.append(prod)
                elif isinstance(data, dict):
                    # Single product JSON
                    prod = parser(data)
                    products.append(prod)
            except Exception as e:
                print(f"Error loading {jf}: {e}")

    return products


if __name__ == "__main__":
    all_products = load_products()

    output_file = BASE_DIR / "all_products.json"
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    print(f"Total products loaded: {len(all_products)}")
