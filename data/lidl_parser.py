import html
import json
import re
from pathlib import Path
from typing import Dict, List, Optional


class LidlProduct:
    """Represents a single Lidl product with parsed information."""

    def __init__(self, raw_data: Dict):
        """
        Initialize a LidlProduct from raw JSON data.

        Args:
            raw_data: Dictionary containing raw product data from JSON
        """
        self.product_id = raw_data.get("productId")
        self.title = raw_data.get("title")
        self.price = self._parse_price(raw_data)

        # Parse description and extract amount
        self.description = self._parse_description(raw_data.get("description"))
        self.amount = self._extract_amount(raw_data)
        self.category = raw_data.get("category", {}).get("main")

    def _parse_price(self, raw_data: Dict) -> Dict[str, Optional[float]]:
        """
        Parse price information including regular and Lidl Plus prices.

        Returns:
            Dictionary with 'current', 'lidl_plus', and 'original' prices
        """
        price_info = raw_data.get("price", {})
        current_price = price_info.get("current")
        original_price = price_info.get("originalPrice")

        # Check for Lidl Plus pricing
        lidl_plus_price = None
        if "lidlPlus" in raw_data:
            lidl_plus_info = raw_data["lidlPlus"].get("price", {})
            lidl_plus_price = lidl_plus_info.get("price")

        return {"current": current_price, "original": original_price, "lidl_plus": lidl_plus_price}

    def _parse_description(self, description: Optional[str]) -> str:
        """
        Parse HTML description and convert to plain text.

        Args:
            description: HTML description string

        Returns:
            Plain text description
        """
        if not description:
            return ""

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", description)
        # Decode HTML entities
        text = html.unescape(text)
        # Clean up whitespace
        text = " ".join(text.split())
        return text

    def _extract_amount(self, raw_data: Dict) -> Optional[str]:
        """
        Extract amount/quantity information from description or other fields.

        Common patterns:
        - "objem: 1 l"
        - "cena za 100 g"
        - "8 kotúčikov"
        - "1,5% tuku"

        Returns:
            Extracted amount string or None
        """
        description = raw_data.get("description", "")
        if not description:
            return None

        # Remove HTML tags first
        text = re.sub(r"<[^>]+>", " ", description)
        text = html.unescape(text)

        # Look for common amount patterns
        patterns = [
            r"objem:\s*([^<]+)",  # Volume
            r"(\d+\s*(?:g|kg|ml|l|ks))",  # Weight/volume/pieces
            r"cena za\s+(\d+\s*g)",  # Price per amount
            r"(\d+)\s+kotúčikov",  # Number of items
            r"(\d+[\d,\.]*\s*%\s*\w+)",  # Percentage (e.g., fat content)
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

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
            price_str = f"{self.price['lidl_plus']} € (Lidl Plus)"
        return f"LidlProduct(name='{self.title}', price={price_str})"


class LidlParser:
    """Parser for Lidl product JSON files."""

    def __init__(self, data_dir: str = "grocery_datasets/lidl"):
        """
        Initialize the parser.

        Args:
            data_dir: Directory containing Lidl JSON files (relative to this file)
        """
        self.data_dir = Path(__file__).parent / data_dir
        self.products: List[LidlProduct] = []

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
        Load all JSON files from the lidl directory.

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
                product = LidlProduct(raw_product)
                # Only include products with a price
                if product.price["current"] is not None or product.price["lidl_plus"] is not None:
                    self.products.append(product)
                    total_products += 1

        print(f"Successfully loaded {total_products} products")
        return total_products

    def get_products_with_price(self) -> List[LidlProduct]:
        """Get all products that have a current price."""
        return [p for p in self.products if p.price["current"] is not None]

    def get_products_with_lidl_plus(self) -> List[LidlProduct]:
        """Get all products with Lidl Plus pricing."""
        return [p for p in self.products if p.price["lidl_plus"] is not None]

    def get_products_by_category(self, category: str) -> List[LidlProduct]:
        """Get all products in a specific category."""
        return [p for p in self.products if p.category and p.category.lower() == category.lower()]

    def export_to_json(self, output_file: str = "lidl_products_parsed.json"):
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
        print("LIDL PRODUCT PARSER SUMMARY")
        print("=" * 60)
        print(f"Total products: {len(self.products)}")
        print(f"Products with price: {len(self.get_products_with_price())}")
        print(f"Products with Lidl Plus: {len(self.get_products_with_lidl_plus())}")

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
    parser = LidlParser()

    # Load all JSON files
    parser.load_all_files()

    # Print summary
    parser.print_summary()

    # Export to JSON
    parser.export_to_json()


if __name__ == "__main__":
    main()
