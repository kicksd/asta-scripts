import requests
import pandas as pd
from io import StringIO

# 1) The NSE CSV URL
midcap_url = "https://www1.nseindia.com/content/indices/ind_nifty_midcap_100list.csv"

# 2) Spoof a browser User-Agent
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    ),
    # You can also add Referer if needed:
    # "Referer": "https://www.nseindia.com/"
}

# 3) Fetch the CSV
resp = requests.get(midcap_url, headers=headers)
resp.raise_for_status()   # ensure we got a 200 OK

# 4) Load into pandas
df_mid = pd.read_csv(StringIO(resp.text))

# 5) Append .NS to each Symbol for yfinance
midcap100 = [sym + ".NS" for sym in df_mid["Symbol"]]
print(midcap100)
