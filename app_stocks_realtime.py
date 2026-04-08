import streamlit as st
import time
from datetime import datetime
from data_source_realtime import DataSource

st.set_page_config(page_title="Day Trading Monitor", layout="wide")

def style_df(styler):
    """Adds color coding for Velocity and RSI."""
    # Velocity Colors
    styler.map(lambda val: 'background-color: #006400; color: white;' if val >= 0.1 
               else ('background-color: #8b0000; color: white;' if val <= -0.1 else ''), 
               subset=['2m Velocity %'])
    # RSI Colors (Blue for Oversold, Orange for Overbought)
    styler.map(lambda val: 'background-color: #1E90FF; color: white; font-weight: bold;' if val <= 30 
               else ('background-color: #FF4500; color: white; font-weight: bold;' if val >= 70 else ''), 
               subset=['RSI'])
    return styler

def main():
    st.title("⚡ Momentum & RSI Command Center")
    data_source = DataSource()
    
    with st.spinner("Analyzing Market Velocity..."):
        df = data_source.get_velocity_data()

    # Safety check: Ensure columns exist before filtering
    required_cols = ['Ticker', 'Price', 'RSI', '2m Velocity %', '1h Change %']
    
    if not df.empty and all(c in df.columns for c in required_cols):
        
        # --- ROW 1: VELOCITY ALERTS ---
        with st.container(border=True):
            st.subheader("🚨 Real-Time Velocity (±0.1% Spikes)")
            q1, q2 = st.columns(2)
            
            fast_up = df[df['2m Velocity %'] >= 0.1].sort_values('2m Velocity %', ascending=False)
            fast_down = df[df['2m Velocity %'] <= -0.1].sort_values('2m Velocity %', ascending=True)
            
            q1.markdown("### 📈 Bullish Spikes")
            q1.dataframe(fast_up[['Ticker', '2m Velocity %', 'Price', 'RSI']], hide_index=True, use_container_width=True)
            
            q2.markdown("### 📉 Bearish Drops")
            q2.dataframe(fast_down[['Ticker', '2m Velocity %', 'Price', 'RSI']], hide_index=True, use_container_width=True)

        # --- ROW 2: RSI REVERSALS ---
        st.write("")
        with st.container(border=True):
            st.subheader("📉 RSI Reversal Watch (Oversold < 30 | Overbought > 70)")
            c1, c2 = st.columns(2)
            
            oversold = df[df['RSI'] <= 30].sort_values('RSI')
            overbought = df[df['RSI'] >= 70].sort_values('RSI', ascending=False)
            
            with c1:
                st.markdown("**🔵 Potential Reversal (Oversold)**")
                st.dataframe(oversold[['Ticker', 'RSI', 'Price', '1h Change %']], hide_index=True, use_container_width=True)
            with c2:
                st.markdown("**🟠 Potential Exhaustion (Overbought)**")
                st.dataframe(overbought[['Ticker', 'RSI', 'Price', '1h Change %']], hide_index=True, use_container_width=True)

        # --- ROW 3: HOURLY TREND ---
        st.write("")
        with st.container(border=True):
            st.subheader("⏳ Hourly Trend Watch (±1.0% Move)")
            hourly = df[df['1h Change %'].abs() >= 1.0].sort_values('1h Change %', ascending=False)
            st.dataframe(hourly[['Ticker', 'Price', '1h Change %', 'RSI', '2m Velocity %']], hide_index=True, use_container_width=True)

        # --- FULL TABLE ---
        st.divider()
        st.subheader("📊 Full Market Overview")
        styled_full = style_df(df.sort_values('2m Velocity %', ascending=False).style).format(precision=2)
        st.dataframe(styled_full, use_container_width=True, height=400, hide_index=True)

    else:
        st.warning("Awaiting sufficient market data (60+ minutes needed for full analysis).")

    # --- FOOTER ---
    st.sidebar.markdown(f"**Last Sync:** {datetime.now().strftime('%H:%M:%S')}")
    st.sidebar.info("Refreshing every 120 seconds.")
    
    time.sleep(120)
    st.rerun()

if __name__ == "__main__":
    main()