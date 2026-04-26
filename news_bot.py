import yfinance as yf
import requests
import os
from datetime import datetime

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- IMPROVED HEADERS FOR RELIABILITY ---
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def send_to_telegram(text):
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": True 
    }
    requests.post(url, json=payload, headers=HEADERS)

def deliver_news():
    header = f"🗞️ *TOP 3 HEADLINES*\n_{datetime.now().strftime('%d %b %Y')}_\n"
    header += "—" * 15 + "\n"
    
    current_message = header
    
    # Using your MY_HOLDINGS dictionary...
    for ticker in MY_HOLDINGS.keys():
        try:
            # Use sessions for more stable connections
            stock = yf.Ticker(ticker)
            news_list = stock.news[:3]
            
            if news_list:
                name = ticker.replace('.NS', '')
                ticker_block = f"\n🔹 *{name}*\n"
                for i, article in enumerate(news_list, 1):
                    title = article.get('title')
                    link = article.get('link')
                    ticker_block += f"{i}. [{title}]({link})\n"
                
                if len(current_message) + len(ticker_block) > 4000:
                    send_to_telegram(current_message)
                    current_message = ticker_block
                else:
                    current_message += ticker_block
        except Exception as e:
            print(f"Skipping {ticker} due to error: {e}")
            continue

    if current_message != header:
        send_to_telegram(current_message)

if __name__ == "__main__":
    deliver_news()
