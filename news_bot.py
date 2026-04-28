import os, requests, http.client, json, yfinance as yf
from datetime import datetime

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '').strip()

# --- ADD YOUR HOLDINGS HERE (Use .NS for NSE) ---
MY_HOLDINGS = ["TATAMOTORS.NS", "MARUTI.NS", "CANBK.NS", "RECLTD.NS", "RELIANCE.NS"]

def send_telegram(text):
    if not TOKEN or not CHAT_ID: return
    conn = http.client.HTTPSConnection("api.telegram.org")
    payload = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    headers = {"Content-Type": "application/json"}
    try:
        conn.request("POST", f"/bot{TOKEN}/sendMessage", payload, headers)
        conn.getresponse()
    finally:
        conn.close()

def get_ticker_news(ticker):
    """Fetches the latest news headline for a ticker using yfinance."""
    try:
        t = yf.Ticker(ticker)
        news = t.news
        if news:
            return f"• *{ticker.replace('.NS','')}:* {news[0]['title']}"
        return f"• *{ticker.replace('.NS','')}:* No recent news found."
    except:
        return f"• *{ticker.replace('.NS','')}:* Data unavailable."

def generate_morning_brief():
    print("📰 Generating Morning Brief...")
    
    msg = f"☀️ *MARKET BRIEF: {datetime.now().strftime('%d %b %Y')}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    # 1. Global/General Market Sentiment (Placeholder for logic)
    msg += "📊 *MARKET SNAPSHOT*\n"
    msg += "• **GIFT Nifty:** Tracking global cues.\n"
    msg += "• **Sentiment:** Focus on Earnings & Macro data.\n\n"
    
    # 2. Automated News for Holdings
    msg += "💼 *HOLDINGS UPDATES*\n"
    for stock in MY_HOLDINGS:
        msg += get_ticker_news(stock) + "\n"
        
    msg += "\n🗞️ *GENERAL MARKET NEWS*\n"
    msg += "• **RBI:** Monitoring liquidity and inflation trends.\n"
    msg += "• **FII/DII:** Watch for institutional flow patterns.\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🚀 *Strategy:* Trade with strict stop-losses."
    
    send_telegram(msg)
    print("✅ News delivered successfully.")

if __name__ == "__main__":
    generate_morning_brief()
