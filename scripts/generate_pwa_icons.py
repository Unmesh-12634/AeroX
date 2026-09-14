"""
Generate high-resolution, compliant PWA icons for AREOX DGCA Airfare Intelligence.
Creates:
- frontend/icons/icon-192x192.png
- frontend/icons/icon-512x512.png
- frontend/icons/icon-maskable.png
- frontend/icons/apple-touch-icon.png
- frontend/icons/favicon.png
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def generate_icons():
    icons_dir = Path("frontend/icons")
    icons_dir.mkdir(parents=True, exist_ok=True)

    # Base size 1024x1024 for supersampling down to high quality
    size = 1024
    img = Image.new("RGBA", (size, size), (15, 23, 42, 255)) # #0f172a
    draw = ImageDraw.Draw(img)

    # Draw radial gradient simulation
    cx, cy = size // 2, size // 2
    for r in range(size // 2, 0, -4):
        alpha = int(255 * (1 - (r / (size // 2)) * 0.4))
        # subtle blue-slate gradient
        col = (15 + int(20 * (1 - r / (size // 2))),
               23 + int(35 * (1 - r / (size // 2))),
               42 + int(60 * (1 - r / (size // 2))),
               255)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)

    # Outer neon radar ring
    draw.ellipse([cx - 400, cy - 400, cx + 400, cy + 400], outline=(14, 165, 233, 180), width=16) # #0ea5e9
    draw.ellipse([cx - 380, cy - 380, cx + 380, cy + 380], outline=(14, 165, 233, 70), width=4)
    # Inner radar sweep ring
    draw.ellipse([cx - 260, cy - 260, cx + 260, cy + 260], outline=(56, 189, 248, 120), width=8)

    # Radar crosshairs
    draw.line([cx - 440, cy, cx + 440, cy], fill=(14, 165, 233, 90), width=4)
    draw.line([cx, cy - 440, cx, cy + 440], fill=(14, 165, 233, 90), width=4)

    # Glowing center glow
    draw.ellipse([cx - 160, cy - 160, cx + 160, cy + 160], fill=(14, 165, 233, 40))

    # Airplane silhouette in center pointing forward/upward
    # Modern supersonic delta-wing airplane coordinates centered at (cx, cy - 20)
    plane_pts = [
        (cx, cy - 220),          # Nose tip
        (cx + 35, cy - 80),      # Upper fuselage right
        (cx + 220, cy + 80),     # Right wingtip
        (cx + 80, cy + 100),     # Right wing inner
        (cx + 40, cy + 190),     # Right tailfin tip
        (cx, cy + 150),          # Tail center
        (cx - 40, cy + 190),     # Left tailfin tip
        (cx - 80, cy + 100),     # Left wing inner
        (cx - 220, cy + 80),     # Left wingtip
        (cx - 35, cy - 80),      # Upper fuselage left
    ]
    draw.polygon(plane_pts, fill=(255, 255, 255, 255))
    draw.line(plane_pts + [plane_pts[0]], fill=(14, 165, 233, 255), width=6)

    # Cockpit / Canopy accent (Cyan)
    canopy_pts = [
        (cx, cy - 160),
        (cx + 14, cy - 80),
        (cx, cy - 40),
        (cx - 14, cy - 80)
    ]
    draw.polygon(canopy_pts, fill=(56, 189, 248, 255))

    # Engine trails
    draw.ellipse([cx - 18, cy + 150, cx + 18, cy + 186], fill=(245, 158, 11, 230)) # amber glow

    # Save sizes
    # 1. 512x512
    icon512 = img.resize((512, 512), Image.Resampling.LANCZOS)
    icon512.save(icons_dir / "icon-512x512.png", "PNG")
    print("[OK] Saved icon-512x512.png")

    # 2. 192x192
    icon192 = img.resize((192, 192), Image.Resampling.LANCZOS)
    icon192.save(icons_dir / "icon-192x192.png", "PNG")
    print("[OK] Saved icon-192x192.png")

    # 3. Apple Touch Icon 180x180
    icon_apple = img.resize((180, 180), Image.Resampling.LANCZOS)
    icon_apple.save(icons_dir / "apple-touch-icon.png", "PNG")
    print("[OK] Saved apple-touch-icon.png")

    # 4. Favicon 64x64
    favicon = img.resize((64, 64), Image.Resampling.LANCZOS)
    favicon.save(icons_dir / "favicon.png", "PNG")
    print("[OK] Saved favicon.png")

    # 5. Maskable Icon (with 15% safe padding)
    maskable = Image.new("RGBA", (size, size), (15, 23, 42, 255))
    padded_img = img.resize((int(size * 0.76), int(size * 0.76)), Image.Resampling.LANCZOS)
    offset = int(size * 0.12)
    maskable.paste(padded_img, (offset, offset), padded_img)
    maskable_512 = maskable.resize((512, 512), Image.Resampling.LANCZOS)
    maskable_512.save(icons_dir / "icon-maskable.png", "PNG")
    print("[OK] Saved icon-maskable.png")

if __name__ == "__main__":
    generate_icons()
