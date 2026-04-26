import yfinance as yf
import requests
import os
from datetime import datetime
import time

# --- AUTH ---
# .strip() removes any accidental spaces or newlines
RAW_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TOKEN = str(RAW_TOKEN).strip()
CHAT_ID = str(os.environ.get("TELEGRAM_CHAT_ID", "")).strip()

TICKERS = ["CHENNPETRO.NS", "ABB.NS", "TATAPOWER.NS", "ONGC.NS", "ADANIPOWER.NS"]

def send_to_telegram(text):
    # Debug info to see if the token is being read correctly
    print(f"DEBUG: Token Length is {len(TOKEN)}")
    print(f"DEBUG: Token starts with: {TOKEN[:5]}...")
    
    if len(TOKEN) < 5:
        print("❌ ERROR: Token is too short or missing!")
        return

    # Using the most basic string concatenation to avoid parsing issues
    api_url = "https://telegram.org" + TOKEN + "/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        r = requests.post(api_url, json=payload, timeout=20)
        print(f"Telegram Response Code: {r.status_code}")
        print(f"Telegram Response Text: {r.text}")
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
    print("🚀 Bot Started...")
    report = f"📊 *EVENING SUMMARY* - {datetime.now().strftime('%d %b %Y')}\n"
    report += "—" * 15 + "\n"
    report += get_sentiment()
    report += "—" * 15 + "\n\n🗞️ *LATEST HEADLINES*\n"
    
    found = False
    for symbol in TICKERS:
        try:
            stock = yf.Ticker(symbol)
            news = stock.news[:2]
            if news:
                found = True
                report += f"\n🔹 *{symbol.replace('.NS', '')}*\n"
                for i, art in enumerate(news, 1):
                    report += f"{i}. [{art['title']}]({art['link']})\n"
            time.sleep(1)
        except: continue

    if not found:
        report += "_No new headlines found for holdings today._"

    send_to_telegram(report)

if __name__ == "__main__":
    deliver_news()
