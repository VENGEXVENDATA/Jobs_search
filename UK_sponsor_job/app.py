from pathlib import Path
import os
import pandas as pd
import streamlit as st

# Automatically resolves the exact folder where app.py lives
CURRENT_DIR = Path(__file__).parent.resolve()
COMPACT_FILE = CURRENT_DIR / "sponsors_compact.csv.gz"
BACKUP_CSV = CURRENT_DIR / "SP_-_Worker_and_Temporary_Worker_Web_Register_-_2026-10-07.csv"

@st.cache_data
def load_data():
    # 1. Prefer the lightweight 1.4MB compressed dataset
    if COMPACT_FILE.exists():
        return pd.read_csv(COMPACT_FILE, compression="gzip")
    
    # 2. Check for uncompressed fallback in current folder
    uncompressed = CURRENT_DIR / "sponsors_compact.csv"
    if uncompressed.exists():
        return pd.read_csv(uncompressed)
    
    # 3. If missing, attempt pipeline only if raw CSV exists
    if BACKUP_CSV.exists():
        try:
            import compress_data
            compress_data.process_and_compress()
            if COMPACT_FILE.exists():
                return pd.read_csv(COMPACT_FILE, compression="gzip")
        except Exception as e:
            st.error(f"Failed to generate dataset: {e}")
            st.stop()

    # Helpful UI diagnostic instead of a generic crash
    st.error(f"""
    **Missing Data File!**  
    Could not find `sponsors_compact.csv.gz` in directory:  
    `{CURRENT_DIR}`  
    
    Please ensure you have pushed `sponsors_compact.csv.gz` to the `UK_sponsor_job` folder in your GitHub repository.
    """)
    st.stop()

df = load_data()