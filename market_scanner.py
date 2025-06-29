#!/usr/bin/env python3
import yfinance as yf
import pandas as pd
import datetime
import time
import logging
import requests

# ——————— CONFIG ———————
TELEGRAM_TOKEN = "7687060477:AAFpMb0ZNiz5tf-MHPwwM-t--6yZ8Ok9WO8"
CHAT_ID        = 707246649
# ——————————————————————

# Logging setup
today_str = datetime.datetime.now().strftime("%Y-%m-%d")
log_dir = "/Users/admin/ytshorts/logs"
log_file = f"{log_dir}/market_scan_{today_str}.log"

import os
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s %(message)s")

# NSE holidays for 2025 (update annually)
NSE_HOLIDAYS = {
    "2025-01-26", "2025-03-29", "2025-04-14", "2025-05-01", "2025-08-15",
    "2025-10-02", "2025-10-24", "2025-11-11", "2025-12-25"
}

def is_market_day():
    today = datetime.datetime.now().date()
    return today.weekday() < 5 and today.isoformat() not in NSE_HOLIDAYS

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        logging.warning(f"⚠️ Telegram failed: {e}")

def retry_download(symbol, period, interval, retries=3):
    for attempt in range(retries):
        try:
            df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=False)
            if not df.empty:
                return df
        except Exception as e:
            logging.warning(f"{symbol} download failed (attempt {attempt+1}): {e}")
        time.sleep(2)
    return None

def find_crossover(ema5, ema50):
    return (
        ema5.iloc[-1] > ema50.iloc[-1] and ema5.iloc[-2] <= ema50.iloc[-2],
        ema5.iloc[-1] < ema50.iloc[-1] and ema5.iloc[-2] >= ema50.iloc[-2],
    )

def nifty_intraday_check():
    logging.info("🔍 Checking NIFTY 15m crossover (if daily crossover exists)")
    df_day = retry_download("^NSEI", "6mo", "1d")
    df_15m = retry_download("^NSEI", "5d", "15m")
    if df_day is None or df_15m is None:
        logging.warning("⚠️ Skipping NIFTY check due to data failure")
        return

    ema5_d = df_day['Close'].ewm(span=5).mean()
    ema50_d = df_day['Close'].ewm(span=50).mean()
    daily_crossed = ema5_d.iloc[-1] > ema50_d.iloc[-1] and ema5_d.iloc[-2] <= ema50_d.iloc[-2]

    if not daily_crossed:
        logging.info("⛔ No daily crossover. Skipping NIFTY 15m scan.")
        return

    ema5_15 = df_15m['Close'].ewm(span=5).mean()
    ema50_15 = df_15m['Close'].ewm(span=50).mean()
    bull, bear = find_crossover(ema5_15, ema50_15)

    if bull:
        msg = "🚨 NIFTY 15-min Bullish Crossover (daily trend confirmed)"
        logging.info(msg)
        send_telegram(msg)
    elif bear:
        msg = "⚠️ NIFTY 15-min Bearish Crossover (daily trend confirmed)"
        logging.info(msg)
        send_telegram(msg)
    else:
        logging.info("✅ NIFTY checked. No crossover at this moment.")

def scan_conditions(symbols):
    logging.info("🧾 Running daily scan for stock crossovers")
    results = []

    for sym in symbols:
        df = retry_download(sym, "6mo", "1d")
        if df is None or df.shape[0] < 60:
            continue

        close = df['Close']
        ema5 = close.ewm(span=5).mean()
        ema50 = close.ewm(span=50).mean()
        bull, bear = find_crossover(ema5, ema50)

        results.append({
            'Symbol': sym,
            'Bullish': bull,
            'Bearish': bear
        })

    if results:
        bullish = [r['Symbol'] for r in results if r['Bullish']]
        bearish = [r['Symbol'] for r in results if r['Bearish']]

        message = f"📈 Daily Crossover Scan ({datetime.datetime.now().strftime('%H:%M')})\n"
        if bullish:
            message += "\n✅ Bullish Crossovers:\n" + "\n".join(bullish)
        if bearish:
            message += "\n⚠️ Bearish Crossovers:\n" + "\n".join(bearish)
        if not bullish and not bearish:
            message += "\nNo crossovers today."

        logging.info(message.replace("\n", " | "))
        send_telegram(message)
    else:
        logging.info("🟡 No crossover signals found today.")
        send_telegram("🟡 No crossover signals found today.")

def main_loop():
    watchlist = [
        "RELIANCE.NS", "INFY.NS", "TCS.NS", "ICICIBANK.NS", "HDFCBANK.NS",
        "LT.NS", "SBIN.NS", "ITC.NS", "AXISBANK.NS", "KOTAKBANK.NS"
    ]

    while True:
        now = datetime.datetime.now()
        if not is_market_day():
            logging.info("🛌 Market is closed today.")
            time.sleep(60 * 30)
            continue

        time_str = now.strftime("%H:%M")

        if now.minute % 15 == 0 and datetime.time(9, 30) <= now.time() <= datetime.time(15, 15):
            nifty_intraday_check()

        if time_str == "15:00":
            scan_conditions(watchlist)

        time.sleep(60)

if __name__ == "__main__":
    main_loop()
