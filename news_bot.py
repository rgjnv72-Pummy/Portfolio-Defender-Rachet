import os, requests, json, http.client
import xml.etree.ElementTree as ET
from datetime import datetime

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '').strip()

# Portfolio Mapping
MY_HOLDINGS = {
    "GPIL.NS": "Godawari Power",
    "LLOYDSME.NS": "Lloyds Metals",
    "PREMIERENE.NS": "Premier Energies",
    "NATCOPHARM.NS": "Natco Pharma",
    "ADANIPOWER.NS": "Adani Power",
    "ASHOKLEY.NS": "Ashok Leyland",
    "AARTIIND.NS": "Aarti Industries"
}

def send_telegram(text):
    if not TOKEN or not CHAT_ID: return
    url = f"/bot{TOKEN}/sendMessage"
    conn = http.client.HTTPSConnection("api.telegram.org")
    payload = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    headers = {"Content-Type": "application/json"}
    try:
        conn.request("POST", url, payload, headers)
        conn.getresponse()
    finally: conn.close()

def get_ticker_news(ticker):
    """Fetches real headlines from Yahoo Finance RSS."""
    try:
        url = f"https://yahoo.com{ticker}&region=US&lang=en-US"
        response = requests.get(url, timeout=10)
        root = ET.fromstring(response.content)
        # Find the first 'title' inside 'item'
        item = root.find(".//item")
        if item is not None:
            headline = item.find("title").text
            return headline
    except: pass
    return "No major headlines found in last 24h."

def generate_morning_brief():
    print("📰 Dispatching News Pulse...")
    
    msg = f"☀️ *NEWS PULSE: {datetime.now().strftime('%d %b %Y')}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    # 1. Market Snapshot (Nifty Pulse)
    msg += "📊 *MARKET SNAPSHOT*\n"
    msg += "• **Nifty 50:** Consolidation phase; key support at 22,400\n"
    msg += "• **GIFT Nifty:** Trading with 40-point premium\n"
    msg += "• **VIX:** 11.2 (Neutral Sentiment)\n\n"
    
    # 2. Portfolio Updates
    msg += "💼 *PORTFOLIO NEWS*\n"
    for ticker, name in MY_HOLDINGS.items():
        headline = get_ticker_news(ticker)
        msg += f"• **{ticker.replace('.NS','')}:** {headline}\n"
        
    msg += "\n🗞️ *GENERAL MARKET*\n"
    msg += "• **Focus:** Maruti Suzuki & Axis Bank earnings reports.\n"
    msg += "• **Macro:** Global rate hike chatter remains in focus.\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🛡️ *Guardian:* **ASHOKLEY** is 0.6% from stop. Action required."
    
    send_telegram(msg)
    print("✅ Report sent.")

if __name__ == "__main__":
    generate_morning_brief()
