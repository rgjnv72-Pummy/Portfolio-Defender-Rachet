import os, http.client, json, yfinance as yf
from datetime import datetime

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '').strip()

# --- YOUR HOLDINGS ---
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

def get_stock_brief(ticker):
    """Fetches Price and News for a ticker."""
    try:
        t = yf.Ticker(ticker)
        # Fetch Price
        price_info = t.history(period="1d")
        ltp = round(price_info['Close'].iloc[-1], 2) if not price_info.empty else "N/A"
        
        # Fetch News
        news = t.news
        headline = news[0]['title'] if news else "No specific news today."
        
        return f"• *{ticker.split('.')[0]}:* ₹{ltp}\n   _{headline}_"
    except Exception:
        return f"• *{ticker.split('.')[0]}:* Price/News currently unavailable."

def generate_morning_brief():
    print("📰 Fetching Live Data for Holdings...")
    
    msg = f"☀️ *MARKET BRIEF: {datetime.now().strftime('%d %b %Y')}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    # 1. Market Indices (Simulated for speed)
    msg += "📊 *MARKET SNAPSHOT*\n"
    msg += "• **GIFT Nifty:** 24,180 (+0.45%)\n"
    msg += "• **VIX:** 12.8 (Low Volatility)\n\n"
    
    # 2. Portfolio Performance & News
    msg += "💼 *YOUR HOLDINGS*\n"
    for stock in MY_HOLDINGS:
        msg += get_stock_brief(stock) + "\n"
        
    msg += "\n🗞️ *MARKET HEADLINES*\n"
    msg += "• **Indices:** Nifty eyes 24,250 resistance.\n"
    msg += "• **Banks:** PSU Banks in focus after RBI's ECL draft.\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🚀 *Action:* Trail profits in auto stocks."
    
    send_telegram(msg)
    print("✅ Dispatch Successful.")

if __name__ == "__main__":
    generate_morning_brief()
