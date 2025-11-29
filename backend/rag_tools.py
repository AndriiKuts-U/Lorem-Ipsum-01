"""
Tools for comparing grocery prices across different stores using RAG.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
from rag import RAGSystem


@dataclass
class GroceryItem:
    """Represents a grocery item from a store."""
    name: str
    store: str
    price: float
    price_original: Optional[float]
    amount: str
    unit: str
    description: str
    category: str
    similarity_score: float


@dataclass
class PriceComparison:
    """Result of price comparison across stores."""
    query: str
    cheapest_store: str
    cheapest_price: float
    items_by_store: Dict[str, List[GroceryItem]]
    price_differences: Dict[str, float]  # percentage difference from cheapest
    recommendation: str


class GroceryPriceComparer:
    """Compare grocery prices across different stores using RAG."""

    def __init__(
        self,
        rag_system: RAGSystem,
        price_threshold_percent: float = 5.0,
        min_similarity_score: float = 0.6
    ):
        """
        Initialize the price comparer.

        Args:
            rag_system: The RAG system instance to use for searching
            price_threshold_percent: Price difference threshold in percentage (default 5%)
            min_similarity_score: Minimum similarity score to consider a match (default 0.3)
        """
        self.rag = rag_system
        self.price_threshold = price_threshold_percent
        self.min_similarity = min_similarity_score

    def search_groceries(
        self,
        query: str,
        top_k: int = 10
    ) -> List[GroceryItem]:
        """
        Search for groceries matching the query.

        Args:
            query: Product query (e.g., "milk", "bread")
            top_k: Number of results to retrieve

        Returns:
            List of GroceryItem objects
        """
        # IMPORTANT: Pass include_metadata=True to get price and store info
        results = self.rag.retrieve_context(query, top_k=top_k, include_metadata=True)

        items = []
        for result in results:
            # Skip if similarity is too low
            if result['score'] < self.min_similarity:
                continue

            # Extract metadata
            try:
                price = float(result.get('price', 0))
                price_original = float(result.get('price_original', 0)) if result.get('price_original') else None
            except (ValueError, TypeError):
                price = 0.0
                price_original = None

            item = GroceryItem(
                name=result.get('text', ''),
                store=result.get('source', 'unknown'),
                price=price,
                price_original=price_original,
                amount=result.get('amount', ''),
                unit=result.get('unit', ''),
                description=result.get('description', ''),
                category=result.get('category', ''),
                similarity_score=result['score']
            )
            items.append(item)

        return items

    def compare_prices(
        self,
        query: str,
        top_k: int = 10
    ) -> Optional[PriceComparison]:
        """
        Compare prices for a grocery item across stores.

        Args:
            query: Product query (e.g., "milk 1L", "whole grain bread")
            top_k: Number of results to search

        Returns:
            PriceComparison object with analysis, or None if no items found
        """
        # Search for items
        items = self.search_groceries(query, top_k=top_k)

        if not items:
            return None

        # Group items by store
        items_by_store = defaultdict(list)
        for item in items:
            items_by_store[item.store].append(item)

        # Find cheapest price per store (take the cheapest item from each store)
        store_prices = {}
        for store, store_items in items_by_store.items():
            # Get the cheapest item from this store
            cheapest = min(store_items, key=lambda x: x.price)
            store_prices[store] = cheapest.price

        # Find overall cheapest
        cheapest_store = min(store_prices, key=store_prices.get)
        cheapest_price = store_prices[cheapest_store]

        # Calculate price differences
        price_differences = {}
        for store, price in store_prices.items():
            if price > 0:
                diff_percent = ((price - cheapest_price) / cheapest_price) * 100
                price_differences[store] = round(diff_percent, 2)
            else:
                price_differences[store] = 0.0

        # Generate recommendation
        recommendation = self._generate_recommendation(
            query,
            cheapest_store,
            cheapest_price,
            store_prices,
            price_differences
        )

        return PriceComparison(
            query=query,
            cheapest_store=cheapest_store,
            cheapest_price=cheapest_price,
            items_by_store=dict(items_by_store),
            price_differences=price_differences,
            recommendation=recommendation
        )

    def _generate_recommendation(
        self,
        query: str,
        cheapest_store: str,
        cheapest_price: float,
        store_prices: Dict[str, float],
        price_differences: Dict[str, float]
    ) -> str:
        """Generate a human-readable recommendation in English."""

        recommendation_parts = [
            f"Price Comparison for '{query}':",
            f"\n{'='*50}",
            f"\nCHEAPEST OPTION:",
            f"  ✓ {cheapest_store}: €{cheapest_price:.2f} - BEST PRICE",
            f"\n{'='*50}"
        ]

        # Add other stores with price differences
        other_stores = []
        for store, price in store_prices.items():
            if store != cheapest_store:
                diff = price_differences[store]
                diff_amount = price - cheapest_price
                if diff <= self.price_threshold:
                    status = "✓ Similar price"
                else:
                    status = "✗ More expensive"
                other_stores.append(
                    f"  {store}: €{price:.2f} ({status}, +€{diff_amount:.2f} / +{diff:.1f}%)"
                )

        if other_stores:
            recommendation_parts.append("\nOTHER STORES:")
            recommendation_parts.extend(other_stores)

        # Add final recommendation
        significant_savings = any(
            diff > self.price_threshold
            for store, diff in price_differences.items()
            if store != cheapest_store
        )

        recommendation_parts.append(f"\n{'='*50}")
        if significant_savings:
            max_savings = max(
                (store_prices[store] - cheapest_price
                 for store in store_prices if store != cheapest_store),
                default=0
            )
            recommendation_parts.append(
                f"RECOMMENDATION: Buy at {cheapest_store} - Save up to €{max_savings:.2f}!"
            )
        else:
            recommendation_parts.append(
                f"RECOMMENDATION: Prices are similar (difference < {self.price_threshold}%), "
                f"you can buy at any store."
            )
        recommendation_parts.append(f"{'='*50}")

        return "\n".join(recommendation_parts)

    def compare_shopping_list(
        self,
        items: List[str],
        top_k_per_item: int = 10
    ) -> Dict[str, PriceComparison]:
        """
        Compare prices for multiple items (shopping list).

        Args:
            items: List of product queries (e.g., ["milk", "bread", "butter"])
            top_k_per_item: Number of results per item

        Returns:
            Dictionary mapping each query to its PriceComparison
        """
        results = {}
        for item in items:
            comparison = self.compare_prices(item, top_k=top_k_per_item)
            if comparison:
                results[item] = comparison
        return results

    def get_best_store_for_list(
        self,
        items: List[str],
        top_k_per_item: int = 10
    ) -> Dict[str, any]:
        """
        Determine the best store for buying all items in a shopping list.

        Args:
            items: List of product queries
            top_k_per_item: Number of results per item

        Returns:
            Dictionary with best store analysis
        """
        comparisons = self.compare_shopping_list(items, top_k_per_item)

        if not comparisons:
            return {
                "recommendation": "No products found",
                "total_by_store": {},
                "items": {},
                "item_details": []
            }

        # Calculate total cost per store and track item details
        store_totals = defaultdict(float)
        store_item_counts = defaultdict(int)
        item_details = []  # Detailed breakdown per item

        # Get all unique stores
        all_stores = set()
        for comparison in comparisons.values():
            all_stores.update(comparison.items_by_store.keys())

        for item_query, comparison in comparisons.items():
            item_info = {
                "query": item_query,
                "prices_by_store": {}
            }

            for store in all_stores:
                store_items = comparison.items_by_store.get(store, [])
                if store_items:
                    best_match = max(store_items, key=lambda x: x.similarity_score)
                    item_info["prices_by_store"][store] = {
                        "name": best_match.name,
                        "price": round(best_match.price, 2),
                        "amount": best_match.amount,
                        "unit": best_match.unit,
                        "similarity": round(best_match.similarity_score, 3)
                    }
                    store_totals[store] += best_match.price
                    store_item_counts[store] += 1
                else:
                    item_info["prices_by_store"][store] = None

            item_details.append(item_info)

        # Find store with lowest total (only consider stores that have all items)
        max_items = len(items)
        valid_stores = {
            store: total
            for store, total in store_totals.items()
            if store_item_counts[store] >= max_items * 0.7  # At least 70% of items
        }

        if not valid_stores:
            return {
                "recommendation": "No store has most of the products",
                "total_by_store": dict(store_totals),
                "items": comparisons,
                "item_details": item_details
            }

        best_store = min(valid_stores, key=valid_stores.get)
        best_total = valid_stores[best_store]

        # Build detailed recommendation text
        recommendation_parts = []
        recommendation_parts.append("=" * 70)
        recommendation_parts.append("SHOPPING LIST PRICE COMPARISON")
        recommendation_parts.append("=" * 70)

        # Item-by-item breakdown
        recommendation_parts.append("\nITEM BREAKDOWN:")
        recommendation_parts.append("-" * 70)

        for item_info in item_details:
            recommendation_parts.append(f"\n📋 {item_info['query']}:")
            for store in sorted(all_stores):
                price_info = item_info['prices_by_store'].get(store)
                if price_info:
                    marker = "✓ BEST" if store == best_store else "  "
                    unit_str = f" ({price_info['amount']} {price_info['unit']})".strip()
                    if unit_str == "()":
                        unit_str = ""
                    recommendation_parts.append(
                        f"  {marker} {store}: €{price_info['price']:.2f} - {price_info['name']}{unit_str}"
                    )
                else:
                    recommendation_parts.append(f"      {store}: Not available")

        # Total prices at all stores
        recommendation_parts.append("\n" + "=" * 70)
        recommendation_parts.append("TOTAL PRICES BY STORE:")
        recommendation_parts.append("-" * 70)

        for store in sorted(all_stores):
            total = store_totals.get(store, 0)
            items_found = store_item_counts.get(store, 0)

            if store == best_store:
                marker = "🏆 BEST"
                savings_text = ""
            elif store in valid_stores:
                savings = total - best_total
                savings_percent = (savings / total) * 100
                marker = "  "
                savings_text = f" (+€{savings:.2f}, +{savings_percent:.1f}%)"
            else:
                marker = "  "
                savings_text = " (incomplete)"

            recommendation_parts.append(
                f"{marker} {store}: €{total:.2f} [{items_found}/{max_items} items]{savings_text}"
            )

        # Final recommendation
        recommendation_parts.append("\n" + "=" * 70)
        recommendation_parts.append("RECOMMENDATION:")
        recommendation_parts.append("-" * 70)
        recommendation_parts.append(f"✓ Shop at: {best_store.upper()}")
        recommendation_parts.append(f"✓ Total cost: €{best_total:.2f}")
        recommendation_parts.append(f"✓ Items found: {store_item_counts[best_store]}/{max_items}")

        # Calculate max savings
        if len(valid_stores) > 1:
            max_savings = max(
                total - best_total
                for store, total in valid_stores.items()
                if store != best_store
            )
            if max_savings > 0:
                recommendation_parts.append(f"✓ You save up to: €{max_savings:.2f} by choosing {best_store}!")

        recommendation_parts.append("=" * 70)

        recommendation = "\n".join(recommendation_parts)

        return {
            "best_store": best_store,
            "best_total": round(best_total, 2),
            "recommendation": recommendation,
            "total_by_store": {k: round(v, 2) for k, v in store_totals.items()},
            "items": comparisons,
            "item_details": item_details
        }


# Standalone functions for easy use

def compare_grocery_prices(
    query: str,
    rag_system: RAGSystem,
    price_threshold: float = 5.0,
    top_k: int = 10
) -> Optional[PriceComparison]:
    """
    Simple function to compare grocery prices.

    Args:
        query: Product query (e.g., "milk", "bread")
        rag_system: RAG system instance
        price_threshold: Price difference threshold in %
        top_k: Number of results

    Returns:
        PriceComparison or None
    """
    comparer = GroceryPriceComparer(rag_system, price_threshold)
    return comparer.compare_prices(query, top_k)


def find_best_store(
    shopping_list: List[str],
    rag_system: RAGSystem,
    price_threshold: float = 5.0
) -> Dict:
    """
    Find the best store for a shopping list.

    Args:
        shopping_list: List of product queries
        rag_system: RAG system instance
        price_threshold: Price difference threshold in %

    Returns:
        Dictionary with analysis
    """
    comparer = GroceryPriceComparer(rag_system, price_threshold)
    return comparer.get_best_store_for_list(shopping_list)


# Example usage
if __name__ == "__main__":
    # Initialize RAG system
    rag = RAGSystem()

    # Example 1: Compare single item
    print("="*60)
    print("Price comparison for a single product:")
    print("="*60)

    result = compare_grocery_prices("chicken", rag, price_threshold=5.0)
    if result:
        print(result.recommendation)
        print()

    # Example 2: Shopping list comparison
    print("\n" + "="*60)
    print("Shopping list comparison:")
    print("="*60)

    shopping_list = ["Radishes", "Chicken thigh", "milk", "tomatoes", "potatoes", "bread"]
    best_store_result = find_best_store(shopping_list, rag)
    print(best_store_result["recommendation"])