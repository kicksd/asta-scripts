#!/usr/bin/env python3

import yfinance as yf
import pandas as pd
import numpy as np

# 1) Download 2 years of daily data for Nifty (raw OHLC)
df = yf.download(
    "^NSEI",
    period="2y",
    interval="1d",
    progress=False,
    auto_adjust=False
)

# 2) Build Heikin-Ashi candles
ha = pd.DataFrame(index=df.index)

# HA-close
ha['ha_close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4

# HA-open (seed + iterative)
ha_open = np.empty(len(ha), dtype=float)
ha_open[0] = (df['Open'].iloc[0] + df['Close'].iloc[0]) / 2
for i in range(1, len(ha_open)):
    ha_open[i] = (ha_open[i-1] + ha['ha_close'].iloc[i-1]) / 2
ha['ha_open'] = ha_open

# HA-high / HA-low
ha['ha_high'] = pd.concat([df['High'], ha['ha_open'], ha['ha_close']], axis=1).max(axis=1)
ha['ha_low']  = pd.concat([df['Low'],  ha['ha_open'], ha['ha_close']], axis=1).min(axis=1)

# 3) Compute EMAs
df['ema_fast'] = df['Close'].ewm(span=5,  adjust=False).mean()
df['ema_slow'] = df['Close'].ewm(span=50, adjust=False).mean()
ha['ema9']     = ha['ha_close'].ewm(span=9,  adjust=False).mean()

# 4) Identify 5/50 EMA crossovers
df['cross_up']   = (df['ema_fast'] > df['ema_slow']) & (df['ema_fast'].shift() <= df['ema_slow'].shift())
df['cross_down'] = (df['ema_fast'] < df['ema_slow']) & (df['ema_fast'].shift() >= df['ema_slow'].shift())

# 5) Prepare HA body-zone boundaries
body_top  = ha[['ha_open', 'ha_close']].max(axis=1)
body_bot  = ha[['ha_open', 'ha_close']].min(axis=1)
body_size = body_top - body_bot
bot_zone  = body_bot + body_size * 0.40
top_zone  = body_top - body_size * 0.40

# 6) Assign HA & zone data back into df
df['ha_open']   = ha['ha_open']
df['ha_close']  = ha['ha_close']
df['ema9']      = ha['ema9']
df['body_top']  = body_top
df['body_bot']  = body_bot
df['bot_zone']  = bot_zone
df['top_zone']  = top_zone
df['isGreenHA'] = ha['ha_close'] > ha['ha_open']
df['isRedHA']   = ha['ha_close'] < ha['ha_open']

# 7) Filter crossovers through the 9-EMA zone test
cond_bull = (
    df['cross_up']
    & df['isGreenHA']
    & (df['ema9'] >= df['bot_zone'])
    & (df['ema9'] <= df['body_top'])
)
cond_bear = (
    df['cross_down']
    & df['isRedHA']
    & (df['ema9'] <= df['top_zone'])
    & (df['ema9'] >= df['body_bot'])
)

# 8) Compute totals & probability
total_cross = int(df['cross_up'].sum() + df['cross_down'].sum())
filtered    = int(cond_bull.sum()    + cond_bear.sum())

print(f"Total 5/50 crossovers: {total_cross}")
print(f"Crossovers passing 9-EMA filter: {filtered}")
print(f"Conditional probability: {filtered/total_cross:.2%}")
