import json
import re
from pathlib import Path
from typing import Dict, List, Optional


class TescoProduct:
    """Represents a single Tesco product with parsed information."""

    def __init__(self, raw_data: Dict):
        """
        Initialize a TescoProduct from raw JSON data.

        Args:
            raw_data: Dictionary containing raw product data from JSON
        """
        self.product_id = raw_data.get("id")
        self.title = raw_data.get("title")

        # Parse price information
        self.price = self._parse_price(raw_data)

        # Parse description from promotion and offerText
        self.description = self._parse_description(raw_data)

        # Extract amount from title
        self.amount = self._extract_amount(raw_data.get("title", ""))

        # Extract category from search URL
        self.category = self._extract_category(raw_data.get("searchUrl", ""))

    def _parse_price(self, raw_data: Dict) -> Dict[str, Optional[float]]:
        """
        Parse price information from pricePerUnit and promotion fields.

        Returns:
            Dictionary with 'current', 'lidl_plus', and 'original' prices
        """
        price_per_unit = raw_data.get("pricePerUnit", "")
        promotion = raw_data.get("promotion")

        # Parse current price from pricePerUnit (e.g., "1,09 €/kg")
        current_price = self._extract_price_value(price_per_unit)

        # Parse Clubcard price from promotion
        clubcard_price = None
        if promotion and "clubcard" in promotion.lower():
            clubcard_price = self._extract_price_value(promotion)

        return {
            "current": current_price,
            "original": None,
            "lidl_plus": clubcard_price,  # Using same field name for consistency
        }

    def _extract_price_value(self, text: str) -> Optional[float]:
        """
        Extract numeric price value from text like "1,09 €/kg" or "1,19 € za kg".

        Args:
            text: Text containing price

        Returns:
            Float price value or None
        """
        if not text:
            return None

        # Match price patterns: "1,09 €" or "1.09 €"
        match = re.search(r"(\d+[,\.]\d+)\s*€", text)
        if match:
            price_str = match.group(1).replace(",", ".")
            try:
                return float(price_str)
            except ValueError:
                return None

        return None

    def _parse_description(self, raw_data: Dict) -> str:
        """
        Parse description from promotion and offerText fields.

        Args:
            raw_data: Raw product data

        Returns:
            Combined description string
        """
        parts = []

        if raw_data.get("promotion"):
            parts.append(raw_data["promotion"])

        if raw_data.get("offerText"):
            parts.append(raw_data["offerText"])

        return " | ".join(parts) if parts else ""

    def _extract_amount(self, title: str) -> Optional[str]:
        """
        Extract amount/quantity from product title.

        Common patterns in titles:
        - "Rožok štandard 50 g"
        - "Chlieb pšenično-ražný konzumný 1000 g"
        - "Uhorka šalátová ks"

        Returns:
            Extracted amount string or None
        """
        if not title:
            return None

        # Look for amount patterns at the end of title
        patterns = [
            r"(\d+\s*(?:g|kg|ml|l|ks))$",  # Weight/volume/pieces at end
            r"(\d+\s*(?:g|kg|ml|l|ks))\s*$",  # With optional space
        ]

        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_category(self, search_url: str) -> Optional[str]:
        """
        Extract category from search URL.

        Example: "https://potravinydomov.itesco.sk/groceries/sk-SK/shop/pekaren/all"
        -> "pekaren"

        Returns:
            Category name or None
        """
        if not search_url:
            return None

        match = re.search(r"/shop/([^/]+)/", search_url)
        if match:
            return match.group(1)

        return None

    def to_dict(self) -> Dict:
        """Convert product to dictionary representation."""
        return {
            "product_id": self.product_id,
            "name": self.title,
            "price": self.price["current"],
            "price_original": self.price["original"],
            "price_lidl_plus": self.price["lidl_plus"],
            "amount": self.amount,
            "description": self.description,
            "category": self.category,
        }

    def __repr__(self) -> str:
        price_str = f"{self.price['current']} €" if self.price["current"] else "N/A"
        if self.price["lidl_plus"]:
            price_str = f"{self.price['lidl_plus']} € (Clubcard)"
        return f"TescoProduct(name='{self.title}', price={price_str})"


