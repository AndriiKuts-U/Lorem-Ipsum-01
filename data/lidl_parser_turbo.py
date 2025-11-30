import asyncio
import json
from pathlib import Path

from openai import AsyncOpenAI
from pydantic import BaseModel
from backend.settings import settings

SYSTEM_PROMPT = "You are an expert data parser. " \
"Given a JSON object representing a product from Lidl, extract data about the product and return it in a structured format. " \
"Some data will be explicitly stated in json while some you will need to infer based on the content. Ensure accuracy and completeness. " \
"Return all data translated into English. " \
"Price per unit is a price per one liter or kilogram, you can calculate from price and amount stated." \
"Price discounted is the price after any discounts have been applied, for example discounts related to lidl plus card. " \
"Discount percentage is the percentage discount applied to the original price. " \
"Amount is the quantity of the product, e.g., 1.5 for 1.5 liters. " \
"Unit is the unit of measurement for the amount, e.g., liters, kilograms, pieces, etc. " \


class ProductStructured(BaseModel):
    id: str
    name: str
    price: float
    price_discounted: float | None
    discount_percentage: float | None
    amount: float | None
    unit: str | None
    description: str
    category: str


def load_json_files(folder_path: str) -> list[dict]:
    all_objects = []
    folder = Path(folder_path)

    for json_file in folder.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                all_objects.extend(data)
            else:
                all_objects.append(data)

    return all_objects


async def process_with_gpt(product: dict, client: AsyncOpenAI, semaphore: asyncio.Semaphore, index: int, total: int) -> ProductStructured:
    async with semaphore:
        print(f"Processing {index}/{total}...")
        completion = await client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(product)},
            ],
            response_format=ProductStructured,
        )

        result = completion.choices[0].message.parsed
        if result is None:
            raise ValueError("GPT returned no parsed result")
        return result


async def main():
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    lidl_folder = Path(__file__).parent / "grocery_datasets" / "lidl"
    products = load_json_files(str(lidl_folder))

    print(f"Loaded {len(products)} products")

    semaphore = asyncio.Semaphore(100)

    tasks = [
        process_with_gpt(product, client, semaphore, i + 1, len(products))
        for i, product in enumerate(products)
    ]

    results = await asyncio.gather(*tasks)

    output_file = Path(__file__).parent / "lidl_parsed_turbo.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump([r.model_dump() for r in results], f, indent=2, ensure_ascii=False)

    print(f"Saved {len(results)} structured products to {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
