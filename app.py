import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Public WiFi Hotspot Analyzer",
    page_icon="📶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 16px;
        border-left: 4px solid #4e89e8;
    }
    .stMetric label { font-size: 13px !important; color: #555 !important; }
    section[data-testid="stSidebar"] { background: #1a1f36; }
    section[data-testid="stSidebar"] * { color: #e0e6ff !important; }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMultiSelect label { color: #aab4d9 !important; }
    div[data-testid="stExpander"] { border: 1px solid #e0e0e0; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour"]      = df["timestamp"].dt.hour
    df["date"]      = df["timestamp"].dt.date
    df["day_name"]  = df["timestamp"].dt.day_name()
    df["week"]      = df["timestamp"].dt.isocalendar().week.astype(int)
    df["data_mb"]   = df["bytes_transferred"] / 1024 / 1024
    df["duration_min"] = df["connection_duration_secs"] / 60
    return df

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.markdown("## 📶 WiFi Analyzer")
    st.markdown("---")

    uploaded = st.file_uploader(
        "Upload CSV dataset",
        type=["csv"],
        help="Must contain: timestamp, node_id, mac_address_hashed, connection_duration_secs, bytes_transferred",
    )

    st.markdown("### Filters")

    data_path = "data/wifi_sessions.csv"

    try:
        raw = load_data(data_path) if uploaded is None else load_data(uploaded)
    except FileNotFoundError:
        st.error("❌ data/wifi_sessions.csv not found. Upload a file or run generate_dataset.py first.")
        st.stop()

    # Date range
    min_date = raw["date"].min()
    max_date = raw["date"].max()
    date_range = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    # Node filter
    all_nodes = sorted(raw["node_id"].unique())
    selected_nodes = st.multiselect(
        "Hotspot nodes",
        options=all_nodes,
        default=all_nodes,
    )

    # Hour range
    hour_range = st.slider("Hour of day", 0, 23, (0, 23))

    st.markdown("---")
    st.markdown("### About")
    st.markdown(
        "Smart City Wi-Fi Analytics Dashboard  \n"
        "Built with Python · Pandas · Plotly · Streamlit"
    )

# --------------------------------------------------
# APPLY FILTERS
# --------------------------------------------------

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range[0]

df = raw[
    (raw["date"] >= start_date)
    & (raw["date"] <= end_date)
    & (raw["node_id"].isin(selected_nodes))
    & (raw["hour"] >= hour_range[0])
    & (raw["hour"] <= hour_range[1])
].copy()

if df.empty:
    st.warning("No data matches the selected filters. Adjust the sidebar options.")
    st.stop()

# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("📶 Public Wi-Fi Hotspot Usage Analyzer")
st.caption(
    f"Showing **{len(df):,}** sessions · "
    f"{start_date} → {end_date} · "
    f"{len(selected_nodes)} node(s) · "
    f"Hours {hour_range[0]}:00 – {hour_range[1]}:00"
)

# --------------------------------------------------
# KPI ROW
# --------------------------------------------------

total_sessions  = len(df)
unique_users    = df["mac_address_hashed"].nunique()
total_data_gb   = df["data_mb"].sum() / 1024
avg_duration    = df["duration_min"].mean()
active_nodes    = df["node_id"].nunique()
repeat_users    = (
    df.groupby("mac_address_hashed").size().gt(1).sum()
)
repeat_pct      = repeat_users / unique_users * 100 if unique_users else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Sessions",   f"{total_sessions:,}")
c2.metric("Unique Users",     f"{unique_users:,}")
c3.metric("Data Transferred", f"{total_data_gb:.2f} GB")
c4.metric("Avg Duration",     f"{avg_duration:.1f} min")
c5.metric("Active Nodes",     active_nodes)
c6.metric("Repeat Users",     f"{repeat_pct:.1f}%")

st.divider()

# --------------------------------------------------
# ROW 1 — TOP HOTSPOTS + HOURLY TREND
# --------------------------------------------------

col_a, col_b = st.columns([1, 1])

with col_a:
    st.subheader("🔥 Top Hotspots by Sessions")
    hotspots = (
        df.groupby("node_id")
        .agg(sessions=("node_id", "count"), data_gb=("data_mb", lambda x: x.sum() / 1024))
        .reset_index()
        .sort_values("sessions", ascending=False)
    )
    fig1 = px.bar(
        hotspots.head(10),
        x="sessions",
        y="node_id",
        orientation="h",
        color="data_gb",
        color_continuous_scale="Blues",
        text="sessions",
        labels={"node_id": "Node", "sessions": "Sessions", "data_gb": "Data (GB)"},
        title="Top 10 Busiest Hotspots",
    )
    fig1.update_traces(textposition="outside")
    fig1.update_layout(
        yaxis=dict(autorange="reversed"),
        coloraxis_colorbar=dict(title="GB"),
        margin=dict(l=10, r=10, t=40, b=10),
        height=360,
    )
    st.plotly_chart(fig1, use_container_width=True)

with col_b:
    st.subheader("⏰ Peak Hour Analysis")
    hourly = (
        df.groupby("hour")
        .agg(sessions=("node_id", "count"), avg_dur=("duration_min", "mean"))
        .reset_index()
    )
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2.add_trace(
        go.Bar(x=hourly["hour"], y=hourly["sessions"], name="Sessions",
               marker_color="#4e89e8", opacity=0.7),
        secondary_y=False,
    )
    fig2.add_trace(
        go.Scatter(x=hourly["hour"], y=hourly["avg_dur"].round(1),
                   name="Avg Duration (min)", mode="lines+markers",
                   line=dict(color="#f97316", width=2), marker=dict(size=5)),
        secondary_y=True,
    )
    fig2.update_layout(
        title="Hourly Usage & Avg Session Duration",
        xaxis=dict(title="Hour of Day", tickmode="linear", dtick=2),
        yaxis=dict(title="Sessions"),
        yaxis2=dict(title="Avg Duration (min)"),
        legend=dict(orientation="h", y=-0.2),
        margin=dict(l=10, r=10, t=40, b=10),
        height=360,
    )
    st.plotly_chart(fig2, use_container_width=True)

# --------------------------------------------------
# ROW 2 — DAILY TREND + DAY OF WEEK
# --------------------------------------------------

col_c, col_d = st.columns([2, 1])

with col_c:
    st.subheader("📈 Daily Traffic Trend")
    daily = (
        df.groupby("date")
        .agg(sessions=("node_id", "count"), data_mb=("data_mb", "sum"))
        .reset_index()
    )
    daily["rolling_7d"] = daily["sessions"].rolling(7, min_periods=1).mean().round(0)
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=daily["date"], y=daily["sessions"],
        fill="tozeroy", name="Daily Sessions",
        line=dict(color="#4e89e8", width=1.5),
        fillcolor="rgba(78,137,232,0.15)",
    ))
    fig3.add_trace(go.Scatter(
        x=daily["date"], y=daily["rolling_7d"],
        name="7-day Avg", line=dict(color="#f97316", width=2, dash="dash"),
    ))
    fig3.update_layout(
        title="Daily Session Trend with 7-Day Rolling Average",
        xaxis_title="Date", yaxis_title="Sessions",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(l=10, r=10, t=40, b=10),
        height=320,
    )
    st.plotly_chart(fig3, use_container_width=True)

with col_d:
    st.subheader("📅 Day of Week")
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow = (
        df.groupby("day_name")
        .size()
        .reindex(day_order)
        .reset_index(name="sessions")
    )
    fig4 = px.bar(
        dow, x="sessions", y="day_name", orientation="h",
        color="sessions", color_continuous_scale="Purples",
        title="Sessions by Day of Week",
        labels={"day_name": "", "sessions": "Sessions"},
    )
    fig4.update_layout(
        coloraxis_showscale=False,
        yaxis=dict(autorange="reversed"),
        margin=dict(l=10, r=10, t=40, b=10),
        height=320,
    )
    st.plotly_chart(fig4, use_container_width=True)

# --------------------------------------------------
# ROW 3 — DURATION + DATA DISTRIBUTION
# --------------------------------------------------

col_e, col_f = st.columns(2)

with col_e:
    st.subheader("⌛ Session Duration Distribution")
    fig5 = px.histogram(
        df, x="duration_min", nbins=40,
        color_discrete_sequence=["#4e89e8"],
        title="Session Duration (minutes)",
        labels={"duration_min": "Duration (min)", "count": "Sessions"},
    )
    fig5.add_vline(
        x=avg_duration, line_dash="dash",
        line_color="#f97316",
        annotation_text=f"Avg: {avg_duration:.1f} min",
        annotation_position="top right",
    )
    fig5.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=300)
    st.plotly_chart(fig5, use_container_width=True)

with col_f:
    st.subheader("📦 Data Consumption Distribution")
    fig6 = px.histogram(
        df, x="data_mb", nbins=40,
        color_discrete_sequence=["#22c55e"],
        title="Data Consumed per Session (MB)",
        labels={"data_mb": "Data (MB)", "count": "Sessions"},
    )
    fig6.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=300)
    st.plotly_chart(fig6, use_container_width=True)

