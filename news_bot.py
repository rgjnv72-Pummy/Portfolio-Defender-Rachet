import yfinance as yf
import requests
import os
from datetime import datetime

# --- AUTH ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

MY_HOLDINGS = [
    "ABB.NS", "CHENNPETRO.NS", "GPIL.NS", "TATAPOWER.NS", 
    "ONGC.NS", "LLOYDSME.NS", "ADANIPOWER.NS", "PREMIERENE.NS", 
    "NATCOPHARM.NS", "ASHOKLEY.NS", "AUROPHARMA.NS", "SAMMAANCAP.NS"
]

def send_to_telegram(text):
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"Telegram response: {r.status_code}")
    except Exception as e:
        print(f"Telegram failed: {e}")

def get_google_news(ticker):
    """Robust backup using simple string splitting"""
    news_items = []
    try:
        query = ticker.replace('.NS', '')
        # Different Google News RSS URL
        url = f"https://google.com{query}+share+price&hl=en-IN&gl=IN&ceid=IN:en"
        response = requests.get(url, timeout=15)
        
        # Split by <item> tags to get individual stories
        parts = response.text.split('<item>')[1:4] 
        for part in parts:
            title = part.split('<title>')[1].split('</title>')[0]
            link = part.split('<link>')[1].split('</link>')[0]
            # Clean up the title (Google adds " - Source" at the end)
            clean_title = title.split(' - ')[0].replace('[', '').replace(']', '')
            news_items.append({'title': clean_title, 'link': link})
    except: pass
    return news_items

def deliver_news():
    header = f"🗞️ *HOLDINGS NEWS UPDATE*\n_{datetime.now().strftime('%d %b %Y, %I:%M %p')}_\n"
    header += "—" * 15 + "\n"
    
    current_message = header
    stocks_with_news = 0
    
    for ticker in MY_HOLDINGS:
        name = ticker.replace('.NS', '')
        # Try Yahoo first
        try:
            stock = yf.Ticker(ticker)
            news_list = stock.news[:3]
        except: news_list = []

        # Use Google if Yahoo is empty
        if not news_list:
            news_list = get_google_news(ticker)
            
        if news_list:
            stocks_with_news += 1
            ticker_block = f"\n🔹 *{name}*\n"
            for i, article in enumerate(news_list, 1):
                title = article.get('title', 'Headline')
                link = article.get('link', '#')
                ticker_block += f"{i}. [{title}]({link})\n"
            
            if len(current_message) + len(ticker_block) > 4000:
                send_to_telegram(current_message)
                current_message = ticker_block
            else:
                current_message += ticker_block

    # FINAL CHECK: If no news found at all, tell the user!
    if stocks_with_news == 0:
        current_message += "\n☕ No new headlines found for your holdings in the last 24 hours."

    send_to_telegram(current_message)

if __name__ == "__main__":
    deliver_news()
