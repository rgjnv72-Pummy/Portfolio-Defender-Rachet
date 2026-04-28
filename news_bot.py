import os, requests, json, http.client
import xml.etree.ElementTree as ET
from datetime import datetime

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '').strip()
MY_HOLDINGS = ["GPIL", "LLOYDSME", "PREMIERENE", "NATCOPHARM", "ADANIPOWER", "ASHOKLEY", "AARTIIND"]

def send_telegram(text):
    if not TOKEN or not CHAT_ID:
        print("❌ Secrets Missing")
        return
    
    # HARDCODED ROBUST URL
    url = f"/bot{TOKEN}/sendMessage"
    conn = http.client.HTTPSConnection("api.telegram.org")
    payload = json.dumps({
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "Markdown"
    })
    headers = {"Content-Type": "application/json"}
    
    try:
        conn.request("POST", url, payload, headers)
        res = conn.getresponse()
        print(f"📡 Telegram Status: {res.status} {res.reason}")
    except Exception as e:
        print(f"❌ Post Failed: {e}")
    finally:
        conn.close()

def get_google_news(query):
    """Fetches headlines via Google RSS."""
    try:
        url = f"https://google.com{query.replace(' ', '+')}+stock+news&hl=en-IN&gl=IN&ceid=IN:en"
        response = requests.get(url, timeout=10)
        root = ET.fromstring(response.content)
        for item in root.findall('.//item'):
            full_title = item.find('title').text
            return full_title.split(' - ')[0] # Return only headline
    except:
        return "No recent headlines found."

def generate_morning_brief():
    print("📰 Generating News Brief for Holdings...")
    
    msg = f"☀️ *NEWS PULSE: {datetime.now().strftime('%d %b %Y')}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    # 1. Market Snapshot
    msg += "📊 *MARKET SNAPSHOT*\n"
    msg += "• **GIFT Nifty:** Tracking global cues\n"
    msg += "• **Sentiment:** Focus on Portfolio Ratchets\n\n"
    
    # 2. News for your actual Portfolio
    msg += "💼 *PORTFOLIO NEWS*\n"
    for stock in MY_HOLDINGS:
        headline = get_google_news(stock)
        msg += f"• **{stock}:** {headline}\n"
        
    msg += "\n🗞️ *GENERAL MARKET*\n"
    msg += f"• {get_google_news('Nifty 50')}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🛡️ *Guardian:* Check stops for ASHOKLEY."
    
    send_telegram(msg)
    print("✅ Dispatch Attempted.")

if __name__ == "__main__":
    generate_morning_brief()
