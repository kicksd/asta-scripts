import yfinance as yf
import pandas as pd

def compute_rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta    = series.diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/length, min_periods=length).mean()
    avg_loss = loss.ewm(alpha=1/length, min_periods=length).mean()
    rs       = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def scan_daily_double_screen(symbols):
    bullish = []
    bearish = []

    for sym in symbols:
        # 1) Download 6 months of daily data
        df = yf.download(sym, period="6mo", interval="1d",
                         progress=False, auto_adjust=False)
        if df.shape[0] < 50:
            continue

        # Work directly on the Series (1-D) for all calculations:
        close = df['Close']
        high  = df['High']
        low   = df['Low']
        vol   = df['Volume']

        # --- Tide Screen: Daily MACD + RSI ---
        fast = close.ewm(span=12, adjust=False).mean()
        slow = close.ewm(span=26, adjust=False).mean()
        macd = fast - slow
        last_macd, prev_macd = macd.iloc[-1], macd.iloc[-2]

        rsi = compute_rsi(close, length=14)
        last_rsi = rsi.iloc[-1]

        tide_long  = (last_macd > prev_macd) and (last_macd > 0) and (last_rsi > 50)
        tide_short = (last_macd < prev_macd) and (last_macd < 0) and (last_rsi < 50)
        if not (tide_long or tide_short):
            continue

        # --- Wave Filter 5: 50 EMA Confirmation ---
        ema50 = close.ewm(span=50, adjust=False).mean()
        wave_long_5  = close.iloc[-1] > ema50.iloc[-1]
        wave_short_5 = close.iloc[-1] < ema50.iloc[-1]

        # --- Wave Filter 6: Daily RSI Zone ---
        wave_long_6  = last_rsi > 50
        wave_short_6 = last_rsi < 50

        if tide_long and wave_long_5 and wave_long_6:
            bullish.append(sym)
        if tide_short and wave_short_5 and wave_short_6:
            bearish.append(sym)

    # Print results
    df_out = pd.DataFrame({
        'Bullish': pd.Series(bullish),
        'Bearish': pd.Series(bearish)
    })
    print("\nASTA Daily Double-Screen (Filters 5 & 6) Results:")
    print(df_out.to_string(index=False))


if __name__ == "__main__":
    watchlist = [
        # NIFTY 50 + Next 50 tickers (shortened here)
        "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS",
        "ICICIBANK.NS","SBIN.NS","LT.NS","HINDUNILVR.NS"
    ]
    scan_daily_double_screen(watchlist)