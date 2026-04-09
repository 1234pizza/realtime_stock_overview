import yfinance as yf
import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime

class DataSource:
    def __init__(self):
        self.index_config = {
            "SMI": ["NESN.SW", "NOVN.SW", "ROG.SW", "UBSG.SW", "ZURN.SW", "ABBN.SW", "CFR.SW", "ALC.SW", "SREN.SW", "SIKA.SW", "LONN.SW", "GIVN.SW", "HOLN.SW", "GEBN.SW", "SCMN.SW"],
            "DAX": ["SAP.DE", "SIE.DE", "ALV.DE", "DTE.DE", "AIR.DE", "MBG.DE", "BMW.DE", "BAS.DE", "BAYN.DE", "ADS.DE", "IFX.DE", "MUV2.DE", "DHL.DE", "RWE.DE", "DBK.DE"],
            "SP500": ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "BRK-B", "TSLA", "V", "JPM", "UNH", "JNJ", "XOM", "WMT", "MA"],
            "NASDAQ": ["AAPL", "ADBE", "MSFT", "AMZN", "NVDA", "AVGO", "META", "COST", "PEP", "NFLX", "AMD", "CMCSA", "TMUS", "TXN", "INTC"]
        }
        self.cols = ['Index', 'Ticker', 'Price', '14d RSI', '2m Velocity %', '1h Change %', 'Today %', 'Last Sync']

    def calculate_rsi(self, series, period=14):
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -1 * delta.clip(upper=0)
        avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
        avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    # REDUCED TTL TO FORCE REFRESH
    @st.cache_data(ttl=30)
    def get_velocity_data(_self):
        try:
            all_tickers = []
            ticker_to_index = {}
            for idx_name, tickers in _self.index_config.items():
                for t in tickers:
                    if t not in all_tickers:
                        all_tickers.append(t)
                        ticker_to_index[t] = idx_name

            # Pulling 7 days ensures we ALWAYS have enough back-data for 1h calculation
            data_1m = yf.download(all_tickers, period="7d", interval="1m", group_by='ticker', auto_adjust=True, progress=False)
            data_1d = yf.download(all_tickers, period="90d", interval="1d", group_by='ticker', auto_adjust=True, progress=False)
            
            combined_results = []
            for ticker in all_tickers:
                try:
                    df_1m = data_1m[ticker].dropna(subset=['Close'])
                    df_1d = data_1d[ticker].dropna(subset=['Close'])
                    
                    if df_1m.empty or df_1d.empty:
                        continue
                    
                    curr_p = df_1m['Close'].iloc[-1]
                    
                    # 1h Change %: If we have 61 mins, use it. If not, use the oldest available in the 7-day set.
                    lookback_1h = min(61, len(df_1m))
                    price_1h_ago = df_1m['Close'].iloc[-lookback_1h]
                    change_1h = ((curr_p - price_1h_ago) / price_1h_ago) * 100

                    # 2m Velocity
                    lookback_2m = min(3, len(df_1m))
                    price_2m_ago = df_1m['Close'].iloc[-lookback_2m]
                    velocity_2m = ((curr_p - price_2m_ago) / price_2m_ago) * 100

                    # RSI Anchor
                    history = df_1d['Close'].copy()
                    today_date = datetime.now().date()
                    history = history[history.index.date < today_date]
                    combined_close = pd.concat([history, pd.Series([curr_p])])
                    
                    rsi_series = _self.calculate_rsi(combined_close, period=14)
                    current_rsi = rsi_series.iloc[-1]

                    # Today's Open from df_1d
                    today_open = df_1d['Open'].iloc[-1]
                    today_pct = ((curr_p - today_open) / today_open) * 100
                    
                    combined_results.append({
                        'Index': ticker_to_index[ticker],
                        'Ticker': ticker.split('.')[0],
                        'Price': round(curr_p, 2),
                        '14d RSI': round(current_rsi, 2),
                        '2m Velocity %': round(velocity_2m, 3),
                        '1h Change %': round(change_1h, 2),
                        'Today %': round(today_pct, 2),
                        'Last Sync': df_1m.index[-1].strftime('%H:%M:%S')
                    })
                except:
                    continue 

            return pd.DataFrame(combined_results)
        except Exception as e:
            st.error(f"Error: {e}")
            return pd.DataFrame(columns=_self.cols)

def main():
    st.set_page_config(page_title="Momentum Tracker", layout="wide")
    st.title("⚡ Momentum & RSI Command Center")
    
    # ADDED: Button to manually clear cache if it gets stuck
    if st.button('Force Refresh Data'):
        st.cache_data.clear()
        st.rerun()

    ds = DataSource()
    df = ds.get_velocity_data()
    
    # REMOVED the "Awaiting data" message block that was stuck on your screen
    if not df.empty:
        df_sorted = df.sort_values('1h Change %', ascending=False)
        st.dataframe(df_sorted, use_container_width=True, hide_index=True)
    else:
        st.warning("No live data found. Ensure market is open or check internet connection.")

if __name__ == "__main__":
    main()