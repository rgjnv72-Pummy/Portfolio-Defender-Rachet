import pandas as pd
import yfinance as yf
import numpy as np
import os
import requests

# --- CONFIG ---
CSV_FILE = 'ind_nifty500list.csv'

def get_local_nse_list():
    if os.path.exists(CSV_FILE):
        print(f"✅ Found {CSV_FILE}")
        return pd.read_csv(CSV_FILE, skipinitialspace=True)
    print("❌ CSV File Missing")
    return None

def find_top_weekly_gainers(df_nse, count=20):
    print(f"📈 Finding Top {count} Weekly Gainers...")
    symbols = [str(s).strip() + ".NS" for s in df_nse['Symbol'].dropna().unique()]
    
    # Download 7 days of data
    data = yf.download(symbols, period="7d", interval="1d", progress=False)
    
    perf = []
    # yfinance 0.2.x+ returns a MultiIndex. We must handle both formats.
    close_data = data['Close'] if 'Close' in data else data
    
    for ticker in symbols:
        try:
            if isinstance(close_data, pd.DataFrame) and ticker in close_data.columns:
                h = close_data[ticker].dropna()
            else:
                continue
                
            if len(h) < 3: continue
            
            # Weekly Performance
            change = ((h.iloc[-1] - h.iloc[0]) / h.iloc[0]) * 100
            perf.append({'Ticker': ticker, 'Gains': change})
        except: continue
        
    return pd.DataFrame(perf).sort_values(by='Gains', ascending=False).head(count)['Ticker'].tolist()

def run_analysis(tickers):
    print("🚀 Running Kronos Simulation (30-Day Forecast)...")
    results = []
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="1y", progress=False)
            if df.empty: continue
            
            # Squeeze to handle potential multi-index or single column DF
            close = df['Close'].iloc[:, 0] if len(df['Close'].shape) > 1 else df['Close']
            close = close.dropna()
            
            cp = float(close.iloc[-1])
            rets = close.pct_change().dropna()
            vol = rets.std()
            
            # Drift calculation (last 30 days)
            lookback = min(30, len(close)-1)
            drift = (cp - close.iloc[-lookback]) / (close.iloc[-lookback] * lookback)
            
            # 50 Monte Carlo Paths
            paths = [cp * np.cumprod(1 + np.random.normal(drift, vol, 30)) for _ in range(50)]
            conf = (sum(1 for p in paths if p[-1] > cp) / 50) * 100
            target = np.mean([p[-1] for p in paths])
            
            results.append({
                'T': ticker.replace('.NS',''), 
                'P': round(cp,1), 
                'C': round(conf,1), 
                'Tr': round(target,1)
            })
        except: continue
    return sorted(results, key=lambda x: x['C'], reverse=True)

def send_telegram_text(results):
    # Ensure these names match the env: section in your nse_scanner.yml
    token = os.getenv('TELEGRAM_TOKEN', '').strip()
    chat_id = os.getenv('CHAT_ID', '').strip()
    
    print(f"📡 Debug: Token Length={len(token)}, ChatID={chat_id}")

    if not token or not chat_id:
        print("❌ ERROR: Secrets not received. Check your YML 'env' section.")
        return

    msg = "🤖 **Kronos Weekly Top 10**\n"
    msg += "-------------------------------\n"
    msg += "`Ticker      Price    Conf%  Target`\n"
    for item in results[:10]:
        indicator = "🔥" if item['C'] > 75 else "📈"
        msg += f"`{item['T']:<11} {item['P']:<8} {item['C']:>4}%` → **{item['Tr']}** {indicator}\n"
    
    url = f"https://telegram.org{token}/sendMessage"
    try:
        r = requests.post(url, json={'chat_id': chat_id, 'text': msg, 'parse_mode': 'Markdown'}, timeout=20)
        print(f"📊 Telegram Status: {r.status_code}")
        if r.status_code != 200:
            print(f"❌ Detail: {r.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    df_nse = get_local_nse_list()
    if df_nse is not None:
        top_list = find_top_weekly_gainers(df_nse)
        if top_list:
            final_res = run_analysis(top_list)
            send_telegram_text(final_res)
        else:
            print("⚠️ No gainers found to analyze.")
