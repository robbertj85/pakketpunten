# Automated Weekly Updates

This document describes how to set up automated weekly updates for the pakketpunten data.

## Overview

The system now includes a complete automated update workflow that:
1. **DHL**: Uses grid-based fetching for complete coverage (~6,000 locations)
2. **Other providers**: Fetches PostNL, VintedGo, and DeBuren per municipality
3. **Integration**: Merges all data into municipality GeoJSON files
4. **National overview**: Regenerates the national overview with deduplication

## Manual Execution

### Quick Start

Run the weekly update with a single command:

```bash
./update.sh
```

This will:
- Activate the virtual environment
- Run the complete update workflow
- Create a timestamped log file
- Show progress in real-time

### Alternative (Python directly)

```bash
source venv/bin/activate
python weekly_update.py
```

## What Gets Updated

The weekly update process performs these steps in order:

### Step 1: DHL Grid-Based Fetch
- **Script**: `dhl_grid_fetch.py`
- **Duration**: ~3-5 minutes
- **Result**: `dhl_all_locations.json` (~6,000 DHL locations)
- **Method**: Grid-based coverage with automatic subdivision

### Step 2: DHL Integration
- **Script**: `integrate_dhl_grid_data.py`
- **Duration**: ~1-2 minutes
- **Result**: Updates all municipality GeoJSON files with complete DHL data
- **Effect**: Large cities now show 50+ DHL locations instead of 15

### Step 3: Other Providers Update
- **Script**: `batch_generate.py`
- **Duration**: ~15-30 minutes (326 municipalities)
- **Result**: Updates PostNL, VintedGo, DeBuren data for all municipalities
- **Method**: Per-municipality API calls with rate limiting

### Step 4: DHL Re-integration
- **Script**: `integrate_dhl_grid_data.py` (again)
- **Duration**: ~1-2 minutes
- **Reason**: Ensures DHL data from grid approach takes precedence

### Step 5: National Overview
- **Script**: `create_national_overview.py`
- **Duration**: ~1-2 minutes
- **Result**: Regenerates `nederland.geojson` with all data
- **Deduplication**: Cross-boundary locations are deduplicated

## Automation Setup

### Option 1: Cron Job (Linux/macOS)

Edit your crontab:

```bash
crontab -e
```

Add a line to run every Sunday at 2 AM:

```cron
0 2 * * 0 /Users/robbertjanssen/Documents/dev/pakketpunten/update.sh >> /Users/robbertjanssen/Documents/dev/pakketpunten/logs/cron_$(date +\%Y\%m\%d).log 2>&1
```

Create the logs directory:

```bash
mkdir -p logs
```

### Option 2: Launchd (macOS preferred)

Create a launchd plist file:

```bash
cat > ~/Library/LaunchAgents/com.pakketpunten.weekly-update.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pakketpunten.weekly-update</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/robbertjanssen/Documents/dev/pakketpunten/update.sh</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/robbertjanssen/Documents/dev/pakketpunten</string>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>0</integer>  <!-- Sunday -->
        <key>Hour</key>
        <integer>2</integer>   <!-- 2 AM -->
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/Users/robbertjanssen/Documents/dev/pakketpunten/logs/launchd-stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/robbertjanssen/Documents/dev/pakketpunten/logs/launchd-stderr.log</string>
</dict>
</plist>
EOF
```

Load the launchd job:

```bash
mkdir -p logs
launchctl load ~/Library/LaunchAgents/com.pakketpunten.weekly-update.plist
```

Check status:

```bash
launchctl list | grep pakketpunten
```

Unload (if needed):

```bash
launchctl unload ~/Library/LaunchAgents/com.pakketpunten.weekly-update.plist
```

### Option 3: GitHub Actions

Create `.github/workflows/weekly-update.yml`:

```yaml
name: Weekly Data Update

on:
  schedule:
    - cron: '0 2 * * 0'  # Every Sunday at 2 AM UTC
  workflow_dispatch:  # Allow manual trigger

jobs:
  update:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run weekly update
        run: |
          python weekly_update.py

      - name: Commit and push changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add webapp/public/data/*.geojson
          git commit -m "Automated weekly data update" || echo "No changes to commit"
          git push
```

