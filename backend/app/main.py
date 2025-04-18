from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import csv
from pathlib import Path
from typing import List
from app.ebay.search import search_ebay

app = FastAPI()

# Enable CORS for frontend access during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Make sure this includes your frontend's origin (e.g., Vercel's URL for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent.parent / "data/vendors"

def load_all_parts() -> List[dict]:
    parts = []
    for file in DATA_DIR.glob("*.csv"):
        with open(file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['vendor_file'] = file.name
                row['type'] = 'vendor'  # Add type to identify as Trusted Supplier

                # Normalize location to support filter toggle
                raw_location = row.get('location', '').lower()
                if any(country in raw_location for country in ['de', 'fr', 'nl', 'pl', 'es', 'eu', 'europe']):
                    row['country'] = 'europe'
                elif 'china' in raw_location:
                    row['country'] = 'china'
                elif any(country in raw_location for country in ['us', 'usa', 'united states']):
                    row['country'] = 'usa'
                else:
                    row['country'] = 'n/a'

                # Ensure quantity is passed through (strip whitespace)
                row['quantity'] = row.get('quantity') or row.get('Quantity') or ''
                row['quantity'] = row['quantity'].strip()

                parts.append(row)
    return parts

@app.get("/parts")
def search_parts(query: str = Query(..., min_length=2)):
    normalized_query = query.replace("-", "").lower()

    # Load and filter vendor CSV matches
    all_parts = load_all_parts()
    csv_matches = [
        p for p in all_parts
        if normalized_query in p['part_number'].replace("-", "").lower()
    ]

    print(f"\n🔍 SEARCH: '{query}' → Normalized: '{normalized_query}'")
    print(f"📦 CSV matches found: {len(csv_matches)}")
    if csv_matches:
        print("🔎 Sample match:", csv_matches[0])  # 🔍 DEBUG LINE

    # Attempt eBay search
    try:
        ebay_data = search_ebay(query)
        ebay_items = ebay_data.get("itemSummaries", [])

        # Filter out items where the seller's registered country is China or where shipping location is different than the registered country
        ebay_items = [
            item for item in ebay_items
            if not ("china" in item['seller']['country'].lower() and item['itemLocation']['country'].lower() != 'china')  # Remove items from sellers registered in China, but shipping from another country
            and not ("china" in item['itemLocation']['country'].lower() and item['seller']['country'].lower() != 'china')  # Remove items where itemLocation is China, but seller is from a different country
        ]

        print(f"🛒 eBay results found: {len(ebay_items)}")
    except Exception as e:
        print(f"❌ eBay API error: {e}")
        ebay_items = []

    return {
        "csv_results": csv_matches,
        "ebay_results": ebay_items
    }

@app.get("/manufacturers/{name}")
def get_by_manufacturer(name: str):
    all_parts = load_all_parts()
    matches = [
        p for p in all_parts
        if name.lower() in p['manufacturer'].lower()
    ]
    return {"results": matches}
