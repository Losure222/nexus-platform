# backend/app/ebay/auth.py
import requests
from base64 import b64encode

# REPLACE THESE with your actual Production Client ID and Client Secret
CLIENT_ID = 'StanloAu-Nexus-PRD-60e9e8612-bab2b20c'
CLIENT_SECRET = 'PRD-0e9e8612f300-dd5c-43dd-ac09-e2a5'

def get_access_token():
    encoded = b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

    headers = {
        'Authorization': f'Basic {encoded}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = {
        'grant_type': 'client_credentials',
        'scope': 'https://api.ebay.com/oauth/api_scope'
    }

    response = requests.post(
        'https://api.ebay.com/identity/v1/oauth2/token',
        headers=headers,
        data=data
    )

    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Failed to get token: {response.status_code} - {response.text}")
