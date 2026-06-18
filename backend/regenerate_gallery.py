"""Delete old gallery images and regenerate them with new categories."""
import glob
import os
from pathlib import Path
from app.services.gallery_images_service import init_gallery_images

GALLERY_DIR = Path("app/static/gallery")

# Remove old jpg files
for f in glob.glob(str(GALLERY_DIR / "*.jpg")):
    os.remove(f)
    print(f"Removed: {f}")

# Regenerate
init_gallery_images()
