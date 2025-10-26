#!/usr/bin/env python3
"""
Compress all .geojson files in webapp/public/data to .geojson.gz format.

This script finds all .geojson files that don't have a corresponding .geojson.gz file
and creates compressed versions with maximum compression (level 9).

The Next.js middleware automatically serves .gz files when available and the browser
supports gzip encoding, providing transparent compression for faster loading.
"""

import gzip
import shutil
from pathlib import Path
from datetime import datetime


def compress_geojson_files(data_dir: Path, force: bool = False):
    """
    Compress all .geojson files in the specified directory.

    Parameters
    ----------
    data_dir : Path
        Directory containing .geojson files
    force : bool
        If True, recompress files even if .gz version exists
    """
    print("🗜️  GeoJSON Compression Utility")
    print("=" * 60)
    print(f"Directory: {data_dir}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Find all .geojson files
    geojson_files = sorted(data_dir.glob("*.geojson"))

    if not geojson_files:
        print("❌ No .geojson files found!")
        return

    print(f"Found {len(geojson_files)} .geojson files")
    print()

    compressed_count = 0
    skipped_count = 0
    total_original_size = 0
    total_compressed_size = 0

    for geojson_file in geojson_files:
        gz_file = Path(str(geojson_file) + '.gz')

        # Skip if .gz exists and force=False
        if gz_file.exists() and not force:
            print(f"⏭️  Skipping {geojson_file.name} (already compressed)")
            skipped_count += 1
            continue

        # Compress the file
        try:
            with open(geojson_file, 'rb') as f_in:
                with gzip.open(gz_file, 'wb', compresslevel=9) as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Calculate sizes
            original_size = geojson_file.stat().st_size
            compressed_size = gz_file.stat().st_size
            compression_ratio = (1 - compressed_size / original_size) * 100

            total_original_size += original_size
            total_compressed_size += compressed_size
            compressed_count += 1

            # Format sizes
            if original_size > 1024 * 1024:  # > 1 MB
                size_str = f"{original_size / (1024 * 1024):.2f} MB → {compressed_size / (1024 * 1024):.2f} MB"
            else:
                size_str = f"{original_size / 1024:.1f} KB → {compressed_size / 1024:.1f} KB"

            print(f"✅ {geojson_file.name}")
            print(f"   {size_str} ({compression_ratio:.1f}% reduction)")

        except Exception as e:
            print(f"❌ Error compressing {geojson_file.name}: {e}")

    # Summary
    print()
    print("=" * 60)
    print("📊 COMPRESSION SUMMARY")
    print("=" * 60)
    print(f"✅ Compressed: {compressed_count} files")
    print(f"⏭️  Skipped: {skipped_count} files (already compressed)")

    if compressed_count > 0:
        overall_ratio = (1 - total_compressed_size / total_original_size) * 100

        # Format total sizes
        if total_original_size > 1024 * 1024:  # > 1 MB
            size_str = f"{total_original_size / (1024 * 1024):.2f} MB → {total_compressed_size / (1024 * 1024):.2f} MB"
        else:
            size_str = f"{total_original_size / 1024:.1f} KB → {total_compressed_size / 1024:.1f} KB"

        print(f"💾 Total size: {size_str}")
        print(f"📉 Overall reduction: {overall_ratio:.1f}%")
        print(f"💰 Space saved: {(total_original_size - total_compressed_size) / (1024 * 1024):.2f} MB")

    print()
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("💡 The Next.js middleware will automatically serve .gz files")
    print("   when browsers support gzip encoding (transparent to users)")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compress all .geojson files to .geojson.gz format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python compress_geojson_files.py                    # Compress new files only
  python compress_geojson_files.py --force            # Recompress all files
  python compress_geojson_files.py --data-dir /path   # Custom data directory
        """
    )

    parser.add_argument(
        '--data-dir',
        type=Path,
        default=Path(__file__).parent.parent / "webapp" / "public" / "data",
        help="Directory containing .geojson files (default: webapp/public/data)"
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help="Recompress files even if .gz version already exists"
    )

    args = parser.parse_args()

    # Validate directory
    if not args.data_dir.exists():
        print(f"❌ Error: Directory does not exist: {args.data_dir}")
        return 1

    if not args.data_dir.is_dir():
        print(f"❌ Error: Not a directory: {args.data_dir}")
        return 1

    # Run compression
    compress_geojson_files(args.data_dir, force=args.force)
    return 0


if __name__ == "__main__":
    exit(main())
