from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import csv
from pathlib import Path
from typing import List
from app.ebay.search import search_ebay

app = FastAPI()

# Enable CORS for frontend access during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can lock this down to just https://stanloautomation.com if you prefer
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
                row['type'] = 'vendor'

                # Normalize location
                raw_location = row.get('location', '').lower()
                if any(country in raw_location for country in ['de', 'fr', 'nl', 'pl', 'es', 'eu', 'europe']):
                    row['country'] = 'europe'
                elif 'china' in raw_location:
                    row['country'] = 'china'
                elif any(country in raw_location for country in ['us', 'usa', 'united states']):
                    row['country'] = 'usa'
                else:
                    row['country'] = 'n/a'

                row['quantity'] = row.get('quantity') or row.get('Quantity') or ''
                row['quantity'] = row['quantity'].strip()

                if 'manufacturer' in row:
                    row['manufacturer'] = row['manufacturer'].strip().lower()

                parts.append(row)
    return parts

@app.get("/parts")
def search_parts(query: str = Query(..., min_length=2)):
    normalized_query = query.replace("-", "").lower()
    all_parts = load_all_parts()

    csv_matches = [
        p for p in all_parts
        if normalized_query in p['part_number'].replace("-", "").lower()
    ]

    print(f"\n🔍 SEARCH: '{query}' → Normalized: '{normalized_query}'")
    print(f"📦 CSV matches found: {len(csv_matches)}")
    if csv_matches:
        print("🔎 Sample match:", csv_matches[0])

    try:
        ebay_data = search_ebay(query)
        ebay_items = ebay_data.get("itemSummaries", [])

        ebay_items = [
            item for item in ebay_items
            if not (
                "china" in item['seller']['country'].lower()
                and item['itemLocation']['country'].lower() != 'china'
            )
            and not (
                "china" in item['itemLocation']['country'].lower()
                and item['seller']['country'].lower() != 'china'
            )
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
        if name.lower() in p['manufacturer']
    ]
    return {"results": matches}

@app.get("/all-parts")
def get_all_parts():
    all_parts = load_all_parts()

    simplified = []
    seen = set()
    for p in all_parts:
        part_number = p.get("part_number", "").strip()
        manufacturer = p.get("manufacturer", "").strip()
        if part_number and manufacturer:
            key = (manufacturer.lower(), part_number.lower())
            if key not in seen:
                seen.add(key)
                simplified.append({
                    "manufacturer": manufacturer,
                    "part_number": part_number
                })

    return JSONResponse(content=simplified)

# ✅ NEW: return list of unique manufacturers
@app.get("/manufacturers")
def get_all_manufacturers():
    # List of approved brand names (normalized to lowercase)
    allowed_brands = {
        "abb", "allen bradley", "b&r", "beckhoff", "bosch rexroth",
        "balluff", "baumer", "baumüller", "berger lahr", "fanuc",
        "indramat", "mitsubishi", "schneider", "siemens", "eaton",
        "control techniques", "danfoss", "festo", "ge fanuc", "keyence",
        "kuka", "lenze", "leuze", "murrelektronik", "omron", "pepperl & fuchs",
        "phoenix contact", "pilz", "rexroth", "schmersal", "sew eurodrive",
        "sick", "vipa", "yaskawa",
    }

    all_parts = load_all_parts()
    found = set()

    for part in all_parts:
        raw = part.get("manufacturer", "").strip().lower()
        if raw in allowed_brands:
            found.add(raw)

    return JSONResponse(content=sorted(list(found)))
