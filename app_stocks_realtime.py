import streamlit as st
import time
from datetime import datetime
from data_source_realtime import DataSource

st.set_page_config(page_title="Day Trading Monitor", layout="wide")

def style_df(styler):
    """Adds color coding for Velocity, RSI, and 1h Change."""
    # 2m Velocity Colors
    styler.map(lambda val: 'background-color: #006400; color: white;' if val >= 0.1 
               else ('background-color: #8b0000; color: white;' if val <= -0.1 else ''), 
               subset=['2m Velocity %'])
    
    # RSI Colors (Blue for Oversold, Orange for Overbought) - MATCHED TO '14d RSI'
    styler.map(lambda val: 'background-color: #1E90FF; color: white; font-weight: bold;' if val <= 35 
               else ('background-color: #FF4500; color: white; font-weight: bold;' if val >= 65 else ''), 
               subset=['14d RSI'])
    
    # 1h Trend Colors (Subtle highlighting for the 1% moves you're looking for)
    styler.map(lambda val: 'border: 2px solid #FFD700;' if abs(val) >= 1.0 else '', 
               subset=['1h Change %'])
    
    return styler

def main():
    st.title("⚡ Momentum & RSI Command Center")
    data_source = DataSource()
    
    # Added a manual refresh button for convenience
    if st.sidebar.button('🔄 Force Refresh Now'):
        st.cache_data.clear()
        st.rerun()

    with st.spinner("Analyzing Market Velocity & Daily RSI..."):
        df = data_source.get_market_data() # Ensure this matches your class method name

    # Updated required columns to match DataSource output
    required_cols = ['Ticker', 'Price', '14d RSI', '2m Velocity %', '1h Change %', 'Volume']
    
    if not df.empty and all(c in df.columns for c in required_cols):
        
        # --- ROW 1: VELOCITY ALERTS ---
        with st.container(border=True):
            st.subheader("🚨 Real-Time Velocity (±0.1% Spikes)")
            q1, q2 = st.columns(2)
            
            fast_up = df[df['2m Velocity %'] >= 0.1].sort_values('2m Velocity %', ascending=False)
            fast_down = df[df['2m Velocity %'] <= -0.1].sort_values('2m Velocity %', ascending=True)
            
            q1.markdown("### 📈 Bullish Spikes")
            q1.dataframe(fast_up[['Ticker', '2m Velocity %', 'Price', '14d RSI']], hide_index=True, use_container_width=True)
            
            q2.markdown("### 📉 Bearish Drops")
            q2.dataframe(fast_down[['Ticker', '2m Velocity %', 'Price', '14d RSI']], hide_index=True, use_container_width=True)

        # --- ROW 2: RSI REVERSALS ---
        st.write("")
        with st.container(border=True):
            st.subheader("📉 Daily RSI Watch (Oversold < 35 | Overbought > 65)")
            c1, c2 = st.columns(2)
            
            # Using 35/65 as thresholds for Daily RSI as it's more stable
            oversold = df[df['14d RSI'] <= 35].sort_values('14d RSI')
            overbought = df[df['14d RSI'] >= 65].sort_values('14d RSI', ascending=False)
            
            with c1:
                st.markdown("**🔵 Oversold (Daily Support)**")
                st.dataframe(oversold[['Ticker', '14d RSI', 'Price', 'Today %']], hide_index=True, use_container_width=True)
            with c2:
                st.markdown("**🟠 Overbought (Daily Resistance)**")
                st.dataframe(overbought[['Ticker', '14d RSI', 'Price', 'Today %']], hide_index=True, use_container_width=True)

        # --- ROW 3: HOURLY TREND & VOLUME ---
        st.write("")
        with st.container(border=True):
            st.subheader("⏳ Hourly Trend Watch (±1.0% Impulse)")
            hourly = df[df['1h Change %'].abs() >= 1.0].sort_values('1h Change %', ascending=False)
            st.dataframe(hourly[['Ticker', 'Price', '1h Change %', 'Volume', '14d RSI', '2m Velocity %']], 
                         hide_index=True, use_container_width=True)

        # --- FULL TABLE ---
        st.divider()
        st.subheader("📊 Full Market Overview")
        # Ensure we sort by 1h change to highlight your 1% movers
        styled_full = style_df(df.sort_values('1h Change %', ascending=False).style).format(precision=2)
        st.dataframe(styled_full, use_container_width=True, height=400, hide_index=True)

    else:
        st.warning("No data found. If the market is open, try 'Force Refresh' in the sidebar.")

    # --- FOOTER ---
    st.sidebar.markdown(f"**Last Sync:** {datetime.now().strftime('%H:%M:%S')}")
    st.sidebar.info("Refreshing every 60 seconds for precision.")
    
    # Auto-refresh logic
    time.sleep(60)
    st.rerun()

if __name__ == "__main__":
    main()