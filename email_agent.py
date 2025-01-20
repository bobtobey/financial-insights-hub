import os
import requests
from datetime import datetime, timezone
from supabase import create_client
import json
from dotenv import load_dotenv
import openai
from typing import Dict, Any
from requests.auth import HTTPBasicAuth

# Load environment variables from .env file
load_dotenv(override=True)

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables.")

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase credentials not found in environment variables")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase.debug = False

# Mailgun Configuration
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')
MAILGUN_FROM_EMAIL = os.getenv('MAILGUN_FROM_EMAIL')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL', '').split(',')  # Match the variable name from .env but keep split for future

# Only check if the keys exist, not if they're empty strings
if None in [MAILGUN_API_KEY, MAILGUN_DOMAIN, MAILGUN_FROM_EMAIL]:
    raise ValueError("Missing required Mailgun configuration. Please check your .env file.")

print(f"Loaded RECIPIENT_EMAIL: {RECIPIENT_EMAIL}")  # Debug print

MAILGUN_API_URL = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"

def fetch_latest_data() -> Dict[str, Any]:
    """Fetch the latest entries from eco_info and btc_price tables"""
    try:
        # Fetch latest eco_info entries (last 10)
        eco_info = supabase.table('eco_info') \
            .select('*') \
            .order('timestamp', desc=True) \
            .limit(10) \
            .execute()

        # Fetch latest btc_price entries (last 5)
        btc_prices = supabase.table('btc_price') \
            .select('*') \
            .order('timestamp', desc=True) \
            .limit(5) \
            .execute()

        return {
            'news': eco_info.data,
            'prices': btc_prices.data
        }
    except Exception as e:
        print(f"Error fetching data from Supabase: {str(e)}")
        return {'news': [], 'prices': []}

def generate_analysis(data: Dict[str, Any]) -> str:
    """Generate analysis using OpenAI based on the provided data"""
    try:
        news_items = []
        for item in data['news']:
            try:
                if isinstance(item['finance_info'], str):
                    news_items.append(item['finance_info'])
                else:
                    news_items.append(json.dumps(item['finance_info']))
            except (KeyError, json.JSONDecodeError):
                continue

        prices_data = [{'price': item['price'], 'timestamp': item['timestamp']} 
                      for item in data['prices']]

        prompt = f"""As a professional financial analyst with expertise in cryptocurrency, 
        provide a very concise analysis of the following data:

        Recent Bitcoin Prices: {json.dumps(prices_data)}
        Recent Financial News: {json.dumps(news_items)}

        Requirements:
        - Start with 'Subject: Financial Market Update'
        - Keep analysis under 200 words
        - Focus on key insights and correlations
        - Be professional and factual
        - Highlight most significant trends
        """

        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional financial and crypto analyst."},
                {"role": "user", "content": prompt}
            ]
        )

        return completion.choices[0].message.content

    except Exception as e:
        print(f"Error generating analysis: {str(e)}")
        return ""

def send_email(content: str) -> bool:
    """Send email using Mailgun API"""
    try:
        lines = content.split('\n')
        subject = 'Financial Market Update'  # Default subject
        
        # Try to find a subject line in the content
        for line in lines:
            if line.lower().startswith('subject:'):
                subject = line.replace('Subject:', '').strip()
                lines.remove(line)
                break

        # Join remaining lines for email body
        email_body = '\n'.join(lines)

        # Debug prints
        print("\nMailgun Configuration:")
        print(f"API URL: {MAILGUN_API_URL}")
        print(f"From: {MAILGUN_FROM_EMAIL}")
        print(f"To: {RECIPIENT_EMAIL}")
        
        response = requests.post(
            MAILGUN_API_URL,
            auth=HTTPBasicAuth("api", MAILGUN_API_KEY),
            data={
                "from": f"Financial AI Agent <{MAILGUN_FROM_EMAIL}>",
                "to": RECIPIENT_EMAIL,
                "subject": subject,
                "text": email_body
            }
        )
        
        print(f"\nMailgun Response:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("Email sent successfully!")
            return True
        else:
            print(f"Failed to send email. Status: {response.status_code}")
            print(f"Error message: {response.text}")
            return False

    except Exception as e:
        print(f"Exception while sending email: {str(e)}")
        return False

def get_finance_email_analysis() -> None:
    """Main function to generate and send finance analysis email"""
    try:
        # Get latest data
        print("Fetching latest data...")
        data = fetch_latest_data()
        if not data['news'] or not data['prices']:
            print("No data available to analyze")
            return

        # Generate analysis
        print("Generating analysis...")
        analysis = generate_analysis(data)
        if not analysis:
            print("Failed to generate analysis")
            return

        # Send email
        print("Sending email...")
        if not send_email(analysis):
            print("Failed to send email")
            return

        print("Financial analysis email process completed successfully")

    except Exception as e:
        print(f"Error in finance email analysis process: {str(e)}")

def test_supabase():
    """Test Supabase connection"""
    try:
        response = supabase.table('eco_info').select('*').limit(1).execute()
        print("Supabase connection test successful")
        return True
    except Exception as e:
        print(f"Supabase test error: {str(e)}")
        return False

def test_openai():
    """Test OpenAI connection"""
    try:
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}]
        )
        print("OpenAI connection test successful")
        return True
    except Exception as e:
        print(f"OpenAI test error: {str(e)}")
        return False

def test_mailgun():
    """Test Mailgun connection"""
    try:
        test_content = "Subject: Test Email\n\nThis is a test email from the Financial AI Agent."
        return send_email(test_content)
    except Exception as e:
        print(f"Mailgun test error: {str(e)}")
        return False

if __name__ == "__main__":
    get_finance_email_analysis()
    # Uncomment to test Mailgun configuration:
    # test_mailgun()
