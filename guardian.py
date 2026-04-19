import yfinance as yf
import pandas as pd
import numpy as np
import http.client, json, os

# --- AUTH FROM GITHUB SECRETS ---
MY_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
MY_TOKEN = os.getenv('TELEGRAM_TOKEN')

# --- YOUR HOLDINGS ---
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

def run_guardian():
    tickers = list(MY_HOLDINGS.keys()) + ["^NSEI"]
    data = yf.download(tickers, period="1y", interval="1d", progress=False, auto_adjust=True)
    
    nifty = data['Close']['^NSEI'].dropna()
    nifty_chg = ((nifty.iloc[-1] - nifty.iloc[-2]) / nifty.iloc[-2]) * 100

    report = f"🚀 *DAILY AUTOMATED REPORT*\nNifty 50: {nifty_chg:+.2f}%\n\n"
    total_val, sector_values = 0, {}

    for ticker, (qty, buy_p, buy_date, sector) in MY_HOLDINGS.items():
        try:
            df = data.xs(ticker, axis=1, level=1).dropna()
            close_p = df['Close'].iloc[-1]
            pnl = ((close_p - buy_p) / buy_p) * 100
            std = df['Close'].pct_change().std()
            mult = 1.0 if pnl > 30 else 1.5 if pnl > 15 else (2.5 if std > 0.025 else 2.0)
            atr = (pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift(1)).abs()], axis=1).max(axis=1)).rolling(14).mean()
            ratchet = (df[df.index >= buy_date]['High'] - (mult * atr[atr.index >= buy_date])).cummax().iloc[-1]
            
            curr_val = close_p * qty
            total_val += curr_val
            sector_values[sector] = sector_values.get(sector, 0) + curr_val

            status = "🚨 *CUT*" if close_p < ratchet else "✅ *HOLD*"
            report += f"*{ticker.replace('.NS','')}*: {pnl:+.1f}% | {status}\n"
        except: continue

    report += "\n🏗️ *SECTOR EXPOSURE*\n"
    for sec, val in sector_values.items():
        report += f"• {sec}: {(val/total_val)*100:.1f}%\n"

    send_msg(report)

if __name__ == "__main__":
    run_guardian()