# --------------------------------------------------
# ROW 4 — TRAFFIC SHARE + HEATMAP
# --------------------------------------------------

col_g, col_h = st.columns([1, 2])

with col_g:
    st.subheader("🥧 Traffic Share by Hotspot")
    traffic = (
        df.groupby("node_id")["data_mb"]
        .sum()
        .reset_index()
        .sort_values("data_mb", ascending=False)
    )
    fig7 = px.pie(
        traffic.head(10),
        names="node_id",
        values="data_mb",
        hole=0.42,
        title="Top 10 Nodes – Data Share",
        color_discrete_sequence=px.colors.sequential.Blues_r,
    )
    fig7.update_traces(textposition="inside", textinfo="percent+label")
    fig7.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=40, b=10),
        height=360,
    )
    st.plotly_chart(fig7, use_container_width=True)

with col_h:
    st.subheader("🌡️ Hourly Activity Heatmap")
    heatmap_data = (
        df.groupby(["hour", "node_id"])
        .size()
        .reset_index(name="sessions")
    )
    fig8 = px.density_heatmap(
        heatmap_data,
        x="hour", y="node_id", z="sessions",
        color_continuous_scale="Blues",
        title="Session Density — Hour × Node",
        labels={"hour": "Hour of Day", "node_id": "Node", "sessions": "Sessions"},
        nbinsx=24,
    )
    fig8.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        height=360,
        xaxis=dict(tickmode="linear", dtick=1),
    )
    st.plotly_chart(fig8, use_container_width=True)

