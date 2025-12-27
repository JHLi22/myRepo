import os
import yfinance as yf
import requests
import time
from IPython.display import clear_output
from dotenv import load_dotenv

load_dotenv()


 # ==========================================
# # 1. USER CONFIGURATION (Telegram Setup)
# # ==========================================
# # Step 1: Search for "@BotFather" on Telegram -> Send "/newbot" -> Copy the Token.
# # Step 2: Search for "@userinfobot" on Telegram -> Copy your "Id".
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

# ==========================================
# 2. PORTFOLIO & STRATEGY RULES
# ==========================================
# Grouping your watchlist for clearer display
PORTFOLIO = {
    "Compute Core":    ["NVDA", "AMD", "AVGO", "MRVL"],
    "Auto & Power":    ["TSLA", "VST", "IREN"],
    "Connectivity":    ["ALAB", "CRDO", "LITE", "NBIS"],
    "High Risk/Drone": ["RCAT", "AVAV", "ONDS"]
}

# Specific "Tech Pro" Wealth Rules we designed
THRESHOLDS = {
    "AVAV": {"type": "bearish",   "level": 240.0, "msg": "⚠️ AVAV ALERT: Head & Shoulders Neckline Broken!"},
    "IREN": {"type": "support",   "level": 38.50, "msg": "🚨 IREN ALERT: Testing Support Zone at $38.50."},
    "NBIS": {"type": "breakout",  "level": 95.00, "msg": "🚀 NBIS ALERT: Breakout confirmed above $95!"},
    "VST":  {"type": "buy_zone",  "level": 158.0, "msg": "📉 VST ALERT: Entering Value Buy Zone ($158)."},
    "RCAT": {"type": "volatility","percent": 5.0, "msg": "🔥 RCAT ALERT: High Volatility (>5%) Detected!"}
}

# General alert threshold for all other stocks (e.g., NVDA jumps 3%)
GENERAL_VOLATILITY_LIMIT = 3.0

# ==========================================
# 3. MONITORING ENGINE
# ==========================================
def send_telegram(message):
    """Sends a push notification to your phone."""
    if "YOUR_" in TG_TOKEN:
        print(f"   [Simulation Mode] Telegram would send: {message}")
        return

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    params = {"chat_id": TG_CHAT_ID, "text": message}
    try:
        requests.get(url, params=params, timeout=5)
    except Exception as e:
        print(f"   [Error] Could not send Telegram: {e}")

def monitor_market():
    print("🚀 2026 Wealth Monitor Initialized...")
    # Dictionary to track the last time we sent an alert (to prevent spam)
    last_alert_time = {}


    # In CI, run single iteration and exit
    try:
        clear_output(wait=True)
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"📡 REAL-TIME WEALTH MONITOR | {current_time}")
        print("=" * 55)

        for group_name, tickers in PORTFOLIO.items():
            print(f"\n🔹 {group_name}")
            for ticker in tickers:
                try:
                    # Fetch live data (1 minute intervals for precision)
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period="1d", interval="1m")

                    if hist.empty:
                        print(f"   {ticker:<5}: [Market Closed / No Data]")
                        continue

                    price = hist['Close'].iloc[-1]

                    # Get previous close to calculate % change
                    prev_close = stock.info.get('previousClose', price)
                    # Fallback if API misses prev_close
                    if prev_close is None or prev_close == 0:
                        prev_close = hist['Open'].iloc[0]

                    change_pct = ((price - prev_close) / prev_close) * 100

                    # --- ALERT LOGIC ---
                    alert_triggered = False
                    alert_text = ""

                    # 1. Check Custom Strategy Rules
                    if ticker in THRESHOLDS:
                        rule = THRESHOLDS[ticker]

                        if rule["type"] == "bearish" and price < rule["level"]:
                            alert_text = f"{rule['msg']} Price: ${price:.2f}"
                            alert_triggered = True

                        elif rule["type"] == "support" and price < rule["level"]:
                            alert_text = f"{rule['msg']} Price: ${price:.2f}"
                            alert_triggered = True

                        elif rule["type"] == "buy_zone" and price < rule["level"]:
                            alert_text = f"{rule['msg']} Price: ${price:.2f}"
                            alert_triggered = True

                        elif rule["type"] == "breakout" and price > rule["level"]:
                            alert_text = f"{rule['msg']} Price: ${price:.2f}"
                            alert_triggered = True

                        elif rule["type"] == "volatility" and abs(change_pct) > rule["percent"]:
                            alert_text = f"{rule['msg']} Move: {change_pct:+.2f}%"
                            alert_triggered = True

                    # 2. Check General Volatility (for stocks like NVDA/TSLA)
                    elif abs(change_pct) > GENERAL_VOLATILITY_LIMIT:
                        alert_text = f"🔔 {ticker} Moving Fast: ${price:.2f} ({change_pct:+.2f}%)"
                        alert_triggered = True

                    # --- NOTIFICATION HANDLER ---
                    status_icon = "  "
                    color_start = "\033[92m" if change_pct > 0 else "\033[91m" # Green/Red
                    color_end = "\033[0m"

                    if alert_triggered:
                        status_icon = "🔥"
                        # Anti-Spam: Only alert once every 60 minutes per stock
                        if time.time() - last_alert_time.get(ticker, 0) > 3600:
                            send_telegram(alert_text)
                            last_alert_time[ticker] = time.time()
                            status_icon = "📤" # Indicates message sent

                    print(f" {status_icon} {ticker:<5}: {color_start}${price:>7.2f} ({change_pct:>+6.2f}%){color_end}")

                except Exception as e:
                    print(f"   {ticker:<5}: Error")

        print("\n" + "=" * 55)
        print("CI run completed.")
    except Exception as e:
        print(f"Global Error: {e}")
    return
