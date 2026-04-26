import yfinance as yf
import requests
import os
import xml.etree.ElementTree as ET
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
    requests.post(url, json=payload)

def get_google_news(ticker):
    """Backup: Fetches top 3 headlines from Google News RSS"""
    news_items = []
    try:
        search_query = ticker.replace('.NS', '')
        url = f"https://google.com{search_query}+stock+news&hl=en-IN&gl=IN&ceid=IN:en"
        response = requests.get(url)
        root = ET.fromstring(response.content)
        for item in root.findall('.//item')[:3]:
            news_items.append({
                'title': item.find('title').text,
                'link': item.find('link').text
            })
    except: pass
    return news_items

def deliver_news():
    header = f"🗞️ *TOP 3 HEADLINES*\n_{datetime.now().strftime('%d %b %Y')}_\n"
    header += "—" * 15 + "\n"
    current_message = header
    
    for ticker in MY_HOLDINGS:
        name = ticker.replace('.NS', '')
        # Try Yahoo first
        try:
            stock = yf.Ticker(ticker)
            news_list = getattr(stock, 'news', [])[:3]
        except: news_list = []

        # If Yahoo is empty, use Google News
        if not news_list:
            news_list = get_google_news(ticker)
            
        if news_list:
            ticker_block = f"\n🔹 *{name}*\n"
            for i, article in enumerate(news_list, 1):
                title = article.get('title', 'No Title').split(' - ')[0] # Clean Google News titles
                link = article.get('link', '#')
                ticker_block += f"{i}. [{title}]({link})\n"
            
            if len(current_message) + len(ticker_block) > 4000:
                send_to_telegram(current_message)
                current_message = ticker_block
            else:
                current_message += ticker_block

    if current_message != header:
        send_to_telegram(current_message)
    else:
        send_to_telegram("🚫 No news headlines found today for your holdings.")

if __name__ == "__main__":
    deliver_news()
