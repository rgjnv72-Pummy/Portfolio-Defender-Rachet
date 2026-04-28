import http.client, json, os, pandas as pd
from nselib import capital_market
from datetime import datetime, timedelta

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '').strip()
MANUAL_N500_CSV = 'ind_nifty500list.csv'

def send_telegram(text):
    if not TOKEN or not CHAT_ID:
        print("❌ Secrets missing.")
        return
    conn = http.client.HTTPSConnection("api.telegram.org")
    payload = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    headers = {"Content-Type": "application/json"}
    try:
        conn.request("POST", f"/bot{TOKEN}/sendMessage", payload, headers)
        res = conn.getresponse()
        print(f"📊 Telegram Status: {res.status}")
    finally:
        conn.close()

def run_scan():
    # 1. Load Manual Nifty 500
    if not os.path.exists(MANUAL_N500_CSV):
        print(f"❌ Error: {MANUAL_N500_CSV} missing.")
        return
    
    n500_df = pd.read_csv(MANUAL_N500_CSV)
    n500_list = n500_df['Symbol'].dropna().unique().tolist()
    print(f"✅ Loaded {len(n500_list)} stocks from manual CSV.")

    # 2. Fetch Price Data
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

    if df is None:
        print("❌ No NSE data found.")
        return

    # --- SMART COLUMN DETECTION ---
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    # Map possible names to standard 'SYMBOL', 'CLOSE', and 'PREV_CLOSE'
    sym_col = next((c for c in df.columns if 'SYMBOL' in c or 'TICKER' in c), None)
    prc_col = next((c for c in df.columns if 'CLOSE' in c and 'PREV' not in c), None)
    prev_col = next((c for c in df.columns if 'PREV' in c and 'CLOSE' in c), None)

    if not sym_col or not prc_col or not prev_col:
        print(f"❌ Column mismatch. Found: {df.columns.tolist()}")
        return

    # 3. Process
    df = df[df[sym_col].isin(n500_list)].copy()
    
    # Convert to numeric
    close_prc = pd.to_numeric(df[prc_col], errors='coerce')
    prev_prc = pd.to_numeric(df[prev_col], errors='coerce')
    
    df['pct'] = ((close_prc - prev_prc) / prev_prc) * 100
    
    top_10 = df.sort_values(by='pct', ascending=False).head(10)

    # 4. Message
    msg = f"🏆 *V4.0 BREAKOUTS ({target_date})*\n━━━━━━━━━━━━━━━━━━━━\n"
    for i, (_, row) in enumerate(top_10.iterrows(), 1):
        msg += f"{i}. *{row[sym_col]}* | {row['pct']:.1f}%\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n🎯 *Focus:* NSE 500 Breakouts."

    send_telegram(msg)
    print(f"✅ Success! Report sent for {target_date}")

if __name__ == "__main__":
    run_scan()
