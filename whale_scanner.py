import pandas as pd
import yfinance as yf
import numpy as np
import os
import requests

# --- CONFIG ---
CSV_FILE = 'ind_nifty500list.csv'

def get_local_nse_list():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE, skipinitialspace=True)
    return None

def find_top_weekly_gainers(df_nse, count=20):
    print("📈 Scanning NSE 500...")
    symbols = [str(s).strip() + ".NS" for s in df_nse['Symbol'].dropna().unique()]
    data = yf.download(symbols, period="7d", interval="1d", progress=False)
    perf = []
    close_data = data['Close'] if 'Close' in data else data
    for ticker in symbols:
        try:
            if isinstance(close_data, pd.DataFrame) and ticker in close_data.columns:
                h = close_data[ticker].dropna()
                if len(h) < 3: continue
                change = ((h.iloc[-1] - h.iloc[0]) / h.iloc[0]) * 100
                perf.append({'Ticker': ticker, 'Gains': change})
        except: continue
    return pd.DataFrame(perf).sort_values(by='Gains', ascending=False).head(count)['Ticker'].tolist()

def run_analysis(tickers):
    print("🚀 Running Kronos Simulation...")
    results = []
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="1y", progress=False)
            if df.empty: continue
            close = df['Close'].iloc[:, 0] if len(df['Close'].shape) > 1 else df['Close']
            close = close.dropna()
            cp = float(close.iloc[-1])
            rets = close.pct_change().dropna()
            vol, lookback = rets.std(), min(30, len(close)-1)
            drift = (cp - close.iloc[-lookback]) / (close.iloc[-lookback] * lookback)
            paths = [cp * np.cumprod(1 + np.random.normal(drift, vol, 30)) for _ in range(50)]
            conf = (sum(1 for p in paths if p[-1] > cp) / 50) * 100
            results.append({'T': ticker.replace('.NS',''), 'P': round(cp,1), 'C': round(conf,1), 'Tr': round(np.mean([p[-1] for p in paths]),1)})
        except: continue
    return sorted(results, key=lambda x: x['C'], reverse=True)

def send_telegram_text(results):
    token = os.getenv('TELEGRAM_TOKEN', '').strip()
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
    
    print(f"📡 Secret Check -> Token Len: {len(token)}, ChatID: {chat_id}")

    if not token or not chat_id:
        print("❌ ERROR: Secrets missing.")
        return

    msg = "🤖 KRONOS WEEKLY TOP 10\n"
    for item in results[:10]:
        msg += f"{item['T']}: {item['P']} | Conf {item['C']}% | Target {item['Tr']}\n"

    # ATTEMPTING DIRECT URL STRING CONCATENATION
    # If this fails with telegram.org error, your SECRET is incorrect.
    url = "https://telegram.org" + token + "/sendMessage"
    
    try:
        r = requests.post(url, json={'chat_id': chat_id, 'text': msg}, timeout=25)
        print(f"📊 Status: {r.status_code}")
        if r.status_code == 200:
            print("✅ SUCCESS!")
        else:
            print(f"❌ Detail: {r.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    df_nse = get_local_nse_list()
    if df_nse is not None:
        selected = find_top_weekly_gainers(df_nse)
        if selected:
            final_res = run_analysis(selected)
            send_telegram_text(final_res)
