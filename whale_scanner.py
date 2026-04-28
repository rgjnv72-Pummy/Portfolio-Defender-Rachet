import http.client, json, os, pandas as pd, numpy as np, yfinance as yf
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

def get_5day_delivery_avg(symbol):
    """Calculates the average delivery % for the last 5 trading days."""
    delivery_data = []
    days_checked = 0
    # Scan back up to 12 days to find 5 active trading sessions
    for i in range(1, 12):
        d = (datetime.now() - timedelta(days=i)).strftime('%d-%m-%Y')
        try:
            df = capital_market.bhav_copy_with_delivery(d)
            if df is not None and not df.empty:
                df.columns = [str(c).strip().upper() for c in df.columns]
                sym_col = next((c for c in df.columns if 'SYMBOL' in c), 'SYMBOL')
                del_col = next((c for c in df.columns if 'DELIV' in c and 'QTY' not in c), None)
                
                if del_col:
                    row = df[df[sym_col] == symbol]
                    if not row.empty:
                        val = pd.to_numeric(row[del_col].iloc[0], errors='coerce')
                        if not np.isnan(val):
                            delivery_data.append(val)
                            days_checked += 1
            if days_checked >= 5: break
        except: continue
    return round(sum(delivery_data)/len(delivery_data), 1) if delivery_data else "N/A"

def run_kronos_forecast(ticker):
    """Calculates 30-day Upside % and Confidence."""
    try:
        df = yf.download(ticker + ".NS", period="2y", progress=False, auto_adjust=True)
        if df.empty: return "N/A", "N/A"
        close = df['Close'].squeeze()
        cp = float(close.iloc[-1])
        vol, drift = close.pct_change().dropna().std(), (cp - close.iloc[-60]) / (close.iloc[-60] * 60)
        paths = [cp * np.cumprod(1 + np.random.normal(drift, vol, 30)) for _ in range(100)]
        conf = (sum(1 for p in paths if p[-1] > cp) / 100) * 100
        upside = ((np.mean([p[-1] for p in paths]) - cp) / cp) * 100
        return round(conf, 1), round(upside, 1)
    except: return "N/A", "N/A"

def run_scan():
    print("🚀 Running Institutional Whale & Kronos Scan...")
    n500_list = pd.read_csv(MANUAL_N500_CSV)['Symbol'].dropna().unique().tolist()
    
    # Get latest data for breakout detection
    df_latest = None
    target_date = ""
    for i in range(1, 8):
        d = (datetime.now() - timedelta(days=i)).strftime('%d-%m-%Y')
        try:
            df_latest = capital_market.bhav_copy_with_delivery(d)
            if df_latest is not None and not df_latest.empty:
                target_date = d; break
        except: continue
    
    if df_latest is None: return

    df_latest.columns = [str(c).strip().upper() for c in df_latest.columns]
    sym_col = next((c for c in df_latest.columns if 'SYMBOL' in c), 'SYMBOL')
    prc_col = next((c for c in df_latest.columns if 'CLOSE' in c and 'PREV' not in c), 'CLOSE')
    prev_col = next((c for c in df_latest.columns if 'PREV' in c), 'PREV_CLOSE')

    # Filter & Sort
    df_latest = df_latest[df_latest[sym_col].isin(n500_list)].copy()
    df_latest['pct'] = ((pd.to_numeric(df_latest[prc_col], errors='coerce') - 
                         pd.to_numeric(df_latest[prev_col], errors='coerce')) / 
                         pd.to_numeric(df_latest[prev_col], errors='coerce')) * 100
    
    top_10 = df_latest.sort_values(by='pct', ascending=False).head(10)

    # Build Report
    msg = f"🐋 *WHALE & KRONOS FORECAST ({target_date})*\n━━━━━━━━━━━━━━━━━━━━\n"
    msg += "`Ticker      D-Avg  Upside  Conf%`\n"

    for _, row in top_10.iterrows():
        sym = row[sym_col]
        d_avg = get_5day_delivery_avg(sym)
        conf, upside = run_kronos_forecast(sym)
        
        # Indicator: High delivery avg + High confidence
        indicator = "🔥" if (isinstance(d_avg, float) and d_avg > 45) and (conf != "N/A" and conf > 70) else "📈"
        msg += f"`{sym:<11} {str(d_avg)+'%':>5}  {upside:>+5}%  {conf:>5}%` {indicator}\n"

    msg += "━━━━━━━━━━━━━━━━━━━━\n🎯 *Focus:* High 5-Day Avg Del (>45%) + Conf."
    send_telegram(msg)
    print("✅ Analysis Sent.")

if __name__ == "__main__":
    run_scan()
