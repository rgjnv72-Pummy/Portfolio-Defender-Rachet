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
    if not TOKEN or not CHAT_ID:
        print("Error: Missing Telegram Credentials")
        return
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": True 
    }
    # Using a common browser User-Agent to avoid being blocked
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    requests.post(url, json=payload, headers=headers)

def deliver_news():
    header = f"🗞️ *TOP 3 HEADLINES*\n_{datetime.now().strftime('%d %b %Y')}_\n"
    header += "—" * 15 + "\n"
    
    current_message = header
    found_any = False

    for ticker in MY_HOLDINGS.keys():
        try:
            # Creating a session to handle cookies/crumb automatically
            stock = yf.Ticker(ticker)
            news_list = stock.news[:3]
            
            if news_list:
                found_any = True
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
            print(f"Skipping {ticker}: {e}")
            continue

    if found_any and current_message != header:
        send_to_telegram(current_message)
    elif not found_any:
        send_to_telegram("No new headlines found for your holdings today.")

if __name__ == "__main__":
    deliver_news()
