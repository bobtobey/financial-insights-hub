import os
import requests
from datetime import datetime, timezone
from supabase import create_client
import json
from dotenv import load_dotenv
import openai

class InfoAgent:
    def __init__(self):
        # Load environment variables
        load_dotenv(override=True)
        
        # Initialize OpenAI
        self.openai_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")
        openai.api_key = self.openai_key
        
        # Initialize Supabase
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.supabase.debug = False
        
        # Initialize Brave API
        self.brave_key = os.getenv('BRAVE_API_KEY')
        if not self.brave_key:
            raise ValueError("BRAVE_API_KEY is not set in environment variables")

    def search_brave(self, query: str) -> dict:
        """Search using Brave Search API"""
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.brave_key
        }
        
        url = f"https://api.search.brave.com/res/v1/web/search?q={query}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Brave Search API error: {response.status_code} - {response.text}")

    def store_news_in_db(self, news_item: str):
        """Store a news item in Supabase"""
        data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'finance_info': news_item
        }
        
        try:
            response = self.supabase.table('eco_info').insert(data).execute()
            print("News item successfully stored in Supabase.")
            return response
        except Exception as e:
            raise Exception(f"Supabase Insert Error: {str(e)}")

    def get_finance_news(self):
        """Main method to get finance news using OpenAI function calling"""
        tools = [{
            "type": "function",
            "function": {
                "name": "search_brave",
                "description": "Search for latest finance news using Brave Search API",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query for finance news"
                        }
                    },
                    "required": ["query"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }]

        try:
            # Get macro economic news
            messages = [
                {
                    "role": "system",
                    "content": "You are a financial news researcher. Search for the latest important macro economic news."
                },
                {
                    "role": "user",
                    "content": "Find the latest important macro economic news."
                }
            ]
            
            completion = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                tools=tools
            )

            if completion.choices[0].message.tool_calls:
                tool_call = completion.choices[0].message.tool_calls[0]
                search_args = json.loads(tool_call.function.arguments)
                search_results = self.search_brave(search_args["query"])

                if search_results.get('web', {}).get('results'):
                    news_item = search_results['web']['results'][0]['description']
                    self.store_news_in_db(news_item)

            # Get Bitcoin news
            messages = [
                {
                    "role": "developer",
                    "content": "You are a cryptocurrency news researcher. Search for the latest important Bitcoin news."
                },
                {
                    "role": "user",
                    "content": "Find the latest important Bitcoin news."
                }
            ]

            completion = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                tools=tools
            )

            if completion.choices[0].message.tool_calls:
                tool_call = completion.choices[0].message.tool_calls[0]
                search_args = json.loads(tool_call.function.arguments)
                search_results = self.search_brave(search_args["query"])

                if search_results.get('web', {}).get('results'):
                    news_item = search_results['web']['results'][0]['description']
                    self.store_news_in_db(news_item)

        except Exception as e:
            print(f"Error occurred: {str(e)}")

    def test_openai(self):
        """Test OpenAI connection"""
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, how are you?"}
            ]
            completion = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            print(completion.choices[0].message.content)
            return True
        except Exception as e:
            print(f"OpenAI Test Error: {str(e)}")
            return False

    def test_brave_search(self):
        """Test Brave Search API"""
        try:
            query = "latest macro economic news"
            results = self.search_brave(query)
            print(json.dumps(results, indent=4))
            return True
        except Exception as e:
            print(f"Brave Search Test Error: {str(e)}")
            return False

    def test_supabase_insert(self):
        """Test Supabase connection"""
        try:
            self.store_news_in_db("Test finance news item.")
            print("Supabase Insert Test Passed.")
            return True
        except Exception as e:
            print(f"Supabase Insert Test Error: {str(e)}")
            return False

def main():
    agent = InfoAgent()
    agent.get_finance_news()
    # agent.test_openai()
    # agent.test_brave_search()
    # agent.test_supabase_insert()

if __name__ == "__main__":
    main()
