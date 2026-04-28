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

    # 3. Process
    df.columns = [str(c).strip().upper() for c in df.columns]
    sym_col = next((c for c in df.columns if 'SYMBOL' in c), None)
    
    df = df[df[sym_col].isin(n500_list)].copy()
    df['pct'] = ((pd.to_numeric(df['CLOSE'], errors='coerce') - 
                  pd.to_numeric(df['PREV_CLOSE'], errors='coerce')) / 
                  pd.to_numeric(df['PREV_CLOSE'], errors='coerce')) * 100
    
    top_10 = df.sort_values(by='pct', ascending=False).head(10)

    # 4. Message
    msg = f"🏆 *V4.0 BREAKOUTS ({target_date})*\n━━━━━━━━━━━━━━━━━━━━\n"
    for i, (_, row) in enumerate(top_10.iterrows(), 1):
        msg += f"{i}. *{row[sym_col]}* | {row['pct']:.1f}%\n"
    
    send_telegram(msg)
    print("✅ Success!")

if __name__ == "__main__":
    run_scan()
