"""Download all 256 official gallery images from NanaDraw online site."""
import json
import requests
import os
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

GALLERY_OFFICIAL = Path("app/static/gallery/gallery_official.json")
GALLERY_DIR = Path("app/static/gallery")
GALLERY_JSON = Path("app/static/gallery/gallery.json")
BASE_URL = "https://cdn-mineru.openxlab.org.cn/mineru-rag/prod/shannon/public/nanadraw/web/gallery"
MAX_WORKERS = 8

def download_image(item: dict) -> tuple:
    """Download a single image. Returns (id, success, message)."""
    image_id = item["id"]
    url = item["image_url"]
    output_path = GALLERY_DIR / f"{image_id}.jpg"

    # Force re-download to ensure quality (remove old placeholder images)
    # if output_path.exists() and output_path.stat().st_size > 1000:
    #     return (image_id, True, "already_exists")

    try:
        r = requests.get(url, timeout=60, stream=True)
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        size = output_path.stat().st_size
        return (image_id, True, f"downloaded {size} bytes")
    except Exception as e:
        return (image_id, False, str(e))


def main():
    # Load official data
    with open(GALLERY_OFFICIAL, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Starting download of {len(data)} images...")
    print(f"Saving to: {GALLERY_DIR.resolve()}")

    # Download with thread pool
    success_count = 0
    fail_count = 0
    failed_items = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(download_image, item): item for item in data}

        for future in as_completed(futures):
            image_id, success, msg = future.result()
            if success:
                success_count += 1
                if msg != "already_exists":
                    print(f"  [{success_count}/{len(data)}] Downloaded: {image_id}.jpg")
            else:
                fail_count += 1
                failed_items.append((image_id, msg))
                print(f"  FAILED: {image_id} - {msg}")

    print(f"\nDownload complete: {success_count} succeeded, {fail_count} failed")

    # Retry failed items once
    if failed_items:
        print(f"\nRetrying {len(failed_items)} failed items...")
        time.sleep(2)
        for image_id, _ in failed_items:
            item = next((x for x in data if x["id"] == image_id), None)
            if item:
                _, success, msg = download_image(item)
                if success:
                    success_count += 1
                    fail_count -= 1
                    print(f"  Retry OK: {image_id}")
                else:
                    print(f"  Retry FAILED: {image_id} - {msg}")

    # Update gallery.json with local relative paths
    print("\nUpdating gallery.json with local paths...")
    local_data = []
    for item in data:
        local_item = dict(item)
        local_item["thumbnail_url"] = f"/static/gallery/{item['id']}.jpg"
        local_item["image_url"] = f"/static/gallery/{item['id']}.jpg"
        local_data.append(local_item)

    with open(GALLERY_JSON, "w", encoding="utf-8") as f:
        json.dump(local_data, f, ensure_ascii=False, indent=2)
    print(f"Updated: {GALLERY_JSON}")

    # Print summary
    print(f"\n{'='*50}")
    print(f"FINAL SUMMARY")
    print(f"{'='*50}")
    print(f"Total items: {len(data)}")
    print(f"Successfully downloaded: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Gallery JSON updated: {GALLERY_JSON}")
    print(f"\nLocal deployment ready!")
    print(f"Images are in: {GALLERY_DIR}")
    print(f"API will serve from: /static/gallery/<id>.jpg")


if __name__ == "__main__":
    main()
