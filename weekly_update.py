"""
Master script for weekly automated updates of all pakketpunten data.

This script orchestrates the complete update workflow:
1. DHL: Grid-based fetch for complete coverage
2. Other providers: Municipality-based fetch (PostNL, VintedGo, DeBuren)
3. National overview regeneration

Designed to be run weekly via cron job or GitHub Actions.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def log_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80 + "\n")


def run_script(script_name: str, description: str) -> bool:
    """
    Run a Python script and return success status.

    Parameters
    ----------
    script_name : str
        Name of the Python script to run
    description : str
        Human-readable description of what the script does

    Returns
    -------
    bool
        True if script succeeded, False otherwise
    """
    log_section(description)

    print(f"Running: {script_name}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=False,
            text=True,
            check=True
        )

        print()
        print(f"✅ {description} completed successfully")
        print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return True

    except subprocess.CalledProcessError as e:
        print()
        print(f"❌ {description} failed with exit code {e.returncode}")
        print(f"Failed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return False
    except Exception as e:
        print()
        print(f"❌ Unexpected error running {script_name}: {e}")
        return False


def verify_files_exist():
    """Verify that required files exist before starting."""
    required_files = [
        "dhl_grid_fetch.py",
        "integrate_dhl_grid_data.py",
        "batch_generate.py",
        "create_national_overview.py",
        "municipalities_all.json",
    ]

    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)

    if missing:
        print("❌ Missing required files:")
        for file in missing:
            print(f"   - {file}")
        return False

    return True


def main():
    """Run the complete weekly update workflow."""

    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " WEEKLY PAKKETPUNTEN DATA UPDATE ".center(78) + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Verify required files
    if not verify_files_exist():
        print("\n❌ Cannot proceed: missing required files")
        sys.exit(1)

    # Track results
    results = {}

    # Step 1: DHL grid-based fetch
    # This gets ALL DHL locations using grid approach (~3-5 minutes)
    results['dhl_fetch'] = run_script(
        "dhl_grid_fetch.py",
        "STEP 1: DHL Grid-Based Fetch (Complete Coverage)"
    )

    if not results['dhl_fetch']:
        print("\n⚠️ DHL fetch failed, but continuing with other providers...")

    # Step 2: Integrate DHL data into municipality files
    if results['dhl_fetch']:
        results['dhl_integrate'] = run_script(
            "integrate_dhl_grid_data.py",
            "STEP 2: Integrate DHL Data into Municipality Files"
        )
    else:
        print("\n⏭️  Skipping DHL integration (fetch failed)")
        results['dhl_integrate'] = False

    # Step 3: Update other providers (PostNL, VintedGo, DeBuren)
    # Note: batch_generate.py will also fetch DHL per-municipality, but we'll
    # merge with the grid-based DHL data which is more complete
    results['other_providers'] = run_script(
        "batch_generate.py",
        "STEP 3: Update Other Providers (PostNL, VintedGo, DeBuren)"
    )

    if not results['other_providers']:
        print("\n❌ Other providers update failed")

    # Step 4: Re-integrate DHL grid data (to ensure DHL data is from grid approach)
    if results['dhl_fetch'] and results['other_providers']:
        print("\n📌 Re-applying DHL grid data to ensure completeness...")
        results['dhl_reintegrate'] = run_script(
            "integrate_dhl_grid_data.py",
            "STEP 4: Re-integrate DHL Grid Data"
        )

    # Step 5: Regenerate national overview
    results['national_overview'] = run_script(
        "create_national_overview.py",
        "STEP 5: Regenerate National Overview"
    )

    # Final summary
    log_section("WEEKLY UPDATE SUMMARY")

    print("Results:")
    print(f"  DHL Grid Fetch:        {'✅ Success' if results.get('dhl_fetch') else '❌ Failed'}")
    print(f"  DHL Integration:       {'✅ Success' if results.get('dhl_integrate') else '❌ Failed/Skipped'}")
    print(f"  Other Providers:       {'✅ Success' if results.get('other_providers') else '❌ Failed'}")
    print(f"  National Overview:     {'✅ Success' if results.get('national_overview') else '❌ Failed'}")
    print()

    # Overall status
    critical_success = results.get('other_providers', False) and results.get('national_overview', False)

    if critical_success:
        print("✅ Weekly update completed successfully!")
        print()
        print("Next steps:")
        print("  1. Check Data Matrix: http://localhost:3000/data-export/matrix")
        print("  2. Verify counts look correct")
        print("  3. Test the map with a few municipalities")
        exit_code = 0
    else:
        print("⚠️  Weekly update completed with errors")
        print("   Check the logs above for details")
        exit_code = 1

    print()
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
