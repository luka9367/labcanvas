import urllib.request
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load gallery data
with open('backend/app/static/gallery/gallery.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Create directory if not exists
os.makedirs('backend/app/static/gallery', exist_ok=True)

def download_image(item):
    image_id = item['id']
    image_url = f"https://raw.githubusercontent.com/Shannon4Science/NanaDraw/main/backend/static/gallery/{image_id}.jpg"
    local_path = f"backend/app/static/gallery/{image_id}.jpg"
    
    if os.path.exists(local_path):
        return f"Skipped {image_id} (already exists)"
    
    try:
        req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(local_path, 'wb') as f:
                f.write(resp.read())
        return f"Downloaded {image_id}"
    except Exception as e:
        return f"Failed {image_id}: {str(e)[:50]}"

# Download images in parallel
print(f"Downloading {len(data)} images...")
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(download_image, item) for item in data]
    for i, future in enumerate(as_completed(futures)):
        result = future.result()
        if i % 20 == 0 or "Failed" in result:
            print(f"[{i+1}/{len(data)}] {result}")

print("\nDownload complete!")

# Count downloaded files
downloaded = len([f for f in os.listdir('backend/app/static/gallery') if f.endswith('.jpg')])
print(f"Total images: {downloaded}/{len(data)}")
