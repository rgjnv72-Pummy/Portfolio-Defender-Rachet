import http.client, json, os, pandas as pd
import numpy as np
import yfinance as yf
from nselib import capital_market
from datetime import datetime, timedelta

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '').strip()
MANUAL_N500_CSV = 'ind_nifty500list.csv'

def send_telegram(text):
    if not TOKEN or not CHAT_ID: return
    conn = http.client.HTTPSConnection("api.telegram.org")
    payload = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    headers = {"Content-Type": "application/json"}
    try:
        conn.request("POST", f"/bot{TOKEN}/sendMessage", payload, headers)
        conn.getresponse()
    finally: conn.close()

def run_kronos(ticker):
    """Runs a 30-day Monte Carlo simulation for a specific ticker."""
    try:
        df = yf.download(ticker + ".NS", period="2y", progress=False, auto_adjust=True)
        if df.empty: return "N/A", "N/A"
        
        close = df['Close'].squeeze()
        cp = float(close.iloc[-1])
        rets = close.pct_change().dropna()
        vol = rets.std()
        # 60-day drift
        drift = (cp - close.iloc[-60]) / (close.iloc[-60] * 60)
        
        sims, days = 100, 30
        paths = [cp * np.cumprod(1 + np.random.normal(drift, vol, days)) for _ in range(sims)]
        conf = (sum(1 for p in paths if p[-1] > cp) / sims) * 100
        target = np.mean([p[-1] for p in paths])
        
        return round(conf, 1), round(target, 1)
    except:
        return "N/A", "N/A"

def run_scan():
    print("📡 Running Whale + Kronos Analysis...")
    # 1. Load Universe
    n500_df = pd.read_csv(MANUAL_N500_CSV)
    n500_list = n500_df['Symbol'].dropna().unique().tolist()

    # 2. Fetch Market Data
    df = None
    target_date = ""
    for i in range(1, 8):
        d = (datetime.now() - timedelta(days=i)).strftime('%d-%m-%Y')
        try:
            df = capital_market.bhav_copy_with_delivery(d)
            if df is not None and not df.empty:
                target_date = d
                break
        except: continue

    if df is None: return

    # 3. Process Columns
    df.columns = [str(c).strip().upper() for c in df.columns]
    sym_col = next((c for c in df.columns if 'SYMBOL' in c), 'SYMBOL')
    prc_col = next((c for c in df.columns if 'CLOSE' in c and 'PREV' not in c), 'CLOSE')
    prev_col = next((c for c in df.columns if 'PREV' in c), 'PREV_CLOSE')

    # 4. Identify Breakouts
    df = df[df[sym_col].isin(n500_list)].copy()
    close_p = pd.to_numeric(df[prc_col], errors='coerce')
    prev_p = pd.to_numeric(df[prev_col], errors='coerce')
    df['pct'] = ((close_p - prev_p) / prev_p) * 100
    
    top_10 = df.sort_values(by='pct', ascending=False).head(10)

    # 5. Run Kronos on Top 10
    msg = f"🤖 *KRONOS AI: 30-DAY FORECAST*\n"
    msg += f"Market Date: {target_date}\n━━━━━━━━━━━━━━━━━━━━\n"
    msg += "`Ticker      Conf%   Target   Gains`\n"

    for _, row in top_10.iterrows():
        sym = row[sym_col]
        conf, target = run_kronos(sym)
        indicator = "🔥" if conf != "N/A" and conf > 70 else "📈"
        
        msg += f"`{sym:<11} {conf:>5}% {target:>8}`  {indicator}\n"

    msg += "━━━━━━━━━━━━━━━━━━━━\n🎯 *Strategy:* Breakout + High Confidence."
    
    send_telegram(msg)
    print("✅ Full Report Sent.")

if __name__ == "__main__":
    run_scan()
