#!/usr/bin/env python3
"""
generate_icons.py
Generates Apple Cupertino-style squircle icons for all apps in the IOSonDroid repository.
Corner radius follows Apple iOS icon specification (~22.5% squircle corner radius).
"""

import os
from PIL import Image, ImageDraw, ImageFont

ICONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'repo', 'icons')
REPO_DIR = os.path.join(os.path.dirname(__file__), '..', 'repo')
os.makedirs(ICONS_DIR, exist_ok=True)

def create_gradient(size, start_color, end_color, vertical=True):
    base = Image.new('RGBA', size, (0, 0, 0, 0))
    top = Image.new('RGBA', size, start_color)
    bottom = Image.new('RGBA', size, end_color)
    mask = Image.new('L', size)
    mask_data = []
    w, h = size
    for y in range(h):
        for x in range(w):
            ratio = y / h if vertical else (x + y) / (w + h)
            mask_data.append(int(255 * ratio))
    mask.putdata(mask_data)
    base.paste(top, (0, 0))
    base.paste(bottom, (0, 0), mask)
    return base

def make_ios_squircle(size=(512, 512), bg_start=(0, 122, 255), bg_end=(88, 86, 214)):
    w, h = size
    grad = create_gradient(size, bg_start, bg_end)
    mask = Image.new('L', size, 0)
    draw_mask = ImageDraw.Draw(mask)
    margin = 16
    radius = int((w - margin * 2) * 0.225)
    draw_mask.rounded_rectangle([margin, margin, w - margin, h - margin], radius=radius, fill=255)
    
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    img.paste(grad, (0, 0), mask)
    return img, draw_mask

def draw_touchhle_icon():
    img, _ = make_ios_squircle((512, 512), (28, 28, 30), (72, 72, 74))
    draw = ImageDraw.Draw(img)
    # Draw classic iPhone bezel / iPod touch outline
    draw.rounded_rectangle([150, 90, 362, 422], radius=32, outline=(255, 255, 255, 230), width=8)
    # Screen
    draw.rectangle([168, 140, 344, 350], fill=(0, 122, 255, 200))
    # Home button
    draw.ellipse([236, 368, 276, 408], outline=(255, 255, 255, 200), width=4)
    draw.rounded_rectangle([248, 380, 264, 396], radius=4, outline=(255, 255, 255, 200), width=2)
    # Speaker bar
    draw.rounded_rectangle([230, 112, 282, 118], radius=3, fill=(200, 200, 200, 220))
    # Emulation gear / play symbol on screen
    draw.polygon([(230, 210), (230, 280), (295, 245)], fill=(255, 255, 255, 255))
    return img

def draw_bluebubbles_icon():
    img, _ = make_ios_squircle((512, 512), (0, 122, 255), (10, 132, 255))
    draw = ImageDraw.Draw(img)
    # Speech bubble
    draw.ellipse([110, 130, 402, 360], fill=(255, 255, 255, 255))
    # Tail
    draw.polygon([(150, 330), (100, 395), (200, 350)], fill=(255, 255, 255, 255))
    # iMessage blue dot inside
    draw.ellipse([190, 225, 225, 260], fill=(0, 122, 255, 255))
    draw.ellipse([240, 225, 275, 260], fill=(0, 122, 255, 255))
    draw.ellipse([290, 225, 325, 260], fill=(0, 122, 255, 255))
    return img

def draw_warpshare_icon():
    img, _ = make_ios_squircle((512, 512), (0, 122, 255), (48, 209, 88))
    draw = ImageDraw.Draw(img)
    # AirDrop concentric radar rings
    center = (256, 256)
    for r, w in [(60, 10), (110, 10), (160, 10)]:
        # Draw arc with bottom cutout
        draw.arc([center[0]-r, center[1]-r, center[0]+r, center[1]+r], start=140, end=400, fill=(255, 255, 255, 250), width=w)
    # Center node
    draw.ellipse([236, 236, 276, 276], fill=(255, 255, 255, 255))
    # Upward share arrow
    draw.polygon([(256, 170), (226, 210), (286, 210)], fill=(255, 255, 255, 255))
    return img

