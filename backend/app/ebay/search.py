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
        'filter': 'buyingOptions:{FIXED_PRICE}'  # Filtering for fixed price items
    }

    try:
        response = requests.get(
            'https://api.ebay.com/buy/browse/v1/item_summary/search',
            headers=headers,
            params=params
        )

        # Log the response code and raw data for debugging
        print(f"🔧 eBay API Response Code: {response.status_code}")
        print(f"🔧 eBay API Response: {response.text[:500]}...")  # Log first 500 characters for easier reading

        if response.status_code == 200:
            data = response.json()
            items = data.get("itemSummaries", [])

            # Normalize search and add "type": "ebay" to each match
            query_normalized = query.replace("-", "").lower()

            filtered = []
            for item in items:
                title_normalized = item.get("title", "").replace("-", "").lower()

                if query_normalized in title_normalized:
                    item["type"] = "ebay"  # Add supplier type tag

                    # Filter based on seller country and shipping location mismatch
                    seller_country = item.get('seller', {}).get('country', '').lower()
                    item_location_country = item.get('itemLocation', {}).get('country', '').lower()

                    # Exclude if seller is in China but shipping from a different country
                    if seller_country == 'china' and item_location_country != 'china':
                        continue

                    # Exclude if the itemLocation is in China but seller is not
                    if item_location_country == 'china' and seller_country != 'china':
                        continue

                    filtered.append(item)

            # Debug print for filtered results
            print(f"\n🔍 eBay search for '{query}' → {len(filtered)} matches found after filtering")
            for i, item in enumerate(filtered, 1):
                print(f"{i}. {item.get('title')} — {item.get('itemWebUrl')}")

            return {"itemSummaries": filtered}

        else:
            raise Exception(f"eBay search failed: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Error occurred during eBay API request: {e}")
        return {"itemSummaries": []}  # Return an empty list if there was an error
