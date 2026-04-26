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
        requests.post(url, json=payload, timeout=15)
    except: pass

def get_google_news(ticker):
    """Reliable headline fetcher using string markers"""
    news_items = []
    try:
        name = ticker.replace('.NS', '')
        url = f"https://google.com{name}+share+price&hl=en-IN&gl=IN&ceid=IN:en"
        response = requests.get(url, timeout=10)
        text = response.text
        
        # Look for the first 3 items manually
        items = text.split('<item>')
        for i in range(1, min(len(items), 4)):
            # Grab Title
            t_start = items[i].find('<title>') + 7
            t_end = items[i].find('</title>')
            title = items[i][t_start:t_end].split(' - ')[0] # Remove source name
            
            # Grab Link
            l_start = items[i].find('<link>') + 6
            l_end = items[i].find('</link>')
            link = items[i][l_start:l_end]
            
            if title and link:
                news_items.append({'title': title, 'link': link})
    except: pass
    return news_items

def deliver_news():
    # 1. MARKET SUMMARY SECTION
    try:
        nifty = yf.Ticker("^NSEI")
        n_history = nifty.history(period="2d")
        n_close = n_history['Close'].iloc[-1]
        n_prev = n_history['Close'].iloc[-2]
        n_chg = ((n_close - n_prev) / n_prev) * 100
        n_icon = "📈" if n_chg > 0 else "📉"
        
        report = f"🏛️ *MARKET SUMMARY*\nNifty 50: {n_close:,.2f} ({n_chg:+.2f}%) {n_icon}\n"
    except:
        report = "🏛️ *MARKET SUMMARY*\nNifty data temporarily unavailable.\n"

    report += f"📅 _{datetime.now().strftime('%d %b %Y, %I:%M %p')}_\n"
    report += "—" * 15 + "\n\n🗞️ *HOLDINGS NEWS*\n"
    
    stocks_found = 0
    for ticker in MY_HOLDINGS:
        name = ticker.replace('.NS', '')
        news = get_google_news(ticker)
        
        if news:
            stocks_found += 1
            report += f"\n🔹 *{name}*\n"
            for i, item in enumerate(news, 1):
                report += f"{i}. [{item['title']}]({item['link']})\n"
        
        # Prevent message from getting too long for Telegram
        if len(report) > 3500:
            send_to_telegram(report)
            report = "🗞️ *CONTINUED...*\n"

    if stocks_found == 0:
        report += "\nNo specific headlines found for your holdings in the last 24h."

    send_to_telegram(report)

if __name__ == "__main__":
    deliver_news()
