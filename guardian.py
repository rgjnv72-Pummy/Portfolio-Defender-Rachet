import yfinance as yf
import pandas as pd
import numpy as np
import http.client, json, os

# 1. HOLDINGS (Top level so News Bot can see it)
MY_HOLDINGS = {
    "CHENNPETRO.NS": [200, 910.00, "2026-03-12", "Energy"],
    "ABB.NS": [30, 6320.00, "2026-03-18", "Capital Goods"],
    "GPIL.NS": [760, 262.98, "2026-03-23", "Metals"],
    "TATAPOWER.NS": [500, 403.00, "2026-03-23", "Energy"],
    "ONGC.NS": [700, 287.20, "2026-04-02", "Energy"],
    "LLOYDSME.NS": [109, 1446.56, "2026-04-07", "Metals"],
    "ADANIPOWER.NS": [1000, 163.36, "2026-04-07", "Energy"],
    "PREMIERENE.NS": [150, 943.30, "2026-04-07", "Infrastructure"],
    "NATCOPHARM.NS": [150, 1066.00, "2026-04-07", "Pharma"],
    "ASHOKLEY.NS": [1400, 173.00, "2026-04-09", "Auto"],
    "AUROPHARMA.NS": [70, 1350.00, "2026-04-10", "Pharma"],
    "SAMMAANCAP.NS": [922, 154.89, "2026-04-13", "Finance"]
}

MY_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
MY_TOKEN = os.getenv('TELEGRAM_TOKEN')

def send_msg(text):
    conn = http.client.HTTPSConnection("api.telegram.org")
    payload = json.dumps({"chat_id": MY_CHAT_ID, "text": text, "parse_mode": "Markdown"})
    headers = {"Content-Type": "application/json"}
    conn.request("POST", f"/bot{MY_TOKEN}/sendMessage", payload, headers)
    conn.close()

# 2. ANALYSIS LOGIC (Wrapped in a function)
def run_advanced_guardian():
    # ... (Your existing calculation code here) ...
    # (Same code you used before for data, nifty, pnl_pct, atr, ratchet, etc.)
    # ...
    report = "🚀 *DYNAMIC PORTFOLIO REPORT*\n..." 
    send_msg(report)

# 3. THE GUARD (Crucial for the News Bot)
if __name__ == "__main__":
    run_advanced_guardian()
