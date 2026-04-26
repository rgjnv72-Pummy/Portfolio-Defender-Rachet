import yfinance as yf
import requests
import os
import sys
from datetime import datetime

# --- AUTH ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- SYNCED HOLDINGS ---
TICKERS = [
    "CHENNPETRO.NS", "ABB.NS", "GPIL.NS", "TATAPOWER.NS", "ONGC.NS", 
    "LLOYDSME.NS", "ADANIPOWER.NS", "PREMIERENE.NS", "NATCOPHARM.NS", 
    "ASHOKLEY.NS", "AUROPHARMA.NS", "SAMMAANCAP.NS"
]

def send_to_telegram(text):
    if not TOKEN or not CHAT_ID:
        print("❌ CRITICAL: TELEGRAM_TOKEN or CHAT_ID missing in Secrets!")
        sys.exit(1)
    
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    # Headers to mimic a browser
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

def get_market_sentiment():
    try:
        # Fetch Nifty and VIX
        mkt = yf.download(["^NSEI", "^INDIAVIX"], period="5d", interval="1d", progress=False)
        if mkt.empty: return "🌍 *MARKET ENVIRONMENT*: No data found.\n"
        
        nifty = mkt['Close']['^NSEI'].dropna()
        n_now, n_prev = nifty.iloc[-1], nifty.iloc[-2]
        n_chg = ((n_now - n_prev) / n_prev) * 100
        vix = mkt['Close']['^INDIAVIX'].dropna().iloc[-1]
        
        v_warn = "⚠️ HIGH" if vix > 19 else "✅ STABLE"
        n_stat = "📉 WEAK" if n_chg < -0.5 else "📈 STRONG" if n_chg > 0.5 else "⚖️ NEUTRAL"
        
        return (f"🌍 *MARKET ENVIRONMENT*\n"
                f"• Nifty 50: {n_now:,.0f} ({n_chg:+.2f}% {n_stat})\n"
                f"• India VIX: {vix:.2f} ({v_warn})\n"
                f"• Bias: *{'Bearish' if vix > 19 and n_chg < 0 else 'Bullish' if vix < 16 else 'Cautious'}*\n")
    except Exception as e:
        print(f"⚠️ Sentiment Fetch Failed: {e}")
        return "🌍 *MARKET ENVIRONMENT*: Data currently unavailable.\n"

def deliver_news():
    print(f"🚀 Starting update for {len(TICKERS)} tickers...")
    report = f"📊 *EVENING SUMMARY* - {datetime.now().strftime('%d %b %Y')}\n"
    report += "—" * 15 + "\n"
    report += get_market_sentiment()
    report += "—" * 15 + "\n\n🗞️ *LATEST HEADLINES*\n"
    
    found_news = False
    for symbol in TICKERS:
        try:
            print(f"Fetching {symbol}...")
            stock = yf.Ticker(symbol)
            news = stock.news[:3]
            if news:
                found_news = True
                report += f"\n🔹 *{symbol.replace('.NS', '')}*\n"
                for i, art in enumerate(news, 1):
                    report += f"{i}. [{art['title']}]({art['link']})\n"
        except Exception as e:
            print(f"⚠️ Skipping {symbol}: {e}")
            continue

    if not found_news:
        report += "_No new headlines found today._"

    send_to_telegram(report)
    print("✅ Process Complete.")

if __name__ == "__main__":
    deliver_news()
