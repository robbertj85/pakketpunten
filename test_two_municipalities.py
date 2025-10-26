"""
Test script to generate data for just Zwolle and Elburg
"""
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from batch_generate import process_municipality

def main():
    municipalities = [
        {"name": "Zwolle", "slug": "zwolle"},
        {"name": "Elburg", "slug": "elburg"}
    ]

    print("🧪 Testing data generation for Zwolle and Elburg")
    print("="*60)

    for gemeente_data in municipalities:
        result = process_municipality(gemeente_data)
        print(f"\nResult for {gemeente_data['name']}: {'✅ Success' if result['success'] else '❌ Failed'}")
        if not result['success']:
            print(f"Error: {result.get('error')}")

    print("\n" + "="*60)
    print("✅ Test complete!")

if __name__ == "__main__":
    main()
