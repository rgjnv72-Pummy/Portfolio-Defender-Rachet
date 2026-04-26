import yfinance as yf
import requests
import os
from datetime import datetime
import time

# --- AUTH ---
TOKEN = str(os.environ.get("TELEGRAM_TOKEN")).strip()
CHAT_ID = str(os.environ.get("TELEGRAM_CHAT_ID")).strip()

TICKERS = [
    "CHENNPETRO.NS", "ABB.NS", "GPIL.NS", "TATAPOWER.NS", "ONGC.NS", 
    "LLOYDSME.NS", "ADANIPOWER.NS", "PREMIERENE.NS", "NATCOPHARM.NS", 
    "ASHOKLEY.NS", "AUROPHARMA.NS", "SAMMAANCAP.NS"
]

def send_to_telegram(text):
    if not TOKEN or "None" in TOKEN:
        print("❌ TOKEN IS MISSING")
        return
    
    # Basic URL structure to prevent parsing errors
    base_url = "https://telegram.org" + TOKEN + "/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    
    try:
        response = requests.post(base_url, json=payload, timeout=20)
        print(f"Telegram Status: {response.status_code}")
        print(f"Telegram Raw Response: {response.text}")
    except Exception as e:
        print(f"❌ Network Error: {e}")

def get_sentiment():
    try:
        # Fetching Nifty and VIX
        mkt = yf.download(["^NSEI", "^INDIAVIX"], period="5d", interval="1d", progress=False)
        nifty = mkt['Close']['^NSEI'].dropna()
        n_now = nifty.iloc[-1]
        n_chg = ((n_now - nifty.iloc[-2]) / nifty.iloc[-2]) * 100
        vix = mkt['Close']['^INDIAVIX'].dropna().iloc[-1]
        
        v_warn = "⚠️ HIGH" if vix > 19 else "✅ STABLE"
        n_stat = "📉 WEAK" if n_chg < -0.5 else "📈 STRONG" if n_chg > 0.5 else "⚖️ NEUTRAL"
        
        return (f"🌍 *MARKET ENVIRONMENT*\n"
                f"• Nifty 50: {n_now:,.0f} ({n_chg:+.2f}% {n_stat})\n"
                f"• India VIX: {vix:.2f} ({v_warn})\n"
                f"• Bias: *{'Bearish' if vix > 19 else 'Cautious'}*\n")
    except:
        return "🌍 *MARKET ENVIRONMENT*: Data busy.\n"

def deliver_news():
    print("🚀 Starting news fetch...")
    
    report = f"📊 *EVENING SUMMARY* - {datetime.now().strftime('%d %b %Y')}\n"
    report += "—" * 15 + "\n"
    report += get_sentiment()
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
            # Sleep briefly to avoid "database is locked" error
            time.sleep(1)
        except: continue

    if not found_news:
        report += "_No news found for holdings today._"

    send_to_telegram(report)

if __name__ == "__main__":
    deliver_news()
