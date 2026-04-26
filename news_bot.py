import yfinance as yf
import requests
import os
from datetime import datetime

# --- AUTH ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- SYNCED HOLDINGS LIST ---
TICKERS = [
    "CHENNPETRO.NS", "ABB.NS", "GPIL.NS", "TATAPOWER.NS", "ONGC.NS", 
    "LLOYDSME.NS", "ADANIPOWER.NS", "PREMIERENE.NS", "NATCOPHARM.NS", 
    "ASHOKLEY.NS", "AUROPHARMA.NS", "SAMMAANCAP.NS"
]

def get_market_sentiment():
    try:
        # Fetching Nifty 50 and India VIX
        mkt = yf.download(["^NSEI", "^INDIAVIX"], period="5d", interval="1d", progress=False)
        nifty = mkt['Close']['^NSEI'].dropna()
        n_now, n_prev = nifty.iloc[-1], nifty.iloc[-2]
        n_chg = ((n_now - n_prev) / n_prev) * 100
        vix = mkt['Close']['^INDIAVIX'].dropna().iloc[-1]
        
        # Logic
        v_warn = "⚠️ HIGH" if vix > 19 else "✅ STABLE"
        n_stat = "📉 WEAK" if n_chg < -0.5 else "📈 STRONG" if n_chg > 0.5 else "⚖️ NEUTRAL"
        bias = "Bearish" if vix > 19 and n_chg < 0 else "Bullish" if vix < 16 else "Cautious"

        return (f"🌍 *MARKET ENVIRONMENT*\n"
                f"• Nifty 50: {n_now:,.0f} ({n_chg:+.2f}% {n_stat})\n"
                f"• India VIX: {vix:.2f} ({v_warn})\n"
                f"• Bias: *{bias}*\n")
    except:
        return "🌍 *MARKET ENVIRONMENT*: Data unavailable.\n"

def send_to_telegram(text):
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": True 
    }
    requests.post(url, json=payload)

def deliver_news():
    # Start Report
    report = f"📊 *EVENING SUMMARY* - {datetime.now().strftime('%d %b')}\n"
    report += "—" * 15 + "\n"
    report += get_market_sentiment()
    report += "—" * 15 + "\n\n🗞️ *HOLDINGS NEWS*\n"
    
    found_news = False
    for symbol in TICKERS:
        try:
            ticker_obj = yf.Ticker(symbol)
            news = ticker_obj.news[:3] # Top 3
            if news:
                found_news = True
                name = symbol.replace('.NS', '')
                report += f"\n🔹 *{name}*\n"
                for i, art in enumerate(news, 1):
                    report += f"{i}. [{art['title']}]({art['link']})\n"
        except:
            continue

    if not found_news:
        report += "_No new headlines found for your tickers today._"

    send_to_telegram(report)

if __name__ == "__main__":
    deliver_news()
