import pandas as pd
import yfinance as yf
import numpy as np
import os
import requests

# --- CONFIGURATION ---
CSV_FILE = 'ind_nifty500list.csv'

def get_local_nse_list():
    if os.path.exists(CSV_FILE):
        print(f"✅ Found {CSV_FILE}")
        return pd.read_csv(CSV_FILE, skipinitialspace=True)
    print("❌ CSV File Missing in Repo")
    return None

def find_top_weekly_gainers(df_nse, count=20):
    print(f"📈 Finding Top {count} Weekly Gainers...")
    symbols = [str(s).strip() + ".NS" for s in df_nse['Symbol'].dropna().unique()]
    
    # Simple download for performance check
    data = yf.download(symbols, period="7d", interval="1d", progress=False)
    
    perf = []
    # Handle both single and multi-index DataFrames from yfinance
    close_data = data['Close']
    
    for ticker in symbols:
        try:
            if ticker not in close_data: continue
            h = close_data[ticker].dropna()
            if len(h) < 3: continue
            
            # (Latest Price - Price 5 sessions ago) / Price 5 sessions ago
            start_price = h.iloc[0]
            end_price = h.iloc[-1]
            change = ((end_price - start_price) / start_price) * 100
            perf.append({'Ticker': ticker, 'Gains': change})
        except: continue
        
    return pd.DataFrame(perf).sort_values(by='Gains', ascending=False).head(count)['Ticker'].tolist()

def run_analysis(tickers):
    print("🚀 Running Kronos Simulation (30-Day Horizon)...")
    final_data = []
    
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="1y", progress=False)
            if df.empty: continue
            
            close = df['Close'].squeeze()
            cp = float(close.iloc[-1])
            
            # Simulation Parameters
            rets = close.pct_change().dropna()
            vol = rets.std()
            lookback = 30 if len(close) > 30 else len(close) - 1
            drift = (cp - close.iloc[-lookback]) / (close.iloc[-lookback] * lookback)
            
            # 50 Monte Carlo Paths
            paths = [cp * np.cumprod(1 + np.random.normal(drift, vol, 30)) for _ in range(50)]
            conf = (sum(1 for p in paths if p[-1] > cp) / 50) * 100
            target = np.mean([p[-1] for p in paths])
            
            final_data.append({
                'T': ticker.replace('.NS', ''),
                'P': round(cp, 1),
                'C': round(conf, 1),
                'Tr': round(target, 1)
            })
        except: continue

    return sorted(final_data, key=lambda x: x['C'], reverse=True)

def send_telegram_text(results):
    token = os.getenv('TELEGRAM_TOKEN', '').strip()
    chat_id = os.getenv('CHAT_ID', '').strip()
    
    # Debug info for GitHub Logs
    print(f"📡 Secret Check: Token Length={len(token)}, ChatID={chat_id}")

    if not token or not chat_id:
        print("❌ CRITICAL: Secrets were not passed to Python!")
        return

    msg = "🤖 **Kronos Weekly Top 10**\n"
    msg += "`-------------------------------` \n"
    msg += "`Ticker      Price    Conf%  Target`\n"
    
    for item in results[:10]:
        indicator = "🔥" if item['C'] > 75 else "📈"
        msg += f"`{item['T']:<11} {item['P']:<8} {item['C']:>4}%` → **{item['Tr']}** {indicator}\n"
    
    msg += "`-------------------------------` \n"
    msg += "📅 *Selection: Top Gainers (NSE 500)*"

    # Precise URL construction
    url = f"https://telegram.org{token}/sendMessage"
    
    try:
        r = requests.post(url, json={'chat_id': chat_id, 'text': msg, 'parse_mode': 'Markdown'}, timeout=20)
        if r.status_code == 200:
            print("✅ Telegram Message Sent!")
        else:
            print(f"❌ Telegram Error {r.status_code}: {r.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    nse_data = get_local_nse_list()
    if nse_data is not None:
        top_list = find_top_weekly_gainers(nse_data)
        if top_list:
            analysis_results = run_analysis(top_list)
            send_telegram_text(analysis_results)
        else:
            print("⚠️ No gainers found to analyze.")
