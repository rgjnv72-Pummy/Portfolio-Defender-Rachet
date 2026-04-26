import yfinance as yf
import requests
import os
from datetime import datetime

# --- AUTH ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

TICKERS = [
    "CHENNPETRO.NS", "ABB.NS", "GPIL.NS", "TATAPOWER.NS", "ONGC.NS", 
    "LLOYDSME.NS", "ADANIPOWER.NS", "PREMIERENE.NS", "NATCOPHARM.NS", 
    "ASHOKLEY.NS", "AUROPHARMA.NS", "SAMMAANCAP.NS"
]

def send_to_telegram(text):
    if not TOKEN or not CHAT_ID:
        print("❌ ERROR: Secrets not found!")
        return
    
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        # 🌟 THIS PRINT IS IMPORTANT: Check GitHub Logs for this!
        print(f"Telegram Response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Network Error: {e}")

def get_sentiment():
    try:
        mkt = yf.download(["^NSEI", "^INDIAVIX"], period="5d", interval="1d", progress=False)
        nifty = mkt['Close']['^NSEI'].dropna()
        n_now = nifty.iloc[-1]
        n_chg = ((n_now - nifty.iloc[-2]) / nifty.iloc[-2]) * 100
        vix = mkt['Close']['^INDIAVIX'].dropna().iloc[-1]
        
        return (f"🌍 *MARKET ENVIRONMENT*\n"
                f"• Nifty 50: {n_now:,.0f} ({n_chg:+.2f}%)\n"
                f"• India VIX: {vix:.2f}\n")
    except:
        return "🌍 *MARKET ENVIRONMENT*: Data busy.\n"

def deliver_news():
    # 🌟 STEP 1: Send a tiny test message first
    send_to_telegram("🔄 *News Bot is attempting to connect...*")

    report = f"📊 *EVENING SUMMARY* - {datetime.now().strftime('%d %b %Y')}\n"
    report += "—" * 15 + "\n"
    report += get_sentiment()
    report += "—" * 15 + "\n\n🗞️ *HOLDINGS NEWS*\n"
    
    found_news = False
    for symbol in TICKERS:
        try:
            stock = yf.Ticker(symbol)
            news = stock.news[:3]
            if news:
                found_news = True
                report += f"\n🔹 *{symbol.replace('.NS', '')}*\n"
                for i, art in enumerate(news, 1):
                    report += f"{i}. [{art['title']}]({art['link']})\n"
        except: continue

    if not found_news:
        report += "_No news found for holdings today._"

    send_to_telegram(report)

if __name__ == "__main__":
    deliver_news()
