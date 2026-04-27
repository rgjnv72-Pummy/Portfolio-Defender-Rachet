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
    
    # Download 1 week of data
    data = yf.download(symbols, period="7d", interval="1d", progress=False)
    
    perf = []
    for ticker in symbols:
        try:
            # Handle yfinance Multi-Index correctly
            if isinstance(data.columns, pd.MultiIndex):
                h = data['Close'][ticker].dropna()
            else:
                h = data['Close'].dropna()
                
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
            
            # Ensure we get a flat series for Close
            close = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
            close = close.dropna()
            
            cp = float(close.iloc[-1])
            rets = close.pct_change().dropna()
            vol = rets.std()
            
            lookback = 30 if len(close) > 30 else len(close) - 1
            drift = (cp - close.iloc[-lookback]) / (close.iloc[-lookback] * lookback)
            
            paths = [cp * np.cumprod(1 + np.random.normal(drift, vol, 30)) for _ in range(50)]
            conf = (sum(1 for p in paths if p[-1] > cp) / 50) * 100
            target = np.mean([p[-1] for p in paths])
            
            final_data.append({
                'T': ticker.replace('.NS',''), 
                'P': round(cp,1), 
                'C': round(conf,1), 
                'Tr': round(target,1)
            })
        except: continue
    return sorted(final_data, key=lambda x: x['C'], reverse=True)

def send_telegram_text(results):
    token = os.getenv('TELEGRAM_TOKEN', '').strip()
    chat_id = os.getenv('CHAT_ID', '').strip()
    
    print(f"📡 Debug: Token Len={len(token)}, ChatID={chat_id}")

    if not token or not chat_id:
        print("❌ ERROR: Secrets not found.")
        return

    msg = "🤖 KRONOS WEEKLY TOP 10\n"
    msg += "-------------------------------\n"
    for item in results[:10]:
        msg += f"{item['T']}: {item['P']} | Conf {item['C']}% | Target {item['Tr']}\n"
    msg += "-------------------------------\n"
    msg += "NSE 500 Weekly Scanner"

    url = f"https://telegram.org{token}/sendMessage"
    try:
        r = requests.post(url, json={'chat_id': chat_id, 'text': msg}, timeout=20)
        print(f"📊 Status: {r.status_code}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    df_nse = get_local_nse_list()
    if df_nse is not None:
        top_list = find_top_weekly_gainers(df_nse)
        if top_list:
            res = run_analysis(top_list)
            send_telegram_text(res)
