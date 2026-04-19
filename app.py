import streamlit as st
from pymongo import MongoClient
import pandas as pd
import os


from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Sansad Dashboard",
    page_icon="🇮🇳",   # 👈 THIS is the flag in browser tab
    layout="wide"
)

# ---------------- LOAD DATA ----------------
@st.cache_resource
def load_data():
    client = MongoClient("mongodb://127.0.0.1:27017/")
    db = client["sansad"]
    data = list(db["attendance"].find({}, {"_id": 0}))
    return pd.DataFrame(data)

df = load_data()

st.title("🇮🇳 Sansad Multi-Session Dashboard")

if df.empty:
    st.error("No data found")
    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.header("Filters")

# Lok Sabha filter
loksabha = st.sidebar.selectbox(
    "Select Lok Sabha",
    sorted(df["loksabha"].unique())
)

# Session filter (depends on Lok Sabha)
session = st.sidebar.selectbox(
    "Select Session",
    sorted(df[df["loksabha"] == loksabha]["session"].unique())
)

# State filter
state = st.sidebar.selectbox(
    "Select State",
    ["All"] + sorted(df["state"].dropna().unique())
)

# ---------------- FILTER ----------------
filtered = df[
    (df["loksabha"] == loksabha) &
    (df["session"] == session)
]

if state != "All":
    filtered = filtered[filtered["state"] == state]

# ---------------- KPI ----------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("MP Count", len(filtered))
c2.metric("Avg Attendance", round(filtered["attendance_days"].mean(), 2))
c3.metric("Max Attendance", filtered["attendance_days"].max())
c4.metric("Min Attendance", filtered["attendance_days"].min())

# ---------------- TOP MPs ----------------
st.subheader("🏆 Top MPs")

top = filtered.sort_values("attendance_days", ascending=False).head(10)
st.dataframe(top[["name", "state", "attendance_days"]])

# ---------------- LOW MPs ----------------
st.subheader("⚠️ Lowest MPs")

low = filtered.sort_values("attendance_days").head(10)
st.dataframe(low[["name", "state", "attendance_days"]])

# ---------------- STATE ANALYSIS ----------------
st.subheader("📊 State-wise Attendance")

state_data = filtered.groupby("state")["attendance_days"].sum()
st.bar_chart(state_data)

# ---------------- SESSION TREND ----------------
st.subheader("📈 Attendance Trend (All Sessions)")

trend = df[df["loksabha"] == loksabha].groupby("session")["attendance_days"].mean()
st.line_chart(trend)

# ---------------- BEST MP PER STATE ----------------
st.subheader("🌟 Best MP per State")

best = filtered.loc[
    filtered.groupby("state")["attendance_days"].idxmax()
]

st.dataframe(best[["state", "name", "attendance_days"]])

# ---------------- SEARCH ----------------
st.subheader("🔍 Search MP")

query = st.text_input("Enter name")

if query:
    result = filtered[
        filtered["name"].str.contains(query, case=False)
    ]
    st.dataframe(result)

# ---------------- INSIGHTS ----------------
st.subheader("🧠 Insights")

zero_att = len(filtered[filtered["attendance_days"] == 0])
high_att = len(filtered[filtered["attendance_days"] > filtered["attendance_days"].mean()])

st.write(f"❗ MPs with ZERO attendance: {zero_att}")
st.write(f"🔥 High performers: {high_att}")

# ---------------- RAW ----------------
with st.expander("📂 View Data"):
    st.dataframe(filtered)