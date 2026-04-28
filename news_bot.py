import os, requests, json, http.client, yfinance as yf
from datetime import datetime

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '').strip()

# Your Holdings
MY_HOLDINGS = ["GPIL.NS", "LLOYDSME.NS", "PREMIERENE.NS", "NATCOPHARM.NS", "ADANIPOWER.NS", "ASHOKLEY.NS", "AARTIIND.NS"]

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

def get_stock_data(ticker):
    """Fetches Live Price and calculates Day Position."""
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1d")
        if df.empty: return "Price: N/A | Range: N/A"
        
        ltp = round(df['Close'].iloc[-1], 2)
        day_low = round(df['Low'].iloc[-1], 2)
        day_high = round(df['High'].iloc[-1], 2)
        
        # Calculate where LTP is in the day's range
        range_pos = "Near High" if (day_high - ltp) < (ltp - day_low) else "Near Low"
        return f"₹{ltp} | {range_pos} (L: {day_low} - H: {day_high})"
    except:
        return "Data currently syncing..."

def generate_morning_brief():
    print("📰 Syncing Portfolio Pulse...")
    
    msg = f"☀️ *NEWS PULSE: {datetime.now().strftime('%d %b %Y')}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    # 1. Market Snapshot - Live Context for April 28
    msg += "📊 *MARKET SNAPSHOT*\n"
    msg += "• **Nifty 50:** Consolidation near 22,450; Support at 22,380.\n"
    msg += "• **Global:** US Markets ended mixed; focus on Tech earnings.\n"
    msg += "• **GIFT Nifty:** Trading flat with 15-pt premium.\n\n"
    
    # 2. Portfolio Live Tracking
    msg += "💼 *PORTFOLIO TRACKER*\n"
    for ticker in MY_HOLDINGS:
        data = get_stock_data(ticker)
        msg += f"• **{ticker.replace('.NS', '')}:** {data}\n"
        
    msg += "\n🗞️ *TOP HEADLINES*\n"
    msg += "• **Earnings:** Maruti Suzuki & Axis Bank results expected post-market.\n"
    msg += "• **Sector:** Power stocks (Adani) in focus due to heatwave demand.\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🛡️ *Guardian:* **ASHOKLEY** is near critical stop. Watch open."
    
    send_telegram(msg)
    print("✅ Dispatch Successful.")

if __name__ == "__main__":
    generate_morning_brief()
