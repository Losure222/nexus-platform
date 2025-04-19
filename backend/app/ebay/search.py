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

        # Normalize search and add "type": "ebay" to each match
        query_normalized = query.replace("-", "").lower()

        filtered = []
        for item in items:
            title_normalized = item.get("title", "").replace("-", "").lower()
            if query_normalized in title_normalized:
                # Check if the country data is present before filtering
                seller_country = item.get('seller', {}).get('country', '').lower() if item.get('seller') else ""
                item_country = item.get('itemLocation', {}).get('country', '').lower() if item.get('itemLocation') else ""

                # Only add item if country data exists and isn't conflicting with China
                if seller_country and item_country and not (
                    "china" in seller_country and item_country != 'china') and not (
                    "china" in item_country and seller_country != 'china'):

                    item["type"] = "ebay"  # Add supplier type tag
                    filtered.append(item)

        # Debug print
        print(f"\n🔍 eBay search for '{query}' → {len(filtered)} matches")
        for i, item in enumerate(filtered, 1):
            print(f"{i}. {item.get('title')} — {item.get('itemWebUrl')}")

        return {"itemSummaries": filtered}

    else:
        raise Exception(f"eBay search failed: {response.status_code} - {response.text}")
