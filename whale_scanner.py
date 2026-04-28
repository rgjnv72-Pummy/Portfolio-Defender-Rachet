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

def get_historical_stats(symbol):
    delivery_data, volume_data = [], []
    today_vol, days_found = 0, 0
    for i in range(1, 15):
        d = (datetime.now() - timedelta(days=i)).strftime('%d-%m-%Y')
        try:
            df = capital_market.bhav_copy_with_delivery(d)
            if df is not None and not df.empty:
                df.columns = [str(c).strip().upper() for c in df.columns]
                row = df[df['SYMBOL'] == symbol]
                if not row.empty:
                    del_col = next((c for c in df.columns if 'DELIV' in c and 'QTY' not in c), None)
                    vol_col = next((c for c in df.columns if 'TOTTRDQTY' in c or 'VOLUME' in c), None)
                    if del_col: delivery_data.append(pd.to_numeric(row[del_col].iloc[0], errors='coerce'))
                    if vol_col:
                        v = pd.to_numeric(row[vol_col].iloc[0], errors='coerce')
                        if days_found == 0: today_vol = v
                        volume_data.append(v)
                    days_found += 1
            if days_found >= 10: break
        except: continue
    
    d_avg = round(sum(delivery_data[:5])/5, 1) if len(delivery_data) >= 5 else "N/A"
    v_avg = sum(volume_data[1:11])/len(volume_data[1:11]) if len(volume_data) > 1 else 0
    vol_x = round(today_vol / v_avg, 1) if v_avg > 0 else 1.0
    return d_avg, vol_x

def run_kronos(ticker):
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
    n500_list = pd.read_csv(MANUAL_N500_CSV)['Symbol'].dropna().unique().tolist()
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
    df_latest = df_latest[df_latest['SYMBOL'].isin(n500_list)].copy()
    df_latest['pct'] = ((pd.to_numeric(df_latest['CLOSE'], errors='coerce') - pd.to_numeric(df_latest['PREV_CLOSE'], errors='coerce')) / pd.to_numeric(df_latest['PREV_CLOSE'], errors='coerce')) * 100
    top_10 = df_latest.sort_values(by='pct', ascending=False).head(10)

    msg = f"🐋 *WHALE WEEKLY SCAN ({target_date})*\n━━━━━━━━━━━━━━━━━━━━\n"
    msg += "`Ticker      D-Avg  Vol-X  Upside`\n"
    tv_list = []

    for _, row in top_10.iterrows():
        sym = row['SYMBOL']
        d_avg, vol_x = get_historical_stats(sym)
        conf, upside = run_kronos(sym)
        tv_list.append(f"NSE:{sym}")
        
        indicator = "🔥" if (isinstance(d_avg, float) and d_avg > 45) and vol_x > 1.5 and (conf != "N/A" and conf > 70) else "📈"
        msg += f"`{sym:<11} {str(d_avg)+'%':>5}  {str(vol_x)+'x':>5}  {upside:>+5}%` {indicator}\n"

    msg += "━━━━━━━━━━━━━━━━━━━━\n📋 *TRADINGVIEW WATCHLIST:*\n"
    msg += f"`{','.join(tv_list)}`"
    
    send_telegram(msg)

if __name__ == "__main__":
    run_scan()
