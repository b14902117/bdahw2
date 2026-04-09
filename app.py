import streamlit as st
import yfinance as yf
import requests
import google.generativeai as genai
import os

# --- 1. THE DATA FETCHING (CACHED) ---
@st.cache_data(ttl=3600)  # Standard cache for 1 hour
def fetch_fresh_data():
    # Fetch MSTR Stock
    mstr = yf.Ticker("MSTR")
    df = mstr.history(period="1mo")
    
    # Fetch BTC Price
    btc_price = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd").json()['bitcoin']['usd']
    
    # Simple mNAV calc (simplified for example)
    df['mNAV'] = (df['Close'] * 194700000) / (252220 * btc_price)
    return df, btc_price

# Initial load
df, btc_price = fetch_fresh_data()

# --- 2. MAIN UI ---
st.title("MSTR Dashboard")
st.line_chart(df['mNAV'])

# --- 3. THE "GENERATE REPORT" LOGIC ---
st.divider() # Visual line

if st.button("🔄 Generate Report & Update Data"):
    with st.spinner("Refetching live data and consulting AI..."):
        # STEP A: Clear the cache so the next call gets fresh data
        fetch_fresh_data.clear()
        
        # STEP B: Get the new data
        new_df, new_btc = fetch_fresh_data()
        
        # STEP C: Trigger the AI Report
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        latest_mnav = round(new_df['mNAV'].iloc[-1], 2)
        prompt = f"The updated mNAV for MSTR is {latest_mnav} and BTC is ${new_btc}. Write a 3-sentence investment summary."
        
        response = model.generate_content(prompt)
        
        # Display the result in a nice box
        st.subheader("AI Insight Report")
        st.success(response.text)
        st.info(f"Data last updated at: {new_df.index[-1].strftime('%Y-%m-%d %H:%M:%S')}")
