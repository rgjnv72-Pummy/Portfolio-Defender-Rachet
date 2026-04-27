import pandas as pd
import yfinance as yf
import numpy as np
import os
import requests

# --- CONFIGURATION ---
CSV_FILE = 'ind_nifty500list.csv'

def get_local_nse_list():
    """Reads the manually uploaded NSE 500 list."""
    if os.path.exists(CSV_FILE):
        print(f"✅ Found {CSV_FILE}")
        return pd.read_csv(CSV_FILE, skipinitialspace=True)
    print("❌ ERROR: CSV File Missing in Repository")
    return None

def find_top_weekly_gainers(df_nse, count=20):
    """Identifies top 20 performers over the last 5 trading sessions."""
    print(f"📈 Scanning NSE 500 for Top {count} Weekly Gainers...")
    symbols = [str(s).strip() + ".NS" for s in df_nse['Symbol'].dropna().unique()]
    
    # Download 7 days of data to ensure we have a full trading week
    data = yf.download(symbols, period="7d", interval="1d", progress=False)
    
    perf = []
    # Handle yfinance multi-index data structure
    close_data = data['Close'] if 'Close' in data else data
    
    for ticker in symbols:
        try:
            if isinstance(close_data, pd.DataFrame) and ticker in close_data.columns:
                h = close_data[ticker].dropna()
                if len(h) < 3: continue
                
                # Performance calculation
                start_p = h.iloc[0]
                end_p = h.iloc[-1]
                change = ((end_p - start_p) / start_p) * 100
                perf.append({'Ticker': ticker, 'Gains': change})
        except: continue
        
    df_perf = pd.DataFrame(perf).sort_values(by='Gains', ascending=False)
    selected = df_perf.head(count)['Ticker'].tolist()
    print(f"✅ Top Gainers: {selected}")
    return selected

def run_analysis(tickers):
    """Runs Kronos Monte Carlo Simulation for a 30-day forecast."""
    print("🚀 Running Kronos Simulation (30-Day Horizon)...")
    results = []
    
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="1y", progress=False)
            if df.empty: continue
            
            # Squeeze to handle single-column dataframes
            close = df['Close'].iloc[:, 0] if len(df['Close'].shape) > 1 else df['Close']
            close = close.dropna()
            
            cp = float(close.iloc[-1])
            rets = close.pct_change().dropna()
            vol = rets.std()
            
            # Drift calculation based on last 30 trading days
            lookback = min(30, len(close)-1)
            drift = (cp - close.iloc[-lookback]) / (close.iloc[-lookback] * lookback)
            
            # 50 Monte Carlo simulation paths
            paths = [cp * np.cumprod(1 + np.random.normal(drift, vol, 30)) for _ in range(50)]
            conf = (sum(1 for p in paths if p[-1] > cp) / 50) * 100
            target = np.mean([p[-1] for p in paths])
            
            results.append({
                'T': ticker.replace('.NS', ''),
                'P': round(cp, 1),
                'C': round(conf, 1),
                'Tr': round(target, 1)
            })
        except: continue

    # Sort results by highest confidence probability
    return sorted(results, key=lambda x: x['C'], reverse=True)

def send_telegram_text(results):
    """Sends the analysis report to Telegram using Guardian credentials."""
    # EXACT names from your working guardian.py workflow
    token = os.getenv('TELEGRAM_TOKEN', '').strip()
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
    
    print(f"📡 Secret Check -> Token Len: {len(token)}, ChatID: {chat_id}")

    if not token or not chat_id:
        print("❌ CRITICAL: Secrets not received. Ensure YML uses TELEGRAM_CHAT_ID.")
        return

    # Build formatted message
    msg = "🤖 **Kronos Weekly Top 10**\n"
    msg += "`-------------------------------` \n"
    msg += "`Ticker      Price    Conf%  Target`\n"
    
    for item in results[:10]:
        indicator = "🔥" if item['C'] > 75 else "📈"
        msg += f"`{item['T']:<11} {item['P']:<8} {item['C']:>4}%` → **{item['Tr']}** {indicator}\n"
    
    msg += "`-------------------------------` \n"
    msg += "📅 *Selection: Top Weekly Gainers (NSE 500)*"

    url = f"https://telegram.org{token}/sendMessage"
    
    try:
        r = requests.post(url, json={'chat_id': chat_id, 'text': msg, 'parse_mode': 'Markdown'}, timeout=20)
        print(f"📊 Telegram Status: {r.status_code}")
        if r.status_code != 200:
            print(f"❌ Error Detail: {r.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    # 1. Load List
    nse_data = get_local_nse_list()
    
    if nse_data is not None:
        # 2. Filter Top 20 Gainers
        top_list = find_top_weekly_gainers(nse_data)
        
        if top_list:
            # 3. Analyze with Kronos
            final_res = run_analysis(top_list)
            
            # 4. Report to Telegram
            send_telegram_text(final_res)
        else:
            print("⚠️ No valid gainers found to analyze.")
