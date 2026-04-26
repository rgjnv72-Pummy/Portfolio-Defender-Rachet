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
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    # We use HTML mode now as it is much more stable than Markdown for news links
    payload = {
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "HTML", 
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        print(f"Status: {r.status_code}, Response: {r.text}")
    except Exception as e:
        print(f"Connection Error: {e}")

def get_google_news(ticker):
    news_items = []
    try:
        name = ticker.replace('.NS', '')
        url = f"https://google.com{name}+share+price&hl=en-IN&gl=IN&ceid=IN:en"
        response = requests.get(url, timeout=10)
        items = response.text.split('<item>')
        for i in range(1, min(len(items), 4)):
            t_start = items[i].find('<title>') + 7
            t_end = items[i].find('</title>')
            title = items[i][t_start:t_end].split(' - ')[0] # Title only
            
            l_start = items[i].find('<link>') + 6
            l_end = items[i].find('</link>')
            link = items[i][l_start:l_end]
            
            if title and link:
                # Clean HTML special characters
                title = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                news_items.append({'title': title, 'link': link})
    except: pass
    return news_items

def deliver_news():
    # 1. MARKET SUMMARY (Always included so the bot always pings you)
    try:
        nifty = yf.Ticker("^NSEI")
        n_close = nifty.history(period="2d")['Close']
        n_chg = ((n_close.iloc[-1] - n_close.iloc[-2]) / n_close.iloc[-2]) * 100
        icon = "🟢" if n_chg > 0 else "🔴"
        report = f"🏛 <b>MARKET SUMMARY</b>\nNifty 50: {n_close.iloc[-1]:,.2f} ({n_chg:+.2f}%) {icon}\n"
    except:
        report = "🏛 <b>MARKET SUMMARY</b>\n(Nifty data unavailable)\n"

    report += f"📅 <i>{datetime.now().strftime('%d %b, %I:%M %p')}</i>\n"
    report += "—" * 10 + "\n\n"
    
    found_news = 0
    for ticker in MY_HOLDINGS:
        name = ticker.replace('.NS', '')
        news = get_google_news(ticker)
        
        if news:
            found_news += 1
            report += f"🔹 <b>{name}</b>\n"
            for i, item in enumerate(news, 1):
                report += f"{i}. <a href='{item['link']}'>{item['title']}</a>\n"
            report += "\n"
        
        if len(report) > 3800:
            send_to_telegram(report)
            report = "<b>...CONTINUED</b>\n"

    if found_news == 0:
        report += "☕ No specific headlines found for your holdings today."

    send_to_telegram(report)

if __name__ == "__main__":
    deliver_news()
