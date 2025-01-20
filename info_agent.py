import os
import requests
from datetime import datetime, timezone
from supabase import create_client, Client
import json
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv(override=True)

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables.")

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase.debug = False

def search_brave(query: str) -> dict:
    """
    Search using Brave Search API
    """
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": os.getenv('BRAVE_API_KEY')
    }
    
    url = f"https://api.search.brave.com/res/v1/web/search?q={query}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Brave Search API error: {response.status_code} - {response.text}")

def store_news_in_db(news_item: str):
    """
    Store a news item in Supabase
    """
    data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'finance_info': news_item
    }
    
    try:
        response = supabase.table('eco_info').insert(data).execute()
        print("News item successfully stored in Supabase.")
        return response
    except Exception as e:
        raise Exception(f"Supabase Insert Error: {str(e)}")

def get_finance_news():
    """
    Main function to get finance news using OpenAI function calling
    """
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

    # First message to get macro economic news
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

    try:
        # Get macro economic news
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            tools=tools
        )

        if completion.choices[0].message.tool_calls:
            tool_call = completion.choices[0].message.tool_calls[0]
            search_args = json.loads(tool_call.function.arguments)
            search_results = search_brave(search_args["query"])

            # Store the first relevant news item
            if search_results.get('web', {}).get('results'):
                news_item = search_results['web']['results'][0]['description']
                store_news_in_db(news_item)

        # Now search for Bitcoin news
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
            search_results = search_brave(search_args["query"])

            # Store the first relevant news item
            if search_results.get('web', {}).get('results'):
                news_item = search_results['web']['results'][0]['description']
                store_news_in_db(news_item)

    except Exception as e:
        print(f"Error occurred: {str(e)}")

def test_openai():
    try:
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "Hello, how are you?"
            }
        ]
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        print(completion.choices[0].message.content)
    except Exception as e:
        print(f"OpenAI Test Error: {str(e)}")

def test_brave_search():
    try:
        query = "latest macro economic news"
        results = search_brave(query)
        print(json.dumps(results, indent=4))
    except Exception as e:
        print(f"Brave Search Test Error: {str(e)}")

def test_supabase_insert():
    try:
        store_news_in_db("Test finance news item.")
        print("Supabase Insert Test Passed.")
    except Exception as e:
        print(f"Supabase Insert Test Error: {str(e)}")

if __name__ == "__main__":
    get_finance_news()
    # test_openai()
    # test_brave_search()
    # test_supabase_insert()
