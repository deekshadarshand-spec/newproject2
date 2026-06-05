import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------

st.set_page_config(
    page_title="Public WiFi Hotspot Analyzer",
    page_icon="📶",
    layout="wide"
)

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------

@st.cache_data
def load_data():

    df = pd.read_csv("data/wifi_sessions.csv")

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df["hour"] = df["timestamp"].dt.hour

    df["date"] = df["timestamp"].dt.date

    df["data_mb"] = (
        df["bytes_transferred"]
        /1024
        /1024
    )

    return df

df = load_data()

# -------------------------------------------------
# TITLE
# -------------------------------------------------

st.title("📶 Public Wi-Fi Hotspot Usage Analyzer")

st.markdown("""
Analyze hotspot traffic,
peak hours,
crowd density,
user behavior,
and network utilization.
""")

# -------------------------------------------------
# KPI SECTION
# -------------------------------------------------

total_sessions = len(df)

unique_users = df["mac_address_hashed"].nunique()

total_data = df["data_mb"].sum()

avg_duration = (
    df["connection_duration_secs"]
    .mean()/60
)

active_hotspots = (
    df["node_id"].nunique()
)

col1,col2,col3,col4,col5 = st.columns(5)

col1.metric(
    "Sessions",
    f"{total_sessions:,}"
)

col2.metric(
    "Users",
    f"{unique_users:,}"
)

col3.metric(
    "Data Used",
    f"{total_data:,.0f} MB"
)

col4.metric(
    "Avg Duration",
    f"{avg_duration:.1f} min"
)

col5.metric(
    "Hotspots",
    active_hotspots
)

st.divider()

# -------------------------------------------------
# TOP HOTSPOTS
# -------------------------------------------------

st.subheader("🔥 Top Hotspots")

hotspots = (
    df.groupby("node_id")
    .size()
    .reset_index(name="sessions")
    .sort_values(
        "sessions",
        ascending=False
    )
)

fig1 = px.bar(
    hotspots.head(10),
    x="node_id",
    y="sessions",
    text="sessions",
    title="Top 10 Busiest Hotspots"
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

# -------------------------------------------------
# HOURLY TREND
# -------------------------------------------------

st.subheader("⏰ Peak Hour Analysis")

hourly = (
    df.groupby("hour")
    .size()
    .reset_index(name="sessions")
)

fig2 = px.line(
    hourly,
    x="hour",
    y="sessions",
    markers=True,
    title="Hourly Usage Pattern"
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

# -------------------------------------------------
# DAILY TREND
# -------------------------------------------------

st.subheader("📈 Daily Traffic Trend")

daily = (
    df.groupby("date")
    .size()
    .reset_index(name="sessions")
)

fig3 = px.area(
    daily,
    x="date",
    y="sessions",
    title="Daily Session Trend"
)

st.plotly_chart(
    fig3,
    use_container_width=True
)

# -------------------------------------------------
# SESSION DURATION
# -------------------------------------------------

st.subheader("⌛ Session Duration Distribution")

fig4 = px.histogram(
    df,
    x="connection_duration_secs",
    nbins=30,
    title="Session Duration"
)

st.plotly_chart(
    fig4,
    use_container_width=True
)

# -------------------------------------------------
# DATA CONSUMPTION
# -------------------------------------------------

st.subheader("📦 Data Usage Distribution")

fig5 = px.histogram(
    df,
    x="data_mb",
    nbins=30,
    title="Data Consumption"
)

st.plotly_chart(
    fig5,
    use_container_width=True
)

# -------------------------------------------------
# HOTSPOT DATA TRAFFIC
# -------------------------------------------------

st.subheader("📊 Traffic Per Hotspot")

traffic = (
    df.groupby("node_id")
    ["data_mb"]
    .sum()
    .reset_index()
    .sort_values(
        "data_mb",
        ascending=False
    )
)

fig6 = px.pie(
    traffic.head(10),
    names="node_id",
    values="data_mb",
    title="Traffic Share by Hotspot"
)

st.plotly_chart(
    fig6,
    use_container_width=True
)

# -------------------------------------------------
# USER ACTIVITY HEATMAP
# -------------------------------------------------

st.subheader("🌡 Hourly Activity Heatmap")

heatmap_data = (
    df.groupby(["hour","node_id"])
    .size()
    .reset_index(name="sessions")
)

fig7 = px.density_heatmap(
    heatmap_data,
    x="hour",
    y="node_id",
    z="sessions",
    title="Hotspot Activity Heatmap"
)

st.plotly_chart(
    fig7,
    use_container_width=True
)

# -------------------------------------------------
# INSIGHTS
# -------------------------------------------------

st.subheader("📝 Key Insights")

peak_hour = hourly.loc[
    hourly["sessions"].idxmax()
]["hour"]

busiest_hotspot = hotspots.iloc[0]["node_id"]

st.success(
    f"Peak Usage Hour: {peak_hour}:00"
)

st.success(
    f"Most Crowded Hotspot: {busiest_hotspot}"
)

st.success(
    f"Average Session Duration: {avg_duration:.2f} minutes"
)

st.success(
    f"Total Data Consumed: {total_data:,.2f} MB"
)

# -------------------------------------------------
# RAW DATA
# -------------------------------------------------

with st.expander("View Dataset"):

    st.dataframe(
        df,
        use_container_width=True
    )

# -------------------------------------------------
# FOOTER
# -------------------------------------------------

st.markdown("---")

st.markdown(
"""
### Smart City Wi-Fi Analytics Dashboard

Built using:

✅ Python

✅ Pandas

✅ Plotly

✅ Streamlit

Hackathon Project
"""
)
