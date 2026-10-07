import os
import re
import pandas as pd

INPUT_CSV = "SP_-_Worker_and_Temporary_Worker_Web_Register_-_2026-10-07.csv"
OUTPUT_COMPACT = "sponsors_compact.csv.gz"

TIER1_BRANDS = [
    "Google", "Amazon", "Microsoft", "Meta", "Apple", "Cisco", "Oracle", "Salesforce", "IBM", "SAP",
    "Deloitte", "PricewaterhouseCoopers", "PwC", "Ernst & Young", "EY", "KPMG", "McKinsey", "Boston Consulting", 
    "Bain", "Accenture", "Capgemini", "Cognizant", "Wipro", "Infosys", "Tata Consultancy", "LTIMindtree",
    "Barclays", "HSBC", "NatWest", "Lloyds", "JPMorgan", "Morgan Stanley", "Goldman Sachs", "Citi", "UBS", 
    "Deutsche Bank", "Bank of America", "Bloomberg", "BlackRock", "Schroders", "Revolut",
    "Vodafone", "BT", "Sky", "Tesco", "Sainsbury", "AstraZeneca", "GSK", "Unilever", "Centrica", "BP", "Shell", "Rolls-Royce"
]

def clean_org_name(name: str) -> str:
    cleaned = re.sub(r"(?i)\b(ltd|limited|llp|plc|inc|uk|services|technologies|corporation|group)\b", "", name)
    cleaned = re.sub(r"[^\w\s]", " ", cleaned).strip()
    return cleaned if len(cleaned) > 2 else name

def assign_tier(name: str) -> int:
    name_clean = clean_org_name(name).lower()
    for brand in TIER1_BRANDS:
        if brand.lower() in name_clean:
            return 1
    if re.search(r"\b(data|analytics|cloud|software|capital|financial|consulting|ai)\b", name.lower()):
        return 2
    return 3

def process_and_compress():
    print("Reading Home Office Register...")
    df = pd.read_csv(INPUT_CSV)
    df.columns = df.columns.str.strip()

    # Filter Skilled Worker & A rating
    mask = (df["Route"].str.contains("Skilled Worker", case=False, na=False)) & \
           (df["Type & Rating"].str.contains("A rating", case=False, na=False))
    sponsors = df[mask][["Organisation Name", "Town/City"]].dropna(subset=["Organisation Name"]).copy()

    sponsors["Town/City"] = sponsors["Town/City"].fillna("Unknown")
    sponsors["Sponsor Tier"] = sponsors["Organisation Name"].apply(assign_tier).astype("int8")
    
    # Sort with Tier 1 first
    sponsors = sponsors.sort_values(by=["Sponsor Tier", "Organisation Name"]).reset_index(drop=True)

    # Save with maximum gzip compression (Compress level 9)
    sponsors.to_csv(OUTPUT_COMPACT, compression={"method": "gzip", "compresslevel": 9}, index=False)
    
    size_mb = os.path.getsize(OUTPUT_COMPACT) / (1024 * 1024)
    print(f"Compact file created: {OUTPUT_COMPACT} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    process_and_compress()