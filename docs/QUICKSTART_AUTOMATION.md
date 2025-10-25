# Quick Start: Automated Updates

## Running a Manual Update

```bash
./update.sh
```

That's it! The script will:
- Update DHL data (grid-based, complete coverage)
- Update PostNL, VintedGo, DeBuren data
- Regenerate national overview
- Create a timestamped log file

## Setting Up Weekly Automation

### macOS (Recommended: Launchd)

```bash
# 1. Create the launchd plist file
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
        <integer>0</integer>
        <key>Hour</key>
        <integer>2</integer>
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

# 2. Create logs directory
mkdir -p logs

# 3. Load the job
launchctl load ~/Library/LaunchAgents/com.pakketpunten.weekly-update.plist

# 4. Verify it's loaded
launchctl list | grep pakketpunten
```

**Result**: Updates run every Sunday at 2 AM automatically.

### Linux/Unix (Cron)

```bash
# 1. Edit crontab
crontab -e

# 2. Add this line (runs every Sunday at 2 AM)
0 2 * * 0 /Users/robbertjanssen/Documents/dev/pakketpunten/update.sh >> /Users/robbertjanssen/Documents/dev/pakketpunten/logs/cron_$(date +\%Y\%m\%d).log 2>&1

# 3. Create logs directory
mkdir -p /Users/robbertjanssen/Documents/dev/pakketpunten/logs
```

## Verifying Updates

After an update runs, check:

1. **View latest log**:
   ```bash
   tail -f $(ls -t weekly_update_*.log | head -1)
   ```

2. **Check Data Matrix**:
   - Open: http://localhost:3000/data-export/matrix
   - Verify DHL counts are updated
   - Large cities should show 50+ DHL locations

3. **Quick verification**:
   ```bash
   # Should show "✅ Weekly update completed successfully!"
   tail -20 $(ls -t weekly_update_*.log | head -1)
   ```

## Troubleshooting

**Update didn't run?**
- Check if launchd job is loaded: `launchctl list | grep pakketpunten`
- Check log files in `logs/` directory
- Verify `update.sh` is executable: `chmod +x update.sh`

**DHL counts still low?**
- Re-run manually: `./update.sh`
- Check `dhl_all_locations.json` file size (should be ~3-5 MB)
- Look for "Hit 50-limit" messages in log

**Other providers not updating?**
- Check network connectivity
- Verify APIs are accessible
- Review error messages in log files

## What Gets Updated

| Provider | Method | Locations | Duration |
|----------|--------|-----------|----------|
| DHL | Grid-based | ~6,000 | 3-5 min |
| PostNL | Per-municipality | ~4,000 | 10-15 min |
| VintedGo | Per-municipality | ~1,800 | 5-10 min |
| DeBuren | Per-municipality | ~170 | 2-5 min |

**Total duration**: ~20-40 minutes

## Files Created

- `weekly_update_YYYYMMDD_HHMMSS.log` - Timestamped log files
- `dhl_all_locations.json` - Complete DHL dataset
- `webapp/public/data/*.geojson` - Updated municipality files
- `webapp/public/data/nederland.geojson` - National overview

## Need Help?

See detailed documentation:
- **Automation setup**: `AUTOMATION.md`
- **DHL grid workflow**: `DHL_GRID_WORKFLOW.md`
- **General usage**: `README.md`
