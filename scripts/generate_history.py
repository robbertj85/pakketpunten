#!/usr/bin/env python3
"""
Generate historical parcel point data from git history.

This script extracts historical data from git commits to track changes in
parcel point counts over time per municipality and provider.

Output: webapp/public/data/history.json
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


def get_data_commits():
    """Get all commits that modified GeoJSON data files."""
    result = subprocess.run(
        ['git', 'log', '--format=%H %ci', '--', 'webapp/public/data/*.geojson'],
        capture_output=True, text=True
    )

    commits = []
    seen_dates = set()  # Only keep one commit per day

    # Minimum date: 2025-W47 starts on 2025-11-17
    min_date = datetime(2025, 11, 17).date()

    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            hash_val = parts[0]
            date_str = parts[1]  # YYYY-MM-DD

            # Skip dates before 2025-W47
            commit_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if commit_date < min_date:
                continue

            # Skip if we already have a commit for this date
            if date_str in seen_dates:
                continue
            seen_dates.add(date_str)

            commits.append({
                'hash': hash_val,
                'date': date_str
            })

    return commits


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


def get_municipality_list():
    """Get list of municipality slugs from the current municipalities.json."""
    municipalities_path = Path('webapp/public/municipalities.json')
    if municipalities_path.exists():
        with open(municipalities_path, 'r') as f:
            data = json.load(f)
            return [m['slug'] for m in data]
    return []


def extract_municipality_data(commit_hash, slug):
    """Extract parcel point data for a municipality at a specific commit."""
    try:
        result = subprocess.run(
            ['git', 'show', f'{commit_hash}:webapp/public/data/{slug}.geojson'],
            capture_output=True, text=True, timeout=10
        )

        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)

        # Count pakketpunten by provider
        provider_counts = defaultdict(int)
        total = 0

        for feature in data.get('features', []):
            props = feature.get('properties', {})
            if props.get('type') == 'pakketpunt':
                provider = props.get('vervoerder', 'Unknown')
                provider_counts[provider] += 1
                total += 1

        return {
            'total': total,
            'providers': dict(provider_counts)
        }
    except Exception as e:
        return None


def extract_current_municipality_data(slug):
    """Extract parcel point data for a municipality from current working tree."""
    try:
        file_path = Path(f'webapp/public/data/{slug}.geojson')
        if not file_path.exists():
            return None

        with open(file_path, 'r') as f:
            data = json.load(f)

        # Count pakketpunten by provider
        provider_counts = defaultdict(int)
        total = 0

        for feature in data.get('features', []):
            props = feature.get('properties', {})
            if props.get('type') == 'pakketpunt':
                provider = props.get('vervoerder', 'Unknown')
                provider_counts[provider] += 1
                total += 1

        return {
            'total': total,
            'providers': dict(provider_counts)
        }
    except Exception as e:
        return None


def main():
    print("Generating historical parcel point data from git history...")

    # Change to git root
    git_root = get_git_root()
    os.chdir(git_root)

    # Get all data commits
    commits = get_data_commits()
    print(f"Found {len(commits)} unique data snapshots")

    if not commits:
        print("No commits found, exiting")
        return

    # Get municipality list
    municipalities = get_municipality_list()
    print(f"Processing {len(municipalities)} municipalities")

    # Structure for output
    history_data = {
        'generated_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'snapshots': [],  # Array of snapshots with date info
        'municipalities': {}  # Per-municipality history
    }

    # Process each commit (oldest first for proper ordering)
    for commit in reversed(commits):
        commit_hash = commit['hash']
        date_str = commit['date']
        week_info = get_week_info(date_str)

        print(f"Processing {date_str} ({week_info['week_label']})...")

        snapshot = {
            'date': date_str,
            **week_info,
            'totals': {
                'total': 0,
                'providers': defaultdict(int)
            }
        }

        # Process each municipality
        for slug in municipalities:
            data = extract_municipality_data(commit_hash, slug)

            if data is None:
                continue

            # Initialize municipality in history if needed
            if slug not in history_data['municipalities']:
                history_data['municipalities'][slug] = {
                    'history': []
                }

            # Add to municipality history
            history_data['municipalities'][slug]['history'].append({
                'date': date_str,
                **week_info,
                'total': data['total'],
                'providers': data['providers']
            })

            # Aggregate totals (skip 'nederland' to avoid double-counting)
            if slug != 'nederland':
                snapshot['totals']['total'] += data['total']
                for provider, count in data['providers'].items():
                    snapshot['totals']['providers'][provider] += count

        # Convert defaultdict to dict for JSON serialization
        snapshot['totals']['providers'] = dict(snapshot['totals']['providers'])
        history_data['snapshots'].append(snapshot)

    # Also process current (uncommitted) state to include latest generated data
    today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    last_snapshot_date = history_data['snapshots'][-1]['date'] if history_data['snapshots'] else None

    # Only add current state if it's a new day (avoid duplicates)
    if last_snapshot_date != today_str:
        print(f"Processing current working tree ({today_str})...")
        week_info = get_week_info(today_str)

        current_snapshot = {
            'date': today_str,
            **week_info,
            'totals': {
                'total': 0,
                'providers': defaultdict(int)
            }
        }

        for slug in municipalities:
            data = extract_current_municipality_data(slug)

            if data is None:
                continue

            # Initialize municipality in history if needed
            if slug not in history_data['municipalities']:
                history_data['municipalities'][slug] = {
                    'history': []
                }

            # Check if we already have an entry for this date
            existing_dates = [h['date'] for h in history_data['municipalities'][slug]['history']]
            if today_str not in existing_dates:
                history_data['municipalities'][slug]['history'].append({
                    'date': today_str,
                    **week_info,
                    'total': data['total'],
                    'providers': data['providers']
                })

            # Aggregate totals (skip 'nederland' to avoid double-counting)
            if slug != 'nederland':
                current_snapshot['totals']['total'] += data['total']
                for provider, count in data['providers'].items():
                    current_snapshot['totals']['providers'][provider] += count

        current_snapshot['totals']['providers'] = dict(current_snapshot['totals']['providers'])
        history_data['snapshots'].append(current_snapshot)

    # Calculate trends (comparing latest to previous)
    if len(history_data['snapshots']) >= 2:
        latest = history_data['snapshots'][-1]
        previous = history_data['snapshots'][-2]

        history_data['trend'] = {
            'period': {
                'from': previous['date'],
                'to': latest['date'],
                'weeks': len(history_data['snapshots'])
            },
            'change': {
                'total': latest['totals']['total'] - previous['totals']['total'],
                'providers': {}
            }
        }

        # Calculate per-provider changes
        all_providers = set(latest['totals']['providers'].keys()) | set(previous['totals']['providers'].keys())
        for provider in all_providers:
            latest_count = latest['totals']['providers'].get(provider, 0)
            previous_count = previous['totals']['providers'].get(provider, 0)
            history_data['trend']['change']['providers'][provider] = latest_count - previous_count

    # Write output
    output_path = Path('webapp/public/data/history.json')
    with open(output_path, 'w') as f:
        json.dump(history_data, f, indent=2)

    print(f"\nGenerated history.json with {len(history_data['snapshots'])} snapshots")
    print(f"Output: {output_path}")

    # Print summary
    if history_data['snapshots']:
        latest = history_data['snapshots'][-1]
        print(f"\nLatest snapshot ({latest['date']}):")
        print(f"  Total: {latest['totals']['total']:,} pakketpunten")
        for provider, count in sorted(latest['totals']['providers'].items()):
            print(f"  {provider}: {count:,}")

        if 'trend' in history_data:
            trend = history_data['trend']
            change = trend['change']['total']
            sign = '+' if change >= 0 else ''
            print(f"\nTrend (since {trend['period']['from']}):")
            print(f"  Total change: {sign}{change}")


if __name__ == '__main__':
    main()
