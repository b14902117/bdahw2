import streamlit as st
import yfinance as yf
import requests
from google import genai
import os

st.header("MSTR and Bitcoin Analyis with Gemini")
st.subheader("deployed by b14902117")
st.write("If [Generate one month report + Gemini review] failed, press again")

# --- 1. THE DATA FETCHING (CACHED) ---
@st.cache_data(ttl=3600)  # Standard cache for 1 hour
def fetch_fresh_data():
    # 1. Fetch MSTR Stock
    mstr = yf.Ticker("MSTR")
    df = mstr.history(period="1y")
    # 2. Fetch BTC Price with Error Handling
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?vs_currencies=usd&ids=bitcoin&x_cg_demo_api_key=CG-cERq4FTNaXGuHTh5Vct8gh1D"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Check if 'bitcoin' is actually in the response
        if 'bitcoin' in data:
            btc_price = data['bitcoin']['usd']
        else:
            #st.warning("CoinGecko rate limit reached. Using fallback price.")
            btc_price = 71868.4  # Safe fallback for calculation
            
    except Exception as e:
        st.error(f"Price fetch failed: {e}")
        btc_price = 71868.4 # Safe fallback
    
    # 3. Calculation
    df['mNAV'] = (df['Close'] * 194700000) / (252220 * btc_price)
    return df, btc_price

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

if st.button("Generate one month report + Gemini review"):
    # Initial load
    df, btc_price = fetch_fresh_data()

    latest_mnav = round(df['mNAV'].iloc[-1], 2)
    
    st.header(f"current mNAV: {latest_mnav}")

    if latest_mnav <= 0.80:
        st.info("Deep Discount")
        st.write("Distress/Skepticism: Investors are pricing the company at less than its Bitcoin is worth. This usually happens if the company has massive debt, high overhead, or the market fears they will be forced to sell their BTC.")
    elif latest_mnav > 0.80 and latest_mnav <= 1.00:
        st.info("Minor Discount")
        st.write('Fair Value/Efficiency: Common for companies with steady operations. It suggests the market views the stock as a near-perfect proxy for the spot price, with little expectation of "extra" BTC growth.')
    elif latest_mnav > 1.00 and latest_mnav <= 1.30:
        st.info("Healthy Premium")
        st.write('Confidence: The "sweet spot." It indicates the market trusts management to manage the BTC stack efficiently. The company can now issue new shares to buy more BTC without diluting existing holders.')
    elif latest_mnav > 1.00 and latest_mnav <= 1.30:
        st.info("Growth Premium")
        st.write('The Accumulation Engine: Typical for companies like MicroStrategy. Investors are paying extra because they expect the company to use its high stock price to "arbitrage" the market and buy even more Bitcoin.')
    else:
        st.info("Euphoric / Speculative")
        st.write('High Leverage: The market is "front-running" a massive Bitcoin rally. While this allows for massive BTC buys, it makes the stock highly volatile.' + "If Bitcoin's price drops," + 'this premium can "collapse" rapidly.')


    st.title("mNAV (MSTR) in the past 1 year")
    st.line_chart(df['mNAV'])

    # --- 3. THE "GENERATE REPORT" LOGIC ---
    st.divider() # Visual line
    st.header("AI insight")
    with st.spinner("Refetching live data and consulting AI..."):

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"The updated mNAV for MSTR is {latest_mnav} and BTC is ${btc_price}. Generate summaries or insights based on the data and provide interpretation or trend analysis"
        )
        
        # Display the result in a nice box
        st.subheader("AI Insight Report")
        st.success(response.text)
        st.info(f"Data last updated at: {df.index[-1].strftime('%Y-%m-%d %H:%M:%S')}")
