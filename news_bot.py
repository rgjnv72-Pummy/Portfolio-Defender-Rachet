import os, requests, http.client, json

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '').strip()

# --- ADD YOUR HOLDINGS HERE ---
MY_HOLDINGS = ["TATA MOTORS", "MARUTI", "CANARA BANK", "RECLTD"]

def send_telegram(text):
    conn = http.client.HTTPSConnection("api.telegram.org")
    payload = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    headers = {"Content-Type": "application/json"}
    conn.request("POST", f"/bot{TOKEN}/sendMessage", payload, headers)
    conn.close()

def generate_morning_brief():
    # Live Data as of April 28, 2026
    msg = "☀️ *GOOD MORNING: MARKET BRIEF*\n"
    msg += "📅 Tuesday, 28 April 2026\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    # General Market Summary
    msg += "📊 *MARKET SNAPSHOT*\n"
    msg += "• **Nifty 50:** 24,049 (-0.18%)\n"
    msg += "• **GIFT Nifty:** 24,017 (Cautious Start)\n"
    msg += "• **VIX:** Stable but mixed undertone\n\n"
    
    # Institutional Activity
    msg += "🐋 *WHALE WATCH (Previous Session)*\n"
    msg += "• Market witnessed buying at lower levels (Nifty +194 pts on 27 Apr).\n\n"
    
    # Portfolio News
    msg += "💼 *HOLDINGS UPDATES*\n"
    if "MARUTI" in MY_HOLDINGS:
        msg += "• **MARUTI:** Q4 Earnings TODAY. Net profit seen rising 12%.\n"
    if "TATA MOTORS" in MY_HOLDINGS:
        msg += "• **TATA MOTORS:** Trading +0.96% at ₹424. Q4 Results scheduled for May 13.\n"
    if "CANARA BANK" in MY_HOLDINGS:
        msg += "• **PSU BANKS:** Falling ~2.5% as RBI finalises ECL norms.\n"
        
    msg += "\n🗞️ *GENERAL NEWS*\n"
    msg += "• **RBI:** Finalising ECL norms impacting PSU banks today.\n"
    msg += "• **Earnings:** REC, Bandhan Bank, and Maruti reporting today.\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🚀 *Strategy:* Watch 23,800 support for Nifty."
    
    send_telegram(news_msg)

if __name__ == "__main__":
    generate_morning_brief()
