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
    print("📈 Finding Top Gainers...")
    symbols = [str(s).strip() + ".NS" for s in df_nse['Symbol'].dropna().unique()]
    data = yf.download(symbols, period="7d", interval="1d", group_by='ticker', threads=True, progress=False)
    
    perf = []
    close_data = data['Close']
    for ticker in symbols:
        try:
            if ticker not in close_data: continue
            h = close_data[ticker].dropna()
            if len(h) < 3: continue
            change = ((h.iloc[-1] - h.iloc[0]) / h.iloc[0]) * 100
            perf.append({'Ticker': ticker, 'Gains': change})
        except: continue
    return pd.DataFrame(perf).sort_values(by='Gains', ascending=False).head(count)['Ticker'].tolist()

def run_analysis(tickers):
    print("🚀 Running Kronos Simulation...")
    final_data = []
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="1y", progress=False)
            if df.empty: continue
            close = df['Close'].squeeze()
            cp = float(close.iloc[-1])
            rets = close.pct_change().dropna()
            vol, drift = rets.std(), (cp - close.iloc[-30]) / (close.iloc[-30] * 30)
            paths = [cp * np.cumprod(1 + np.random.normal(drift, vol, 30)) for _ in range(50)]
            conf = (sum(1 for p in paths if p[-1] > cp) / 50) * 100
            final_data.append({'T': ticker.replace('.NS',''), 'P': round(cp,1), 'C': round(conf,1), 'Tr': round(np.mean([p[-1] for p in paths]),1)})
        except: continue
    return sorted(final_data, key=lambda x: x['C'], reverse=True)

def send_telegram_text(results):
    token = os.getenv('TELEGRAM_TOKEN', '').strip()
    chat_id = os.getenv('CHAT_ID', '').strip()
    
    print(f"📡 Debug: Token Length={len(token)}, ChatID={chat_id}")

    if not token or not chat_id:
        print("❌ ERROR: Secrets not found. Check GitHub Repository Secrets.")
        return

    # Plain text message (No Markdown to avoid parsing errors)
    msg = "🤖 KRONOS WEEKLY TOP 10\n"
    msg += "-------------------------------\n"
    for item in results[:10]:
        msg += f"{item['T']}: Price {item['P']} | Conf {item['C']}% | Target {item['Tr']}\n"
    msg += "-------------------------------\n"
    msg += "NSE 500 Weekly Scanner"

    url = f"https://telegram.org{token}/sendMessage"
    try:
        r = requests.post(url, json={'chat_id': chat_id, 'text': msg}, timeout=20)
        print(f"📊 Response: {r.status_code}")
        if r.status_code != 200: print(f"❌ Error: {r.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    df_nse = get_local_nse_list()
    if df_nse is not None:
        top_20 = find_top_weekly_gainers(df_nse)
        final_results = run_analysis(top_20)
        if final_results:
            send_telegram_text(final_results)