def draw_airguard_icon():
    img, _ = make_ios_squircle((512, 512), (52, 199, 89), (0, 122, 255))
    draw = ImageDraw.Draw(img)
    # Shield shape
    shield = [(256, 110), (370, 150), (350, 320), (256, 410), (162, 320), (142, 150)]
    draw.polygon(shield, fill=(255, 255, 255, 240))
    # Inner radar rings (Apple Find My)
    for r in [40, 80]:
        draw.ellipse([256-r, 260-r, 256+r, 260+r], outline=(52, 199, 89, 255), width=6)
    # Radar sweep line
    draw.line([(256, 260), (312, 204)], fill=(52, 199, 89, 255), width=6)
    draw.ellipse([250, 254, 262, 266], fill=(52, 199, 89, 255))
    return img

def draw_smartisland_icon():
    img, _ = make_ios_squircle((512, 512), (0, 0, 0), (28, 28, 30))
    draw = ImageDraw.Draw(img)
    # Dynamic Island pill
    draw.rounded_rectangle([100, 206, 412, 306], radius=50, fill=(44, 44, 46, 255), outline=(255, 255, 255, 60), width=4)
    # Camera circle cutout
    draw.ellipse([135, 238, 175, 274], fill=(10, 10, 10, 255), outline=(255, 255, 255, 40), width=3)
    # Sensor pill cutout
    draw.rounded_rectangle([190, 246, 225, 266], radius=10, fill=(10, 10, 10, 255))
    # Live activity wave / audio equalizer bars (Apple style orange/green)
    bars = [(300, 246, 308, 266), (316, 236, 324, 276), (332, 240, 340, 272), (348, 248, 356, 264)]
    for bar in bars:
        draw.rounded_rectangle(bar, radius=4, fill=(48, 209, 88, 255))
    # Orange mic/orange dot
    draw.ellipse([375, 251, 385, 261], fill=(255, 149, 0, 255))
    return img

def draw_folio_icon():
    img, _ = make_ios_squircle((512, 512), (255, 45, 85), (88, 86, 214))
    draw = ImageDraw.Draw(img)
    # 3x3 App Grid (iOS Springboard)
    colors = [
        (255, 59, 48),  (255, 149, 0), (255, 204, 0),
        (52, 199, 89),  (0, 122, 255), (88, 86, 214),
        (255, 45, 85),  (175, 82, 222),(142, 142, 147)
    ]
    idx = 0
    start_x, start_y = 136, 136
    spacing = 88
    size = 64
    for row in range(3):
        for col in range(3):
            x = start_x + col * spacing
            y = start_y + row * spacing
            draw.rounded_rectangle([x, y, x + size, y + size], radius=16, fill=colors[idx])
            idx += 1
    return img

def draw_calculator_icon():
    img, _ = make_ios_squircle((512, 512), (28, 28, 30), (44, 44, 46))
    draw = ImageDraw.Draw(img)
    # Circle buttons of iOS Calculator: light gray, orange
    # Top-right orange button
    draw.ellipse([290, 120, 390, 220], fill=(255, 159, 10, 255))
    draw.line([(318, 170), (362, 170)], fill=(255, 255, 255), width=8)
    draw.line([(340, 148), (340, 192)], fill=(255, 255, 255), width=8)
    # Top-left gray button
    draw.ellipse([122, 120, 222, 220], fill=(165, 165, 165, 255))
    draw.line([(150, 170), (194, 170)], fill=(0, 0, 0), width=8)
    # Bottom-left dark button
    draw.ellipse([122, 290, 222, 390], fill=(51, 51, 51, 255))
    # Bottom-right orange button (=)
    draw.ellipse([290, 290, 390, 390], fill=(255, 159, 10, 255))
    draw.line([(318, 330), (362, 330)], fill=(255, 255, 255), width=8)
    draw.line([(318, 350), (362, 350)], fill=(255, 255, 255), width=8)
    return img

