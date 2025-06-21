#!/usr/bin/env python3
import yfinance as yf
import pandas as pd
import requests
import sys

# ——————— CONFIG ———————
TELEGRAM_TOKEN = "7687060477:AAFpMb0ZNiz5tf-MHPwwM-t--6yZ8Ok9WO8"
CHAT_ID        = 707246649
# ——————————————————————

def compute_rsi(series: pd.Series, length=14) -> pd.Series:
    delta    = series.diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/length, min_periods=length).mean()
    avg_loss = loss.ewm(alpha=1/length, min_periods=length).mean()
    rs       = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def scan_conditions(symbols):
    records = []
    for sym in symbols:
        # 1) Download & skip on error
        try:
            df = yf.download(sym, period="6mo", interval="1d",
                             progress=False, auto_adjust=False)
        except Exception as e:
            print(f"⚠️  Skipping {sym}: download failed ({e})", file=sys.stderr)
            continue

        if df.shape[0] < 50:
            # not enough history
            continue

        close = df['Close']

        # 2) MACD & RSI
        macd_vals = (close.ewm(span=12).mean() - close.ewm(span=26).mean()).to_numpy()
        last_macd, prev_macd = macd_vals[-1].item(), macd_vals[-2].item()
        last_rsi = compute_rsi(close).to_numpy()[-1].item()

        long_tide  = last_macd > prev_macd and last_macd > 0 and last_rsi > 60
        short_tide = last_macd < prev_macd and last_macd < 0 and last_rsi < 60

        # 3) BB‐mid filter
        price = close.iloc[-1].item()
        mid   = close.rolling(20).mean().iloc[-1].item()
        bb_pass = (long_tide and price > mid) or (short_tide and price < mid)
        tide_pass = (long_tide or short_tide) and bb_pass

        # 4) EMA‐5/50 crossover
        ema5_vals  = close.ewm(span=5).mean().to_numpy()
        ema50_vals = close.ewm(span=50).mean().to_numpy()
        e5_now, e5_prev     = ema5_vals[-1].item(),  ema5_vals[-2].item()
        e50_now, e50_prev   = ema50_vals[-1].item(), ema50_vals[-2].item()
        crossed_up   = e5_now > e50_now and e5_prev <= e50_prev
        crossed_down = e5_now < e50_now and e5_prev >= e50_prev

        # 5) Record
        records.append({
            'Symbol':       sym,
            'Tide+BB Long':  '✔' if tide_pass and long_tide  else '',
            'Tide+BB Short': '✔' if tide_pass and short_tide else '',
            'EMA Bullish':   '↑' if crossed_up   else '',
            'EMA Bearish':   '↓' if crossed_down else ''
        })

    return pd.DataFrame(records).set_index('Symbol')

def send_telegram(body: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": f"<pre>{body}</pre>",
        "parse_mode": "HTML"
    }
    resp = requests.post(url, json=payload, timeout=10)
    if not resp.ok:
        print("❌ Telegram send failed:", resp.text, file=sys.stderr)

