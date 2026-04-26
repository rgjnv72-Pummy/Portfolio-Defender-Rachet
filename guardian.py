import yfinance as yf
import pandas as pd
import numpy as np
import http.client, json, os

# --- AUTH ---
MY_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
MY_TOKEN = os.getenv('TELEGRAM_TOKEN')

# --- HOLDINGS (The single source of truth) ---
MY_HOLDINGS = {
    "CHENNPETRO.NS": [200, 910.00, "2026-03-12", "Energy"],
    "ABB.NS": [30, 6320.00, "2026-03-18", "Capital Goods"],
    "GPIL.NS": [760, 262.98, "2026-03-23", "Metals"],
    "TATAPOWER.NS": [500, 403.00, "2026-03-23", "Energy"],
    "ONGC.NS": [700, 287.20, "2026-04-02", "Energy"],
    "LLOYDSME.NS": [109, 1446.56, "2026-04-07", "Metals"],
    "ADANIPOWER.NS": [1000, 163.36, "2026-04-07", "Energy"],
    "PREMIERENE.NS": [150, 943.30, "2026-04-07", "Infrastructure"],
    "NATCOPHARM.NS": [150, 1066.00, "2026-04-07", "Pharma"],
    "ASHOKLEY.NS": [1400, 173.00, "2026-04-09", "Auto"],
    "AUROPHARMA.NS": [70, 1350.00, "2026-04-10", "Pharma"],
    "SAMMAANCAP.NS": [922, 154.89, "2026-04-13", "Finance"]
}

def send_msg(text):
    conn = http.client.HTTPSConnection("api.telegram.org")
    payload = json.dumps({"chat_id": MY_CHAT_ID, "text": text, "parse_mode": "Markdown"})
    headers = {"Content-Type": "application/json"}
    conn.request("POST", f"/bot{MY_TOKEN}/sendMessage", payload, headers)
    conn.close()

def run_advanced_guardian():
    tickers = list(MY_HOLDINGS.keys()) + ["^NSEI"]
    data = yf.download(tickers, period="1y", interval="1d", progress=False, auto_adjust=True)
    
    nifty = data['Close']['^NSEI'].dropna()
    nifty_chg = ((nifty.iloc[-1] - nifty.iloc[-2]) / nifty.iloc[-2]) * 100

    results = []
    total_val, daily_gain_sum = 0, 0
    sector_values = {}

    for ticker, (qty, buy_p, buy_date, sector) in MY_HOLDINGS.items():
        try:
            df = data.xs(ticker, axis=1, level=1).dropna()
            close_p, prev_p = df['Close'].iloc[-1], df['Close'].iloc[-2]
            pnl_pct = ((close_p - buy_p) / buy_p) * 100
            
            std = df['Close'].pct_change().std()
            mult = 1.0 if pnl_pct > 30 else 1.5 if pnl_pct > 15 else (2.5 if std > 0.025 else 2.0)
            
            tr = pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift(1)).abs()], axis=1).max(axis=1)
            atr = tr.rolling(14).mean()
            ratchet = (df[df.index >= buy_date]['High'] - (mult * atr[atr.index >= buy_date])).cummax().iloc[-1]
            
            dist_to_stop = ((close_p - ratchet) / close_p) * 100
            total_val += (close_p * qty)
            daily_gain_sum += (close_p - prev_p) * qty
            sector_values[sector] = sector_values.get(sector, 0) + (close_p * qty)

            status_icon = "🚨 *CUT*" if close_p < ratchet else "✅"
            results.append({
                'text': f"*{ticker.replace('.NS','')}*: {pnl_pct:+.1f}% | {status_icon}\n_Stop: ₹{ratchet:.1f} ({dist_to_stop:.1f}% cushion)_\n\n",
                'is_cut': close_p < ratchet
            })
        except: continue

    report = "🚀 *DYNAMIC PORTFOLIO REPORT*\n"
    report += f"Nifty 50: {nifty_chg:+.2f}% 🏛️\n\n"
    
    sorted_results = sorted(results, key=lambda x: x['is_cut'], reverse=True)
    for res in sorted_results: report += res['text']

    report += "🏗️ *SECTOR EXPOSURE*\n"
    for sec, val in sorted(sector_values.items(), key=lambda x: x[1], reverse=True):
        report += f"• {sec}: {(val/total_val)*100:.1f}%\n"

    port_daily_pct = (daily_gain_sum / (total_val - daily_gain_sum)) * 100
    alpha = port_daily_pct - nifty_chg
    
    report += f"\n📊 *SUMMARY*\nTotal Value: ₹{total_val:,.0f}\n"
    report += f"Daily Gain: ₹{daily_gain_sum:,.0f} ({port_daily_pct:+.2f}%)\n"
    report += f"Alpha: {alpha:+.2f}% {'🔥' if alpha > 0 else '❄️'}"
    
    send_msg(report)

if __name__ == "__main__":
    run_advanced_guardian()