## Monitoring and Logs

### Check Recent Logs

```bash
# List recent log files
ls -lt weekly_update_*.log | head -5

# View the latest log
tail -f $(ls -t weekly_update_*.log | head -1)
```

### Log File Format

Each log file contains:
- Timestamp when each step started/completed
- Number of locations fetched
- Success/failure status for each step
- Final summary with overall status

### Expected Output

Successful run should show:

```
✅ Weekly update completed successfully!

Results:
  DHL Grid Fetch:        ✅ Success
  DHL Integration:       ✅ Success
  Other Providers:       ✅ Success
  National Overview:     ✅ Success
```

## Troubleshooting

### DHL Fetch Fails

**Symptoms**: DHL grid fetch returns fewer than 5,000 locations

**Solutions**:
1. Check network connectivity
2. Verify DHL API is accessible
3. Increase rate limit delay in `dhl_grid_fetch.py` if getting 429 errors
4. Check subdivision logic if seeing "Hit 50-limit" warnings

### Other Providers Fail

**Symptoms**: PostNL/VintedGo/DeBuren data not updating

**Solutions**:
1. Check API endpoints are accessible
2. Verify rate limiting delays are sufficient
3. Check for API changes or authentication requirements
4. Review error messages in log files

### National Overview Issues

**Symptoms**: Nederland counts don't match sum of municipalities

**Solutions**:
1. This is expected - Nederland deduplicates cross-boundary locations
2. Check Data Matrix to verify counts
3. Ensure `integrate_dhl_grid_data.py` ran successfully

### Disk Space

The complete dataset requires:
- DHL locations file: ~3-5 MB
- All municipality GeoJSON files: ~500 MB
- National overview: ~5 MB
- Log files: ~1-2 MB per run

Clean up old logs periodically:

```bash
# Keep only last 30 days of logs
find . -name "weekly_update_*.log" -mtime +30 -delete
```

## Performance

Expected execution times:

| Step | Duration | API Calls |
|------|----------|-----------|
| DHL Grid Fetch | 3-5 min | ~150-250 |
| DHL Integration | 1-2 min | 0 |
| Other Providers | 15-30 min | ~1000+ |
| DHL Re-integration | 1-2 min | 0 |
| National Overview | 1-2 min | 0 |
| **Total** | **20-40 min** | **1150-1250** |

## Data Quality Checks

After each run, verify:

1. **Data Matrix**: http://localhost:3000/data-export/matrix
   - Check DHL counts are no longer all 15
   - Large cities should show 50+ DHL locations
   - Total counts look reasonable

2. **National Overview**:
   - Total pakketpunten: ~10,000-11,000
   - DHL: ~4,000 (deduplicated)
   - PostNL: ~4,000
   - VintedGo: ~1,800
   - DeBuren: ~170

3. **Individual Municipalities**:
   - Test Amsterdam: Should have 90+ DHL locations
   - Test Rotterdam: Should have 70+ DHL locations
   - Test smaller cities: Should have reasonable counts

## Maintenance

### Monthly Tasks

- Review log files for recurring errors
- Check disk space usage
- Verify API endpoints are still valid
- Update municipality list if new municipalities are added

### Quarterly Tasks

- Review and optimize rate limiting delays
- Check for API changes from providers
- Update documentation if workflow changes
- Verify deduplication logic is working correctly

### Annual Tasks

- Review entire update process for optimizations
- Consider caching strategies for rarely-changing data
- Evaluate need for additional data sources
- Update Python dependencies

## Support

For issues with:
- **DHL grid fetch**: See `DHL_GRID_WORKFLOW.md`
- **Municipality processing**: See `batch_generate.py` comments
- **Automation setup**: Check this document

## Future Enhancements

Potential improvements:
1. **Incremental updates**: Only update changed municipalities
2. **Parallel processing**: Speed up batch generation
3. **Health checks**: Automated data quality validation
4. **Notifications**: Email/Slack alerts on failures
5. **Dashboard**: Real-time monitoring of update progress
