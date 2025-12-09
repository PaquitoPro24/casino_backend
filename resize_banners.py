from PIL import Image
import os

# Paths to the massive images
images = [
    r"c:\Users\23e06\Videos\proyectos uni\casino_backend\static\img\tragamonedas.jpg",
    r"c:\Users\23e06\Videos\proyectos uni\casino_backend\static\img\ruleta.jpg",
    r"c:\Users\23e06\Videos\proyectos uni\casino_backend\static\img\blackjack.jpg"
]

MAX_WIDTH = 1024

for img_path in images:
    try:
        if not os.path.exists(img_path):
            print(f"Skipping {img_path}, not found.")
            continue
            
        with Image.open(img_path) as img:
            # Calculate new height to maintain aspect ratio
            width_percent = (MAX_WIDTH / float(img.size[0]))
            hsize = int((float(img.size[1]) * float(width_percent)))
            
            # Resize using LANCZOS for high quality downsampling
            img_resized = img.resize((MAX_WIDTH, hsize), Image.Resampling.LANCZOS)
            
            # Save back to the same path (overwrite) with compression
            img_resized.save(img_path, "JPEG", optimize=True, quality=80)
            
            print(f"[OK] Optimized {os.path.basename(img_path)}: {img.size} -> {img_resized.size}")
            
    except Exception as e:
        print(f"[ERROR] processing {img_path}: {e}")
