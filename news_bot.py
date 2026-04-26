import yfinance as yf
import requests
import os
from datetime import datetime
import time

# --- AUTH ---
# We use simple string concatenation to avoid any f-string or formatting errors
TOKEN = str(os.environ.get("TELEGRAM_TOKEN", "")).strip()
CHAT_ID = str(os.environ.get("TELEGRAM_CHAT_ID", "")).strip()

TICKERS = [
    "CHENNPETRO.NS", "ABB.NS", "GPIL.NS", "TATAPOWER.NS", "ONGC.NS", 
    "LLOYDSME.NS", "ADANIPOWER.NS", "PREMIERENE.NS", "NATCOPHARM.NS", 
    "ASHOKLEY.NS", "AUROPHARMA.NS", "SAMMAANCAP.NS"
]

def send_to_telegram(text):
    if not TOKEN or len(TOKEN) < 10:
        print("❌ TOKEN ERROR: Secret is missing or too short.")
        return

    # BUILD URL MANUALLY TO PREVENT PARSING ERRORS
    url = "https://telegram.org" + TOKEN + "/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        # We don't use custom headers here to keep it as basic as possible
        r = requests.post(url, json=payload, timeout=20)
        print("Telegram Status Code:", r.status_code)
        print("Telegram Response:", r.text)
    except Exception as e:
        print("❌ Connection Error:", e)

def get_market_pulse():
    try:
        # Fetching Nifty and VIX
        mkt = yf.download(["^NSEI", "^INDIAVIX"], period="5d", interval="1d", progress=False)
        nifty = mkt['Close']['^NSEI'].dropna()
        n_now = nifty.iloc[-1]
        n_chg = ((n_now - nifty.iloc[-2]) / nifty.iloc[-2]) * 100
        vix = mkt['Close']['^INDIAVIX'].dropna().iloc[-1]
        
        return (f"🌍 *MARKET PULSE*\n"
                f"• Nifty 50: {n_now:,.0f} ({n_chg:+.2f}%)\n"
                f"• India VIX: {vix:.2f}\n")
    except:
        return "🌍 *MARKET PULSE*: Data temporarily unavailable.\n"

def deliver_news():
    print("🚀 Execution Started...")
    
    report = f"📊 *EVENING SUMMARY* - {datetime.now().strftime('%d %b %Y')}\n"
    report += "—" * 15 + "\n"
    report += get_market_pulse()
    report += "—" * 15 + "\n\n🗞️ *HOLDINGS NEWS*\n"
    
    found_news = False
    for symbol in TICKERS:
        try:
            stock = yf.Ticker(symbol)
            news = stock.news[:2] 
            if news:
                found_news = True
                name = symbol.replace('.NS', '')
                report += f"\n🔹 *{name}*\n"
                for i, art in enumerate(news, 1):
                    report += f"{i}. [{art['title']}]({art['link']})\n"
            # Crucial: pause to prevent 'database is locked' error
            time.sleep(1.5)
        except: continue

    if not found_news:
        report += "_No news found for your holdings today._"

    send_to_telegram(report)
    print("✅ Process Finished.")

if __name__ == "__main__":
    deliver_news()
