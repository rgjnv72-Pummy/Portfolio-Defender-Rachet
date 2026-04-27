import pandas as pd
import yfinance as yf
import numpy as np
import os
import requests
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('Agg')

# --- CONFIG ---
CSV_FILE = 'ind_nifty500list.csv'
OUTPUT_EXCEL = "Whale_Scan_Report.xlsx"
FORECAST_PLOT = "kronos_forecast.png"

def get_local_nse_list():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE, skipinitialspace=True)
    print("❌ CSV File Missing")
    return None

def find_top_weekly_gainers(df_nse, count=20):
    print(f"📈 Finding Top {count} Gainers...")
    symbols = [str(s).strip() + ".NS" for s in df_nse['Symbol'].dropna().unique()]
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

def run_analysis(tickers):
    print("🚀 Analyzing & Simulating...")
    final_data = []
    plt.style.use('dark_background')
    fig, axes = plt.subplots(5, 1, figsize=(8, 15)) # Smaller figure
    
    for i, ticker in enumerate(tickers):
        try:
            df = yf.download(ticker, period="1y", progress=False)
            if df.empty: continue
            
            cp = float(df['Close'].iloc[-1])
            rets = df['Close'].pct_change().dropna()
            vol, drift = rets.std(), (cp - df['Close'].iloc[-60]) / (df['Close'].iloc[-60] * 60)
            
            paths = [cp * np.cumprod(1 + np.random.normal(drift, vol, 30)) for _ in range(30)] # Fewer paths
            conf = (sum(1 for p in paths if p[-1] > cp) / 30) * 100
            
            final_data.append({'Ticker': ticker, 'Conf%': round(conf, 1), 'Price': round(cp, 1)})

            if i < 5:
                ax = axes[i]
                ax.plot(df['Close'].values[-50:], color='#00ffcc')
                for p in paths[:5]: ax.plot(np.arange(50, 80), p, color='yellow', alpha=0.2)
                ax.set_title(f"{ticker} ({conf}%)")
        except: continue

    plt.tight_layout()
    plt.savefig(FORECAST_PLOT, dpi=80) # Lower DPI for faster upload
    return pd.DataFrame(final_data)

def send_to_telegram(excel, plot):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    # 1. Immediate Heartbeat Text
    requests.post(f"https://telegram.org{token}/sendMessage", 
                  data={'chat_id': chat_id, 'text': "✅ **Whale Scan Complete.** Uploading files...", 'parse_mode': 'Markdown'})

    def upload(method, files, caption):
        url = f"https://telegram.org{token}/{method}"
        r = requests.post(url, data={'chat_id': chat_id, 'caption': caption}, files=files, timeout=60)
        print(f"📡 Telegram Response ({method}): {r.status_code} - {r.text}")

    if os.path.exists(plot):
        with open(plot, "rb") as p: upload("sendPhoto", {'photo': p}, "🔥 Kronos Top 5")
    
    if os.path.exists(excel):
        with open(excel, "rb") as e: upload("sendDocument", {'document': e}, "📊 Full Report")

if __name__ == "__main__":
    nse_df = get_local_nse_list()
    if nse_df is not None:
        top_20 = find_top_weekly_gainers(nse_df)
        res_df = run_analysis(top_20)
        if not res_df.empty:
            res_df.to_excel(OUTPUT_EXCEL, index=False)
            send_to_telegram(OUTPUT_EXCEL, FORECAST_PLOT)
