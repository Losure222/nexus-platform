from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pathlib import Path
from typing import List
import csv
import os
import stripe
from app.ebay.search import search_ebay

app = FastAPI()

# CORS settings for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File paths
VENDOR_DIR = Path(__file__).parent.parent / "data/vendors"
SEO_FILE = Path(__file__).parent.parent / "data/seo/master_parts.csv"

# Brand name cleanup rules
brand_aliases = {
    "rexroth": "bosch rexroth",
    # Add more brand mappings if needed
}

def normalize_manufacturer(name: str) -> str:
    return brand_aliases.get(name.lower(), name.lower())

def load_all_vendor_parts() -> List[dict]:
    parts = []
    for file in VENDOR_DIR.glob("*.csv"):
        with open(file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['vendor_file'] = file.name
                row['type'] = 'vendor'
                row['manufacturer'] = normalize_manufacturer(row.get('manufacturer', '').strip())
                row['part_number'] = row.get('part_number', '').strip()
                row['quantity'] = row.get('quantity', '').strip()

                # Country tagging
                location = row.get('location', '').lower()
                if any(c in location for c in ['de', 'fr', 'nl', 'pl', 'es', 'eu', 'europe']):
                    row['country'] = 'europe'
                elif 'china' in location:
                    row['country'] = 'china'
                elif any(c in location for c in ['us', 'usa', 'united states']):
                    row['country'] = 'usa'
                else:
                    row['country'] = 'n/a'

                parts.append(row)
    return parts

def load_seo_parts() -> List[dict]:
    if not SEO_FILE.exists():
        return []
    with open(SEO_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [{
            "manufacturer": normalize_manufacturer(row.get("manufacturer", "").strip()),
            "part_number": row.get("part_number", "").strip(),
            "description": row.get("description", ""),
            "source": "seo"
        } for row in reader]

def is_chinese_seller(item):
    seller_country = item.get("seller", {}).get("country", "").lower()
    item_country = item.get("itemLocation", {}).get("country", "").lower()
    return "china" in seller_country or "china" in item_country

@app.get("/parts")
def search_vendor_parts(query: str = Query(..., min_length=2)):
    normalized = query.replace("-", "").lower()
    vendor_parts = load_all_vendor_parts()
    matches = [p for p in vendor_parts if normalized in p.get('part_number', '').replace("-", "").lower()]

    try:
        ebay_data = search_ebay(query)
        ebay_items = [item for item in ebay_data.get("itemSummaries", []) if not is_chinese_seller(item)]
    except Exception as e:
        print(f"eBay error: {e}")
        ebay_items = []

    return {
        "csv_results": matches,
        "ebay_results": ebay_items
    }

@app.get("/seo-parts")
def search_seo_parts(query: str = Query(..., min_length=2)):
    normalized = query.replace("-", "").lower()
    seo_parts = load_seo_parts()
    matches = [p for p in seo_parts if normalized in p['part_number'].replace("-", "").lower()]
    return {"results": matches}

@app.get("/master")
def get_master_parts(query: str = None, manufacturer: str = None):
    if not SEO_FILE.exists():
        return {"results": []}

    normalized_query = query.replace("-", "").lower() if query else None
    results = []

    with open(SEO_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_manufacturer = normalize_manufacturer(row.get("manufacturer", "").strip())
            part_number = row.get("part_number", "").strip()
            description = row.get("description", "").strip()

            # Manufacturer filter
            if manufacturer and row_manufacturer != normalize_manufacturer(manufacturer):
                continue

            # Part number filter
            if normalized_query and normalized_query not in part_number.replace("-", "").lower():
                continue

            results.append({
                "manufacturer": row_manufacturer,
                "part_number": part_number,
                "description": description,
                "source": "seo"
            })

    return {"results": results}

@app.get("/manufacturers/{name}")
def get_vendor_parts_by_manufacturer(name: str):
    vendor_parts = load_all_vendor_parts()
    target = normalize_manufacturer(name)
    matches = [p for p in vendor_parts if target in p['manufacturer']]
    return {"results": matches}

@app.get("/all-parts")
def get_all_unique_vendor_parts():
    all_parts = load_all_vendor_parts()
    seen = set()
    unique = []
    for p in all_parts:
        key = (p['manufacturer'].lower(), p['part_number'].lower())
        if key not in seen:
            seen.add(key)
            unique.append({"manufacturer": p['manufacturer'], "part_number": p['part_number']})
    return JSONResponse(content=unique)

@app.get("/manufacturers")
def list_approved_manufacturers():
    allowed = {
        "abb", "allen bradley", "b&r", "beckhoff", "bosch rexroth",
        "balluff", "baumer", "baumüller", "berger lahr", "fanuc",
        "indramat", "mitsubishi", "schneider", "siemens", "eaton",
        "control techniques", "danfoss", "festo", "ge fanuc", "keyence",
        "kuka", "lenze", "leuze", "murrelektronik", "omron", "pepperl & fuchs",
        "phoenix contact", "pilz", "rexroth", "schmersal", "sew eurodrive",
        "sick", "vipa", "yaskawa"
    }
    vendor_parts = load_all_vendor_parts()
    found = {p['manufacturer'] for p in vendor_parts if p['manufacturer'] in allowed}
    return JSONResponse(content=sorted(list(found)))

# Stripe payment endpoint
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

class PaymentRequest(BaseModel):
    name: str
    amount: float  # in USD

@app.post("/create-payment-link")
def create_payment_link(req: PaymentRequest):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": req.name},
                    "unit_amount": int(req.amount * 100)
                },
                "quantity": 1
            }],
            mode="payment",
            success_url="https://stanloautomation.com/thank-you",
            cancel_url="https://stanloautomation.com/cancel"
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
