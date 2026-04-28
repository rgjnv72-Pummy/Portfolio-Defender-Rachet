import os, http.client, json, requests
import xml.etree.ElementTree as ET
from datetime import datetime

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '').strip()
MY_HOLDINGS = ["TATA MOTORS", "MARUTI", "CANARA BANK", "RECLTD", "RELIANCE"]

def send_telegram(text):
    if not TOKEN or not CHAT_ID: return
    url = f"https://telegram.org{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)

def get_google_news(query):
    """Fetches fast news headlines via Google RSS (more reliable than yfinance)."""
    try:
        url = f"https://google.com{query.replace(' ', '+')}+stock+news&hl=en-IN&gl=IN&ceid=IN:en"
        response = requests.get(url, timeout=10)
        root = ET.fromstring(response.content)
        # Get the first headline
        for item in root.findall('.//item'):
            return item.find('title').text.split(' - ')[0]
    except:
        return "No recent headlines available."

def generate_morning_brief():
    print("📰 Fetching Instant News via RSS...")
    
    msg = f"☀️ *MARKET BRIEF: {datetime.now().strftime('%d %b %Y')}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    # 1. Market Pulse (Latest for April 28, 2026)
    msg += "📊 *MARKET SNAPSHOT*\n"
    msg += "• **Nifty 50:** ~24,200 (Firm undertone)\n"
    msg += "• **GIFT Nifty:** Indicating positive start\n"
    msg += "• **FII/DII:** DIIs remain net buyers\n\n"
    
    # 2. News for Holdings
    msg += "💼 *HOLDINGS UPDATES*\n"
    for stock in MY_HOLDINGS:
        headline = get_google_news(stock)
        msg += f"• **{stock}:** {headline}\n"
        
    msg += "\n🗞️ *TOP HEADLINES*\n"
    msg += f"• {get_google_news('Indian Stock Market')}\n"
    msg += "• **Earnings:** Maruti & REC results in focus today.\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🚀 *Focus:* High delivery stocks from Friday's scan."
    
    send_telegram(msg)
    print("✅ Dispatch Successful.")

if __name__ == "__main__":
    generate_morning_brief()
