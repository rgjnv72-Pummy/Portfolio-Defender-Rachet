import pandas as pd
import yfinance as yf
import numpy as np
import os
import requests
import matplotlib
import matplotlib.pyplot as plt

# Force non-interactive backend for GitHub server
matplotlib.use('Agg')

# --- CONFIGURATION ---
CSV_FILE = 'ind_nifty500list.csv'
OUTPUT_EXCEL = "Whale_Scan_Report.xlsx"
FORECAST_PLOT = "kronos_forecast.png"

def get_local_nse_list():
    """Reads the manually uploaded NSE 500 file."""
    if os.path.exists(CSV_FILE):
        print(f"✅ Found {CSV_FILE}. Loading...")
        return pd.read_csv(CSV_FILE)
    else:
        print(f"❌ Error: {CSV_FILE} not found. Please upload it to your repo.")
        return None

def find_top_weekly_gainers(df_nse, count=20):
    """Batches data to find the best performers in the last 5 trading days."""
    print(f"📈 Identifying Top {count} Weekly Gainers...")
    # Clean symbols and add .NS
    symbols = [str(s).strip() + ".NS" for s in df_nse['Symbol'].tolist()]
    
    # Batch download last 10 days to ensure 1 week of data
    data = yf.download(symbols, period="10d", interval="1d", group_by='ticker', threads=True, progress=False)
    
    performance = []
    for ticker in symbols:
        try:
            hist = data[ticker].dropna()
            if len(hist) < 5: continue
            
            cp = hist['Close'].iloc[-1]
            prev_p = hist['Close'].iloc[-5]
            pct_change = ((cp - prev_p) / prev_p) * 100
            performance.append({'Ticker': ticker, 'Weekly_Gains': pct_change})
        except: continue
        
    perf_df = pd.DataFrame(performance).sort_values(by='Weekly_Gains', ascending=False)
    return perf_df.head(count)['Ticker'].tolist()

def run_whale_kronos_analysis(top_tickers, df_nse):
    """Combines V4.0 Techno-Funda scoring with Kronos AI Simulation."""
    print("🚀 Running Institutional Whale + Kronos Simulation...")
    # Map industries
    sec_col = 'Industry' if 'Industry' in df_nse.columns else 'Sector'
    sector_map = dict(zip(df_nse['Symbol'] + ".NS", df_nse[sec_col]))
    
    final_data = []
    plt.style.use('dark_background')
    fig, axes = plt.subplots(min(5, len(top_tickers)), 1, figsize=(12, 35))
    
    for i, ticker in enumerate(top_tickers):
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="2y")
            if len(df) < 200: continue

            # --- TECHNO FUNDA SCORING ---
            close = df['Close']
            curr_price = close.iloc[-1]
            ema200 = close.ewm(span=200, adjust=False).mean().iloc[-1]
            
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain.iloc[-1] / (loss.iloc[-1] + 1e-9))))
            
            rvol = df['Volume'].iloc[-1] / (df['Volume'].rolling(20).mean().iloc[-1] + 1e-9)

            score = 0
            if curr_price > ema200: score += 5
            if 60 < rsi < 78: score += 5
            if rvol > 1.5: score += 5

            # --- KRONOS AI SIMULATION (30 DAYS) ---
            returns = close.pct_change().dropna()
            vol = returns.std()
            drift = ((curr_price - close.iloc[-60]) / close.iloc[-60]) / 60
            
            sim_paths = []
            success = 0
            for _ in range(100):
                path = curr_price * np.cumprod(1 + np.random.normal(drift, vol, 30))
                sim_paths.append(path)
                if path[-1] > curr_price: success += 1
            
            conf = (success / 100) * 100
            target = np.mean([p[-1] for p in sim_paths])

            final_data.append({
                'Ticker': ticker.replace('.NS', ''),
                'Sector': sector_map.get(ticker, 'Unknown'),
                'V4_Score': score,
                'RSI': round(rsi, 1),
                'Conf_Prob': f"{conf}%",
                'Target_1M': round(target, 2),
                'Upside%': round(((target-curr_price)/curr_price)*100, 2)
            })

            # Plot top 5
            if i < 5:
                ax = axes[i]
                ax.plot(close.values[-100:], color='#00ffcc', label='Price')
                for p in sim_paths[:10]: ax.plot(np.arange(100, 130), p, color='yellow', alpha=0.2)
                ax.set_title(f"{ticker} | Score: {score} | Conf: {conf}%", color='gold')

        except: continue

    plt.tight_layout()
    plt.savefig(FORECAST_PLOT)
    return pd.DataFrame(final_data)

def send_to_telegram(excel, plot):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if not token or not chat_id: return

    # Send Photo
    with open(plot, "rb") as p:
        requests.post(f"https://telegram.org{token}/sendPhoto", 
                      data={'chat_id': chat_id, 'caption': "🔥 **Top 5 Kronos Forecasts**", 'parse_mode': 'Markdown'}, files={'photo': p})
    
    # Send Excel
    with open(excel, "rb") as e:
        requests.post(f"https://telegram.org{token}/sendDocument", 
                      data={'chat_id': chat_id, 'caption': "📊 **Full Whale Scan Results**", 'parse_mode': 'Markdown'}, files={'document': e})

if __name__ == "__main__":
    df_nse = get_local_nse_list()
    if df_nse is not None:
        top_20 = find_top_weekly_gainers(df_nse)
        report_df = run_whale_kronos_analysis(top_20, df_nse)
        
        if not report_df.empty:
            report_df.to_excel(OUTPUT_EXCEL, index=False)
            send_to_telegram(OUTPUT_EXCEL, FORECAST_PLOT)
            print("✨ Done! Report and Plots sent to Telegram.")
