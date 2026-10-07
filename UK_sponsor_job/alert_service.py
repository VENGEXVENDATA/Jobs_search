import os
import json
import pandas as pd
import requests

WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")  # Slack or Discord Webhook URL


def send_webhook_alert(message: str):
    if not WEBHOOK_URL:
        print("[Alert Service] No Webhook configured. Printing to stdout:")
        print(message)
        return
    try:
        # Standard Slack / Discord compatible payload
        payload = {"text": message, "content": message}
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=5)
        print(f"[Alert Service] Notification sent. Status: {resp.status_code}")
    except Exception as e:
        print(f"[Alert Service] Failed to send alert: {e}")


def check_for_new_targets(
    data_file="enriched_sponsors.parquet",
    target_sectors=None,
    target_cities=None,
    limit=5,
):
    if target_sectors is None:
        target_sectors = ["Data & AI", "Software & Cloud", "Fintech & Finance"]
    if target_cities is None:
        target_cities = ["London", "Edinburgh", "Manchester"]

    if not os.path.exists(data_file):
        print(f"Data file {data_file} not found. Run pipeline.py first.")
        return

    df = (
        pd.read_parquet(data_file)
        if data_file.endswith(".parquet")
        else pd.read_csv(data_file)
    )

    matches = df[
        (df["Sector"].isin(target_sectors))
        & (df["Town/City"].isin(target_cities))
    ]

    sample = matches.sample(min(limit, len(matches)))
    alert_lines = [
        "🚨 *Sponsor Alert: High-Probability Target Employers for Data Roles*"
    ]
    for _, row in sample.iterrows():
        alert_lines.append(
            f"• *{row['Organisation Name']}* ({row['Town/City']}) - Sector: `{row['Sector']}`\n"
            f"  👉 [Careers Portals]({row['Careers Portal (Google)']}) | [Find Recruiters]({row['HR / Recruiter Leads']})"
        )

    send_webhook_alert("\n\n".join(alert_lines))


if __name__ == "__main__":
    check_for_new_targets()