import urllib.request
import json
import os

# Create directory if not exists
os.makedirs('backend/app/static/gallery', exist_ok=True)

url = 'https://raw.githubusercontent.com/Shannon4Science/NanaDraw/main/backend/static/gallery/gallery.json'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=60)
data = json.loads(resp.read().decode('utf-8'))

# Save to local file
with open('backend/app/static/gallery/gallery.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'Downloaded {len(data)} reference images metadata')
categories = list(set(item.get('category', 'unknown') for item in data))
print(f'Categories: {categories}')
print('\nFirst 5 items:')
for item in data[:5]:
    print(f"  - {item['id']}: {item['name'][:50]}...")
