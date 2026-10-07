import math
import os
import re
import urllib.parse
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="UK Skilled Worker Sponsor Portal",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- Responsive CSS for PC + Mobile -----------------
st.markdown("""
<style>
    /* Responsive card & container styling */
    .company-card {
        background-color: var(--secondary-background-color);
        padding: 1.1rem;
        border-radius: 0.75rem;
        border: 1px solid rgba(128, 128, 128, 0.2);
        margin-bottom: 0.75rem;
        transition: transform 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
    }
    .company-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    .badge-tier1 {
        background-color: #2e7d32;
        color: white;
        padding: 0.2rem 0.55rem;
        border-radius: 0.35rem;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .badge-tier2 {
        background-color: #0288d1;
        color: white;
        padding: 0.2rem 0.55rem;
        border-radius: 0.35rem;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .badge-tier3 {
        background-color: #616161;
        color: white;
        padding: 0.2rem 0.55rem;
        border-radius: 0.35rem;
        font-weight: 600;
        font-size: 0.75rem;
    }
    /* Responsive metric pill */
    .metric-pill {
        display: inline-block;
        font-size: 0.82rem;
        color: #888;
        margin-top: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- Safe Multi-Path Data Locator -----------------
CURRENT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = CURRENT_DIR.parent

possible_paths = [
    CURRENT_DIR / "sponsors_compact.csv.gz",
    REPO_ROOT / "sponsors_compact.csv.gz",
    CURRENT_DIR / "sponsors_compact.csv",
    REPO_ROOT / "sponsors_compact.csv",
    Path("sponsors_compact.csv.gz"),
    Path("UK_sponsor_job/sponsors_compact.csv.gz")
]

target_file = None
for p in possible_paths:
    if p.exists():
        target_file = p
        break

if not target_file:
    st.error(f"Cannot locate dataset `sponsors_compact.csv.gz` in `{CURRENT_DIR}`.")
    st.stop()

@st.cache_data
def load_data(filepath):
    if str(filepath).endswith(".gz"):
        return pd.read_csv(filepath, compression="gzip")
    return pd.read_csv(filepath)

df = load_data(target_file)

# ----------------- Dynamic Helper Functions -----------------
def clean_org_name(name: str) -> str:
    cleaned = re.sub(r"(?i)\b(ltd|limited|llp|plc|inc|uk|services|technologies|corporation|group)\b", "", str(name))
    cleaned = re.sub(r"[^\w\s]", " ", cleaned).strip()
    return cleaned if len(cleaned) > 2 else str(name)

def build_links(name: str):
    term = urllib.parse.quote(clean_org_name(name))
    return {
        "linkedin_company": f"https://www.linkedin.com/search/results/companies/?keywords={term}",
        "linkedin_jobs": f"https://www.linkedin.com/jobs/search/?keywords={term}%20(data%20OR%20analyst%20OR%20engineer)&location=United%20Kingdom",
        "linkedin_hr": f"https://www.linkedin.com/search/results/people/?keywords={term}%20(%22talent%22%20OR%20%22recruiter%22)",
        "indeed_jobs": f"https://uk.indeed.com/jobs?q={term}+data&l=United+Kingdom",
        "google_careers": f"https://www.google.com/search?q={term}+careers+data+analyst"
    }

# ----------------- Top Header & Benchmarks -----------------
st.title("🎯 UK Skilled Worker Sponsor Directory")
st.caption("Targeted portal for Data Analysts, Business Analysts, Data Engineers, and Data Scientists")

with st.expander("⚖️ Visa Salary Rules: Student Switcher Discount vs Standard", expanded=False):
    st.markdown("""
    * **New Entrant Minimum (Switching from UK Student / Graduate Visa):** **£33,400 / yr** *(Mandatory legal floor)*
    * **Standard Experienced Rate:** **£41,700 / yr**
    * *As a student/recent graduate, companies can sponsor you starting from **£33,400**, saving them up to 30% in salary requirements.*
    """)

# ----------------- Sidebar Filters -----------------
with st.sidebar:
    st.header("🔍 Search & Filter")
    search_query = st.text_input("Company Name", "", placeholder="e.g. Barclays, Revolut, Amazon...")

    tier_options = sorted(df["Sponsor Tier"].unique().tolist())
    selected_tiers = st.multiselect(
        "Sponsor Reputation & Scale",
        options=tier_options,
        default=[t for t in [1, 2] if t in tier_options] or tier_options,
        format_func=lambda x: {
            1: "Tier 1: Global Enterprise / FTSE",
            2: "Tier 2: Tech, Data & Scale-ups",
            3: "Tier 3: Other UK Employers"
        }.get(x, f"Tier {x}")
    )

    top_cities = ["London", "Edinburgh", "Manchester", "Birmingham", "Leeds", "Bristol", "Cambridge", "Glasgow"]
    all_cities = sorted(df["Town/City"].dropna().unique().tolist())
    selected_cities = st.multiselect(
        "Town / City",
        options=all_cities,
        default=[c for c in top_cities if c in all_cities]
    )
    
    st.markdown("---")
    view_mode = st.radio(
        "🖥️ Display Mode",
        ["🖥️ PC Workspace (Side-by-Side)", "📊 Full Data Table", "📱 Card Grid (Mobile-First)"]
    )

# Filter dataframe
filtered = df[df["Sponsor Tier"].isin(selected_tiers)]

if search_query:
    filtered = filtered[filtered["Organisation Name"].str.contains(search_query, case=False, na=False)]

if selected_cities:
    filtered = filtered[filtered["Town/City"].isin(selected_cities)]

total_results = len(filtered)

# ----------------- Top KPI Metric Row -----------------
m1, m2, m3, m4 = st.columns(4)
m1.metric("Matching Sponsors", f"{total_results:,}")
m2.metric("Tier 1 Mega-Sponsors", f"{len(filtered[filtered['Sponsor Tier'] == 1]):,}")
m3.metric("Tier 2 Tech/Data", f"{len(filtered[filtered['Sponsor Tier'] == 2]):,}")
m4.metric("Fresher Visa Min", "£33,400 / yr")

st.markdown("---")

# =========================================================
# MODE 1: PC WORKSPACE (Side-by-Side List + Detailed Inspector)
# =========================================================
if view_mode.startswith("🖥️"):
    st.subheader(f"Ranked Sponsors ({total_results:,})")
    left_col, right_col = st.columns([1.2, 1.8], gap="large")

    PAGE_SIZE = 12
    total_pages = max(1, math.ceil(total_results / PAGE_SIZE))

    with left_col:
        p_col, _ = st.columns([1.5, 1])
        with p_col:
            page = st.number_input(f"Page (of {total_pages})", min_value=1, max_value=total_pages, value=1, step=1)

        start_idx = (page - 1) * PAGE_SIZE
        page_data = filtered.iloc[start_idx:start_idx + PAGE_SIZE]

        company_names = page_data["Organisation Name"].tolist()
        
        selected_company = st.radio(
            "Select a company to inspect:",
            options=company_names if company_names else ["No results"],
            index=0 if company_names else None,
            label_visibility="collapsed"
        )

    with right_col:
        if selected_company and selected_company != "No results":
            row = filtered[filtered["Organisation Name"] == selected_company].iloc[0]
            tier = int(row["Sponsor Tier"])
            tier_label = {1: "Tier 1: Global Enterprise / FTSE", 2: "Tier 2: Tech, Scale-up & Fintech", 3: "Tier 3: Standard Sponsor"}.get(tier, f"Tier {tier}")
            badge_class = f"badge-tier{tier}"
            links = build_links(row["Organisation Name"])

            with st.container(border=True):
                st.markdown(f'<span class="{badge_class}">{tier_label}</span>', unsafe_allow_html=True)
                st.header(row["Organisation Name"])
                st.markdown(f"📍 **Location:** `{row['Town/City']}` &nbsp;|&nbsp; 💰 **Fresher Visa Minimum:** `£33,400 / yr`")
                st.markdown("---")

                st.subheader("⚡ 1-Click Outreach & Application Hub")
                
                b_c1, b_c2 = st.columns(2)
                with b_c1:
                    st.link_button("👔 Search Technical Recruiters & HR", links["linkedin_hr"], use_container_width=True)
                    st.link_button("💼 Live Data Roles (LinkedIn)", links["linkedin_jobs"], use_container_width=True)
                    st.link_button("🏢 Official LinkedIn Company Page", links["linkedin_company"], use_container_width=True)
                with b_c2:
                    st.link_button("📄 Search Indeed UK Live Postings", links["indeed_jobs"], use_container_width=True)
                    st.link_button("🌐 Google Careers Portal Lookup", links["google_careers"], use_container_width=True)

                st.markdown("---")
                st.info(f"💡 **Cold Outreach Tip:** Click 'Search Technical Recruiters' above to connect directly with In-House Talent Partners at **{clean_org_name(row['Organisation Name'])}** mentioning your availability under the New Entrant threshold.")

# =========================================================
# MODE 2: FULL DATA TABLE (Desktop Optimized Excel-Style View)
# =========================================================
elif view_mode.startswith("📊"):
    st.subheader(f"Sponsor Database ({total_results:,} results)")
    
    # Process links on-demand for preview rows to maximize performance
    preview_limit = 250
    preview_df = filtered.head(preview_limit).copy()
    
    links = [build_links(name) for name in preview_df["Organisation Name"]]
    preview_df["LinkedIn Page"] = [l["linkedin_company"] for l in links]
    preview_df["Jobs"] = [l["linkedin_jobs"] for l in links]
    preview_df["HR Search"] = [l["linkedin_hr"] for l in links]
    preview_df["Indeed"] = [l["indeed_jobs"] for l in links]
    preview_df["Min Salary"] = "£33,400"

    st.dataframe(
        preview_df[[
            "Sponsor Tier",
            "Organisation Name",
            "Town/City",
            "Min Salary",
            "LinkedIn Page",
            "Jobs",
            "HR Search",
            "Indeed"
        ]],
        column_config={
            "Sponsor Tier": st.column_config.NumberColumn("Tier", help="1 = High-Volume FTSE/Enterprise, 2 = Tech & Data, 3 = Standard"),
            "Organisation Name": st.column_config.TextColumn("Company"),
            "Town/City": st.column_config.TextColumn("City"),
            "Min Salary": st.column_config.TextColumn("Min Visa Salary"),
            "LinkedIn Page": st.column_config.LinkColumn("Company", display_text="Open Page"),
            "Jobs": st.column_config.LinkColumn("Live Data Roles", display_text="Search Jobs"),
            "HR Search": st.column_config.LinkColumn("Talent Contacts", display_text="Find HR"),
            "Indeed": st.column_config.LinkColumn("Indeed UK", display_text="Indeed"),
        },
        hide_index=True,
        use_container_width=True,
        height=620
    )
    if total_results > preview_limit:
        st.caption(f"Showing top {preview_limit} results. Use the sidebar search to narrow down specific companies.")

# =========================================================
# MODE 3: CARD GRID (Mobile & Tablet First)
# =========================================================
else:
    PAGE_SIZE = 12
    total_pages = max(1, math.ceil(total_results / PAGE_SIZE))

    col_p, _ = st.columns([1, 3])
    with col_p:
        page = st.number_input(f"Page (of {total_pages})", min_value=1, max_value=total_pages, value=1, step=1)

    start_idx = (page - 1) * PAGE_SIZE
    page_data = filtered.iloc[start_idx:start_idx + PAGE_SIZE]

    # Responsive 2-column grid on desktop, stacks into 1 column on mobile
    grid_cols = st.columns(2)

    for idx, (_, row) in enumerate(page_data.iterrows()):
        tier = int(row["Sponsor Tier"])
        tier_label = {1: "Tier 1: Enterprise", 2: "Tier 2: Tech / Data", 3: "Tier 3: Standard"}.get(tier, f"Tier {tier}")
        badge_class = f"badge-tier{tier}"
        links = build_links(row["Organisation Name"])

        target_col = grid_cols[idx % 2]
        with target_col:
            with st.container(border=True):
                st.markdown(f'<span class="{badge_class}">{tier_label}</span>', unsafe_allow_html=True)
                st.subheader(row["Organisation Name"])
                st.caption(f"📍 **{row['Town/City']}** &nbsp;|&nbsp; 💰 Min Salary: **£33,400/yr**")
                
                b1, b2, b3 = st.columns(3)
                with b1:
                    st.link_button("👔 Recruiter", links["linkedin_hr"], use_container_width=True)
                with b2:
                    st.link_button("💼 Live Jobs", links["linkedin_jobs"], use_container_width=True)
                with b3:
                    st.link_button("🏢 Company", links["linkedin_company"], use_container_width=True)