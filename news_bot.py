import yfinance as yf
import requests
import os
import re
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
        requests.post(url, json=payload, timeout=10)
    except: pass

def get_fallback_news(ticker):
    """Simple text-based backup to avoid XML crashes"""
    news_items = []
    try:
        query = ticker.replace('.NS', '')
        url = f"https://google.com{query}+stock+news&hl=en-IN&gl=IN&ceid=IN:en"
        response = requests.get(url, timeout=10)
        # Use Regex to find titles and links (more stable than XML parsing)
        titles = re.findall(r'<title>(.*?)</title>', response.text)[1:4] # Skip feed title
        links = re.findall(r'<link>(.*?)</link>', response.text)[1:4]
        for t, l in zip(titles, links):
            news_items.append({'title': t, 'link': l})
    except: pass
    return news_items

def deliver_news():
    header = f"🗞️ *TOP 3 HEADLINES*\n_{datetime.now().strftime('%d %b %Y')}_\n"
    header += "—" * 15 + "\n"
    current_message = header
    found_any = False
    
    for ticker in MY_HOLDINGS:
        name = ticker.replace('.NS', '')
        news_list = []
        
        # 1. Try Yahoo Finance
        try:
            stock = yf.Ticker(ticker)
            news_list = stock.news[:3]
        except: pass

        # 2. Try Fallback if Yahoo is empty
        if not news_list:
            news_list = get_fallback_news(ticker)
            
        if news_list:
            found_any = True
            ticker_block = f"\n🔹 *{name}*\n"
            for i, article in enumerate(news_list, 1):
                title = article.get('title', 'No Title').replace('[', '').replace(']', '') # Clean Markdown
                link = article.get('link', '#')
                ticker_block += f"{i}. [{title}]({link})\n"
            
            # Send and reset if message gets too long
            if len(current_message) + len(ticker_block) > 4000:
                send_to_telegram(current_message)
                current_message = ticker_block
            else:
                current_message += ticker_block

    if not found_any:
        send_to_telegram(header + "\nNo major news found for your holdings today.")
    elif current_message != header:
        send_to_telegram(current_message)

if __name__ == "__main__":
    deliver_news()
