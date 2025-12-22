#!/usr/bin/env python3
"""
Backfill totals_history.json from git commit history.

Run this once to populate historical data from past commits.
"""

import subprocess
import json
import os
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from pathlib import Path


def get_git_root():
    """Get the root directory of the git repository."""
    result = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'],
        capture_output=True, text=True
    )
    return result.stdout.strip()


def get_week_info(date_str):
    """Get ISO week number and date range for a given date."""
    date = datetime.strptime(date_str, '%Y-%m-%d')
    iso_calendar = date.isocalendar()
    week_num = iso_calendar[1]
    year = iso_calendar[0]

    # Calculate week start (Monday) and end (Sunday)
    week_start = date - timedelta(days=date.weekday())
    week_end = week_start + timedelta(days=6)

    return {
        'week': week_num,
        'year': year,
        'week_label': f"{year}-W{week_num:02d}",
        'date_from': week_start.strftime('%Y-%m-%d'),
        'date_to': week_end.strftime('%Y-%m-%d')
    }


def get_data_commits():
    """Get all robot commits that modified GeoJSON data files."""
    result = subprocess.run(
        ['git', 'log', '--format=%H %ci %s', '--', 'webapp/public/data/*.geojson'],
        capture_output=True, text=True
    )

    commits = []
    seen_weeks = set()

    # Minimum week to include (API improvements were made before this)
    min_week = '2025-W47'

    for line in result.stdout.strip().split('\n'):
        if not line:
            continue

        # Only include robot commits (weekly updates)
        if '🤖 Update pakketpunten data' not in line:
            continue

        parts = line.split()
        if len(parts) >= 2:
            hash_val = parts[0]
            date_str = parts[1]  # YYYY-MM-DD

            week_info = get_week_info(date_str)
            week_label = week_info['week_label']

            # Skip weeks before minimum
            if week_label < min_week:
                continue

            # Only keep one commit per week
            if week_label in seen_weeks:
                continue
            seen_weeks.add(week_label)

            commits.append({
                'hash': hash_val,
                'date': date_str,
                'week_label': week_label
            })

    return commits


def get_municipality_slugs_from_commit(commit_hash):
    """Get list of municipality GeoJSON files at a specific commit."""
    result = subprocess.run(
        ['git', 'ls-tree', '--name-only', commit_hash, 'webapp/public/data/'],
        capture_output=True, text=True
    )

    slugs = []
    for line in result.stdout.strip().split('\n'):
        if line.endswith('.geojson'):
            slug = line.replace('webapp/public/data/', '').replace('.geojson', '')
            if slug != 'nederland':  # Skip national overview
                slugs.append(slug)
    return slugs


def extract_totals_from_commit(commit_hash, slugs):
    """Extract parcel point totals from a specific commit."""
    totals = {
        'total': 0,
        'providers': defaultdict(int),
        'municipalities': {}
    }

    for slug in slugs:
        try:
            result = subprocess.run(
                ['git', 'show', f'{commit_hash}:webapp/public/data/{slug}.geojson'],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                continue

            data = json.loads(result.stdout)

            municipality_total = 0
            municipality_providers = defaultdict(int)

            for feature in data.get('features', []):
                props = feature.get('properties', {})
                if props.get('type') == 'pakketpunt':
                    provider = props.get('vervoerder', 'Unknown')
                    municipality_providers[provider] += 1
                    municipality_total += 1
                    totals['providers'][provider] += 1
                    totals['total'] += 1

            totals['municipalities'][slug] = {
                'total': municipality_total,
                'providers': dict(municipality_providers)
            }

        except Exception as e:
            print(f"  Warning: Could not process {slug}: {e}")

    totals['providers'] = dict(totals['providers'])
    return totals


def main():
    print("Backfilling totals history from git commits...")

    # Change to git root
    git_root = get_git_root()
    os.chdir(git_root)

    # Load existing history
    history_path = Path('webapp/public/data/totals_history.json')
    if history_path.exists():
        with open(history_path, 'r') as f:
            history = json.load(f)
    else:
        history = {'snapshots': [], 'municipalities': {}}

    existing_weeks = {s['week_label'] for s in history['snapshots']}
    print(f"Existing weeks: {sorted(existing_weeks)}")

    # Get all data commits
    commits = get_data_commits()
    print(f"Found {len(commits)} weekly data commits")

    # Process commits (oldest first)
    for commit in reversed(commits):
        week_label = commit['week_label']

        if week_label in existing_weeks:
            print(f"Skipping {week_label} (already exists)")
            continue

        print(f"Processing {commit['date']} ({week_label})...")

        # Get municipality list from that commit
        slugs = get_municipality_slugs_from_commit(commit['hash'])
        print(f"  Found {len(slugs)} municipalities")

        # Extract totals
        totals = extract_totals_from_commit(commit['hash'], slugs)
        week_info = get_week_info(commit['date'])

        # Create snapshot
        snapshot = {
            'date': commit['date'],
            **week_info,
            'totals': {
                'total': totals['total'],
                'providers': totals['providers']
            }
        }
        history['snapshots'].append(snapshot)

        # Add municipality data
        for slug, muni_data in totals['municipalities'].items():
            if slug not in history['municipalities']:
                history['municipalities'][slug] = {'history': []}

            history['municipalities'][slug]['history'].append({
                'date': commit['date'],
                **week_info,
                'total': muni_data['total'],
                'providers': muni_data['providers']
            })

        print(f"  Total: {totals['total']:,} pakketpunten")

    # Sort snapshots by date
    history['snapshots'].sort(key=lambda x: x['date'])

    # Sort municipality histories by date
    for slug in history['municipalities']:
        history['municipalities'][slug]['history'].sort(key=lambda x: x['date'])

    # Update metadata
    history['updated_at'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    # Recalculate trend
    if len(history['snapshots']) >= 2:
        latest = history['snapshots'][-1]
        previous = history['snapshots'][-2]

        history['trend'] = {
            'period': {
                'from': previous['date'],
                'to': latest['date'],
                'weeks': len(history['snapshots'])
            },
            'change': {
                'total': latest['totals']['total'] - previous['totals']['total'],
                'providers': {}
            }
        }

        all_providers = set(latest['totals']['providers'].keys()) | set(previous['totals']['providers'].keys())
        for provider in all_providers:
            latest_count = latest['totals']['providers'].get(provider, 0)
            previous_count = previous['totals']['providers'].get(provider, 0)
            history['trend']['change']['providers'][provider] = latest_count - previous_count

    # Save
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)

    print(f"\nBackfill complete!")
    print(f"Total snapshots: {len(history['snapshots'])}")

    if history['snapshots']:
        oldest = history['snapshots'][0]
        latest = history['snapshots'][-1]
        print(f"Range: {oldest['week_label']} to {latest['week_label']}")
        print(f"  {oldest['totals']['total']:,} -> {latest['totals']['total']:,}")


if __name__ == '__main__':
    main()
