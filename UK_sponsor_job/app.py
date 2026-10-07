import math
import os
import re
import urllib.parse
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="UK Sponsor Jobs | Mobile Portal",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🎯 UK Sponsor Job Finder")
st.caption("Data Analyst / Engineering / Science roles with Skilled Worker Visa")

# 1. Look for the pre-compressed file in the repo
CURRENT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = CURRENT_DIR.parent

possible_paths = [
    CURRENT_DIR / "sponsors_compact.csv.gz",
    REPO_ROOT / "sponsors_compact.csv.gz",
    Path("sponsors_compact.csv.gz"),
    Path("UK_sponsor_job/sponsors_compact.csv.gz"),
]

target_file = None
for p in possible_paths:
    if p.exists():
        target_file = p
        break

if not target_file:
    st.error(
        f"""
    ### ⚠️ Missing dataset file!
    Could not find `sponsors_compact.csv.gz` in `{CURRENT_DIR}`.
    
    Please upload `sponsors_compact.csv.gz` to your GitHub repository in the same folder as `app.py`.
    """
    )
    st.stop()


@st.cache_data
def load_data(filepath):
    return pd.read_csv(filepath, compression="gzip")


df = load_data(target_file)


# Helper function to generate LinkedIn links dynamically
def clean_org_name(name: str) -> str:
    cleaned = re.sub(
        r"(?i)\b(ltd|limited|llp|plc|inc|uk|services|technologies|corporation|group)\b",
        "",
        str(name),
    )
    cleaned = re.sub(r"[^\w\s]", " ", cleaned).strip()
    return cleaned if len(cleaned) > 2 else str(name)


def build_links(name: str):
    term = urllib.parse.quote(clean_org_name(name))
    return {
        "linkedin_company": f"https://www.linkedin.com/search/results/companies/?keywords={term}",
        "linkedin_jobs": f"https://www.linkedin.com/jobs/search/?keywords={term}%20(data%20OR%20analyst%20OR%20engineer)&location=United%20Kingdom",
        "linkedin_hr": f"https://www.linkedin.com/search/results/people/?keywords={term}%20(%22talent%22%20OR%20%22recruiter%22)",
    }


# Filters
with st.sidebar:
    st.header("🔍 Filters")
    search_query = st.text_input(
        "Search Company", "", placeholder="e.g. Amazon, Barclays..."
    )

    tier_options = sorted(df["Sponsor Tier"].unique().tolist())
    selected_tiers = st.multiselect(
        "Company Tier",
        options=tier_options,
        default=[t for t in [1, 2] if t in tier_options] or tier_options,
        format_func=lambda x: {
            1: "Tier 1: Global / FTSE",
            2: "Tier 2: Tech / Fintech",
            3: "Tier 3: Other",
        }.get(x, str(x)),
    )

    top_cities = [
        "London",
        "Edinburgh",
        "Manchester",
        "Birmingham",
        "Leeds",
        "Bristol",
        "Glasgow",
    ]
    all_cities = sorted(df["Town/City"].dropna().unique().tolist())
    selected_cities = st.multiselect(
        "Town / City",
        options=all_cities,
        default=[c for c in top_cities if c in all_cities],
    )

filtered = df[df["Sponsor Tier"].isin(selected_tiers)]

if search_query:
    filtered = filtered[
        filtered["Organisation Name"].str.contains(
            search_query, case=False, na=False
        )
    ]

if selected_cities:
    filtered = filtered[filtered["Town/City"].isin(selected_cities)]

st.write(f"**Found {len(filtered):,} employers matching filters**")

# Display as cards
PAGE_SIZE = 15
total_pages = max(1, math.ceil(len(filtered) / PAGE_SIZE))

col_p, _ = st.columns([1, 3])
with col_p:
    page = st.number_input(
        f"Page (of {total_pages})",
        min_value=1,
        max_value=total_pages,
        value=1,
        step=1,
    )

start_idx = (page - 1) * PAGE_SIZE
page_data = filtered.iloc[start_idx : start_idx + PAGE_SIZE]

for _, row in page_data.iterrows():
    tier = int(row["Sponsor Tier"])
    tier_label = {
        1: "Tier 1: Enterprise",
        2: "Tier 2: Tech / Data",
        3: "Tier 3: Standard",
    }.get(tier, f"Tier {tier}")
    links = build_links(row["Organisation Name"])

    with st.container(border=True):
        st.caption(f"🏷️ **{tier_label}** | 📍 **{row['Town/City']}**")
        st.subheader(row["Organisation Name"])
        st.markdown("Min Salary Floor (New Entrant): **£33,400/yr**")

        b1, b2, b3 = st.columns(3)
        with b1:
            st.link_button(
                "👔 Recruiter", links["linkedin_hr"], use_container_width=True
            )
        with b2:
            st.link_button(
                "💼 Live Jobs", links["linkedin_jobs"], use_container_width=True
            )
        with b3:
            st.link_button(
                "🏢 Company",
                links["linkedin_company"],
                use_container_width=True,
            )