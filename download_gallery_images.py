"""Download gallery images from official NanaDraw demo site."""
import json
import os
import urllib.request
import urllib.error
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Create SSL context that doesn't verify certificates (for some sites)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def download_image(item):
    """Download a single gallery image."""
    image_id = item['id']
    
    # Try multiple sources
    urls_to_try = [
        # Official demo site
        f"https://shannon.opendatalab.com/nanadraw/static/gallery/{image_id}.jpg",
        # Alternative paths
        f"https://shannon.opendatalab.com/static/gallery/{image_id}.jpg",
        f"/static/gallery/{image_id}.jpg",
    ]
    
    local_path = f"backend/static/gallery/{image_id}.jpg"
    
    if os.path.exists(local_path):
        return f"Skipped {image_id} (already exists)"
    
    for url in urls_to_try:
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Referer': 'https://shannon.opendatalab.com/',
            })
            
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as resp:
                if resp.status == 200:
                    with open(local_path, 'wb') as f:
                        f.write(resp.read())
                    return f"Downloaded {image_id} from {url}"
        except Exception as e:
            continue
    
    return f"Failed {image_id}: All URLs failed"


def main():
    # Load gallery metadata
    gallery_path = Path("backend/static/gallery/gallery.json")
    if not gallery_path.exists():
        print(f"Gallery metadata not found: {gallery_path}")
        return
    
    with open(gallery_path, 'r', encoding='utf-8') as f:
        gallery_data = json.load(f)
    
    print(f"Total images to download: {len(gallery_data)}")
    
    # Create directory
    os.makedirs("backend/static/gallery", exist_ok=True)
    
    # Download with thread pool
    success_count = 0
    fail_count = 0
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(download_image, item): item for item in gallery_data}
        
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            if result.startswith("Downloaded"):
                success_count += 1
            elif result.startswith("Failed"):
                fail_count += 1
            
            if (i + 1) % 10 == 0 or i == len(gallery_data) - 1:
                print(f"Progress: {i+1}/{len(gallery_data)} | Success: {success_count} | Failed: {fail_count}")
            
            # Print occasional status
            if i < 5 or result.startswith("Failed"):
                print(f"  {result}")
    
    print(f"\nDownload complete!")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")


if __name__ == "__main__":
    main()
