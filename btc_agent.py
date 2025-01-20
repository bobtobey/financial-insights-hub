import requests
from supabase import create_client
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
import jwt
import json

# Load environment variables from .env file
load_dotenv(override=True)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase.debug = False

# Decode and print the JWT
# decoded = jwt.decode(SUPABASE_KEY, options={"verify_signature": False})
# print(f"Decoded JWT: {decoded}")

def get_btc_price():
    """
    Fetch the current Bitcoin price and store it in Supabase
    """
    # Test a basic Supabase connection
    print("Testing basic Supabase connection...")
    try:
        response = supabase.table('btc_price').select('*').execute()
        # print(f"Supabase SELECT Test Response: {response}")
    except Exception as e:
        print(f"Error during Supabase SELECT test: {type(e).__name__} - {str(e)}")

    try:
        # Fetch BTC price from CoinGecko
        print("Fetching Bitcoin price from CoinGecko...")
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        response = requests.get(url)
        response.raise_for_status()

        # Extract and print BTC price
        data = response.json()
        btc_price = data['bitcoin']['usd']
        print(f"Fetched BTC Price: ${btc_price:,.2f} USD")

        # Prepare payload
        payload = {
            'price': btc_price,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        print("Payload:", json.dumps(payload, indent=4))

        # Store BTC price in Supabase
        try:
            print("Attempting to insert data into Supabase...")
            result = supabase.table('btc_price').insert(payload).execute()
            print("Supabase Insert Response:", result)
        except Exception as e:
            print(f"Supabase Insert Error: {type(e).__name__} - {str(e)}")

        print(f"Final Bitcoin price: ${btc_price:,.2f} USD")
        return btc_price

    except Exception as e:
        print(f"Error: {type(e).__name__} - {str(e)}")
        return None

if __name__ == "__main__":
    get_btc_price()
