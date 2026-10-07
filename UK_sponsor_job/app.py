import math
import os
import re
import urllib.parse
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="UK Sponsor Jobs | Mobile Portal",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",  # Keep sidebar collapsed by default for mobile screens
)

# Custom mobile-first responsive CSS
st.markdown("""
<style>
    /* Card layout */
    .company-card {
        background-color: var(--secondary-background-color);
        padding: 1rem;
        border-radius: 0.75rem;
        margin-bottom: 0.75rem;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    .badge-tier1 {
        background-color: #2e7d32;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.35rem;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .badge-tier2 {
        background-color: #0288d1;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.35rem;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .badge-tier3 {
        background-color: #616161;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.35rem;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .salary-info {
        font-size: 0.85rem;
        color: #888;
        margin-top: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- Fast Data Loading -----------------
@st.cache_data
def load_data():
    file_path = "sponsors_compact.csv.gz"
    if not os.path.exists(file_path):
        import compress_data
        compress_data.process_and_compress()
    return pd.read_csv(file_path, compression="gzip")

df = load_data()

def clean_org_name(name: str) -> str:
    cleaned = re.sub(r"(?i)\b(ltd|limited|llp|plc|inc|uk|services|technologies|corporation|group)\b", "", name)
    cleaned = re.sub(r"[^\w\s]", " ", cleaned).strip()
    return cleaned if len(cleaned) > 2 else name

def build_links(name: str):
    term = urllib.parse.quote(clean_org_name(name))
    return {
        "linkedin_company": f"https://www.linkedin.com/search/results/companies/?keywords={term}",
        "linkedin_jobs": f"https://www.linkedin.com/jobs/search/?keywords={term}%20(data%20OR%20analyst%20OR%20engineer)&location=United%20Kingdom",
        "linkedin_hr": f"https://www.linkedin.com/search/results/people/?keywords={term}%20(%22talent%22%20OR%20%22recruiter%22)",
    }

# ----------------- Header & Salary Alert -----------------
st.title("🎯 UK Sponsor Job Finder")
st.caption("Data Analyst / Engineering / Science roles with Skilled Worker Visa")

with st.expander("ℹ️ Visa Salary Requirements (New Entrant vs Standard)", expanded=False):
    st.markdown("""
    * **Student/Graduate Switcher Minimum (New Entrant):** **£33,400 / yr**
    * **Standard Experienced Worker Minimum:** **£41,700 / yr**
    * *Any sponsor offer for a data analyst must meet or exceed the £33,400 statutory minimum threshold.*
    """)

# ----------------- Mobile-Friendly Filter Expander -----------------
with st.expander("🔍 Filter Employers", expanded=True):
    col_search, col_tier = st.columns([2, 1])
    with col_search:
        search_query = st.text_input("Search Company", "", placeholder="e.g. Amazon, Revolut, Barclays...")
    with col_tier:
        selected_tiers = st.multiselect(
            "Company Tier",
            options=[1, 2, 3],
            default=[1, 2],
            format_func=lambda x: {1: "Tier 1: Global / FTSE", 2: "Tier 2: Tech / Fintech", 3: "Tier 3: Other"}[x]
        )

    top_cities = ["London", "Edinburgh", "Manchester", "Birmingham", "Leeds", "Bristol", "Glasgow"]
    all_cities = sorted(df["Town/City"].dropna().unique().tolist())
    selected_cities = st.multiselect("Town / City", options=all_cities, default=[c for c in top_cities if c in all_cities])

# ----------------- Filtering Logic -----------------
filtered = df[df["Sponsor Tier"].isin(selected_tiers)]

if search_query:
    filtered = filtered[filtered["Organisation Name"].str.contains(search_query, case=False, na=False)]

if selected_cities:
    filtered = filtered[filtered["Town/City"].isin(selected_cities)]

total_results = len(filtered)
st.write(f"**Found {total_results:,} employers matching filters**")

# ----------------- View Mode Toggle -----------------
view_mode = st.radio("Display Style", ["📱 Mobile Cards (Recommended)", "💻 Full Table"], horizontal=True)

# ----------------- Mobile Cards View -----------------
if view_mode.startswith("📱"):
    # Client-side pagination to eliminate scroll fatigue and lag
    PAGE_SIZE = 15
    total_pages = max(1, math.ceil(total_results / PAGE_SIZE))
    
    col_p1, col_p2 = st.columns([1, 2])
    with col_p1:
        page = st.number_input(f"Page (of {total_pages})", min_value=1, max_value=total_pages, value=1, step=1)
    
    start_idx = (page - 1) * PAGE_SIZE
    page_data = filtered.iloc[start_idx:start_idx + PAGE_SIZE]

    for _, row in page_data.iterrows():
        tier = int(row["Sponsor Tier"])
        tier_label = {1: "Tier 1: Enterprise", 2: "Tier 2: Tech / Data", 3: "Tier 3: Standard"}[tier]
        badge_class = f"badge-tier{tier}"
        links = build_links(row["Organisation Name"])

        # Responsive card
        st.markdown(f"""
        <div class="company-card">
            <span class="{badge_class}">{tier_label}</span>
            <h3 style="margin-top: 0.4rem; margin-bottom: 0.1rem;">{row["Organisation Name"]}</h3>
            <p style="margin-bottom: 0.2rem;">📍 <b>{row["Town/City"]}</b></p>
            <div class="salary-info">Min Required Salary: <b>£33,400/yr</b> (New Entrant)</div>
        </div>
        """, unsafe_allow_html=True)

        # 3 responsive mobile action buttons per company card
        b1, b2, b3 = st.columns(3)
        with b1:
            st.link_button("👔 Recruiter", links["linkedin_hr"], use_container_width=True)
        with b2:
            st.link_button("💼 Live Jobs", links["linkedin_jobs"], use_container_width=True)
        with b3:
            st.link_button("🏢 Page", links["linkedin_company"], use_container_width=True)
            
        st.write("")

# ----------------- Full Table View -----------------
else:
    # On-demand link generation only for table preview to prevent lag
    preview_df = filtered.head(200).copy()
    links = [build_links(name) for name in preview_df["Organisation Name"]]
    preview_df["LinkedIn Page"] = [l["linkedin_company"] for l in links]
    preview_df["Jobs"] = [l["linkedin_jobs"] for l in links]
    preview_df["HR Search"] = [l["linkedin_hr"] for l in links]
    preview_df["Min Salary"] = "£33,400"

    st.dataframe(
        preview_df[["Sponsor Tier", "Organisation Name", "Town/City", "Min Salary", "LinkedIn Page", "Jobs", "HR Search"]],
        column_config={
            "LinkedIn Page": st.column_config.LinkColumn("Company", display_text="Open"),
            "Jobs": st.column_config.LinkColumn("Roles", display_text="Find Jobs"),
            "HR Search": st.column_config.LinkColumn("Talent Leads", display_text="Recruiters"),
        },
        hide_index=True,
        use_container_width=True,
        height=550,
    )