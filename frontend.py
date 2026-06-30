import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. Page configuration
st.set_page_config(page_title="AQI Intelligence", page_icon="🌍", layout="wide")

# --- PROFESSIONAL HEADER BAR (Theme Matched) ---
st.markdown("""
    <style>
    .header-bar {
        background-color: #455A64; /* Matched to Chart Color */
        padding: 25px;
        border-radius: 0px 0px 15px 15px;
        margin-bottom: 35px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        text-align: left;
    }
    .header-title {
        color: #FFFFFF; /* White text for contrast */
        font-family: 'Helvetica Neue', sans-serif;
        font-size: 36px;
        font-weight: 800;
        letter-spacing: 1px;
        margin: 0;
    }
    .header-subtitle {
        color: #CFD8DC; /* Light Blue-Grey for subtitle */
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 5px;
    }
    </style>
    
    <div class="header-bar">
        <div class="header-subtitle">Environmental Monitoring Intelligence</div>
        <div class="header-title">REAL-TIME AQI TRACKER</div>
    </div>
    """, unsafe_allow_html=True)

# 3. SEARCH AREA
with st.container():
    col_in1, col_in2 = st.columns([4, 1])
    with col_in1:
        city = st.text_input("SEARCH", value="Islamabad", label_visibility="collapsed", placeholder="Enter city name (e.g. London, Tokyo, Lahore)...")
    with col_in2:
        run_button = st.button("RUN ANALYSIS", use_container_width=True)

if run_button:
    try:
        # Fetch Data from Backend
        curr_resp = requests.get(f"http://127.0.0.1:8000/aqi?city={city}")
        curr_data = curr_resp.json()

        if "error" in curr_data:
            st.error("City not found. Please check the spelling.")
        else:
            # Extract Main Metrics
            aqi_num = curr_data.get('aqi_reading')
            status = curr_data.get('status')
            safety = curr_data.get('safety')
            p_data = curr_data.get('pollutants', {})

            # --- ROW 1: KEY METRICS ---
            st.write("### Dashboard Overview")
            m1, m2, m3 = st.columns(3)
            m1.metric("US-AQI SCORE", aqi_num)
            m2.metric("STATUS", status)
            m3.metric("SAFETY", safety)
            st.write("---")

            # --- ROW 2: MAP & POLLUTANTS ---
            left, right = st.columns(2)
            with left:
                st.subheader(f"📍 Location: {city.title()}")
                map_df = pd.DataFrame({'lat': [curr_data['lat']], 'lon': [curr_data['lon']]})
                st.map(map_df, zoom=11)
            
            with right:
                st.subheader("📊 Pollutant Breakdown")
                chart_df = pd.DataFrame({
                    'Pollutant': [k.upper() for k in p_data.keys()],
                    'Value': list(p_data.values())
                })
                fig_poll = px.bar(chart_df, x='Pollutant', y='Value', color='Value', 
                                  color_continuous_scale='Reds', template="plotly_white")
                st.plotly_chart(fig_poll, use_container_width=True)

            # --- ROW 3: 5-DAY FORECAST ---
            st.write("---")
            st.subheader("🗓️ 5-Day Air Quality Forecast")
            fore_resp = requests.get(f"http://127.0.0.1:8000/forecast?city={city}")
            fore_data = fore_resp.json()

            if "forecast" in fore_data:
                f_df = pd.DataFrame(fore_data['forecast'])
                f_df['date'] = pd.to_datetime(f_df['date'], unit='s').dt.strftime('%b %d')

                fig_fore = px.bar(
                    f_df, x='date', y='aqi_score', text='aqi_score',
                    labels={'aqi_score': 'AQI Score', 'date': 'Date'},
                    color_discrete_sequence=['#455A64']
                )
                fig_fore.update_traces(textposition='outside', opacity=0.85)
                fig_fore.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    yaxis=dict(range=[0, 500]),
                    xaxis_title=None
                )
                st.plotly_chart(fig_fore, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Connection Error: Ensure your FastAPI server is running on port 8000. ({e})")
        
        
        