import yfinance as yf
import pandas as pd
import numpy as np
import http.client, json, os
from datetime import datetime

# --- AUTH ---
MY_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
MY_TOKEN = os.getenv('TELEGRAM_TOKEN')

# --- UPDATED HOLDINGS ---
MY_HOLDINGS = {
    "CHENNPETRO.NS": [200, 910.00, "2026-03-12", "Energy"],
    "TATAPOWER.NS": [500, 403.00, "2026-03-23", "Energy"],
    "LLOYDSME.NS": [109, 1446.56, "2026-04-07", "Metals"],
    "ADANIPOWER.NS": [1000, 163.36, "2026-04-07", "Energy"],
    "PREMIERENE.NS": [150, 943.30, "2026-04-07", "Infrastructure"],
    "NATCOPHARM.NS": [150, 1066.00, "2026-04-07", "Pharma"],
    "ORIENTELEC.NS": [700, 184.00, "2026-04-21", "Consumer Durables"],
    "SKYGOLD.NS": [218, 417.00, "2026-04-22", "Consumer Durables"],
    "AARTIIND.NS": [218, 459.54, "2026-04-22", "Chemicals"],
    "ABB.NS": [15, 7432.00, "2026-04-28", "Capital Goods"],
    "HITACHIENER.NS": [4, 32905.00, "2026-04-29", "Capital Goods"],
    "KIRLOSENG.NS": [60, 1694.80, "2026-04-30", "Capital Goods"],
    "BHEL.NS": [300, 349.00, "2026-04-30", "Capital Goods"],
    "HFCL.NS": [1000, 122.50, "2026-05-04", "Telecommunication"],
    "ADANIPORTS.NS": [70, 1702.00, "2026-05-04", "Infrastructure"],
    "TENNIND.NS": [145, 635.00, "2026-05-04", "Auto Components"]
}








def send_msg(text):
    # .strip() is CRITICAL here to remove hidden \n characters from GitHub Secrets
    token = MY_TOKEN.strip() if MY_TOKEN else None
    chat_id = MY_CHAT_ID.strip() if MY_CHAT_ID else None
    
    if not token or not chat_id:
        print("❌ Secrets Missing!")
        return
    try:
        conn = http.client.HTTPSConnection("api.telegram.org")
        payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
        headers = {"Content-Type": "application/json"}
        # Clean URL construction
        url = f"/bot{token}/sendMessage"
        conn.request("POST", url, payload, headers)
        res = conn.getresponse()
        print(f"📡 Telegram Status: {res.status} {res.reason}")
        conn.close()
    except Exception as e:
        print(f"❌ Telegram Failed: {e}")

def run_advanced_guardian():
    tickers = list(MY_HOLDINGS.keys()) + ["^NSEI"]
    print(f"🛡️ Guarding {len(MY_HOLDINGS)} stocks...")
    
    data = yf.download(tickers, period="1y", interval="1d", progress=False, auto_adjust=True)
    
    if data.empty:
        print("❌ Error: No data downloaded.")
        return

    try:
        nifty_close = data['Close']['^NSEI'].dropna()
        nifty_chg = ((nifty_close.iloc[-1] - nifty_close.iloc[-2]) / nifty_close.iloc[-2]) * 100
    except:
        nifty_chg = 0.0

    results = []
    total_val, daily_gain_sum = 0, 0
    sector_values = {}

    for ticker, (qty, buy_p, buy_date, sector) in MY_HOLDINGS.items():
        try:
            # Multi-Index safe extraction
            df = data.iloc[:, data.columns.get_level_values(1) == ticker].copy()
            df.columns = df.columns.get_level_values(0)
            df = df.dropna()
            
            if len(df) < 15: continue
            
            close_p, prev_p = df['Close'].iloc[-1], df['Close'].iloc[-2]
            pnl_pct = ((close_p - buy_p) / buy_p) * 100
            
            # Dynamic Multiplier
            std = df['Close'].pct_change().std()
            mult = 1.0 if pnl_pct > 30 else 1.5 if pnl_pct > 15 else (2.5 if std > 0.025 else 2.0)
            
            # ATR Calculation
            tr = pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift(1)).abs(), (df['Low']-df['Close'].shift(1)).abs()], axis=1).max(axis=1)
            atr = tr.rolling(14).mean()
            
            # Ratchet Logic
            valid_df = df[df.index >= buy_date].copy()
            if valid_df.empty: valid_df = df.iloc[-5:]
            
            ratchet_series = (valid_df['High'] - (mult * atr.reindex(valid_df.index))).cummax()
            ratchet = ratchet_series.iloc[-1]
            
            dist_to_stop = ((close_p - ratchet) / close_p) * 100
            total_val += (close_p * qty)
            daily_gain_sum += (close_p - prev_p) * qty
            sector_values[sector] = sector_values.get(sector, 0) + (close_p * qty)

            status_icon = "🚨 *EXIT*" if close_p < ratchet else "✅"
            results.append({
                'text': f"*{ticker.replace('.NS','')}*: {pnl_pct:+.1f}% | {status_icon}\n_Stop: ₹{ratchet:.1f} ({dist_to_stop:.1f}% cushion)_\n\n",
                'is_cut': close_p < ratchet
            })
        except Exception as e:
            print(f"⚠️ Error on {ticker}: {e}")
            continue

    # Build Header
    report = f"🚀 *PORTFOLIO RATCHET: {datetime.now().strftime('%d %b')}*\n"
    report += f"Nifty 50: {nifty_chg:+.2f}% 🏛️\n"
    report += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Sort: Exits first
    sorted_results = sorted(results, key=lambda x: x['is_cut'], reverse=True)
    for res in sorted_results: report += res['text']

    report += "🏗️ *SECTOR EXPOSURE*\n"
    for sec, val in sorted(sector_values.items(), key=lambda item: item[1], reverse=True):
        report += f"• {sec}: {(val/total_val)*100:.1f}%\n"

    port_daily_pct = (daily_gain_sum / (total_val - daily_gain_sum)) * 100 if total_val > daily_gain_sum else 0
    alpha = port_daily_pct - nifty_chg
    
    report += f"\n📊 *SUMMARY*\nValue: ₹{total_val:,.0f}\n"
    report += f"Daily: ₹{daily_gain_sum:,.0f} ({port_daily_pct:+.2f}%)\n"
    report += f"Alpha: {alpha:+.2f}% {'🔥' if alpha > 0 else '❄️'}"
    
    send_msg(report)

if __name__ == "__main__":
    run_advanced_guardian()
