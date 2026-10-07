import os
import re
import urllib.parse
import pandas as pd

INPUT_CSV = "SP_-_Worker_and_Temporary_Worker_Web_Register_-_2026-10-07.csv"
OUTPUT_PARQUET = "enriched_sponsors.parquet"

# High-reputation enterprise sponsors (Tier 1)
TIER1_REPUTED = [
    # Big Tech & Cloud
    "Google", "Amazon", "Microsoft", "Meta", "Apple", "Cisco", "Oracle", "Salesforce", "IBM", "SAP",
    # Big 4 & Management Consultancies
    "Deloitte", "PricewaterhouseCoopers", "PwC", "Ernst & Young", "EY", "KPMG", "McKinsey", "Boston Consulting", "Bain", "Accenture", "Capgemini", "Cognizant", "Wipro", "Infosys", "Tata Consultancy", "LTIMindtree",
    # Tier 1 Banks & Financial Institutions
    "Barclays", "HSBC", "NatWest", "Lloyds", "JPMorgan", "Morgan Stanley", "Goldman Sachs", "Citi", "UBS", "Deutsche Bank", "Bank of America", "Bloomberg", "BlackRock", "Schroders", "Revolut",
    # Major Retail, Telecom & Healthcare
    "Vodafone", "BT", "Sky", "Tesco", "Sainsbury", "AstraZeneca", "GSK", "Unilever", "Centrica", "BP", "Shell", "Rolls-Royce"
]

def clean_company_name(name: str) -> str:
    cleaned = re.sub(r"(?i)\b(ltd|limited|llp|plc|inc|uk|services|technologies|corporation|group)\b", "", name)
    cleaned = re.sub(r"[^\w\s]", " ", cleaned).strip()
    return cleaned if len(cleaned) > 2 else name

def assign_tier(name: str) -> int:
    name_clean = clean_company_name(name).lower()
    for brand in TIER1_REPUTED:
        if brand.lower() in name_clean:
            return 1  # Tier 1: Mega-sponsor / High reputation
    # Check tech/data indicator keywords for Tier 2
    if re.search(r"\b(data|analytics|cloud|software|capital|financial|consulting|ai)\b", name.lower()):
        return 2  # Tier 2: Specialized Data/Tech/Finance Sponsor
    return 3      # Tier 3: Standard Licensed Sponsor

def run_pipeline():
    print("Loading Home Office Register...")
    df = pd.read_csv(INPUT_CSV)
    df.columns = df.columns.str.strip()

    # 1. Filter valid Skilled Worker A-rated
    mask = (df["Route"].str.contains("Skilled Worker", case=False, na=False)) & \
           (df["Type & Rating"].str.contains("A rating", case=False, na=False))
    sponsors = df[mask].copy().reset_index(drop=True)

    # 2. Score company size & reputation
    sponsors["Sponsor Tier"] = sponsors["Organisation Name"].apply(assign_tier)

    # 3. Build native, direct navigation links
    def make_links(row):
        org = row["Organisation Name"]
        cleaned = clean_company_name(org)
        enc_search = urllib.parse.quote(cleaned)
        
        # Direct LinkedIn Company Profile
        li_company = f"https://www.linkedin.com/search/results/companies/?keywords={enc_search}"
        # Direct LinkedIn Data Analyst / Engineer Vacancies
        li_jobs = f"https://www.linkedin.com/jobs/search/?keywords={enc_search}%20%28data%20analyst%20OR%20data%20engineer%29&location=United%20Kingdom"
        # Direct LinkedIn Technical Recruiter / Talent Acquisition Search
        li_hr = f"https://www.linkedin.com/search/results/people/?keywords={enc_search}%20%28%22Talent%20Acquisition%22%20OR%20%22Recruiter%22%29"
        
        return li_company, li_jobs, li_hr

    links = sponsors.apply(make_links, axis=1)
    sponsors["LinkedIn Company"] = [x[0] for x in links]
    sponsors["LinkedIn Data Jobs"] = [x[1] for x in links]
    sponsors["HR / Recruiter Search"] = [x[2] for x in links]
    
    # 4. Salary threshold indicator (New Entrant vs Standard)
    sponsors["Visa Min Salary (New Entrant)"] = "£33,400"
    sponsors["Visa Min Salary (Standard)"] = "£41,700"

    # Sort primarily by Sponsor Tier (Tier 1 first, then Tier 2, then Tier 3)
    sponsors = sponsors.sort_values(by=["Sponsor Tier", "Organisation Name"]).reset_index(drop=True)
    
    sponsors.to_parquet(OUTPUT_PARQUET, index=False)
    print(f"Enriched database saved to {OUTPUT_PARQUET}. Ready for dashboard.")

if __name__ == "__main__":
    run_pipeline()