if __name__ == "__main__":
    watchlist = [
       
        # NIFTY 50
        "ADANIENT.NS","ADANIPORTS.NS","APOLLOHOSP.NS","ASIANPAINT.NS","AXISBANK.NS",
        "BAJAJ-AUTO.NS","BAJFINANCE.NS","BAJAJFINSV.NS","BEL.NS","BHARTIARTL.NS",
        "CIPLA.NS","COALINDIA.NS","DRREDDY.NS","EICHERMOT.NS","EXIDEIND.NS",
        "GRASIM.NS","HCLTECH.NS","HDFCBANK.NS","HDFCLIFE.NS","HEROMOTOCO.NS",
        "HINDALCO.NS","HINDUNILVR.NS","ICICIBANK.NS","INDUSINDBK.NS","INFY.NS",
        "ITC.NS","JSWSTEEL.NS","KOTAKBANK.NS","LT.NS","M&M.NS",
        "MARUTI.NS","NESTLEIND.NS","NTPC.NS","ONGC.NS","POWERGRID.NS",
        "RELIANCE.NS","SBILIFE.NS","SBIN.NS","SUNPHARMA.NS","TCS.NS",
        "TATACONSUM.NS","TATAMOTORS.NS","TATASTEEL.NS","TECHM.NS","TITAN.NS",
        "ULTRACEMCO.NS","WIPRO.NS",

        # NIFTY Next 50
        "ABB.NS","ADANIENSOL.NS","ADANIGREEN.NS","ADANIPOWER.NS","AMBUJACEM.NS",
        "BAJAJHLDNG.NS","BAJAJHFL.NS","BANKBARODA.NS","BPCL.NS","BRITANNIA.NS",
        "BOSCHLTD.NS","CANBK.NS","CHOLAFIN.NS","DABUR.NS","DIVISLAB.NS",
        "DLF.NS","DMART.NS","GAIL.NS","GODREJCP.NS","HAVELLS.NS",
        "HAL.NS","HINDZINC.NS","ICICIGI.NS","ICICIPRULI.NS","INDHOTEL.NS",
        "IOC.NS","INDIGO.NS","IRFC.NS","JINDALSTEL.NS","JSWENERGY.NS",
        "LICI.NS","LTIM.NS","MOTHERSON.NS","NAUKRI.NS","PIDILITIND.NS",
        "PFC.NS","PNB.NS","RECLTD.NS","SHREECEM.NS","SIEMENS.NS",
        "TATAPOWER.NS","TORNTPHARM.NS","TVSMOTOR.NS","VEDL.NS","ZEEL.NS",
        "ZYDUSLIFE.NS",

        # NIFTY Midcap 50 (GMRINFRA, REC removed)
        "ALKEM.NS","ATUL.NS","AUBANK.NS","BALKRISIND.NS","BATAINDIA.NS",
        "BEL.NS","CUMMINSIND.NS","COROMANDEL.NS","COFORGE.NS","DIXON.NS",
        "ESCORTS.NS","GUJGASLTD.NS","GODREJPROP.NS","IDFCFIRSTB.NS",
        "INDIAMART.NS","JUBLFOOD.NS","LODHA.NS","LTTS.NS","MANAPPURAM.NS",
        "MRPL.NS","MPHASIS.NS","MUTHOOTFIN.NS","NHPC.NS","NMDC.NS",
        "PAGEIND.NS","PEL.NS","PIIND.NS","POLYCAB.NS","RAJESHEXPO.NS",
        "SRF.NS","SUNDARMFIN.NS","SUNTV.NS","THERMAX.NS",
        "TRENT.NS","TVSMOTOR.NS","UBL.NS","UNIONBANK.NS","VOLTAS.NS",
        "ZYDUSLIFE.NS","CANFINHOME.NS","DEEPAKNTR.NS","FEDERALBNK.NS","GLAND.NS",
        "GRINDWELL.NS","IIFL.NS","INDIANB.NS","IPCALAB.NS","JINDALSAW.NS"
    
    ]

    df = scan_conditions(watchlist)

    # Build lists
    tide_long_syms  = df[df['Tide+BB Long']=='✔'].index.tolist()
    tide_short_syms = df[df['Tide+BB Short']=='✔'].index.tolist()
    ema_up_syms     = df[df['EMA Bullish']=='↑'].index.tolist()
    ema_down_syms   = df[df['EMA Bearish']=='↓'].index.tolist()

    # Construct message
    parts = [
      "🌀 *Tide+BB Bullish*:\n"  + (", ".join(tide_long_syms)  or "None"),
      "🌀 *Tide+BB Bearish*:\n" + (", ".join(tide_short_syms) or "None"),
      "🔀 *EMA Bullish Cross*:\n"   + (", ".join(ema_up_syms)    or "None"),
      "🔀 *EMA Bearish Cross*:\n"   + (", ".join(ema_down_syms)  or "None"),
    ]
    body = "\n\n".join(parts)
    print(body)
    send_telegram(body)
