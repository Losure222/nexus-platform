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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent.parent / "data/vendors"

brand_aliases = {
    "rexroth": "bosch rexroth",
    # Add more aliases as needed
}

def normalize_manufacturer(name):
    return brand_aliases.get(name.lower(), name.lower())

def load_all_parts() -> List[dict]:
    parts = []
    for file in DATA_DIR.glob("*.csv"):
        with open(file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['vendor_file'] = file.name
                row['type'] = 'vendor'

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
                    row['manufacturer'] = normalize_manufacturer(row['manufacturer'].strip())

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
    except Exception as e:
        print(f"eBay API error: {e}")
        ebay_items = []

    return {
        "csv_results": csv_matches,
        "ebay_results": ebay_items
    }

@app.get("/manufacturers/{name}")
def get_by_manufacturer(name: str):
    all_parts = load_all_parts()
    target = normalize_manufacturer(name)
    matches = [p for p in all_parts if target in p['manufacturer']]
    return {"results": matches}

@app.get("/all-parts")
def get_all_parts():
    all_parts = load_all_parts()
    seen = set()
    simplified = []
    for p in all_parts:
        part_number = p.get("part_number", "").strip()
        manufacturer = p.get("manufacturer", "").strip()
        key = (manufacturer.lower(), part_number.lower())
        if key not in seen:
            seen.add(key)
            simplified.append({"manufacturer": manufacturer, "part_number": part_number})
    return JSONResponse(content=simplified)

@app.get("/manufacturers")
def get_all_manufacturers():
    allowed = {
        "abb", "allen bradley", "b&r", "beckhoff", "bosch rexroth",
        "balluff", "baumer", "baumüller", "berger lahr", "fanuc",
        "indramat", "mitsubishi", "schneider", "siemens", "eaton",
        "control techniques", "danfoss", "festo", "ge fanuc", "keyence",
        "kuka", "lenze", "leuze", "murrelektronik", "omron", "pepperl & fuchs",
        "phoenix contact", "pilz", "rexroth", "schmersal", "sew eurodrive",
        "sick", "vipa", "yaskawa"
    }

    all_parts = load_all_parts()
    found = {p['manufacturer'] for p in all_parts if p['manufacturer'] in allowed}
    return JSONResponse(content=sorted(list(found)))

import stripe
from fastapi import HTTPException
from pydantic import BaseModel

import os
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

class PaymentRequest(BaseModel):
    name: str
    amount: float  # in USD

@app.post("/create-payment-link")
def create_payment_link(req: PaymentRequest):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': req.name,
                    },
                    'unit_amount': int(req.amount * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://stanloautomation.com/success',
            cancel_url='https://stanloautomation.com/cancel',
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
