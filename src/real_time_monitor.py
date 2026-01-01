import warnings
warnings.simplefilter('ignore')

import os
import urllib3
urllib3.disable_warnings()

import yfinance as yf
import requests
import time
import datetime
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
    "Indexes":    ["QQQ"],
    "Foundation":    ["NVDA", "AMZN", "HOOD", "GOOG", "MSFT", "VST"],
    "AI Topic":  ["TSLA", "MRVL", "ALAB", "CRDO", "MU", "RCAT", "ONDS", "IREN", "NBIS"]
}

# Specific "Tech Pro" Wealth Rules we designed
THRESHOLDS = {
    "AVAV": {"type": "bearish",   "level": 240.0, "msg": "⚠️ AVAV ALERT: Head & Shoulders Neckline Broken!"},
    "IREN": {"type": "support",   "level": 38.50, "msg": "🚨 IREN ALERT: Testing Support Zone at $38.50."},
    "NBIS": {"type": "breakout",  "level": 95.00, "msg": "🚀 NBIS ALERT: Breakout confirmed above $95!"},
    "VST":  {"type": "buy_zone",  "level": 158.0, "msg": "📉 VST ALERT: Entering Value Buy Zone ($158)."},
    "RCAT": {"type": "volatility","percent": 5.0, "msg": "🔥 RCAT ALERT: High Volatility (>5%) Detected!"}
}

# Volatility thresholds per portfolio group (for stocks without specific rules)
GROUP_VOLATILITY_THRESHOLDS = {
    "Indexes": 2.0,      # Lower threshold for stable indexes
    "Foundation": 5.0,   # Standard for core holdings
    "AI Topic": 8.0,     # Higher for volatile AI stocks
}

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

def is_federal_holiday():
    """Check if today is a US federal holiday."""
    today = datetime.date.today()
    year = today.year
    holidays = []
    # New Year
    holidays.append(datetime.date(year, 1, 1))
    # MLK Day: 3rd Monday in January
    jan_1 = datetime.date(year, 1, 1)
    jan_1_weekday = jan_1.weekday()
    days_to_first_monday = (0 - jan_1_weekday) % 7
    first_monday = jan_1 + datetime.timedelta(days=days_to_first_monday)
    mlk = first_monday + datetime.timedelta(days=14)
    holidays.append(mlk)
    # Washington's Birthday: 3rd Monday in February
    feb_1 = datetime.date(year, 2, 1)
    feb_1_weekday = feb_1.weekday()
    days_to_first_monday_feb = (0 - feb_1_weekday) % 7
    first_monday_feb = feb_1 + datetime.timedelta(days=days_to_first_monday_feb)
    washington = first_monday_feb + datetime.timedelta(days=14)
    holidays.append(washington)
    # Memorial Day: Last Monday in May
    may_31 = datetime.date(year, 5, 31)
    may_31_weekday = may_31.weekday()
    days_back_to_monday = (may_31_weekday - 0) % 7
    memorial = may_31 - datetime.timedelta(days=days_back_to_monday)
    holidays.append(memorial)
    # Juneteenth
    holidays.append(datetime.date(year, 6, 19))
    # Independence Day
    holidays.append(datetime.date(year, 7, 4))
    # Labor Day: 1st Monday in September
    sep_1 = datetime.date(year, 9, 1)
    sep_1_weekday = sep_1.weekday()
    days_to_first_monday_sep = (0 - sep_1_weekday) % 7
    labor = sep_1 + datetime.timedelta(days=days_to_first_monday_sep)
    holidays.append(labor)
    # Columbus Day: 2nd Monday in October
    oct_1 = datetime.date(year, 10, 1)
    oct_1_weekday = oct_1.weekday()
    days_to_first_monday_oct = (0 - oct_1_weekday) % 7
    first_monday_oct = oct_1 + datetime.timedelta(days=days_to_first_monday_oct)
    columbus = first_monday_oct + datetime.timedelta(days=7)
    holidays.append(columbus)
    # Veterans Day
    holidays.append(datetime.date(year, 11, 11))
    # Thanksgiving: 4th Thursday in November
    nov_1 = datetime.date(year, 11, 1)
    nov_1_weekday = nov_1.weekday()
    days_to_first_thursday = (3 - nov_1_weekday) % 7
    first_thursday = nov_1 + datetime.timedelta(days=days_to_first_thursday)
    thanksgiving = first_thursday + datetime.timedelta(days=21)
    holidays.append(thanksgiving)
    # Christmas
    holidays.append(datetime.date(year, 12, 25))
    return today in holidays

def monitor_market():
    print("🚀 2026 Wealth Monitor Initialized...")

    # Check if today is a federal holiday
    if is_federal_holiday():
        print('Today is a federal holiday. Skipping.')
        return

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

                    group_threshold = GROUP_VOLATILITY_THRESHOLDS.get(group_name)
                    if abs(change_pct) >= group_threshold:
                        alert_text = f"🔔 {ticker} Alert: High Volativity ${price:.2f} ({change_pct:+.2f}%)"
                        alert_triggered = True

                    # --- NOTIFICATION HANDLER ---
                    status_icon = "  "
                    color_start = "\033[92m" if change_pct > 0 else "\033[91m" # Green/Red
                    color_end = "\033[0m"

                    if alert_triggered:
                        status_icon = "🔥"
                        # Anti-Spam: Only alert once every 4 hours per stock
                        if time.time() - last_alert_time.get(ticker, 0) > 4*3600:
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

# uncomment below to run the monitor locally
# if __name__ == "__main__":
#     monitor_market()