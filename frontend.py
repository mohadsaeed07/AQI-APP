import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="AQI Intelligence", page_icon="🌍", layout="wide")

st.markdown(
    """
    <style>
    .header-bar {
        background-color: #455A64;
        padding: 25px;
        border-radius: 0px 0px 15px 15px;
        margin-bottom: 35px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        text-align: left;
    }
    .header-title {
        color: #FFFFFF;
        font-family: 'Helvetica Neue', sans-serif;
        font-size: 36px;
        font-weight: 800;
        letter-spacing: 1px;
        margin: 0;
    }
    .header-subtitle {
        color: #CFD8DC;
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
    """,
    unsafe_allow_html=True,
)

with st.container():
    col_in1, col_in2 = st.columns([4, 1])
    with col_in1:
        city = st.text_input(
            "SEARCH",
            value="Islamabad",
            label_visibility="collapsed",
            placeholder="Enter city name (e.g. London, Tokyo, Lahore)...",
        )
    with col_in2:
        run_button = st.button("RUN ANALYSIS", use_container_width=True)

if run_button:
    try:
        curr_resp = requests.get(f"{BACKEND_URL}/aqi?city={city}", timeout=15)

        if curr_resp.status_code == 404:
            st.error(f"City '{city}' not found. Please verify the spelling.")
        elif curr_resp.status_code != 200:
            error_msg = curr_resp.json().get("detail", "Failed to retrieve AQI data.")
            st.error(f"Error ({curr_resp.status_code}): {error_msg}")
        else:
            curr_data = curr_resp.json()
            aqi_num = curr_data.get("aqi_reading")
            status = curr_data.get("status")
            safety = curr_data.get("safety")
            p_data = curr_data.get("pollutants", {})

            st.write("### Dashboard Overview")
            m1, m2, m3 = st.columns(3)
            m1.metric("US-AQI SCORE", aqi_num)
            m2.metric("STATUS", status)
            m3.metric("SAFETY", safety)
            st.write("---")

            left, right = st.columns(2)
            with left:
                st.subheader(f"📍 Location: {city.title()}")
                map_df = pd.DataFrame(
                    {"lat": [curr_data["lat"]], "lon": [curr_data["lon"]]}
                )
                st.map(map_df, zoom=11)

            with right:
                st.subheader("📊 Pollutant Breakdown")
                chart_df = pd.DataFrame({
                    "Pollutant": [k.upper() for k in p_data],
                    "Value": list(p_data.values()),
                })
                fig_poll = px.bar(
                    chart_df,
                    x="Pollutant",
                    y="Value",
                    color="Value",
                    color_continuous_scale="Reds",
                    template="plotly_white",
                )
                st.plotly_chart(fig_poll, use_container_width=True)

            st.write("---")
            st.subheader("🗓️ 5-Day Air Quality Forecast")
            fore_resp = requests.get(f"{BACKEND_URL}/forecast?city={city}", timeout=15)

            if fore_resp.status_code == 200:
                fore_data = fore_resp.json()
                if "forecast" in fore_data:
                    f_df = pd.DataFrame(fore_data["forecast"])
                    f_df["date"] = pd.to_datetime(f_df["date"], unit="s").dt.strftime("%b %d")

                    fig_fore = px.bar(
                        f_df,
                        x="date",
                        y="aqi_score",
                        text="aqi_score",
                        labels={"aqi_score": "AQI Score", "date": "Date"},
                        color_discrete_sequence=["#455A64"],
                    )
                    fig_fore.update_traces(textposition="outside", opacity=0.85)
                    fig_fore.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        yaxis={"range": [0, 500]},
                        xaxis_title=None,
                    )
                    st.plotly_chart(fig_fore, use_container_width=True)
            else:
                st.warning("Could not load 5-day forecast at this time.")

    except Exception as e:
        st.error(f"⚠️ Connection Error: Unable to reach backend at {BACKEND_URL}. ({e})")
