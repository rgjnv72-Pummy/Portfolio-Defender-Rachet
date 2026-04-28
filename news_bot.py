import os, requests, json
import xml.etree.ElementTree as ET
from datetime import datetime

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '').strip()
MY_HOLDINGS = ["TATA MOTORS", "MARUTI", "CANARA BANK", "RECLTD", "RELIANCE"]

def send_telegram(text):
    if not TOKEN or not CHAT_ID:
        print("❌ Secrets Missing")
        return
    
    # FIXED URL CONSTRUCTION
    url = f"https://telegram.org{TOKEN}/sendMessage"
    
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    
    try:
        r = requests.post(url, json=payload, timeout=15)
        print(f"📡 Telegram Status: {r.status_code}")
        if r.status_code != 200:
            print(f"❌ Error Detail: {r.text}")
    except Exception as e:
        print(f"❌ Post Failed: {e}")

def get_google_news(query):
    """Fetches headlines via Google RSS."""
    try:
        url = f"https://google.com{query.replace(' ', '+')}+stock+news&hl=en-IN&gl=IN&ceid=IN:en"
        response = requests.get(url, timeout=10)
        root = ET.fromstring(response.content)
        for item in root.findall('.//item'):
            full_title = item.find('title').text
            # Clean headline (removes source name after ' - ')
            return full_title.split(' - ')[0]
    except:
        return "No recent headlines available."

def generate_morning_brief():
    print("📰 Fetching News Brief...")
    
    msg = f"☀️ *MARKET BRIEF: {datetime.now().strftime('%d %b %Y')}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    # 1. Market Snapshot
    msg += "📊 *MARKET SNAPSHOT*\n"
    msg += "• **Nifty 50:** Trading near 24,200\n"
    msg += "• **Sentiment:** Positive global cues\n\n"
    
    # 2. News for Holdings
    msg += "💼 *HOLDINGS UPDATES*\n"
    for stock in MY_HOLDINGS:
        headline = get_google_news(stock)
        msg += f"• **{stock}:** {headline}\n"
        
    msg += "\n🗞️ *TOP HEADLINES*\n"
    market_news = get_google_news('Indian Stock Market')
    msg += f"• {market_news}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🚀 *Focus:* High Delivery + Momentum stocks."
    
    send_telegram(msg)
    print("✅ Dispatch Attempted.")

if __name__ == "__main__":
    generate_morning_brief()
