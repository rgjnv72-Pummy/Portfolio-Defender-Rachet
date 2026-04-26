import yfinance as yf
import requests
import os
from datetime import datetime
# 🚀 Auto-picks from your guardian.py
from guardian import MY_HOLDINGS  

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def get_market_sentiment():
    try:
        # Fetching Nifty and VIX for the market environment check
        # April 2026 Context: VIX near 20 indicates high tension
        mkt = yf.download(["^NSEI", "^INDIAVIX"], period="5d", interval="1d", progress=False)
        
        nifty = mkt['Close']['^NSEI'].dropna()
        nifty_now, nifty_prev = nifty.iloc[-1], nifty.iloc[-2]
        nifty_chg = ((nifty_now - nifty_prev) / nifty_prev) * 100
        
        vix = mkt['Close']['^INDIAVIX'].dropna().iloc[-1]
        
        # Sentiment Logic
        vix_status = "⚠️ HIGH" if vix > 19 else "✅ STABLE"
        nifty_status = "📉 WEAK" if nifty_chg < -0.5 else "📈 STRONG" if nifty_chg > 0.5 else "⚖️ NEUTRAL"
        bias = "Bearish" if vix > 19 and nifty_chg < 0 else "Bullish" if vix < 16 else "Cautious"

        sentiment = (
            f"🌍 *MARKET ENVIRONMENT*\n"
            f"• Nifty 50: {nifty_now:,.0f} ({nifty_chg:+.2f}% {nifty_status})\n"
            f"• India VIX: {vix:.2f} ({vix_status})\n"
            f"• Market Bias: *{bias}*\n"
        )
        return sentiment
    except:
        return "🌍 *MARKET ENVIRONMENT*: Service temporarily unavailable.\n"

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
    # 1. Header & Market Environment
    report = f"📊 *EVENING SUMMARY* - {datetime.now().strftime('%d %b')}\n"
    report += "—" * 15 + "\n"
    report += get_market_sentiment()
    report += "—" * 15 + "\n"
    
    # 2. Top 3 Headlines for your Holdings
    news_content = "\n🗞️ *HOLDINGS NEWS*\n"
    found_any = False
    
    for ticker in MY_HOLDINGS.keys():
        try:
            stock = yf.Ticker(ticker)
            headlines = stock.news[:3]
            
            if headlines:
                found_any = True
                name = ticker.replace('.NS', '')
                news_content += f"\n🔹 *{name}*\n"
                for i, article in enumerate(headlines, 1):
                    news_content += f"{i}. [{article['title']}]({article['link']})\n"
        except: continue

    if not found_any:
        news_content += "_No new headlines found for your tickers today._"
    
    report += news_content

    # 3. Final Send
    if len(report) > 4000:
        send_to_telegram(report[:4000])
    else:
        send_to_telegram(report)

if __name__ == "__main__":
    deliver_news()
