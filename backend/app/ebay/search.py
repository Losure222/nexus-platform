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

        # Log the raw results to check if eBay returns anything
        print(f"\nRaw eBay results for '{query}':")
        for item in items:
            print(f"Title: {item.get('title')}, Seller Country: {item.get('seller', {}).get('country')}")

        # Normalize search and add "type": "ebay" to each match
        query_normalized = query.replace("-", "").lower()

        # Include all eBay results, no filtering
        filtered = []
        for item in items:
            title_normalized = item.get("title", "").replace("-", "").lower()
            if query_normalized in title_normalized:
                item["type"] = "ebay"  # Add supplier type tag
                filtered.append(item)

        # Debug print
        print(f"\n🔍 eBay search for '{query}' → {len(filtered)} matches")
        for i, item in enumerate(filtered, 1):
            print(f"{i}. {item.get('title')} — {item.get('itemWebUrl')}")

        return {"itemSummaries": filtered}

    else:
        raise Exception(f"eBay search failed: {response.status_code} - {response.text}")
