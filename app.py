import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="FDA Submission Dashboard", layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel("data/fda_submissions_merged.xlsx", parse_dates=["Submission_Date"])
    df = df.dropna(subset=["Submission_Date"])  # drop rows for time-series
    df["Status"] = df["Status"].map({
        "AP": "Approved",
        "TA": "Tentative Approval"
    }).fillna(df["Status"])

    df["Submission_Type"] = df["Submission_Type"].map({
        "ORIG": "Original",
        "SUPPL": "Supplemental",
        "AP": "Abbreviated NDA",
        "TP": "Therapeutic"
    }).fillna(df["Submission_Type"])

    df["Sponsor"] = df["Sponsor"].fillna("Unknown")
    df["DrugName"] = df["DrugName"].fillna("Unknown")
    df["Submission_Year"] = df["Submission_Date"].dt.year
    return df

df = load_data()

# Sidebar filters
st.sidebar.title("🔍 Filter Submissions")

search = st.sidebar.text_input("Search Application No or Drug Name")
years = st.sidebar.slider("Submission Year", int(df["Submission_Year"].min()), int(df["Submission_Year"].max()),
                          (int(df["Submission_Year"].min()), int(df["Submission_Year"].max())))

selected_status = st.sidebar.multiselect("Submission Status", df["Status"].unique(), default=df["Status"].unique())
selected_sponsors = st.sidebar.multiselect("Sponsor", df["Sponsor"].unique()[:30], default=df["Sponsor"].unique()[:10])
selected_drugs = st.sidebar.multiselect("Drug Name", df["DrugName"].unique()[:50], default=df["DrugName"].unique()[:5])

# Apply filters
filtered = df[
    df["Submission_Year"].between(*years) &
    df["Status"].isin(selected_status) &
    df["Sponsor"].isin(selected_sponsors) &
    df["DrugName"].isin(selected_drugs)
]

if search:
    filtered = filtered[
        filtered["Application_No"].astype(str).str.contains(search, case=False) |
        filtered["DrugName"].str.contains(search, case=False)
    ]

# Header
st.title("💊 FDA Regulatory Submission Dashboard (DEMO)")

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Submissions", f"{len(filtered):,}")
col2.metric("Unique Sponsors", filtered["Sponsor"].nunique())
col3.metric("Approved", (filtered["Status"] == "Approved").sum())
col4.metric("Unique Drugs", filtered["DrugName"].nunique())

# Top Sponsors Bar Chart
st.subheader("🏢 Top Sponsors by Submission Count")
top_sponsors = filtered["Sponsor"].value_counts().nlargest(10).reset_index()
top_sponsors.columns = ["Sponsor", "Count"]
fig1 = px.bar(top_sponsors, x="Sponsor", y="Count", color="Sponsor", template="plotly_dark", text="Count")
fig1.update_layout(showlegend=False, xaxis_tickangle=45, height=400)
st.plotly_chart(fig1, use_container_width=True)

# Time Series Line Chart
st.subheader("📈 Monthly Submission Trend")
monthly = filtered.set_index("Submission_Date").resample("ME").size().reset_index(name="Submissions")
fig2 = px.line(monthly, x="Submission_Date", y="Submissions", markers=True,
               title="Monthly Submission Trend", template="plotly_dark")
fig2.update_layout(height=400)
st.plotly_chart(fig2, use_container_width=True)

# Pie Chart for Status
st.subheader("📂 Submission Status Distribution")
status_counts = filtered["Status"].value_counts().reset_index()
status_counts.columns = ["Status", "Count"]
fig3 = px.pie(status_counts, names="Status", values="Count", template="plotly_dark", hole=0.3)
fig3.update_traces(textinfo="percent+label")
st.plotly_chart(fig3, use_container_width=True)

# Submission Type Breakdown
st.subheader("📋 Submission Type Breakdown")
type_counts = filtered["Submission_Type"].value_counts().reset_index()
type_counts.columns = ["Submission Type", "Count"]
fig4 = px.bar(type_counts, x="Submission Type", y="Count", color="Submission Type", text="Count",
              template="plotly_dark")
fig4.update_layout(showlegend=False, height=400)
st.plotly_chart(fig4, use_container_width=True)

# Table with Download Option
st.subheader("🧾 Filtered Submissions Table")
st.dataframe(filtered, use_container_width=True, height=400)

csv = filtered.to_csv(index=False)
st.download_button("📥 Download Filtered Data", data=csv, file_name="filtered_fda_submissions.csv", mime="text/csv")
