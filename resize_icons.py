from PIL import Image
import os

def resize_and_crop(input_path, output_path, size):
    try:
        with Image.open(input_path) as img:
            # Resize to cover the target size
            img_ratio = img.width / img.height
            target_ratio = size[0] / size[1]
            
            if img_ratio > target_ratio:
                # Image is wider than target
                new_height = size[1]
                new_width = int(new_height * img_ratio)
            else:
                # Image is taller than target
                new_width = size[0]
                new_height = int(new_width / img_ratio)
                
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Center crop
            left = (new_width - size[0]) / 2
            top = (new_height - size[1]) / 2
            right = (new_width + size[0]) / 2
            bottom = (new_height + size[1]) / 2
            
            img = img.crop((left, top, right, bottom))
            img.save(output_path)
            print(f"Successfully saved {output_path}")
    except Exception as e:
        print(f"Error processing {input_path}: {e}")

base_dir = r"c:\Users\Fernando\Music\casino_backend\static\img"
blackjack_path = os.path.join(base_dir, "blackjack.jpg")

if os.path.exists(blackjack_path):
    # Create a vertical screenshot for mobile (720x1280)
    resize_and_crop(blackjack_path, os.path.join(base_dir, "screenshot-mobile.jpg"), (720, 1280))
else:
    print(f"Source image not found at {blackjack_path}")
