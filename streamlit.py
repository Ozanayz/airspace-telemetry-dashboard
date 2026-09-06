import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import requests

#wp name
st.set_page_config(page_title="Airspace Monitoring Dashboard", layout="wide", page_icon=":airplane:")
st.title("Operational Airspace Monitoring Dashboard")


#database
conn = sqlite3.connect("airspace.db")
query = '''
SELECT 
    f.flight_id,
    f.icao24,
    f.callsign,
    f.airline_code,
    a.origin_country,
    t.latitude,
    t.longitude,
    ROUND(t.baro_alt * 3.28084) AS altitude_ft,
    ROUND(t.velocity_knots, 1) AS velocity_knots,
    ROUND(t.vertical_rate_fpm, 1) AS vertical_rate_fpm,
    CASE 
        WHEN t.vertical_rate_fpm > 500 THEN 'Climb'
        WHEN t.vertical_rate_fpm < -500 THEN 'Descent'
        ELSE 'Cruise'
    END AS flight_phase,
    CASE 
        WHEN ABS(t.vertical_rate_fpm) >= 2500 THEN 'Anomaly'
        ELSE 'Normal'
    END AS operation_status
FROM flights f
JOIN telemetry_logs t ON f.flight_id = t.flight_id
JOIN aircraft a ON f.icao24 = a.icao24
WHERE t.latitude IS NOT NULL 
  AND t.longitude IS NOT NULL;
'''
df = pd.read_sql_query(query, conn)
conn.close()

#Sidebar
airline = sorted([x for x in df["airline_code"].dropna().unique()])

multiselect_val = st.sidebar.multiselect("Select Airline", airline)


#Filter
if multiselect_val:
    filtered = df[df["airline_code"].isin(multiselect_val)]
else:
    filtered = df


#Metrics
col1,col2,col3=st.columns(3)
col1.metric(value=filtered["flight_id"].nunique(), label="Total Active Flights")

col2.metric(label="Monitored Airlines", value=filtered["airline_code"].nunique())

anomaly=filtered[filtered["operation_status"]=='Anomaly']["flight_id"].nunique()
col3.metric(value=anomaly, label="Critical Anomalies")


#Map
fig_map = px.scatter_geo(
    filtered,
    lat="latitude",
    lon="longitude",
    color="flight_phase",
    color_discrete_map={"Climb": "#2ecc71", "Cruise": "#3498db", "Descent": "#e74c3c"},
    symbol="operation_status",
    hover_name="callsign",
    hover_data={
        "airline_code": True,
        "altitude_ft": ":,d",
        "velocity_knots": ":.1f",
        "vertical_rate_fpm": True,
        "latitude": False,
        "longitude": False
    },
    labels={
        "flight_phase":"Flight Phase",
        "operation_status":"Operational Status",
        "callsign":"Callsign"
    },
    title="Air Traffic Overview",
    height=600,
    custom_data=["callsign", "icao24"]
)

fig_map.update_geos(
    resolution=50,
    showcountries=True,
    showcoastlines=True,
    showland=True,
    countrycolor="#2c3e50",
    coastlinecolor="#7f8c8d",
    landcolor="#c9cdd1",
    fitbounds="locations",
)


map_events = st.plotly_chart(
    fig_map, 
    use_container_width=True, 
    on_select="rerun", 
    selection_mode="points",
    key="airspace_map"
)


# 2 Col
col1,col2=st.columns([1,1])

with col1:
    filtered_df = filtered[filtered["airline_code"].notna()].groupby("airline_code")["flight_id"].nunique().reset_index(name="Total Flights").sort_values(by="Total Flights", ascending=False).head(10)

    st.subheader("Total Top 10 Flights")
    fig = px.bar(
            filtered_df,
            x="airline_code",
            y="Total Flights",
            color="Total Flights",
            text="Total Flights",
            color_continuous_scale="blues",
            labels={"airline_code":"Airline Code"}
        )
    
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=30, b=20), bargap=0.05)
    fig.update_traces(textposition='outside')

    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Vertical Rate Anomalies (|V.Rate| >= 2500 fpm)")
    df_anomaly = filtered[filtered["operation_status"]=='Anomaly'][
        ["callsign", "airline_code", "altitude_ft", "velocity_knots", "vertical_rate_fpm"]].sort_values("vertical_rate_fpm", key=abs,ascending=False)

    if not df_anomaly.empty:
        st.dataframe(df_anomaly, height=350, use_container_width=True)
    else:
        st.info("No anomaly with this callsign/s")


st.divider()

st.subheader("Selected Aircraft Details & Spotter Photo")

selected_points = map_events.get("selection", {}).get("points", [])

if selected_points:
    custom_data=selected_points[0].get("customdata", [])
    selected_callsign=custom_data[0]
    raw_icao24=custom_data[1]
    target_icao=str(raw_icao24).strip().lower()

    selected_row=filtered[filtered["callsign"]==selected_callsign].iloc[0]

    # 2 Col
    img_col, info_col = st.columns([1.5, 1])

    with img_col:
        api_url=f"https://api.planespotters.net/pub/photos/hex/{target_icao}"
        headers={"User-Agent": "AirspaceAnalyticsApp/1.0 (contact: info@example.com)"}

        try:
            res=requests.get(api_url, headers=headers, timeout=5)
            if res.status_code == 200:
                veri=res.json()
                photo = veri.get("photos", [])
                if photo:
                    resim_url=photo[0]["thumbnail_large"]["src"]
                    fotografci=photo[0].get("photographer", "Unknown")
                    st.image(resim_url, caption=f"Photographer : {fotografci} (planespotters.net)", width="stretch")
                else:
                    st.info(f"No photo found for ICAO24 : {target_icao.upper()}")
            else:
                 st.info("Photo service unavailable")
        except Exception as e:
             st.error(f"Connection Error: {e}")

    with info_col:
        st.write(f"**Origin Country:** {selected_row["origin_country"]}")
        st.write(f"**Callsign:** {selected_row["callsign"]}")
        st.write(f"**Latitude:** {selected_row["latitude"]}")
        st.write(f"**Longitude:** {selected_row["longitude"]}")
        st.write(f"**Altitude:** {selected_row["altitude_ft"]} **ft**")
        st.write(f"**Velocity:** {selected_row["velocity_knots"]} **knots**")
        st.write(f"**Vertical Rate:** {selected_row["vertical_rate_fpm"]}")
        st.write(f"**Flight Phase:** {selected_row["flight_phase"]}")

else:
                st.info("Click on an aircraft on the map to view its details and photo.")