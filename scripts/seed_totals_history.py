#!/usr/bin/env python3
"""
Seed totals_history.json from existing history.json data.

Run this once to migrate existing historical data to the new format.
"""

import json
from pathlib import Path
from datetime import datetime, timezone


def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / 'webapp' / 'public' / 'data'

    old_history_path = data_dir / 'history.json'
    new_history_path = data_dir / 'totals_history.json'

    if not old_history_path.exists():
        print("No existing history.json found.")
        return

    print("Reading existing history.json...")
    with open(old_history_path, 'r') as f:
        old_data = json.load(f)

    # Create new structure
    new_history = {
        'updated_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'snapshots': old_data.get('snapshots', []),
        'municipalities': old_data.get('municipalities', {}),
        'trend': old_data.get('trend')
    }

    # Save new history
    with open(new_history_path, 'w') as f:
        json.dump(new_history, f, indent=2)

    print(f"Created {new_history_path}")
    print(f"Migrated {len(new_history['snapshots'])} snapshots")
    print(f"Migrated {len(new_history['municipalities'])} municipalities")


if __name__ == '__main__':
    main()