class TescoParser:
    """Parser for Tesco product JSON files."""

    def __init__(self, data_dir: str = "grocery_datasets/tesco"):
        """
        Initialize the parser.

        Args:
            data_dir: Directory containing Tesco JSON files (relative to this file)
        """
        self.data_dir = Path(__file__).parent / data_dir
        self.products: List[TescoProduct] = []

    def load_json_file(self, file_path: Path) -> List[Dict]:
        """
        Load a single JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            List of product dictionaries
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                else:
                    return [data]
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return []

    def load_all_files(self) -> int:
        """
        Load all JSON files from the tesco directory.

        Returns:
            Number of products loaded
        """
        if not self.data_dir.exists():
            print(f"Directory not found: {self.data_dir}")
            return 0

        json_files = list(self.data_dir.glob("*.json"))
        print(f"Found {len(json_files)} JSON file(s) in {self.data_dir}")

        total_products = 0
        for json_file in json_files:
            print(f"Loading {json_file.name}...")
            raw_products = self.load_json_file(json_file)

            for raw_product in raw_products:
                product = TescoProduct(raw_product)
                # Only include products with a price
                if product.price["current"] is not None or product.price["lidl_plus"] is not None:
                    self.products.append(product)
                    total_products += 1

        print(f"Successfully loaded {total_products} products")
        return total_products

    def get_products_with_price(self) -> List[TescoProduct]:
        """Get all products that have a current price."""
        return [p for p in self.products if p.price["current"] is not None]

    def get_products_with_clubcard(self) -> List[TescoProduct]:
        """Get all products with Clubcard pricing."""
        return [p for p in self.products if p.price["lidl_plus"] is not None]

    def get_products_by_category(self, category: str) -> List[TescoProduct]:
        """Get all products in a specific category."""
        return [p for p in self.products if p.category and p.category.lower() == category.lower()]

    def export_to_json(self, output_file: str = "tesco_products_parsed.json"):
        """
        Export parsed products to a JSON file.

        Args:
            output_file: Output filename
        """
        output_path = Path(__file__).parent / output_file
        data = [p.to_dict() for p in self.products]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Exported {len(data)} products to {output_path}")

    def print_summary(self):
        """Print a summary of loaded products."""
        print("\n" + "=" * 60)
        print("TESCO PRODUCT PARSER SUMMARY")
        print("=" * 60)
        print(f"Total products: {len(self.products)}")
        print(f"Products with price: {len(self.get_products_with_price())}")
        print(f"Products with Clubcard: {len(self.get_products_with_clubcard())}")

        # Count by category
        categories = {}
        for p in self.products:
            cat = p.category or "Unknown"
            categories[cat] = categories.get(cat, 0) + 1

        print("\nProducts by category:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: {count}")

        print("\nSample products:")
        for i, product in enumerate(self.products[:5], 1):
            print(f"\n{i}. {product}")
            if product.amount:
                print(f"   Amount: {product.amount}")
            if product.description:
                desc = (
                    product.description[:100] + "..."
                    if len(product.description) > 100
                    else product.description
                )
                print(f"   Description: {desc}")


def main():
    """Main function to demonstrate the parser."""
    parser = TescoParser()

    # Load all JSON files
    parser.load_all_files()

    # Print summary
    parser.print_summary()

    # Export to JSON
    parser.export_to_json()

    # Example queries
    print("\n" + "=" * 60)
    print("EXAMPLE QUERIES")
    print("=" * 60)

    print("\nProducts with Clubcard pricing (first 3):")
    for product in parser.get_products_with_clubcard()[:3]:
        print(f"  {product}")

    # Show categories
    categories = set(p.category for p in parser.products if p.category)
    if categories:
        cat = list(categories)[0]
        print(f"\n'{cat}' category products (first 3):")
        for product in parser.get_products_by_category(cat)[:3]:
            print(f"  {product}")


if __name__ == "__main__":
    main()