def draw_notes_icon():
    img, _ = make_ios_squircle((512, 512), (247, 247, 247), (230, 230, 230))
    draw = ImageDraw.Draw(img)
    # Yellow notepad header
    draw.rectangle([16, 16, 496, 140], fill=(255, 204, 0, 255))
    # Tear strip
    draw.line([(16, 140), (496, 140)], fill=(210, 165, 0, 255), width=4)
    # Ruled lines
    for y in [210, 270, 330, 390]:
        draw.line([(80, y), (432, y)], fill=(200, 200, 200, 180), width=3)
    # Pen glyph
    draw.line([(320, 380), (390, 310)], fill=(255, 149, 0, 255), width=14)
    draw.polygon([(305, 395), (320, 380), (310, 365)], fill=(100, 100, 100, 255))
    return img

def draw_controlcenter_icon():
    img, _ = make_ios_squircle((512, 512), (50, 50, 52), (28, 28, 30))
    draw = ImageDraw.Draw(img)
    # Sliders box
    draw.rounded_rectangle([130, 130, 230, 382], radius=32, fill=(80, 80, 82, 230))
    draw.rounded_rectangle([130, 240, 230, 382], radius=32, fill=(255, 255, 255, 255)) # filled volume
    draw.rounded_rectangle([282, 130, 382, 382], radius=32, fill=(80, 80, 82, 230))
    draw.rounded_rectangle([282, 200, 382, 382], radius=32, fill=(255, 255, 255, 255)) # filled brightness
    # Sun glyph on brightness
    draw.ellipse([316, 316, 348, 348], fill=(50, 50, 52, 255))
    return img

def draw_openhaystack_icon():
    img, _ = make_ios_squircle((512, 512), (0, 122, 255), (88, 86, 214))
    draw = ImageDraw.Draw(img)
    # Pin shape
    draw.ellipse([196, 130, 316, 250], fill=(255, 255, 255, 255))
    draw.polygon([(206, 215), (306, 215), (256, 360)], fill=(255, 255, 255, 255))
    draw.ellipse([236, 170, 276, 210], fill=(0, 122, 255, 255))
    # Radar ring underneath
    draw.ellipse([176, 350, 336, 400], outline=(255, 255, 255, 180), width=6)
    return img

def draw_spotube_icon():
    img, _ = make_ios_squircle((512, 512), (250, 36, 60), (254, 44, 85)) # Apple Music pink/red
    draw = ImageDraw.Draw(img)
    # Dual eighth notes (Apple Music icon style)
    draw.ellipse([150, 300, 220, 370], fill=(255, 255, 255, 255))
    draw.ellipse([292, 260, 362, 330], fill=(255, 255, 255, 255))
    draw.rectangle([200, 150, 220, 340], fill=(255, 255, 255, 255))
    draw.rectangle([342, 120, 362, 300], fill=(255, 255, 255, 255))
    draw.polygon([(200, 150), (362, 120), (362, 170), (200, 200)], fill=(255, 255, 255, 255))
    return img

def draw_infinity_icon():
    img, _ = make_ios_squircle((512, 512), (255, 69, 0), (255, 140, 0)) # Reddit orange
    draw = ImageDraw.Draw(img)
    # Apollo-style astronaut helmet visor with clean curved curves
    draw.ellipse([136, 136, 376, 376], fill=(255, 255, 255, 255))
    draw.rounded_rectangle([166, 186, 346, 326], radius=48, fill=(28, 28, 30, 255))
    # Visor reflection
    draw.arc([186, 206, 326, 306], start=200, end=320, fill=(255, 255, 255, 180), width=8)
    return img

