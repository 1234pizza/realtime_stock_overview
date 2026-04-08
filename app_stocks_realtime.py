import streamlit as st
import time
from datetime import datetime
from data_source_realtime import DataSource

st.set_page_config(page_title="Day Trading Monitor", layout="wide")

def style_df(styler):
    # Colors velocity
    styler.map(lambda val: 'background-color: #006400; color: white;' if val >= 0.1 else ('background-color: #8b0000; color: white;' if val <= -0.1 else ''), subset=['2m Velocity %'])
    # Colors RSI
    styler.map(lambda val: 'background-color: #1E90FF; color: white; font-weight: bold;' if val <= 30 else ('background-color: #FF4500; color: white; font-weight: bold;' if val >= 70 else ''), subset=['RSI'])
    return styler

def main():
    st.title("⚡ Momentum & RSI Command Center")
    data_source = DataSource()
    
    with st.spinner("Syncing markets..."):
        df = data_source.get_velocity_data()

    if not df.empty:
        # --- ROW 1: VELOCITY ALERTS ---
        with st.container(border=True):
            st.subheader("🚨 Real-Time Velocity (±0.1%)")
            q1, q2 = st.columns(2)
            fast_up = df[df['2m Velocity %'] >= 0.1]
            fast_down = df[df['2m Velocity %'] <= -0.1]
            q1.dataframe(fast_up[['Ticker', '2m Velocity %', 'Price', 'RSI']], hide_index=True, use_container_width=True)
            q2.dataframe(fast_down[['Ticker', '2m Velocity %', 'Price', 'RSI']], hide_index=True, use_container_width=True)

        # --- ROW 2: RSI EXTREMES (NEW) ---
        st.write("")
        with st.container(border=True):
            st.subheader("📉 RSI Extremes (Oversold < 30 | Overbought > 70)")
            oversold = df[df['RSI'] <= 30].sort_values('RSI')
            overbought = df[df['RSI'] >= 70].sort_values('RSI', ascending=False)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**🔵 Potential Reversal (Oversold)**")
                st.dataframe(oversold[['Ticker', 'RSI', 'Price', '1h Change %']], hide_index=True, use_container_width=True)
            with c2:
                st.markdown("**🟠 Potential Exhaustion (Overbought)**")
                st.dataframe(overbought[['Ticker', 'RSI', 'Price', '1h Change %']], hide_index=True, use_container_width=True)

        # --- ROW 3: HOURLY TREND ---
        st.write("")
        with st.container(border=True):
            st.subheader("⏳ Hourly Trend Watch (±1.0%)")
            hourly = df[df['1h Change %'].abs() >= 1.0].sort_values('1h Change %', ascending=False)
            st.dataframe(hourly[['Ticker', 'Price', '1h Change %', 'RSI']], hide_index=True, use_container_width=True)

        st.divider()
        st.subheader("📊 Full Market Overview")
        st.dataframe(style_df(df.sort_values('2m Velocity %', ascending=False).style).format(precision=2), use_container_width=True, height=400, hide_index=True)

    else:
        st.warning("Awaiting market data stream...")

    st.sidebar.markdown(f"**Last Sync:** {datetime.now().strftime('%H:%M:%S')}")
    time.sleep(120)
    st.rerun()

if __name__ == "__main__":
    main()