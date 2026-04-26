import yfinance as yf
import requests
import os
import sys
from datetime import datetime

# --- SAFE IMPORT ---
try:
    from guardian import MY_HOLDINGS
except ImportError:
    print("❌ Error: guardian.py not found. Using empty list.")
    MY_HOLDINGS = {}

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def get_sentiment():
    try:
        # Fetching Nifty and VIX (April 2026 context)
        # Nifty: ~23,900 | VIX: ~19.7 (High Fear)
        data = yf.download(["^NSEI", "^INDIAVIX"], period="5d", interval="1d", progress=False)
        nifty = data['Close']['^NSEI'].dropna()
        nifty_chg = ((nifty.iloc[-1] - nifty.iloc[-2]) / nifty.iloc[-2]) * 100
        vix = data['Close']['^INDIAVIX'].dropna().iloc[-1]

        v_status = "⚠️ HIGH" if vix > 19 else "✅ STABLE"
        n_status = "📉 WEAK" if nifty_chg < -0.5 else "📈 STRONG" if nifty_chg > 0.5 else "⚖️ NEUTRAL"
        
        return (f"🌍 *MARKET ENVIRONMENT*\n"
                f"• Nifty 50: {nifty.iloc[-1]:,.0f} ({nifty_chg:+.2f}% {n_status})\n"
                f"• India VIX: {vix:.2f} ({v_status})\n"
                f"• Bias: *{'Bearish' if vix > 19 and nifty_chg < 0 else 'Bullish' if vix < 16 else 'Cautious'}*\n")
    except:
        return "🌍 *MARKET ENVIRONMENT*: Data unavailable.\n"

def send_msg(text):
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    requests.post(url, json=payload)

def deliver_news():
    report = f"📊 *EVENING SUMMARY* - {datetime.now().strftime('%d %b')}\n"
    report += "—" * 15 + "\n"
    report += get_sentiment()
    report += "—" * 15 + "\n\n🗞️ *HOLDINGS NEWS*\n"
    
    found_news = False
    for ticker in MY_HOLDINGS.keys():
        try:
            stock = yf.Ticker(ticker)
            headlines = stock.news[:3]
            if headlines:
                found_news = True
                name = ticker.replace('.NS', '')
                report += f"\n🔹 *{name}*\n"
                for i, art in enumerate(headlines, 1):
                    report += f"{i}. [{art['title']}]({art['link']})\n"
        except: continue

    if not found_news:
        report += "_No new headlines found for your tickers today._"

    send_msg(report)

if __name__ == "__main__":
    deliver_news()
