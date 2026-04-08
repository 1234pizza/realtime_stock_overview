import yfinance as yf
import pandas as pd
import streamlit as st
import numpy as np

class DataSource:
    def __init__(self):
        # Top liquid stocks per index
        self.index_config = {
            "SMI": ["NESN.SW", "NOVN.SW", "ROG.SW", "UBSG.SW", "ZURN.SW", "ABBN.SW", "CFR.SW", "ALC.SW", "SREN.SW", "SIKA.SW", "LONN.SW", "GIVN.SW", "HOLN.SW", "GEBN.SW", "SCMN.SW"],
            "DAX": ["SAP.DE", "SIE.DE", "ALV.DE", "DTE.DE", "AIR.DE", "MBG.DE", "BMW.DE", "BAS.DE", "BAYN.DE", "ADS.DE", "IFX.DE", "MUV2.DE", "DHL.DE", "RWE.DE", "DBK.DE"],
            "SP500": ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "BRK-B", "TSLA", "V", "JPM", "UNH", "JNJ", "XOM", "WMT", "MA"],
            "NASDAQ": ["AAPL", "MSFT", "AMZN", "NVDA", "AVGO", "META", "ADBE", "COST", "PEP", "NFLX", "AMD", "CMCSA", "TMUS", "TXN", "INTC"]
        }
        # Explicitly define columns to prevent KeyErrors in the UI
        self.cols = ['Index', 'Ticker', 'Price', 'RSI', '2m Velocity %', '1h Change %', 'Today %', 'Last Sync']

    def calculate_rsi(self, series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @st.cache_data(ttl=115)
    def get_velocity_data(_self):
        try:
            all_tickers = []
            ticker_to_index = {}
            for idx_name, tickers in _self.index_config.items():
                for t in tickers:
                    if t not in all_tickers:
                        all_tickers.append(t)
                        ticker_to_index[t] = idx_name

            # Download 2 days of 1m data to ensure we have a full hour of history
            data_1m = yf.download(all_tickers, period="2d", interval="1m", group_by='ticker', progress=False)
            data_1d = yf.download(all_tickers, period="35d", interval="1d", group_by='ticker', progress=False)
            
            if data_1m.empty:
                return pd.DataFrame(columns=_self.cols)

            combined_results = []
            for ticker in all_tickers:
                try:
                    if ticker not in data_1m.columns.get_level_values(0):
                        continue
                        
                    df_1m = data_1m[ticker].dropna()
                    df_1d = data_1d[ticker].dropna() if ticker in data_1d.columns.get_level_values(0) else pd.DataFrame()
                    
                    # Ensure we have at least 61 minutes of data
                    if len(df_1m) < 61:
                        continue
                    
                    curr_p = df_1m['Close'].iloc[-1]
                    
                    # 2m Velocity
                    prev_2m_p = df_1m['Close'].iloc[-3]
                    velocity_2m = ((curr_p - prev_2m_p) / prev_2m_p) * 100
                    
                    # 1h Change
                    prev_1h_p = df_1m['Close'].iloc[-61]
                    change_1h = ((curr_p - prev_1h_p) / prev_1h_p) * 100

                    # RSI
                    rsi_series = _self.calculate_rsi(df_1m['Close'])
                    current_rsi = rsi_series.iloc[-1]

                    # Today Change
                    today_pct = 0.0
                    if not df_1d.empty:
                        today_open = df_1d['Open'].iloc[-1]
                        today_pct = ((curr_p - today_open) / today_open) * 100
                    
                    combined_results.append({
                        'Index': ticker_to_index[ticker],
                        'Ticker': ticker.split('.')[0],
                        'Price': round(curr_p, 2),
                        'RSI': round(current_rsi, 2),
                        '2m Velocity %': round(velocity_2m, 3),
                        '1h Change %': round(change_1h, 2),
                        'Today %': round(today_pct, 2),
                        'Last Sync': df_1m.index[-1].strftime('%H:%M:%S')
                    })
                except:
                    continue 

            return pd.DataFrame(combined_results) if combined_results else pd.DataFrame(columns=_self.cols)
            
        except Exception as e:
            st.error(f"Data Fetching Error: {str(e)}")
            return pd.DataFrame(columns=_self.cols)