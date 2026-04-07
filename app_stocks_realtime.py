import streamlit as st
import time
from datetime import datetime
from data_source_stocks import DataSource

st.set_page_config(page_title="Day Trading Monitor", layout="wide")

def style_velocity(val):
    if val >= 0.1: return 'background-color: #006400; color: white; font-weight: bold;'
    if val <= -0.1: return 'background-color: #8b0000; color: white; font-weight: bold;'
    return ''

def main():
    # --- HEADER ---
    st.title("⚡ Momentum Command Center")
    data_source = DataSource()
    alert_threshold = 0.10

    # Fetch Data
    with st.spinner("Analyzing market velocity..."):
        df = data_source.get_velocity_data()

    if not df.empty:
        # --- TOP QUADRANTS (Alerts) ---
        # We separate these into a distinct container at the top
        with st.container(border=True):
            st.subheader("🚨 Real-Time Velocity Alerts (±0.1% Move)")
            
            # Filter the alerts
            fast_up = df[df['2m Velocity %'] >= alert_threshold].sort_values('2m Velocity %', ascending=False)
            fast_down = df[df['2m Velocity %'] <= -alert_threshold].sort_values('2m Velocity %', ascending=True)

            q1, q2 = st.columns(2)
            
            with q1:
                st.markdown("### 📈 Bullish Spikes")
                if not fast_up.empty:
                    # Using a table for the top quadrant for high visibility
                    st.dataframe(fast_up[['Ticker', 'Index', '2m Velocity %', 'Price']], 
                                 hide_index=True, use_container_width=True)
                else:
                    st.info("No stocks trending up > 0.1% right now.")

            with q2:
                st.markdown("### 📉 Bearish Drops")
                if not fast_down.empty:
                    st.dataframe(fast_down[['Ticker', 'Index', '2m Velocity %', 'Price']], 
                                 hide_index=True, use_container_width=True)
                else:
                    st.info("No stocks trending down < -0.1% right now.")

        st.write("") # Spacer
        st.divider()

        # --- MAIN LIST SECTION ---
        st.subheader("📊 All Monitored Stocks (Full List)")
        
        # Styling and Sorting
        styled_df = df.sort_values('2m Velocity %', ascending=False).style.map(
            style_velocity, subset=['2m Velocity %']
        ).format(precision=3)

        st.dataframe(styled_df, use_container_width=True, height=500, hide_index=True)

    else:
        st.warning("Awaiting market data stream...")

    # --- FOOTER / REFRESH ---
    st.sidebar.markdown(f"**Last Sync:** {datetime.now().strftime('%H:%M:%S')}")
    st.sidebar.markdown("Refreshing every 120 seconds.")
    
    time.sleep(120)
    st.rerun()

if __name__ == "__main__":
    main()