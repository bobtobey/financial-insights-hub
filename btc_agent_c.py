import requests
from supabase import create_client
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
import json

class BTCAgent:
    def __init__(self):
        # Load environment variables
        load_dotenv(override=True)
        
        # Initialize Supabase client
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not found in environment variables")
            
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.supabase.debug = False

    def test_supabase_connection(self):
        """Test the Supabase connection"""
        print("Testing basic Supabase connection...")
        try:
            response = self.supabase.table('btc_price').select('*').execute()
            return True
        except Exception as e:
            print(f"Error during Supabase SELECT test: {type(e).__name__} - {str(e)}")
            return False

    def fetch_btc_price(self):
        """Fetch Bitcoin price from CoinGecko"""
        print("Fetching Bitcoin price from CoinGecko...")
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            btc_price = data['bitcoin']['usd']
            print(f"Fetched BTC Price: ${btc_price:,.2f} USD")
            return btc_price
            
        except Exception as e:
            print(f"Error fetching BTC price: {type(e).__name__} - {str(e)}")
            return None

    def store_price(self, btc_price: float):
        """Store Bitcoin price in Supabase"""
        if btc_price is None:
            return False
            
        payload = {
            'price': btc_price,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        print("Payload:", json.dumps(payload, indent=4))
        
        try:
            print("Attempting to insert data into Supabase...")
            result = self.supabase.table('btc_price').insert(payload).execute()
            print("Supabase Insert Response:", result)
            return True
        except Exception as e:
            print(f"Supabase Insert Error: {type(e).__name__} - {str(e)}")
            return False

    def get_btc_price(self):
        """Main method to fetch and store Bitcoin price"""
        try:
            # Test Supabase connection
            if not self.test_supabase_connection():
                raise Exception("Failed to connect to Supabase")
                
            # Fetch BTC price
            btc_price = self.fetch_btc_price()
            if btc_price is None:
                raise Exception("Failed to fetch BTC price")
                
            # Store price in database
            if not self.store_price(btc_price):
                raise Exception("Failed to store BTC price")
                
            print(f"Final Bitcoin price: ${btc_price:,.2f} USD")
            return btc_price
            
        except Exception as e:
            print(f"Error in get_btc_price: {type(e).__name__} - {str(e)}")
            return None

def main():
    agent = BTCAgent()
    agent.get_btc_price()

if __name__ == "__main__":
    main()
