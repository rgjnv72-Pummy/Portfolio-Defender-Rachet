import yfinance as yf
import pandas as pd
import numpy as np
import http.client, json, os

# --- AUTH ---
MY_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
MY_TOKEN = os.getenv('TELEGRAM_TOKEN')

# --- UPDATED HOLDINGS ---
MY_HOLDINGS = {
    "GPIL.NS": [230, 276.75, "2026-04-02", "Metals"],
    "LLOYDSME.NS": [109, 1446.56, "2026-04-07", "Metals"],
    "PREMIERENE.NS": [150, 943.30, "2026-04-07", "Infrastructure"],
    "NATCOPHARM.NS": [150, 1066.00, "2026-04-07", "Pharma"],
    "ADANIPOWER.NS": [1000, 163.36, "2026-04-07", "Energy"],
    "ASHOKLEY.NS": [1400, 173.00, "2026-04-09", "Auto"],
    "SAMMAANCAP.NS": [922, 154.89, "2026-04-13", "Finance"],
    "ORIENTELEC.NS": [600, 184.00, "2026-04-21", "Consumer Durables"],
    "AARTIIND.NS": [200, 455.00, "2026-04-22", "Chemicals"],
    "SKYGOLD.NS": [218, 417.00, "2026-04-22", "Consumer Jewelry"]
}

def send_msg(text):
    try:
        conn = http.client.HTTPSConnection("api.telegram.org")
        payload = json.dumps({"chat_id": MY_CHAT_ID, "text": text, "parse_mode": "Markdown"})
        headers = {"Content-Type": "application/json"}
        conn.request("POST", f"/bot{MY_TOKEN}/sendMessage", payload, headers)
        conn.close()
    except: pass

def run_advanced_guardian():
    tickers = list(MY_HOLDINGS.keys()) + ["^NSEI"]
    # Added auto_adjust=True and multi-threading check
    data = yf.download(tickers, period="1y", interval="1d", progress=False, auto_adjust=True)
    
    if data.empty:
        print("Error: No data downloaded from Yahoo Finance.")
        return

    nifty = data['Close']['^NSEI'].dropna()
    nifty_chg = ((nifty.iloc[-1] - nifty.iloc[-2]) / nifty.iloc[-2]) * 100

    results = []
    total_val, daily_gain_sum = 0, 0
    sector_values = {}

    for ticker, (qty, buy_p, buy_date, sector) in MY_HOLDINGS.items():
        try:
            df = data.xs(ticker, axis=1, level=1).dropna()
            if len(df) < 15: continue # Skip if not enough history
            
            close_p, prev_p = df['Close'].iloc[-1], df['Close'].iloc[-2]
            pnl_pct = ((close_p - buy_p) / buy_p) * 100
            
            std = df['Close'].pct_change().std()
            mult = 1.0 if pnl_pct > 30 else 1.5 if pnl_pct > 15 else (2.5 if std > 0.025 else 2.0)
            
            tr = pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift(1)).abs()], axis=1).max(axis=1)
            atr = tr.rolling(14).mean()
            
            # Filter by buy date
            valid_df = df[df.index >= buy_date]
            if valid_df.empty: valid_df = df.iloc[-5:] # Fallback
            
            ratchet = (valid_df['High'] - (mult * atr.reindex(valid_df.index))).cummax().iloc[-1]
            
            dist_to_stop = ((close_p - ratchet) / close_p) * 100
            total_val += (close_p * qty)
            daily_gain_sum += (close_p - prev_p) * qty
            sector_values[sector] = sector_values.get(sector, 0) + (close_p * qty)

            status_icon = "🚨 *CUT*" if close_p < ratchet else "✅"
            results.append({
                'text': f"*{ticker.replace('.NS','')}*: {pnl_pct:+.1f}% | {status_icon}\n_Stop: ₹{ratchet:.1f} ({dist_to_stop:.1f}% cushion)_\n\n",
                'is_cut': close_p < ratchet
            })
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            continue

    report = "🚀 *DYNAMIC PORTFOLIO REPORT*\n"
    report += f"Nifty 50: {nifty_chg:+.2f}% 🏛️\n\n"
    
    sorted_results = sorted(results, key=lambda x: x['is_cut'], reverse=True)
    for res in sorted_results: report += res['text']

    report += "🏗️ *SECTOR EXPOSURE*\n"
    for sec, val in sorted(sector_values.items(), key=lambda item: item[1], reverse=True):
        report += f"• {sec}: {(val/total_val)*100:.1f}%\n"

    port_daily_pct = (daily_gain_sum / (total_val - daily_gain_sum)) * 100 if total_val > daily_gain_sum else 0
    alpha = port_daily_pct - nifty_chg
    
    report += f"\n📊 *SUMMARY*\nTotal Value: ₹{total_val:,.0f}\n"
    report += f"Daily Gain: ₹{daily_gain_sum:,.0f} ({port_daily_pct:+.2f}%)\n"
    report += f"Alpha: {alpha:+.2f}% {'🔥' if alpha > 0 else '❄️'}"
    
    send_msg(report)

if __name__ == "__main__":
    run_advanced_guardian()
