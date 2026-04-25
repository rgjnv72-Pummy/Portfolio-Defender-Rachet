import yfinance as yf
import requests
import os
from datetime import datetime

# --- AUTH ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- YOUR HOLDINGS ---
MY_HOLDINGS = {
    "CHENNPETRO.NS": [200, 910.00, "2026-03-12", "Energy"],
    "ABB.NS": [30, 6320.00, "2026-03-18", "Capital Goods"],
    "GPIL.NS": [760, 262.98, "2026-03-23", "Metals"],
    "TATAPOWER.NS": [500, 403.00, "2026-03-23", "Energy"],
    "ONGC.NS": [700, 287.20, "2026-04-02", "Energy"],
    "LLOYDSME.NS": [109, 1446.56, "2026-04-07", "Metals"],
    "ADANIPOWER.NS": [1000, 163.36, "2026-04-07", "Energy"],
    "PREMIERENE.NS": [150, 943.30, "2026-04-07", "Infrastructure"],
    "NATCOPHARM.NS": [150, 1066.00, "2026-04-07", "Pharma"],
    "ASHOKLEY.NS": [1400, 173.00, "2026-04-09", "Auto"],
    "AUROPHARMA.NS": [70, 1350.00, "2026-04-10", "Pharma"],
    "SAMMAANCAP.NS": [922, 154.89, "2026-04-13", "Finance"]
}

def send_to_telegram(text):
    url = f"https://telegram.org{TOKEN}/sendMessage"
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
    
    for ticker in MY_HOLDINGS.keys():
        try:
            stock = yf.Ticker(ticker)
            news_list = stock.news[:3]
            
            if news_list:
                name = ticker.replace('.NS', '')
                ticker_block = f"\n🔹 *{name}*\n"
                for i, article in enumerate(news_list, 1):
                    title = article.get('title')
                    link = article.get('link')
                    ticker_block += f"{i}. [{title}]({link})\n"
                
                # Check for Telegram's 4096 char limit
                if len(current_message) + len(ticker_block) > 4000:
                    send_to_telegram(current_message)
                    current_message = ticker_block
                else:
                    current_message += ticker_block
        except: continue

    if current_message != header:
        send_to_telegram(current_message)

if __name__ == "__main__":
    deliver_news()
  
