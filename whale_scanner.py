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
    print("❌ CSV File Missing")
    return None

def find_top_weekly_gainers(df_nse, count=20):
    print(f"📈 Finding Top {count} Gainers...")
    symbols = [str(s).strip() + ".NS" for s in df_nse['Symbol'].dropna().unique()]
    # Fetch data for weekly change
    data = yf.download(symbols, period="10d", interval="1d", group_by='ticker', threads=True, progress=False)
    
    perf = []
    for ticker in symbols:
        try:
            h = data[ticker]['Close'].dropna()
            if len(h) < 5: continue
            change = ((h.iloc[-1] - h.iloc[-5]) / h.iloc[-5]) * 100
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
            
            close_series = df['Close'].squeeze()
            cp = float(close_series.iloc[-1])
            
            rets = close_series.pct_change().dropna()
            vol = rets.std()
            lookback = 60 if len(close_series) > 60 else len(close_series) - 1
            drift = (cp - close_series.iloc[-lookback]) / (close_series.iloc[-lookback] * lookback)
            
            # Kronos Simulation (50 paths)
            paths = [cp * np.cumprod(1 + np.random.normal(drift, vol, 30)) for _ in range(50)]
            conf = (sum(1 for p in paths if p[-1] > cp) / 50) * 100
            target = np.mean([p[-1] for p in paths])
            
            final_data.append({
                'Ticker': ticker.replace('.NS', ''),
                'Price': round(cp, 1),
                'Conf': round(conf, 1),
                'Target': round(target, 1)
            })
        except: continue

    return sorted(final_data, key=lambda x: x['Conf'], reverse=True)

def send_telegram_text(results):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not results:
        msg = "⚠️ **Scanner Warning**: No data generated today."
    else:
        msg = "🤖 **Kronos Top 10 Forecast**\n"
        msg += "Selection: Top Weekly Gainers (NSE 500)\n"
        msg += "----------------------------------\n"
        msg += f"{'Ticker':<12} {'Price':<8} {'Conf%':<6} {'Target'}\n"
        
        for item in results[:10]:
            indicator = "🔥" if item['Conf'] > 70 else "📈"
            msg += f"`{item['Ticker']:<12} {item['Price']:<8} {item['Conf']:>5}%` → **{item['Target']}** {indicator}\n"
        
        msg += "----------------------------------\n"
        msg += "📅 *30-Day Simulation Horizon*"

    url = f"https://telegram.org{token}/sendMessage"
    r = requests.post(url, data={'chat_id': chat_id, 'text': msg, 'parse_mode': 'Markdown'})
    print(f"📡 Telegram Status: {r.status_code}")

if __name__ == "__main__":
    nse_df = get_local_nse_list()
    if nse_df is not None:
        top_20 = find_top_weekly_gainers(nse_df)
        final_results = run_analysis(top_20)
        send_telegram_text(final_results)
