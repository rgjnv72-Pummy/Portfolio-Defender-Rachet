import http.client, json, os, pandas as pd
from nselib import capital_market
from niftystocks import ns
from datetime import datetime, timedelta

# --- CONFIG (Pulls from your Screenshot names) ---
TOKEN = os.getenv('TELEGRAM_TOKEN', '').strip()
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '').strip()

def send_telegram_direct(text):
    # This print helps us verify the secrets are reaching the script
    print(f"📡 Secret Check -> Token Len: {len(TOKEN)}, ChatID: {CHAT_ID}")
    
    if not TOKEN or not CHAT_ID:
        print("❌ ERROR: Secrets missing from GitHub Environment mapping.")
        return
    
    conn = http.client.HTTPSConnection("api.telegram.org")
    payload = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    headers = {"Content-Type": "application/json"}
    try:
        # Constructing the exact URL that worked in your Colab
        conn.request("POST", f"/bot{TOKEN}/sendMessage", payload, headers)
        res = conn.getresponse()
        print(f"📊 Telegram Status: {res.status} {res.reason}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")
    finally:
        conn.close()

def run_scan():
    print("📡 Fetching Market Data...")
    df = None
    target_date = ""
    # Try last 5 days to handle holidays
    for i in range(1, 6):
        d = (datetime.now() - timedelta(days=i)).strftime('%d-%m-%Y')
        try:
            df = capital_market.bhav_copy_with_delivery(d)
            if df is not None and not df.empty:
                target_date = d
                break
        except: continue

    if df is None:
        print("❌ Could not fetch NSE data.")
        return

    # Clean Columns
    df.columns = [c.strip().upper() for c in df.columns]
    n500 = ns.get_nifty500()
    df = df[df['SYMBOL'].isin(n500)].copy()

    # V4.0 Calculation
    df['pct'] = ((pd.to_numeric(df['CLOSE'], errors='coerce') - 
                  pd.to_numeric(df['PREV_CLOSE'], errors='coerce')) / 
                  pd.to_numeric(df['PREV_CLOSE'], errors='coerce')) * 100
    
    top_15 = df.sort_values(by='pct', ascending=False).head(15)

    # Format Message
    msg = f"🏆 *V4.0 BREAKOUTS ({target_date})*\n━━━━━━━━━━━━━━━━━━━━\n"
    for i, (_, row) in enumerate(top_15.iterrows(), 1):
        msg += f"{i}. *{row['SYMBOL']}* | {row['pct']:.1f}%\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n🎯 *Focus:* High volume breakouts."

    send_telegram_direct(msg)

if __name__ == "__main__":
    run_scan()
