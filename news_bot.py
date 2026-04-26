import yfinance as yf
import requests
import os
from datetime import datetime

# --- AUTH ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- YOUR HOLDINGS ---
MY_HOLDINGS = [
    "ABB.NS", "CHENNPETRO.NS", "GPIL.NS", "TATAPOWER.NS", 
    "ONGC.NS", "LLOYDSME.NS", "ADANIPOWER.NS", "PREMIERENE.NS", 
    "NATCOPHARM.NS", "ASHOKLEY.NS", "AUROPHARMA.NS", "SAMMAANCAP.NS"
]

def send_to_telegram(text):
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": True 
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Telegram Error: {e}")

def deliver_news():
    header = f"🗞️ *TOP 3 HEADLINES*\n_{datetime.now().strftime('%d %b %Y')}_\n"
    header += "—" * 15 + "\n"
    
    current_message = header
    found_any_news = False
    
    for ticker in MY_HOLDINGS:
        try:
            stock = yf.Ticker(ticker)
            # Safely fetch news; if it fails or is empty, news_list becomes []
            news_list = getattr(stock, 'news', [])[:3]
            
            if news_list:
                found_any_news = True
                name = ticker.replace('.NS', '')
                ticker_block = f"\n🔹 *{name}*\n"
                
                for i, article in enumerate(news_list, 1):
                    title = article.get('title', 'No Title')
                    link = article.get('link', '#')
                    ticker_block += f"{i}. [{title}]({link})\n"
                
                # Check for Telegram's character limit
                if len(current_message) + len(ticker_block) > 4000:
                    send_to_telegram(current_message)
                    current_message = ticker_block
                else:
                    current_message += ticker_block
        except Exception as e:
            print(f"Skipping {ticker} due to error: {e}")
            continue

    if not found_any_news:
        current_message += "\nNo significant news found for your holdings today."

    send_to_telegram(current_message)

if __name__ == "__main__":
    deliver_news()
