import streamlit as st
import pandas as pd
import os
from pymongo import MongoClient

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Sansad Intelligence Dashboard",
    page_icon="🇮🇳",
    layout="wide"
)

# ---------------- DB CONNECTION ----------------
@st.cache_resource
def load_data():
    MONGO_URI = os.getenv("MONGO_URI")
    client = MongoClient(MONGO_URI)
    db = client["sansad"]
    collection = db["attendance"]

    data = list(collection.find({}, {"_id": 0}))
    return pd.DataFrame(data)

df = load_data()

# ---------------- TITLE ----------------
st.markdown(
    "<h1 style='text-align: center;'>🇮🇳 Sansad Intelligence Dashboard</h1>",
    unsafe_allow_html=True
)

# ---------------- CHECK ----------------
if df.empty:
    st.error("❌ No data found. Run your scraper to populate MongoDB Atlas.")
    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.header("Filters")

# Lok Sabha filter
loksabha = st.sidebar.selectbox(
    "Select Lok Sabha",
    sorted(df["loksabha"].dropna().unique())
)

# Session filter (dynamic)
session = st.sidebar.selectbox(
    "Select Session",
    sorted(df[df["loksabha"] == loksabha]["session"].dropna().unique())
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

c1.metric("Total MPs", len(filtered))
c2.metric("Avg Attendance", round(filtered["attendance_days"].mean(), 2))
c3.metric("Max Attendance", filtered["attendance_days"].max())
c4.metric("Min Attendance", filtered["attendance_days"].min())

# ---------------- TOP MPs ----------------
st.subheader("🏆 Top 10 MPs")

top = filtered.sort_values("attendance_days", ascending=False).head(10)
top["Rank"] = range(1, len(top) + 1)

st.dataframe(top[["Rank", "name", "state", "attendance_days"]])

# ---------------- LOW MPs ----------------
st.subheader("⚠️ Lowest 10 MPs")

low = filtered.sort_values("attendance_days").head(10)
low["Rank"] = range(1, len(low) + 1)

st.dataframe(low[["Rank", "name", "state", "attendance_days"]])

# ---------------- STATE ANALYSIS ----------------
st.subheader("📊 State-wise Attendance")

state_data = filtered.groupby("state")["attendance_days"].sum()
st.bar_chart(state_data)

# ---------------- SESSION TREND ----------------
st.subheader("📈 Attendance Trend (All Sessions of Selected Lok Sabha)")

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

query = st.text_input("Enter MP name")

if query:
    result = filtered[
        filtered["name"].str.contains(query, case=False, na=False)
    ]
    st.dataframe(result)

# ---------------- INSIGHTS ----------------
st.subheader("🧠 Insights")

zero_att = len(filtered[filtered["attendance_days"] == 0])
high_att = len(filtered[filtered["attendance_days"] > filtered["attendance_days"].mean()])

st.write(f"❗ MPs with ZERO attendance: {zero_att}")
st.write(f"🔥 High performers (> avg): {high_att}")

# ---------------- RAW DATA ----------------
with st.expander("📂 View Raw Data"):
    st.dataframe(filtered)