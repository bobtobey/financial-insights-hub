import os
import requests
from datetime import datetime, timezone
from supabase import create_client, Client
import json
from dotenv import load_dotenv
import openai
from requests.auth import HTTPBasicAuth
from typing import Any

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

class FinancialEmailAgent:
    def __init__(self):
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # Use the global Supabase client
        self.supabase = supabase

        # Mailgun configuration
        self.MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
        self.MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')
        self.MAILGUN_API_URL = f"https://api.mailgun.net/v3/{self.MAILGUN_DOMAIN}/messages"
        self.MAILGUN_FROM_EMAIL = os.getenv('MAILGUN_FROM_EMAIL')
        self.RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL', '').split(',')
    
    def get_latest_data(self) -> dict[str, Any]:
        # Fetch the latest entries from eco_info and bc_prices tables in Supabase
        try:
            # Fetch the latest entries (last 10)
            news_response = self.supabase.table('eco_info') \
                .select('*') \
                .order('timestamp', desc=True) \
                .limit(10) \
                .execute()

            # Fetch the latest BTC price (last 5)
            prices_response = self.supabase.table('btc_price') \
                .select('*') \
                .order('timestamp', desc=True) \
                .limit(5) \
                .execute()

            # Add these debug prints
            print(f"News data:", news_response.data)
            print(f"Price data:", prices_response.data)

            return {
                'news': news_response.data,
                'prices': prices_response.data
            }
        except Exception as e:
            print(f"Error fetching data: {e}")
            return {'news': [], 'prices': []}
    
    def generate_email_content(self, data: dict[str, Any]) -> str:
        # Generate email content using OpenAI
        try:
            # Format the data for the prompt
            news_items = []
            for item in data['news']:
                try:
                    # Handle cases where finance_info might already be a dict
                    if isinstance(item['finance_info'], str):
                        news_items.append(item['finance_info'])
                    else:
                        news_items.append(item['finance_info'])
                except (json.JSONDecodeError, KeyError):
                    continue

            prices_data = [{'price': item['price'], 'timestamp': item['timestamp']} for item in data['prices']]
            
            # Create the prompt
            prompt = f"""You are a professional financial and crypto analyst, with 20 years of experience. Generate a very concise financial email with analysis of the following data: 
            
            1. Latest Bitcoin price: {json.dumps(prices_data)}
            2. Latest financial news: {json.dumps(news_items)}

            Requirements:
            - Start the email with "Subject: Financial Update - BTC and Market Analysis"
            - Put the subject on its own line at the start of the email
            - After the subject line, greet the recipient
            - Keep the email concise and to the point, and should not be longer than 300 words
            - Focus on the most significant news, insights, and trends
            - Be professional and concise and factual
            - End with 'Best regards, Financial AI Agent'
            
            Format your response exactly like this:
            Subject: Financial Update - BTC and Market Analysis
            
            Dear Valued Investor,
            
            [Email content here]
            
            Best regards,
            Financial AI Agent
            """
            
            completion = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional financial and crypto analyst, with 20 years of experience."},
                    {"role": "user", "content": prompt}
                ]
            )

            return completion.choices[0].message.content
        
        except Exception as e:
            print(f"Error generating email content: {e}")
            return ""
        
    def send_email(self, content: str) -> bool:
        try:
            lines = content.split('\n')
            # Set default subject
            subject = 'Financial Update'  # Default subject
            
            # Try to find a subject line in the content
            for line in lines:
                if line.lower().startswith('subject:'):
                    subject = line.replace('Subject:', '').strip()
                    # Remove this line from the content
                    lines.remove(line)
                    break

            # Join remaining lines for email body
            email_body = '\n'.join(lines)

            # Add debug prints
            print(f"Sending email with:")
            print(f"Subject: {subject}")
            print(f"From: {self.MAILGUN_FROM_EMAIL}")
            print(f"To: {', '.join(self.RECIPIENT_EMAIL)}")
            print(f"URL: {self.MAILGUN_API_URL}")
            
            response = requests.post(
                self.MAILGUN_API_URL,
                auth=HTTPBasicAuth("api", self.MAILGUN_API_KEY),
                data={
                    "from": self.MAILGUN_FROM_EMAIL,
                    "to": self.RECIPIENT_EMAIL,  # Mailgun accepts a list of recipients
                    "subject": subject,
                    "text": email_body
                }
            )

            if response.status_code == 200:
                print("Email sent successfully")
                return True
            else:
                print(f"Failed to send email. Status code: {response.status_code}")
                print(f"Response text: {response.text}")
                return False
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
        
    def send_to_mailing_list(self, content: str) -> bool:
        try:
            lines = content.split('\n')
            # Set default subject
            subject = 'Financial Update'  # Default subject
            
            # Try to find a subject line in the content
            for line in lines:
                if line.lower().startswith('subject:'):
                    subject = line.replace('Subject:', '').strip()
                    # Remove this line from the content
                    lines.remove(line)
                    break

            # Join remaining lines for email body
            email_body = '\n'.join(lines)

            # Add debug prints
            print(f"Sending email with:")
            print(f"Subject: {subject}")
            print(f"From: {self.MAILGUN_FROM_EMAIL}")
            print(f"To: {', '.join(self.RECIPIENT_EMAIL)}")
            print(f"URL: {self.MAILGUN_API_URL}")
            
            response = requests.post(
                self.MAILGUN_API_URL,
                auth=HTTPBasicAuth("api", self.MAILGUN_API_KEY),
                data={
                    "from": self.MAILGUN_FROM_EMAIL,
                    "to": "mylist@" + self.MAILGUN_DOMAIN,  # Your mailing list address
                    "subject": subject,
                    "text": email_body
                }
            )

            if response.status_code == 200:
                print("Email sent successfully to mailing list")
                return True
            else:
                print(f"Failed to send email to mailing list. Status code: {response.status_code}")
                print(f"Response text: {response.text}")
                return False
            
        except Exception as e:
            print(f"Error sending email to mailing list: {e}")
            return False
        
    def run(self) -> None:
        # Main function to run the agent
        try:
            # Get the latest data
            data = self.get_latest_data()

            if not data['news'] or not data['prices']:
                print("No data available to generate email.")
                return
            
            # Generate email content
            email_content = self.generate_email_content(data)
            if not email_content:
                print("Failed to generate email content.")
                return
            
            # Send the email
            if not self.send_email(email_content):
                print("Failed to send email.")
                return
            
            print("Email sent successfully.")

        except Exception as e:
            print(f"Error running the email agent: {e}")

if __name__ == "__main__":
    agent = FinancialEmailAgent()
    agent.run()
