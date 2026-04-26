import yfinance as yf
import requests
import os
import sys
from datetime import datetime

# --- AUTH ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

MY_HOLDINGS = [
    "CHENNPETRO.NS", "ABB.NS", "GPIL.NS", "TATAPOWER.NS", 
    "ONGC.NS", "LLOYDSME.NS", "ADANIPOWER.NS", "PREMIERENE.NS", 
    "NATCOPHARM.NS", "ASHOKLEY.NS", "AUROPHARMA.NS", "SAMMAANCAP.NS"
]

def send_to_telegram(text):
    if not TOKEN or not CHAT_ID:
        print("❌ ERROR: TELEGRAM_TOKEN or TELEGRAM_CHAT_ID is missing in GitHub Secrets!")
        sys.exit(1)
    
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Telegram Failed: {e}")

def deliver_news():
    print(f"🚀 Starting news fetch for {len(MY_HOLDINGS)} tickers...")
    header = f"🗞️ *TOP 3 HEADLINES*\n_{datetime.now().strftime('%d %b %Y')}_\n"
    header += "—" * 15 + "\n"
    
    current_message = header
    found_any = False

    for ticker in MY_HOLDINGS:
        try:
            print(f"Checking {ticker}...")
            stock = yf.Ticker(ticker)
            news_list = stock.news
            
            if news_list:
                found_any = True
                name = ticker.replace('.NS', '')
                ticker_block = f"\n🔹 *{name}*\n"
                for i, article in enumerate(news_list[:3], 1):
                    ticker_block += f"{i}. [{article['title']}]({article['link']})\n"
                
                if len(current_message) + len(ticker_block) > 4000:
                    send_to_telegram(current_message)
                    current_message = ticker_block
                else:
                    current_message += ticker_block
        except Exception as e:
            print(f"⚠️ Warning: Could not get news for {ticker}: {e}")
            continue

    if found_any:
        send_to_telegram(current_message)
        print("✅ News delivered successfully!")
    else:
        print("ℹ️ No news found for any tickers today.")
        send_to_telegram("No new headlines found for your holdings today.")

if __name__ == "__main__":
    deliver_news()