def draw_procreate_icon():
    # Procreate: Dark canvas with vibrant neon artistic curved brush stroke
    img, _ = make_ios_squircle((512, 512), (28, 28, 34), (14, 14, 18))
    draw = ImageDraw.Draw(img)
    
    # Curved multi-color brush ribbon
    ribbon_segments = [
        ((110, 390), (160, 320), (175, 82, 222), 26),   # Purple/Violet
        ((160, 320), (210, 240), (255, 45, 85), 32),    # Neon Pink / Magenta
        ((210, 240), (265, 175), (255, 149, 0), 34),   # Bright Orange
        ((265, 175), (325, 135), (255, 204, 0), 30),   # Golden Yellow
        ((325, 135), (385, 120), (52, 199, 89), 24),   # Neon Green
        ((385, 120), (430, 130), (0, 199, 255), 18),   # Electric Cyan
    ]
    for (p1, p2, col, w) in ribbon_segments:
        draw.line([p1, p2], fill=col + (245,), width=w)
        draw.line([(p1[0]+2, p1[1]-2), (p2[0]+2, p2[1]-2)], fill=(255, 255, 255, 90), width=max(4, w // 4))

    # Paint splatters / artistic brush points
    splatters = [
        (130, 340, 5, (175, 82, 222)),
        (185, 280, 7, (255, 45, 85)),
        (240, 205, 8, (255, 149, 0)),
        (300, 150, 6, (255, 204, 0)),
        (360, 125, 5, (52, 199, 89)),
        (405, 122, 4, (0, 199, 255)),
        (420, 145, 3, (0, 122, 255)),
    ]
    for (x, y, r, col) in splatters:
        draw.ellipse([x-r, y-r, x+r, y+r], fill=col + (230,))

    # Brush tip stylus feathering effect
    draw.polygon([(100, 405), (125, 375), (115, 395)], fill=(175, 82, 222, 255))
    return img

def draw_repo_icon():
    # IOSonDroid Logo: Apple shape combined with Android droid antennas & Cupertino blue
    img, _ = make_ios_squircle((512, 512), (0, 122, 255), (88, 86, 214))
    draw = ImageDraw.Draw(img)
    # Droid Head with Apple silhouette
    # Antennas
    draw.line([(190, 180), (150, 130)], fill=(255, 255, 255, 255), width=16)
    draw.line([(322, 180), (362, 130)], fill=(255, 255, 255, 255))
    # Head dome
    draw.pieslice([146, 150, 366, 370], start=180, end=360, fill=(255, 255, 255, 255))
    # Eyes
    draw.ellipse([196, 210, 224, 238], fill=(0, 122, 255, 255))
    draw.ellipse([288, 210, 316, 238], fill=(0, 122, 255, 255))
    # Apple leaf on top
    draw.pieslice([240, 90, 290, 140], start=45, end=225, fill=(52, 199, 89, 255))
    # "iOS" text badge
    draw.rounded_rectangle([176, 290, 336, 350], radius=16, fill=(255, 255, 255, 240))
    # Small line accents
    draw.line([(206, 320), (306, 320)], fill=(0, 122, 255, 255), width=6)
    return img

def main():
    icons = {
        'org.touchhle.android.png': draw_touchhle_icon(),
        'si.savage.procreate.png': draw_procreate_icon(),
        'com.bluebubbles.messaging.png': draw_bluebubbles_icon(),
        'com.moseoridev.warpshare.png': draw_warpshare_icon(),
        'de.seemoo.at_tracking_detection.png': draw_airguard_icon(),
        'com.agupta07505.smartisland.png': draw_smartisland_icon(),
        'com.mccal.folio.png': draw_folio_icon(),
        'io.iosondroid.calculator.png': draw_calculator_icon(),
        'io.iosondroid.notes.png': draw_notes_icon(),
        'io.iosondroid.controlcenter.png': draw_controlcenter_icon(),
        'de.seemoo.openhaystack.png': draw_openhaystack_icon(),
        'oss.krtirtho.spotube.png': draw_spotube_icon(),
        'ml.docilealligator.infinityforreddit.png': draw_infinity_icon()
    }
    
    for filename, icon in icons.items():
        out_path = os.path.join(ICONS_DIR, filename)
        icon.save(out_path, format='PNG')
        print(f'Generated icon: {out_path}')
        
    repo_icon = draw_repo_icon()
    repo_icon_path = os.path.join(REPO_DIR, 'icon.png')
    repo_icon.save(repo_icon_path, format='PNG')
    # Also save to assets
    os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'assets'), exist_ok=True)
    repo_icon.save(os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.png'), format='PNG')
    print(f'Generated repo icon: {repo_icon_path}')

if __name__ == '__main__':
    main()
