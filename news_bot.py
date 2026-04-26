import yfinance as yf
import requests
import os
from datetime import datetime

# --- AUTH ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- TICKERS ---
TICKERS = [
    "CHENNPETRO.NS", "ABB.NS", "GPIL.NS", "TATAPOWER.NS", "ONGC.NS", 
    "LLOYDSME.NS", "ADANIPOWER.NS", "PREMIERENE.NS", "NATCOPHARM.NS", 
    "ASHOKLEY.NS", "AUROPHARMA.NS", "SAMMAANCAP.NS"
]

def send_to_telegram(text):
    if not TOKEN or not CHAT_ID:
        print("Missing Credentials")
        return
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def get_sentiment():
    try:
        # Fetch Nifty and VIX
        data = yf.download(["^NSEI", "^INDIAVIX"], period="5d", interval="1d", progress=False)
        nifty = data['Close']['^NSEI'].dropna()
        n_now, n_prev = nifty.iloc[-1], nifty.iloc[-2]
        n_chg = ((n_now - n_prev) / n_prev) * 100
        vix = data['Close']['^INDIAVIX'].dropna().iloc[-1]
        
        status = "📉 WEAK" if n_chg < -0.5 else "📈 STRONG" if n_chg > 0.5 else "⚖️ NEUTRAL"
        v_warn = "⚠️ HIGH" if vix > 19 else "✅ STABLE"
        
        return (f"🌍 *MARKET ENVIRONMENT*\n"
                f"• Nifty 50: {n_now:,.0f} ({n_chg:+.2f}% {status})\n"
                f"• India VIX: {vix:.2f} ({v_warn})\n"
                f"• Bias: *{'Bearish' if vix > 19 and n_chg < 0 else 'Bullish' if vix < 16 else 'Cautious'}*\n")
    except Exception as e:
        return f"🌍 *MARKET ENVIRONMENT*: Service unavailable ({str(e)[:30]})\n"

def deliver_news():
    report = f"📊 *EVENING SUMMARY* - {datetime.now().strftime('%d %b %Y')}\n"
    report += "—" * 15 + "\n"
    report += get_sentiment()
    report += "—" * 15 + "\n\n🗞️ *LATEST HEADLINES*\n"
    
    found_news = False
    for symbol in TICKERS:
        try:
            stock = yf.Ticker(symbol)
            news_items = stock.news[:3]
            if news_items:
                found_news = True
                name = symbol.replace('.NS', '')
                report += f"\n🔹 *{name}*\n"
                for i, art in enumerate(news_items, 1):
                    report += f"{i}. [{art['title']}]({art['link']})\n"
        except:
            continue

    if not found_news:
        report += "_No new headlines found for your holdings today._"

    send_to_telegram(report)

if __name__ == "__main__":
    deliver_news()
