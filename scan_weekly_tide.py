import yfinance as yf
import pandas as pd

def compute_rsi(series, length=14):
    delta    = series.diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/length, min_periods=length).mean()
    avg_loss = loss.ewm(alpha=1/length, min_periods=length).mean()
    rs       = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def daily_tide_scan(symbols):
    bullish = []
    bearish = []

    for sym in symbols:
        # 1) Download 6 months of daily data
        df = yf.download(sym, period="6mo", interval="1d",
                         progress=False, auto_adjust=False)
        if df.empty or len(df) < 15:
            continue

        # 2) Compute daily MACD
        fast = df['Close'].ewm(span=12, adjust=False).mean()
        slow = df['Close'].ewm(span=26, adjust=False).mean()
        macd = fast - slow
        macd_arr = macd.to_numpy()
        last_macd, prev_macd = macd_arr[-1], macd_arr[-2]

        # 3) Compute daily RSI
        rsi_arr = compute_rsi(df['Close'], length=14).to_numpy()
        last_rsi = rsi_arr[-1]

        # 4) Bullish condition: MACD rising, >0, RSI >50
        if last_macd > prev_macd and last_macd > 0 and last_rsi > 50:
            bullish.append(sym)

        # 5) Bearish condition: MACD falling, <0, RSI <50
        if last_macd < prev_macd and last_macd < 0 and last_rsi < 50:
            bearish.append(sym)

    # 6) Display results
    results = pd.DataFrame({
        'Bullish': pd.Series(bullish),
        'Bearish': pd.Series(bearish)
    })
    print("\nDaily ASTA Tide Scan Results:\n", results.to_string(index=False))
if __name__ == "__main__":
    # NIFTY 50 + NIFTY Next 50 (append .NS)
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
        "ZYDUSLIFE.NS"
    ]
    daily_tide_scan(watchlist)
