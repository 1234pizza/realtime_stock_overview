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
        # Use com=period-1 for exact Wilder's Smoothing
        avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
        rs = avg_gain / avg_loss
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

            # AUTO_ADJUST=True is critical for RSI accuracy
            data_1m = yf.download(all_tickers, period="2d", interval="1m", group_by='ticker', auto_adjust=True, progress=False)
            data_1d = yf.download(all_tickers, period="90d", interval="1d", group_by='ticker', auto_adjust=True, progress=False)
            
            combined_results = []
            for ticker in all_tickers:
                try:
                    # Cleanly extract the ticker's data to avoid MultiIndex leakage
                    df_1m = data_1m[ticker].dropna(subset=['Close'])
                    df_1d = data_1d[ticker].dropna(subset=['Close'])
                    
                    if len(df_1m) < 61 or len(df_1d) < 30:
                        continue
                    
                    curr_p = df_1m['Close'].iloc[-1]
                    
                    # Short term velocity
                    prev_2m_p = df_1m['Close'].iloc[-3]
                    velocity_2m = ((curr_p - prev_2m_p) / prev_2m_p) * 100
                    
                    # --- THE FIX FOR ADOBE ---
                    # 1. Get ONLY historical closes (excluding today)
                    history = df_1d['Close'].copy()
                    today_date = datetime.now().date()
                    history = history[history.index.date < today_date]
                    
                    # 2. Re-verify the history is long enough
                    if len(history) < 14: continue

                    # 3. Append today's live price as the final data point
                    combined_close = pd.concat([history, pd.Series([curr_p])])
                    
                    # 4. Calculate RSI on this "Clean" sequence
                    rsi_series = _self.calculate_rsi(combined_close, period=14)
                    current_rsi = rsi_series.iloc[-1]

                    # Verify Today % against the actual Daily Open
                    today_open = df_1d['Open'].iloc[-1]
                    today_pct = ((curr_p - today_open) / today_open) * 100
                    
                    combined_results.append({
                        'Index': ticker_to_index[ticker],
                        'Ticker': ticker.split('.')[0],
                        'Price': round(curr_p, 2),
                        '14d RSI': round(current_rsi, 2),
                        '2m Velocity %': round(velocity_2m, 3),
                        '1h Change %': round(((curr_p - df_1m['Close'].iloc[-61]) / df_1m['Close'].iloc[-61]) * 100, 2),
                        'Today %': round(today_pct, 2),
                        'Last Sync': df_1m.index[-1].strftime('%H:%M:%S')
                    })
                except: continue 

            return pd.DataFrame(combined_results)
        except Exception as e:
            st.error(f"Error: {e}")
            return pd.DataFrame(columns=_self.cols)