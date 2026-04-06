"""
Cache guard utility for carrier data fetches.

Compares newly fetched location counts against the existing cache.
If the count drops by more than a configurable threshold (default 20%),
the existing cache is preserved and the script exits with a special
exit code so the GitHub Actions workflow can send an alert.

Usage in fetch scripts:
    from cache_guard import safe_save

    safe_save(
        carrier="DHL",
        new_locations=locations_list,
        output_path=output_path,
        metadata={...},
    )

Exit codes:
    0 = success (data saved)
    2 = data anomaly detected, existing cache preserved
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Exit code that signals "anomaly detected, cache preserved"
EXIT_CODE_ANOMALY = 2
THRESHOLD_PCT = 20


def _load_existing_count(cache_path: Path) -> Optional[int]:
    """Read the location count from an existing cache file."""
    if not cache_path.exists():
        return None
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        locations = data.get('locations', [])
        return len(locations)
    except Exception:
        return None


def safe_save(
    carrier: str,
    new_locations: List[Dict[str, Any]],
    output_path: Path,
    metadata: Dict[str, Any],
) -> bool:
    """
    Save fetched locations to cache, with a guard against anomalous drops.

    If the new count is >20% lower than the existing cache, the save is
    skipped and the process exits with code 2.

    Returns True if data was saved, False if skipped (before exiting).
    """
    output_path = Path(output_path)
    new_count = len(new_locations)
    old_count = _load_existing_count(output_path)

    # Zero results: never overwrite
    if new_count == 0:
        print()
        print(f"WARNING: {carrier} fetched 0 locations.")
        if old_count and old_count > 0:
            print(f"Keeping existing cache ({old_count} locations) to prevent data loss.")
        else:
            print("No existing cache to preserve.")
        print()
        sys.exit(EXIT_CODE_ANOMALY)

    # Check for anomalous drop
    if old_count is not None and old_count > 0:
        drop_pct = ((old_count - new_count) / old_count) * 100
        if drop_pct > THRESHOLD_PCT:
            print()
            print("=" * 80)
            print(f"ANOMALY DETECTED: {carrier}")
            print("=" * 80)
            print(f"  Existing cache: {old_count} locations")
            print(f"  New fetch:      {new_count} locations")
            print(f"  Change:         {-drop_pct:.1f}% (threshold: -{THRESHOLD_PCT}%)")
            print()
            print(f"Keeping existing cache to prevent data loss.")
            print(f"Investigate the {carrier} API before re-running.")
            print("=" * 80)
            sys.exit(EXIT_CODE_ANOMALY)

        # Log the change (informational)
        if abs(drop_pct) > 5:
            direction = "decrease" if drop_pct > 0 else "increase"
            print(f"  ℹ️  {carrier}: {abs(drop_pct):.1f}% {direction} ({old_count} → {new_count})")

    # Add standard metadata fields
    metadata["total_locations"] = new_count
    if "fetched_at" not in metadata:
        metadata["fetched_at"] = datetime.now(timezone.utc).isoformat()

    output = {
        "metadata": metadata,
        "locations": new_locations,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    file_size_kb = output_path.stat().st_size / 1024
    print(f"💾 Saved to: {output_path}")
    print(f"   File size: {file_size_kb:.1f} KB")
    print(f"   Locations: {new_count}")

    return True
