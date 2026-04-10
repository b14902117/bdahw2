import streamlit as st
import yfinance as yf
import requests
from google import genai
import os

# --- 1. THE DATA FETCHING (CACHED) ---
@st.cache_data(ttl=3600)  # Standard cache for 1 hour
def fetch_fresh_data():
    # 1. Fetch MSTR Stock
    mstr = yf.Ticker("MSTR")
    df = mstr.history(period="1mo")
    
    # 2. Fetch BTC Price with Error Handling
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Check if 'bitcoin' is actually in the response
        if 'bitcoin' in data:
            btc_price = data['bitcoin']['usd']
        else:
            st.warning("CoinGecko rate limit reached. Using fallback price.")
            btc_price = 70000.0  # Safe fallback for calculation
            
    except Exception as e:
        st.error(f"Price fetch failed: {e}")
        btc_price = 70000.0 # Safe fallback
    
    # 3. Calculation
    df['mNAV'] = (df['Close'] * 194700000) / (252220 * btc_price)
    return df, btc_price

if st.button("Generate 1 month report"):
    # Initial load
    df, btc_price = fetch_fresh_data()

    # --- 2. MAIN UI ---
    st.title("MSTR Dashboard")
    st.line_chart(df['mNAV'])

    # --- 3. THE "GENERATE REPORT" LOGIC ---
    st.divider() # Visual line

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    if st.button("Generate AI Report"):
        with st.spinner("Refetching live data and consulting AI..."):
            
            latest_mnav = round(df['mNAV'].iloc[-1], 2)

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"The updated mNAV for MSTR is {latest_mnav} and BTC is ${btc_price}. Generate summaries or insights based on the data and provide interpretation or trend analysis"
            )
            
            # Display the result in a nice box
            st.subheader("AI Insight Report")
            st.success(response.text)
            st.info(f"Data last updated at: {df.index[-1].strftime('%Y-%m-%d %H:%M:%S')}")
