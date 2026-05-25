"""
FIFA Men's World Ranking Scraper
=================================
Fetches historical and current FIFA men's world rankings using two APIs:

  OLD-format IDs (id1 … id14xxx, ~341 dates back to 1992):
    https://inside.fifa.com/api/ranking-overview?locale=en&dateId=<id>
    Response: {"rankings": [{"rankingItem": {...}, "tag": {...}}, ...]}

  NEW-format IDs (FRS_Male_Football_*, ~5 most recent dates):
    https://api.fifa.com/api/v3/fifarankings/rankings/rankingsbyschedule
        ?rankingScheduleId=<id>&language=en
    Response: {"Results": [{"Rank": 1, "TeamName": [...], ...}, ...]}

Usage:
    pip install requests

    python fifa_ranking_scraper.py                          # full history
    python fifa_ranking_scraper.py --latest                 # most recent only
    python fifa_ranking_scraper.py --start 2024-01-01 --end 2026-12-31
    python fifa_ranking_scraper.py --list-dates
    python fifa_ranking_scraper.py --output my_file.csv
"""

import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime, date

import requests

# ── Endpoints ────────────────────────────────────────────────────────────────
RANKING_PAGE_URL  = "https://inside.fifa.com/fifa-world-ranking/men"
OLD_API_URL       = "https://inside.fifa.com/api/ranking-overview"
NEW_API_URL       = "https://api.fifa.com/api/v3/fifarankings/rankings/rankingsbyschedule"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://inside.fifa.com/fifa-world-ranking/men",
}

REQUEST_DELAY = 0.75  # seconds between calls


# ── Date discovery ────────────────────────────────────────────────────────────

def get_all_dates(session: requests.Session) -> list[dict]:
    """
    Returns the flat allAvailableDates list from __NEXT_DATA__, newest first.
    Each entry: {"id": "...", "date": "YYYY-MM-DD", "matchWindowEndDate": "YYYY-MM-DD"}
    """
    resp = session.get(
        RANKING_PAGE_URL,
        headers={**HEADERS, "Accept": "text/html"},
        timeout=30,
    )
    resp.raise_for_status()
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
    if not m:
        raise RuntimeError("Could not find __NEXT_DATA__ in FIFA page.")
    nd = json.loads(m.group(1))
    dates = (
        nd.get("props", {})
          .get("pageProps", {})
          .get("pageData", {})
          .get("ranking", {})
          .get("allAvailableDates", [])
    )
    if not dates:
        raise RuntimeError("allAvailableDates not found in __NEXT_DATA__.")
    return dates


# ── Filtering ─────────────────────────────────────────────────────────────────

def parse_date(d: dict) -> date | None:
    raw = d.get("matchWindowEndDate") or d.get("date", "")
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def filter_dates(dates, start, end):
    result = []
    for d in dates:
        parsed = parse_date(d)
        if parsed is None:
            continue
        if start and parsed < start:
            continue
        if end and parsed > end:
            continue
        result.append({**d, "_parsed_date": parsed})
    return result


def is_new_format(date_id: str) -> bool:
    return date_id.startswith("FRS_")


# ── Fetching ──────────────────────────────────────────────────────────────────

def fetch_old_format(session: requests.Session, date_id: str, date_label: str) -> list[dict]:
    """Old IDs: inside.fifa.com/api/ranking-overview"""
    resp = session.get(
        OLD_API_URL,
        params={"locale": "en", "dateId": date_id},
        headers=HEADERS,
        timeout=20,
    )
    resp.raise_for_status()
    rows = []
    for entry in resp.json().get("rankings", []):
        ri  = entry.get("rankingItem", {})
        tag = entry.get("tag", {})
        rows.append({
            "ranking_date":    date_label,
            "date_id":         date_id,
            "rank":            ri.get("rank"),
            "rank_previous":   ri.get("previousRank"),
            "team_name":       ri.get("name"),
            "team_code":       ri.get("countryCode"),
            "confederation":   tag.get("text"),
            "points":          ri.get("totalPoints"),
            "points_previous": entry.get("previousPoints"),
        })
    return rows


