import requests
from .auth import get_access_token

def search_ebay(query, limit=20):
    token = get_access_token()

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    # Broaden keyword slightly: "1756-M02AS" → "1756 M02AS"
    normalized_keywords = query.replace("-", " ")

    params = {
        'q': normalized_keywords,
        'limit': limit,
        # Optional: add eBay category for Industrial Automation (categoryId = 55816)
        # 'category_ids': '55816',  # remove this line if you want broader results
        'filter': 'buyingOptions:{FIXED_PRICE}'
    }

    response = requests.get(
        'https://api.ebay.com/buy/browse/v1/item_summary/search',
        headers=headers,
        params=params
    )

    if response.status_code == 200:
        data = response.json()
        items = data.get("itemSummaries", [])

        # 🔍 Optional: Filter manually to ensure part number is in the title
        query_normalized = query.replace("-", "").lower()
        filtered = [
            item for item in items
            if query_normalized in item.get("title", "").replace("-", "").lower()
        ]

        # 🧾 Debug print (can be removed later)
        print(f"\n🔍 eBay search for '{query}' → {len(filtered)} matches")
        for i, item in enumerate(filtered, 1):
            print(f"{i}. {item.get('title')} — {item.get('itemWebUrl')}")

        return {"itemSummaries": filtered}
    else:
        raise Exception(f"eBay search failed: {response.status_code} - {response.text}")
