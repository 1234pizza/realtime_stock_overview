import yfinance as yf
import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime

class DataSource:
    def __init__(self):
        # 1. Expanded and Deduplicated Index Configuration
        raw_indices = {
            "SMI": ["NESN.SW", "NOVN.SW", "ROG.SW", "UBSG.SW", "ZURN.SW", "ABBN.SW", "CFR.SW", "ALC.SW", "SREN.SW", "SIKA.SW", "LONN.SW", "GIVN.SW", "HOLN.SW", "GEBN.SW", "SCMN.SW", "SLHN.SW", "LOGN.SW", "PGHN.SW", "BAER.SW", "SANDO.SW"],
            "DAX": ["SAP.DE", "SIE.DE", "ALV.DE", "DTE.DE", "AIR.DE", "MBG.DE", "BMW.DE", "BAS.DE", "BAYN.DE", "ADS.DE", "IFX.DE", "MUV2.DE", "DHL.DE", "RWE.DE", "DBK.DE", "ENR.DE", "RHM.DE", "HEI.DE", "CON.DE", "BEI.DE"],
            "NASDAQ": ["AAPL", "MSFT", "AMZN", "NVDA", "AVGO", "META", "TSLA", "GOOGL", "GOOG", "COST", "NFLX", "ADBE", "AMD", "PEP", "TMUS", "TXN", "INTC", "AMGN", "ISRG"],
            "SP500": ["BRK-B", "V", "JPM", "UNH", "JNJ", "XOM", "WMT", "MA", "LLY", "PG", "HD", "CVX", "ABBV", "MRK", "KO", "ORCL", "BAC", "SCHW", "TMO", "AVB"]
        }

        self.index_config = {}
        seen = set()
        for idx, tickers in raw_indices.items():
            unique = []
            for t in tickers:
                if t not in seen:
                    unique.append(t)
                    seen.add(t)
            self.index_config[idx] = unique

        # Added 'Volume' to the columns
        self.cols = ['Index', 'Ticker', 'Price', '14d RSI', 'Volume', '2m Velocity %', '1h Change %', 'Today %', 'Last Sync']

    def calculate_rsi(self, series, period=14):
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -1 * delta.clip(upper=0)
        # Wilder's Smoothing (RMA)
        avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
        avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def format_volume(self, volume):
        if volume >= 1_000_000:
            return f"{volume / 1_000_000:.2f}M"
        if volume >= 1_000:
            return f"{volume / 1_000:.1f}K"
        return str(int(volume))

    @st.cache_data(ttl=60)
    def get_market_data(_self):
        try:
            all_tickers = [t for sublist in _self.index_config.values() for t in sublist]
            ticker_to_index = {t: idx for idx, tickers in _self.index_config.items() for t in tickers}

            # Fetch data with 7-day 1m buffer to ensure "1h Change" works instantly
            data_1m = yf.download(all_tickers, period="7d", interval="1m", group_by='ticker', auto_adjust=True, progress=False)
            data_1d = yf.download(all_tickers, period="90d", interval="1d", group_by='ticker', auto_adjust=True, progress=False)
            
            results = []
            for ticker in all_tickers:
                try:
                    df_1m = data_1m[ticker].dropna(subset=['Close'])
                    df_1d = data_1d[ticker].dropna(subset=['Close'])
                    
                    if df_1m.empty or df_1d.empty: continue
                    
                    curr_p = df_1m['Close'].iloc[-1]
                    
                    # 1. Volume Logic (Latest Daily Volume)
                    raw_volume = df_1d['Volume'].iloc[-1]
                    formatted_vol = _self.format_volume(raw_volume)

                    # 2. 1h Change (Instant-on: uses 7-day buffer)
                    lookback_1h = min(61, len(df_1m))
                    change_1h = ((curr_p - df_1m['Close'].iloc[-lookback_1h]) / df_1m['Close'].iloc[-lookback_1h]) * 100

                    # 3. 2m Velocity
                    lookback_2m = min(3, len(df_1m))
                    velocity_2m = ((curr_p - df_1m['Close'].iloc[-lookback_2m]) / df_1m['Close'].iloc[-lookback_2m]) * 100

                    # 4. RSI Logic (Stable Daily Anchor)
                    history = df_1d['Close'].copy()
                    today_date = datetime.now().date()
                    history = history[history.index.date < today_date]
                    combined_close = pd.concat([history, pd.Series([curr_p])])
                    current_rsi = _self.calculate_rsi(combined_close).iloc[-1]

                    results.append({
                        'Index': ticker_to_index[ticker],
                        'Ticker': ticker.split('.')[0],
                        'Price': round(curr_p, 2),
                        '14d RSI': round(current_rsi, 2),
                        'Volume': formatted_vol,
                        '2m Velocity %': round(velocity_2m, 3),
                        '1h Change %': round(change_1h, 2),
                        'Today %': round(((curr_p - df_1d['Open'].iloc[-1]) / df_1d['Open'].iloc[-1]) * 100, 2),
                        'Last Sync': df_1m.index[-1].strftime('%H:%M:%S')
                    })
                except: continue
            return pd.DataFrame(results)
        except Exception as e:
            st.error(f"Error: {e}")
            return pd.DataFrame()

def main():
    st.set_page_config(page_title="Market Terminal", layout="wide")
    st.title("📊 Live Momentum & Volume Dashboard")
    
    if st.button('Force Refresh'):
        st.cache_data.clear()
        st.rerun()

    ds = DataSource()
    df = ds.get_market_data()
    
    if not df.empty:
        # Highlighting logic for the 1% moves you're looking for
        def style_rows(row):
            color = ''
            if row['1h Change %'] >= 1.0: color = 'background-color: #052e16' # Dark Green
            elif row['1h Change %'] <= -1.0: color = 'background-color: #450a0a' # Dark Red
            return [color] * len(row)

        st.dataframe(df.sort_values('1h Change %', ascending=False).style.apply(style_rows, axis=1), 
                     use_container_width=True, hide_index=True)
    else:
        st.info("Loading initial market data...")

if __name__ == "__main__":
    main()