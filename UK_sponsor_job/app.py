import os
import streamlit as st
import pandas as pd

st.set_page_config(page_title="UK Data Analyst Sponsorship Tracker", page_icon="🎯", layout="wide")

@st.cache_data
def load_data():
    if not os.path.exists("enriched_sponsors.parquet"):
        import pipeline
        pipeline.run_pipeline()
    return pd.read_parquet("enriched_sponsors.parquet")

df = load_data()

# ---------------- Header & Salary Thresholds ----------------
st.title("🎯 UK Skilled Worker Sponsor Directory: Data Roles")
st.markdown("""
**Salary Benchmark for Junior / 0–1 Year Experience Data Analysts (SOC 2425):**
* **New Entrant Minimum (Students / Recent Grads):** `£33,400 / yr` *(Absolute legal minimum)*
* **Standard Minimum (Without New Entrant discount):** `£41,700 / yr`
* **Market Going Rate (Mid/Senior):** `£45,000 – £65,000+ / yr`
""")

# ---------------- Sidebar Controls ----------------
st.sidebar.header("🔍 Filters")
search_query = st.sidebar.text_input("Search Company Name", "")

tier_selection = st.sidebar.multiselect(
    "Filter by Sponsor Reputation & Size",
    options=[1, 2, 3],
    default=[1, 2],
    format_func=lambda x: {
        1: "Tier 1: High Volume / Enterprise (Big 4, Tech, FTSE 100)",
        2: "Tier 2: Tech, Data & Fintech Companies",
        3: "Tier 3: Other Licensed UK Employers"
    }[x]
)

top_cities = ["London", "Edinburgh", "Manchester", "Birmingham", "Leeds", "Bristol", "Cambridge", "Glasgow"]
all_cities = sorted(df["Town/City"].dropna().unique().tolist())
selected_cities = st.sidebar.multiselect("Town / City", options=all_cities, default=[c for c in top_cities if c in all_cities])

# ---------------- Data Filtering ----------------
filtered = df[df["Sponsor Tier"].isin(tier_selection)]

if search_query:
    filtered = filtered[filtered["Organisation Name"].str.contains(search_query, case=False, na=False)]

if selected_cities:
    filtered = filtered[filtered["Town/City"].isin(selected_cities)]

st.subheader(f"Showing {len(filtered):,} Ranked Companies (Tier 1 & 2 Prioritized)")

# ---------------- Interactive Table ----------------
st.dataframe(
    filtered[[
        "Sponsor Tier",
        "Organisation Name",
        "Town/City",
        "Visa Min Salary (New Entrant)",
        "LinkedIn Company",
        "LinkedIn Data Jobs",
        "HR / Recruiter Search"
    ]],
    column_config={
        "Sponsor Tier": st.column_config.NumberColumn("Tier", help="1 = High-Volume Enterprise, 2 = Tech/Data focused, 3 = General"),
        "Visa Min Salary (New Entrant)": st.column_config.TextColumn("Min Required Salary", help="Required salary threshold for freshers on student visa switch"),
        "LinkedIn Company": st.column_config.LinkColumn("Company Profile", display_text="LinkedIn Page"),
        "LinkedIn Data Jobs": st.column_config.LinkColumn("Live Data Roles", display_text="Search Roles"),
        "HR / Recruiter Search": st.column_config.LinkColumn("HR / Recruiter Leads", display_text="Find Recruiters"),
    },
    hide_index=True,
    use_container_width=True,
    height=600
)