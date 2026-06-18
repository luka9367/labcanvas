"""Fetch official gallery data from NanaDraw online site."""
import requests
import json
import os
from pathlib import Path

GALLERY_API = "https://shannon.opendatalab.com/nanadraw/api/v1/gallery"
OUTPUT_DIR = Path("app/static/gallery")

def main():
    print("Fetching official gallery data...")
    r = requests.get(GALLERY_API, timeout=30)
    r.raise_for_status()
    data = r.json()
    print(f"Total items: {len(data)}")

    # Save official data
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    official_path = OUTPUT_DIR / "gallery_official.json"
    with open(official_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved to {official_path}")

    # Show sample URLs
    print("\nSample items:")
    for i in range(3):
        item = data[i]
        print(f"  ID: {item['id']}")
        print(f"  thumbnail: {item['thumbnail_url']}")
        print(f"  image: {item['image_url']}")
        print(f"  category: {item['category']}")

    # Count categories
    cats = {}
    for item in data:
        c = item["category"]
        cats[c] = cats.get(c, 0) + 1
    print(f"\nCategories: {cats}")

    # Check if image URLs are relative or absolute
    all_relative = all(item["image_url"].startswith("/") for item in data)
    print(f"\nAll URLs relative: {all_relative}")

if __name__ == "__main__":
    main()
