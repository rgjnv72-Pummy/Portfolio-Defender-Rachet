import os, json, http.client, numpy as np, pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# --- AUTH ---
MY_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
MY_TOKEN = os.getenv('TELEGRAM_TOKEN')

def send_msg(text):
    try:
        conn = http.client.HTTPSConnection("api.telegram.org")
        payload = json.dumps({"chat_id": MY_CHAT_ID, "text": text, "parse_mode": "Markdown"})
        headers = {"Content-Type": "application/json"}
        conn.request("POST", f"/bot{MY_TOKEN}/sendMessage", payload, headers)
        conn.getresponse()
        conn.close()
    except: pass

# --- INDICATOR MATH ---
def get_hma(series, length):
    def wma(s, p):
        weights = np.arange(1, p + 1)
        return s.rolling(p).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_len, sqrt_len = int(length/2), int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_len) - wma(series, length)
    return wma(raw_hma, sqrt_len)

def get_rsi(series, length=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

def get_ema(series, length):
    return series.ewm(span=length, adjust=False).mean()

def get_atr(df, length=14):
    h, l, c = df['High'], df['Low'], df['Close']
    tr = pd.concat([h-l, abs(h-c.shift(1)), abs(l-c.shift(1))], axis=1).max(axis=1)
    return tr.rolling(window=length).mean()

def scan_master_confluence(symbol):
    try:
        clean_s = str(symbol).strip().replace(".NS", "")
        df = yf.download(f"{clean_s}.NS", period="2y", progress=False, auto_adjust=True, threads=False)
        if df is None or len(df) < 250: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        c, h, l = df['Close'].astype(float), df['High'].astype(float), df['Low'].astype(float)
        
        drift = (((c.iloc[-1]/c.iloc[-250])-1)/250 * 0.7) + (((c.iloc[-1]/c.iloc[-20])-1)/20 * 0.3)
        upside = ((c.iloc[-1] * (1 + (drift * 30)) - c.iloc[-1]) / c.iloc[-1]) * 100
        
        # CORE FILTER (Set wide for testing)
        if not (1.0 < upside < 40): return None

        score, signals = 0, []
        sma20, std20 = c.rolling(20).mean(), c.rolling(20).std()
        atr20 = get_atr(df, 20)

        if (sma20 + (2*std20)).iloc[-1] < (sma20 + (1.5*atr20)).iloc[-1]: score += 1; signals.append("SQZ")
        if ((std20 * 4) / (sma20 + 1e-9) * 100).iloc[-1] <= ((std20 * 4) / (sma20 + 1e-9) * 100).tail(21).min(): score += 1; signals.append("ULT")
        if get_hma(c, 55).iloc[-1] > get_hma(c, 55).iloc[-2]: score += 1; signals.append("HUL")
        if get_rsi(c, 14).iloc[-1] > 55: score += 1; signals.append("RSI")

        st_p, lt_p = [3, 5, 8, 10, 12, 15], [30, 35, 40, 45, 50, 60]
        if pd.concat([get_ema(c, p) for p in st_p], axis=1).min(axis=1).iloc[-1] > pd.concat([get_ema(c, p) for p in lt_p], axis=1).max(axis=1).iloc[-1]:
            score += 1; signals.append("GUP")

        vam_votes, vam_lens, mults = 0, [10, 20, 30, 40, 50], [1.2, 1.5, 2.0, 2.5, 3.0]
        for v_len, m in zip(vam_lens, mults):
            if c.iloc[-1] > (c.rolling(v_len).mean().iloc[-1] + (get_atr(df, v_len).iloc[-1] * m)): vam_votes += 1
        if vam_votes >= 3: score += 1; signals.append("VAM")

        return {'Symbol': clean_s, 'Score': score, 'Upside%': round(upside, 2), 'Signals': "+".join(signals)}
    except: return None

def run_master_scan():
    # TEST CONNECTION
    send_msg("🛰 *KRONOS:* Connection verified. Starting Nifty 500 Scan...")

    CSV_NAME = "ind_nifty500list.csv"
    try:
        # Standard NSE files sometimes need header=0
        df_csv = pd.read_csv(CSV_NAME)
        # Find symbol column: Check for 'Symbol' or use 3rd column
        col = next((c for c in df_csv.columns if 'symbol' in c.lower()), df_csv.columns[2])
        tickers = df_csv[col].dropna().unique().tolist()
    except:
        send_msg("❌ *Error:* Could not read CSV column logic.")
        return

    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        for res in executor.map(scan_master_confluence, tickers):
            if res: results.append(res)

    if not results:
        send_msg("📡 *KRONOS:* Scan complete. 0 stocks met confluence criteria.")
        return
    
    final_df = pd.DataFrame(results).sort_values(by=['Score', 'Upside%'], ascending=False).head(25)
    
    msg = f"🏆 *KRONOS MASTER:* `{CSV_NAME}`\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for _, r in final_df.head(20).iterrows():
        icon = "💎" if r['Score'] >= 4 else "🔥"
        msg += f"{icon} `{r['Symbol']}`: *Score {r['Score']}* | {r['Upside%']}% Up\n"
    
    tv_list = ",".join([f"NSE:{s}" for s in final_df['Symbol']])
    msg += f"\n📺 *TV LIST*\n`{tv_list}`"
    send_msg(msg)

if __name__ == "__main__":
    run_master_scan()