def fetch_new_format(session: requests.Session, date_id: str, date_label: str) -> list[dict]:
    """
    New IDs: api.fifa.com/api/v3/fifarankings/rankings/rankingsbyschedule
    Supports pagination via ContinuationToken.
    Response shape:
        {
          "ContinuationToken": <str|null>,
          "Results": [
            {
              "Rank": 1, "PrevRank": 1,
              "TeamName": [{"Locale": "en-GB", "Description": "France"}],
              "IdCountry": "FRA",
              "ConfederationName": "UEFA",
              "Points": 1903.0,
              "PreviousPoints": 1890.0,
              ...
            }, ...
          ]
        }
    """
    rows = []
    continuation_token = None

    while True:
        params = {"rankingScheduleId": date_id, "language": "en"}
        if continuation_token:
            params["continuationToken"] = continuation_token

        resp = session.get(NEW_API_URL, params=params, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        for entry in data.get("Results", []):
            # TeamName is a list of locale objects; grab the English one
            name_list = entry.get("TeamName", [])
            name = next(
                (n["Description"] for n in name_list if "en" in n.get("Locale", "").lower()),
                name_list[0]["Description"] if name_list else None,
            )
            rows.append({
                "ranking_date":    date_label,
                "date_id":         date_id,
                "rank":            entry.get("Rank"),
                "rank_previous":   entry.get("PrevRank"),
                "team_name":       name,
                "team_code":       entry.get("IdCountry"),
                "confederation":   entry.get("ConfederationName"),
                "points":          entry.get("Points"),
                "points_previous": entry.get("PreviousPoints"),
            })

        continuation_token = data.get("ContinuationToken")
        if not continuation_token:
            break
        time.sleep(0.3)

    return rows


# ── CSV output ────────────────────────────────────────────────────────────────

def save_to_csv(rows: list[dict], output_file: str) -> None:
    if not rows:
        print("No data to save.")
        return
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n✓ Saved {len(rows):,} rows → '{output_file}'")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape FIFA Men's World Rankings (historical + current)."
    )
    parser.add_argument("--start", metavar="YYYY-MM-DD",
                        help="Earliest ranking date to include (inclusive).")
    parser.add_argument("--end",   metavar="YYYY-MM-DD",
                        help="Latest ranking date to include (inclusive).")
    parser.add_argument("--latest", action="store_true",
                        help="Fetch only the most recent ranking.")
    parser.add_argument("--list-dates", action="store_true",
                        help="Print all available dates and exit.")
    parser.add_argument("--output", default="fifa_rankings.csv",
                        help="Output CSV file (default: fifa_rankings.csv).")
    args = parser.parse_args()

    start_date = datetime.strptime(args.start, "%Y-%m-%d").date() if args.start else None
    end_date   = datetime.strptime(args.end,   "%Y-%m-%d").date() if args.end   else None

    session = requests.Session()

    # ── Discover all dates ───────────────────────────────────────────────
    print("Loading FIFA ranking page to discover available dates...")
    try:
        all_dates = get_all_dates(session)
    except Exception as exc:
        sys.exit(f"[error] {exc}")
    print(f"  → Found {len(all_dates)} ranking dates total.")

    if args.list_dates:
        print("\nAvailable dates (newest first):")
        for d in all_dates:
            fmt = "NEW" if is_new_format(d["id"]) else "old"
            print(f"  [{fmt}]  {d.get('date',''):12s}  {d['id']}")
        return

    # ── Filter ───────────────────────────────────────────────────────────
    selected = [all_dates[0]] if args.latest else filter_dates(all_dates, start_date, end_date)
    if not selected:
        sys.exit("No dates matched the specified range.")

    # Attach human-readable label
    for d in selected:
        dt = parse_date(d)
        d["_label"] = dt.strftime("%d %B %Y") if dt else d.get("date", d["id"])

    old_dates = [d for d in selected if not is_new_format(d["id"])]
    new_dates = [d for d in selected if     is_new_format(d["id"])]
    print(f"  → {len(new_dates)} new-format + {len(old_dates)} old-format = {len(selected)} total\n")

    all_rows: list[dict] = []

    # ── New-format: api.fifa.com/v3/fifarankings ─────────────────────────
    if new_dates:
        print(f"Fetching {len(new_dates)} new-format date(s) via api.fifa.com...")
        for i, d in enumerate(new_dates, 1):
            date_id, date_label = d["id"], d["_label"]
            print(f"  [{i:>3}/{len(new_dates)}]  {date_label:<20} ({date_id})", end="", flush=True)
            try:
                rows = fetch_new_format(session, date_id, date_label)
                all_rows.extend(rows)
                print(f"  → {len(rows)} teams")
            except requests.HTTPError as exc:
                print(f"  [HTTP {exc.response.status_code}] skipping")
            except Exception as exc:
                print(f"  [error] {exc}")
            if i < len(new_dates):
                time.sleep(REQUEST_DELAY)

    # ── Old-format: inside.fifa.com/api/ranking-overview ─────────────────
    if old_dates:
        print(f"\nFetching {len(old_dates)} old-format date(s) via inside.fifa.com...")
        for i, d in enumerate(old_dates, 1):
            date_id, date_label = d["id"], d["_label"]
            print(f"  [{i:>4}/{len(old_dates)}]  {date_label:<20} ({date_id})", end="", flush=True)
            try:
                rows = fetch_old_format(session, date_id, date_label)
                all_rows.extend(rows)
                print(f"  → {len(rows)} teams")
            except requests.HTTPError as exc:
                print(f"  [HTTP {exc.response.status_code}] skipping")
            except Exception as exc:
                print(f"  [error] {exc}")
            if i < len(old_dates):
                time.sleep(REQUEST_DELAY)

    # ── Save ─────────────────────────────────────────────────────────────
    save_to_csv(all_rows, args.output)


if __name__ == "__main__":
    main()
