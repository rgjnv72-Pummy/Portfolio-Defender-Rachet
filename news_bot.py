import yfinance as yf
import requests
import os
from datetime import datetime
from guardian import MY_HOLDINGS  # 🚀 Auto-pick from guardian

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": True 
    }
    requests.post(url, json=payload)

def deliver_news():
    header = f"🗞️ *TOP 3 HEADLINES*\n_{datetime.now().strftime('%d %b %Y')}_\n"
    header += "—" * 15 + "\n"
    
    current_message = header
    found_any = False

    for ticker in MY_HOLDINGS.keys():
        try:
            stock = yf.Ticker(ticker)
            news_list = stock.news[:3]
            
            if news_list:
                found_any = True
                name = ticker.replace('.NS', '')
                ticker_block = f"\n🔹 *{name}*\n"
                for i, article in enumerate(news_list, 1):
                    ticker_block += f"{i}. [{article['title']}]({article['link']})\n"
                
                if len(current_message) + len(ticker_block) > 4000:
                    send_to_telegram(current_message)
                    current_message = ticker_block
                else:
                    current_message += ticker_block
        except: continue

    if not found_any:
        send_to_telegram(header + "\nNo major news found for your holdings today.")
    else:
        send_to_telegram(current_message)

if __name__ == "__main__":
    deliver_news()
