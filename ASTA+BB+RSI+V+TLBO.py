import argparse
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

def daily_tide_bb_tl_scan(symbols, apply_bb, apply_volume, apply_tlbo):
    bullish = []
    bearish = []
    tlbo_bullish = []
    tlbo_bearish = []

    for sym in symbols:
        df = yf.download(sym, period="6mo", interval="1d",
                         progress=False, auto_adjust=False)
        if df.shape[0] < 21:
            continue

        close  = df['Close']
        high   = df['High']
        low    = df['Low']
        volume = df['Volume']

        # Core Tide: MACD + RSI
        macd_arr = (close.ewm(span=12).mean() - close.ewm(span=26).mean()).to_numpy()
        last_macd, prev_macd = macd_arr[-1], macd_arr[-2]
        last_rsi = compute_rsi(close).to_numpy()[-1]

        tide_long  = (last_macd > prev_macd) and (last_macd > 0) and (last_rsi > 60)
        tide_short = (last_macd < prev_macd) and (last_macd < 0) and (last_rsi < 60)
        if not (tide_long or tide_short):
            continue

        price = close.to_numpy()[-1]
        vol_ma20 = volume.rolling(20).mean().to_numpy()[-1]
        vol_last = volume.to_numpy()[-1]

        if apply_bb:
            mid = close.rolling(20).mean().to_numpy()[-1]
            if tide_long  and not (price > mid): continue
            if tide_short and not (price < mid): continue

        if apply_volume:
            if tide_long  and not (vol_last > 1.5 * vol_ma20): continue
            if tide_short and not (vol_last > 1.5 * vol_ma20): continue

        is_tlbo = False
        if apply_tlbo:
            prev_high20 = high.to_numpy()[-21:-1].max()
            prev_low20  = low.to_numpy()[-21:-1].min()
            if tide_long and (price > prev_high20):
                is_tlbo = True
            elif tide_short and (price < prev_low20):
                is_tlbo = True
            else:
                continue

        # Signal passed all enabled filters
        if tide_long:
            bullish.append(sym)
            if is_tlbo:
                tlbo_bullish.append(sym)
        if tide_short:
            bearish.append(sym)
            if is_tlbo:
                tlbo_bearish.append(sym)

    df_out = pd.DataFrame({
        'Bullish': pd.Series(bullish),
        'Bearish': pd.Series(bearish),
        'TLBO Breakout': pd.Series(tlbo_bullish),
        'TLBO Breakdown': pd.Series(tlbo_bearish)
    })
    print("\nDaily ASTA Scan Results:")
    filters = ["Tide"]
    if apply_bb:     filters.append("BB")
    if apply_volume: filters.append("Volume")
    if apply_tlbo:   filters.append("TLBO")
    print(" Applied Filters:", " + ".join(filters))
    print(df_out.to_string(index=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Daily ASTA Tide Scanner with optional BB, Volume & TLBO filters"
    )
    parser.add_argument('--bb',     action='store_true', help="Apply BB-Challenge filter")
    parser.add_argument('--volume', action='store_true', help="Apply Volume Spike filter")
    parser.add_argument('--tlbo',   action='store_true', help="Apply Trend-Line Breakout filter")
    args = parser.parse_args()

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

    daily_tide_bb_tl_scan(
        watchlist,
        apply_bb     = args.bb,
        apply_volume = args.volume,
        apply_tlbo   = args.tlbo
    )
