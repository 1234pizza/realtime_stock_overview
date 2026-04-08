import yfinance as yf
import pandas as pd
import streamlit as st

class DataSource:
    def __init__(self):
        # Top 15 liquid stocks per index for momentum tracking
        self.index_config = {
            "SMI": ["NESN.SW", "NOVN.SW", "ROG.SW", "UBSG.SW", "ZURN.SW", "ABBN.SW", "CFR.SW", "ALC.SW", "SREN.SW", "SIKA.SW", "LONN.SW", "GIVN.SW", "HOLN.SW", "GEBN.SW", "SCMN.SW"],
            "DAX": ["SAP.DE", "SIE.DE", "ALV.DE", "DTE.DE", "AIR.DE", "MBG.DE", "BMW.DE", "BAS.DE", "BAYN.DE", "ADS.DE", "IFX.DE", "MUV2.DE", "DHL.DE", "RWE.DE", "DBK.DE"],
            "SP500": ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "BRK-B", "TSLA", "V", "JPM", "UNH", "JNJ", "XOM", "WMT", "MA"],
            "NASDAQ": ["AAPL", "MSFT", "AMZN", "NVDA", "AVGO", "META", "ADBE", "COST", "PEP", "NFLX", "AMD", "CMCSA", "TMUS", "TXN", "INTC"]
        }

    @st.cache_data(ttl=115)
    def get_velocity_data(_self):
        """
        Fetches 1m data for velocity and 1d data for overviews.
        Calculates 2-min momentum and new 1-hour change tracking.
        """
        try:
            # 1. Prepare Tickers
            all_tickers = []
            ticker_to_index = {}
            for idx_name, tickers in _self.index_config.items():
                for t in tickers:
                    if t not in all_tickers:
                        all_tickers.append(t)
                        ticker_to_index[t] = idx_name

            # 2. Batch Download
            # Period "2d" is necessary for 1m interval to get a full hour of data reliably
            data_1m = yf.download(all_tickers, period="2d", interval="1m", group_by='ticker', progress=False)
            data_1d = yf.download(all_tickers, period="35d", interval="1d", group_by='ticker', progress=False)
            
            if data_1m.empty or data_1d.empty:
                return pd.DataFrame()

            combined_results = []
            
            for ticker in all_tickers:
                try:
                    if ticker not in data_1m.columns.get_level_values(0) or ticker not in data_1d.columns.get_level_values(0):
                        continue
                        
                    df_1m = data_1m[ticker].dropna()
                    df_1d = data_1d[ticker].dropna()
                    
                    # Check for enough data: 3 for 2m velocity, 61 for 1h change
                    if len(df_1m) < 61 or len(df_1d) < 22:
                        continue
                    
                    # --- PRICE POINTS ---
                    curr_p = df_1m['Close'].iloc[-1]
                    
                    # --- 2-MINUTE VELOCITY ---
                    prev_2m_p = df_1m['Close'].iloc[-3]
                    velocity_2m = ((curr_p - prev_2m_p) / prev_2m_p) * 100
                    
                    # --- 1-HOUR CHANGE (60 minutes) ---
                    # Using -61 because -1 is current, so 60 bars ago is index -61
                    prev_1h_p = df_1m['Close'].iloc[-61]
                    change_1h = ((curr_p - prev_1h_p) / prev_1h_p) * 100

                    # --- TREND OVERVIEWS ---
                    p_5d_ago = df_1d['Close'].iloc[-6]
                    total_5d_pct = ((curr_p - p_5d_ago) / p_5d_ago) * 100
                    
                    p_1m_ago = df_1d['Close'].iloc[0]
                    total_1m_pct = ((curr_p - p_1m_ago) / p_1m_ago) * 100

                    today_open = df_1d['Open'].iloc[-1]
                    today_pct = ((curr_p - today_open) / today_open) * 100
                    
                    combined_results.append({
                        'Index': ticker_to_index[ticker],
                        'Ticker': ticker.split('.')[0],
                        'Price': round(curr_p, 2),
                        '2m Velocity %': round(velocity_2m, 3),
                        '1h Change %': round(change_1h, 2), # New field for your dashboard
                        'Today %': round(today_pct, 2),
                        'Total 5D %': round(total_5d_pct, 2),
                        'Total 1M %': round(total_1m_pct, 2),
                        'Last Sync': df_1m.index[-1].strftime('%H:%M:%S')
                    })
                except Exception:
                    continue 

            return pd.DataFrame(combined_results)
            
        except Exception as e:
            st.error(f"Data Fetching Error: {str(e)}")
            return pd.DataFrame()