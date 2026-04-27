import pandas as pd
import yfinance as yf
import numpy as np
import os
import requests
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
NSE_500_URL = "https://nseindia.com"
OUTPUT_EXCEL = "Whale_Scan_Report.xlsx"
FORECAST_PLOT = "kronos_forecast.png"

def get_nse_500_list():
    print("📥 Fetching NSE 500 list...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(NSE_500_URL, headers=headers)
    with open("nifty500.csv", "wb") as f: f.write(r.content)
    return pd.read_csv("nifty500.csv")

def find_top_weekly_gainers(df_nse, count=20):
    print(f"📈 Filtering Top {count} Weekly Gainers...")
    symbols = [s + ".NS" for s in df_nse['Symbol'].tolist()]
    data = yf.download(symbols, period="10d", interval="1d", group_by='ticker', threads=True, progress=False)
    
    perf = []
    for ticker in symbols:
        try:
            h = data[ticker].dropna()
            if len(h) < 5: continue
            change = ((h['Close'].iloc[-1] - h['Close'].iloc[-5]) / h['Close'].iloc[-5]) * 100
            perf.append({'Ticker': ticker, 'Gains': change})
        except: continue
    return pd.DataFrame(perf).sort_values(by='Gains', ascending=False).head(count)['Ticker'].tolist()

def run_kronos_simulation(tickers):
    print(f"🤖 Kronos AI: Simulating 30-Day Forecasts for {len(tickers)} stocks...")
    plt.style.use('dark_background')
    data = yf.download(tickers, period="2y", progress=False, auto_adjust=True)
    
    analysis = []
    for ticker in tickers:
        try:
            df = data['Close'][ticker].dropna()
            price = df.iloc[-1]
            returns = df.pct_change().dropna()
            vol = returns.std()
            drift = ((price - df.iloc[-60]) / df.iloc[-60]) / 60

            sims, days = 250, 30
            paths = []
            success = 0
            for _ in range(sims):
                path = price * np.cumprod(1 + np.random.normal(drift, vol, days))
                paths.append(path)
                if path[-1] > price: success += 1

            analysis.append({
                'ticker': ticker.replace('.NS', ''),
                'price': price,
                'confidence': (success / sims) * 100,
                'target_1m': np.mean([p[-1] for p in paths]),
                'paths': paths,
                'df': df
            })
        except: continue
    
    ranked = sorted(analysis, key=lambda x: x['confidence'], reverse=True)
    
    # Generate Visuals for Top 3
    fig, axes = plt.subplots(min(3, len(ranked)), 1, figsize=(10, 15))
    if len(ranked) == 1: axes = [axes]
    
    for i in range(min(3, len(ranked))):
        item = ranked[i]
        ax = axes[i]
        ax.plot(item['df'].values[-100:], color='#00ffcc', label='History')
        for p in item['paths'][:10]:
            ax.plot(np.arange(100, 130), p, color='yellow', alpha=0.2)
        ax.set_title(f"{item['ticker']} - Conf: {item['confidence']:.1f}%")
    
    plt.tight_layout()
    plt.savefig(FORECAST_PLOT)
    return ranked

def send_telegram(file_path, caption, is_image=False):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    method = "sendPhoto" if is_image else "sendDocument"
    key = "photo" if is_image else "document"
    
    url = f"https://telegram.org{token}/{method}"
    with open(file_path, "rb") as f:
        requests.post(url, data={'chat_id': chat_id, 'caption': caption}, files={key: f})

if __name__ == "__main__":
    nse_df = get_nse_500_list()
    top_20 = find_top_weekly_gainers(nse_df)
    results = run_kronos_simulation(top_20)
    
    if results:
        df_final = pd.DataFrame(results).drop(columns=['paths', 'df'])
        df_final.to_excel(OUTPUT_EXCEL, index=False)
        
        # Send Reports
        send_telegram(OUTPUT_EXCEL, "📊 **Weekly Whale & Kronos Report**")
        send_telegram(FORECAST_PLOT, "📈 **Kronos 30-Day Forecast Visuals**", is_image=True)