# --------------------------------------------------
# ROW 5 — USER BEHAVIOUR
# --------------------------------------------------

st.subheader("👤 User Behaviour Analysis")

col_i, col_j = st.columns(2)

with col_i:
    user_sessions = df.groupby("mac_address_hashed").size().reset_index(name="sessions")
    fig9 = px.histogram(
        user_sessions, x="sessions", nbins=30,
        color_discrete_sequence=["#a855f7"],
        title="Sessions per User (frequency)",
        labels={"sessions": "Number of Sessions", "count": "Users"},
    )
    fig9.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=280)
    st.plotly_chart(fig9, use_container_width=True)

with col_j:
    top_users = (
        df.groupby("mac_address_hashed")
        .agg(sessions=("node_id", "count"), data_mb=("data_mb", "sum"), avg_dur=("duration_min", "mean"))
        .reset_index()
        .sort_values("sessions", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
    top_users.index += 1
    top_users.columns = ["MAC (hashed)", "Sessions", "Data (MB)", "Avg Duration (min)"]
    top_users["Data (MB)"] = top_users["Data (MB)"].round(1)
    top_users["Avg Duration (min)"] = top_users["Avg Duration (min)"].round(1)
    st.markdown("**Top 10 Power Users**")
    st.dataframe(top_users, use_container_width=True, height=260)

# --------------------------------------------------
# KEY INSIGHTS
# --------------------------------------------------

st.divider()
st.subheader("📝 Key Insights")

peak_hour      = int(hourly.loc[hourly["sessions"].idxmax(), "hour"])
busiest_node   = hotspots.iloc[0]["node_id"]
top_day        = dow.loc[dow["sessions"].idxmax(), "day_name"]
heaviest_user  = (
    df.groupby("mac_address_hashed")["data_mb"]
    .sum().idxmax()
)
heaviest_usage = df.groupby("mac_address_hashed")["data_mb"].sum().max()

i1, i2, i3, i4 = st.columns(4)
i1.success(f"🕐 Peak Hour: **{peak_hour}:00**")
i2.success(f"📡 Busiest Node: **{busiest_node}**")
i3.success(f"📅 Busiest Day: **{top_day}**")
i4.success(f"📊 Avg Session: **{avg_duration:.1f} min**")

i5, i6, i7, i8 = st.columns(4)
i5.info(f"📶 Total Sessions: **{total_sessions:,}**")
i6.info(f"👤 Unique Users: **{unique_users:,}**")
i7.info(f"🔁 Repeat User Rate: **{repeat_pct:.1f}%**")
i8.info(f"💾 Total Data: **{total_data_gb:.2f} GB**")

# --------------------------------------------------
# RAW DATA EXPLORER
# --------------------------------------------------

with st.expander("🗂️ Raw Data Explorer"):
    search = st.text_input("Filter by Node ID or MAC", "")
    display_df = df if not search else df[
        df["node_id"].str.contains(search, case=False) |
        df["mac_address_hashed"].str.contains(search, case=False)
    ]
    st.dataframe(
        display_df[[
            "timestamp", "node_id", "mac_address_hashed",
            "connection_duration_secs", "bytes_transferred", "data_mb", "duration_min"
        ]].rename(columns={
            "connection_duration_secs": "duration_secs",
            "bytes_transferred": "bytes",
            "data_mb": "data_mb",
            "duration_min": "duration_min",
        }),
        use_container_width=True,
        height=350,
    )
    st.caption(f"Showing {len(display_df):,} of {len(df):,} rows")

    csv_export = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download filtered data as CSV",
        data=csv_export,
        file_name="wifi_filtered.csv",
        mime="text/csv",
    )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#888;font-size:13px'>"
    "📶 Smart City Wi-Fi Analytics Dashboard &nbsp;·&nbsp; "
    "Built with Python · Pandas · Plotly · Streamlit &nbsp;·&nbsp; Hackathon Project"
    "</div>",
    unsafe_allow_html=True,
)
