import json
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

workspace = r"C:\Users\ivmai\workspace\astro-prints"

# Exact physical dimensions:
# Diameter = 180.0 mm -> Circumference = pi * 180.0 = 565.487 mm
# Height = 250.0 mm
# Scale: 10 pixels per mm (254 DPI)
W = 5655
H = 2500

# Margins:
# Top: 18 mm = 180 px (Month calendar strip)
# Bottom: 18 mm = 180 px (Right Ascension hour ruler & legend)
# Sky area: 214 mm = 2140 px
Y_TOP = 180
Y_BOT = 2320
H_SKY = Y_BOT - Y_TOP

# Sky coordinates:
# Declination: -70 deg (bottom) to +70 deg (top) -> Total span = 140 deg
# 140 deg across 214mm = 1.528 mm/deg
# Circumference: 360 deg across 565.5mm = 1.571 mm/deg
# Virtually exact 1:1 isotropic projection (less than 2.8% difference)!
DEC_MIN = -70.0
DEC_MAX = 70.0

CONSTELLATION_NAMES = {
    'And': 'ANDROMEDA', 'Ant': 'ANTLIA', 'Aps': 'APUS', 'Aqr': 'AQUARIUS',
    'Aql': 'AQUILA', 'Ara': 'ARA', 'Ari': 'ARIES', 'Aur': 'AURIGA',
    'Boo': 'BOOTES', 'Cae': 'CAELUM', 'Cam': 'CAMELOPARDALIS', 'Cnc': 'CANCER',
    'CVn': 'CANES VENATICI', 'CMa': 'CANIS MAJOR', 'CMi': 'CANIS MINOR',
    'Cap': 'CAPRICORNUS', 'Car': 'CARINA', 'Cas': 'CASSIOPEIA', 'Cen': 'CENTAURUS',
    'Cep': 'CEPHEUS', 'Cet': 'CETUS', 'Cha': 'CHAMAELEON', 'Cir': 'CIRCINUS',
    'Col': 'COLUMBA', 'Com': 'COMA BERENICES', 'CrA': 'CORONA AUSTRINA',
    'CrB': 'CORONA BOREALIS', 'Crv': 'CORVUS', 'Crt': 'CRATER', 'Cru': 'CRUX',
    'Cyg': 'CYGNUS', 'Del': 'DELPHINUS', 'Dor': 'DORADO', 'Dra': 'DRACO',
    'Equ': 'EQUULEUS', 'Eri': 'ERIDANUS', 'For': 'FORNAX', 'Gem': 'GEMINI',
    'Gru': 'GRUS', 'Her': 'HERCULES', 'Hor': 'HOROLOGIUM', 'Hya': 'HYDRA',
    'Hyi': 'HYDRUS', 'Ind': 'INDUS', 'Lac': 'LACERTA', 'Leo': 'LEO',
    'LMi': 'LEO MINOR', 'Lep': 'LEPUS', 'Lib': 'LIBRA', 'Lup': 'LUPUS',
    'Lyn': 'LYNX', 'Lyr': 'LYRA', 'Men': 'MENSA', 'Mic': 'MICROSCOPIUM',
    'Mon': 'MONOCEROS', 'Mus': 'MUSCA', 'Nor': 'NORMA', 'Oct': 'OCTANS',
    'Oph': 'OPHIUCHUS', 'Ori': 'ORION', 'Pav': 'PAVO', 'Peg': 'PEGASUS',
    'Per': 'PERSEUS', 'Phe': 'PHOENIX', 'Pic': 'PICTOR', 'Psc': 'PISCES',
    'PsA': 'PISCIS AUSTRINUS', 'Pup': 'PUPPIS', 'Pyx': 'PYXIS', 'Ret': 'RETICULUM',
    'Sge': 'SAGITTA', 'Sgr': 'SAGITTARIUS', 'Sco': 'SCORPIUS', 'Scl': 'SCULPTOR',
    'Sct': 'SCUTUM', 'Ser': 'SERPENS', 'Sex': 'SEXTANS', 'Tau': 'TAURUS',
    'Tel': 'TELESCOPIUM', 'Tri': 'TRIANGULUM', 'TrA': 'TRIANGULUM AUSTRALE',
    'Tuc': 'TUCANA', 'UMa': 'URSA MAJOR', 'UMi': 'URSA MINOR', 'Vel': 'VELA',
    'Vir': 'VIRGO', 'Vol': 'VOLANS', 'Vul': 'VULPECULA'
}

PROMINENT = {
    'Ori', 'UMa', 'Cas', 'Leo', 'Cyg', 'Lyr', 'Aql', 'Tau',
    'Gem', 'CMa', 'Peg', 'Sco', 'Sgr', 'Boo', 'Her', 'Vir',
    'And', 'Per', 'Aur', 'Cep', 'Cru', 'Cen', 'Car', 'Hya',
    'Oph', 'Cet', 'Cap', 'Aqr', 'Psc', 'Ari', 'Dra'
}

EXCLUDE = {"Mic", "Tel", "Cae", "Ant", "Sex", "Vul", "Equ", "Men", "Cha", "Vol", "Mus"}

CUSTOM_OFFSETS = {
    'CrB': (0, 75),       # Corona Borealis into crown arc
    'Del': (-80, -40),    # Delphinus away from Aquila
    'Lep': (0, 75),       # Lepus south of Canis Major
    'CrA': (0, 60),       # Corona Austrina down
    'Lup': (80, 50),      # Lupus away from Scorpius
    'Ser': (40, -35),     # Serpens Caput clear of Ophiuchus
}

# Load datasets
with open(os.path.join(workspace, 'stars.6.json'), encoding='utf-8') as f:
    stars_data = json.load(f)
with open(os.path.join(workspace, 'constellations.lines.json'), encoding='utf-8') as f:
    lines_data = json.load(f)
with open(os.path.join(workspace, 'constellations.json'), encoding='utf-8') as f:
    names_data = json.load(f)

def ra_dec_to_xy(ra_deg, dec_deg):
    x = (1.0 - ((ra_deg % 360.0) / 360.0)) * W
    y = Y_TOP + (DEC_MAX - dec_deg) / (DEC_MAX - DEC_MIN) * H_SKY
    return x, y

def draw_tracked_text(draw, pos, text, font, fill, tracking=13):
    x, y = pos
    for ch in text:
        draw.text((x, y), ch, fill=fill, font=font)
        bb = draw.textbbox((0, 0), ch, font=font)
        x += (bb[2] - bb[0]) + tracking

def get_tracked_bbox(draw, text, font, tracking=13):
    total_w = 0
    max_h = 0
    for ch in text:
        bb = draw.textbbox((0, 0), ch, font=font)
        total_w += (bb[2] - bb[0]) + tracking
        max_h = max(max_h, bb[3] - bb[1])
    return total_w - tracking, max_h

def render_map(mode='multicolor'):
    """
    mode: 'lithophane' (pure high-contrast grayscale) or 'multicolor' (H2C 5-Color)
    """
    if mode == 'lithophane':
        c_bg = (0, 0, 0)
        c_ruler_bg = (10, 10, 10)
        c_ruler_line = (255, 255, 255)
        c_ruler_text = (255, 255, 255)
        c_grid = (50, 50, 50)
        c_grid_eq = (120, 120, 120)
        c_ecliptic = (180, 180, 180)
        c_const_line = (230, 230, 230)
        c_star_bright = (255, 255, 255)
        c_star_mid = (235, 235, 235)
        c_star_faint = (180, 180, 180)
        c_text_prom = (255, 255, 255)
        c_text_sec = (190, 190, 190)
    else:  # multicolor (H2C 5-Color: 1:TransGreen, 2:Red, 3:Yellow, 4:White, 5:Black)
        c_bg = (17, 17, 17)            # Filament 5: Black dewshield body
        c_ruler_bg = (17, 17, 17)
        c_ruler_line = (255, 255, 255) # Filament 4: White index
        c_ruler_text = (255, 255, 255)
        c_grid = (180, 180, 180)       # Filament 4: White grid
        c_grid_eq = (255, 255, 255)
        c_ecliptic = (0, 224, 128)     # Filament 1: TransparentGreen ecliptic
        c_const_line = (255, 32, 32)   # Filament 2: Red constellation lines
        c_star_bright = (255, 215, 0)  # Filament 3: Yellow stars
        c_star_mid = (255, 215, 0)
        c_star_faint = (255, 215, 0)
        c_text_prom = (0, 224, 128)    # Filament 1: TransparentGreen labels
        c_text_sec = (0, 224, 128)

    img = Image.new('RGB', (W, H), c_bg)
    draw = ImageDraw.Draw(img)

    # 1. RA Grid lines every 15 deg (1 hour)
    for h in range(24):
        ra = h * 15.0
        x, _ = ra_dec_to_xy(ra, 0)
        draw.line([(x, Y_TOP), (x, Y_BOT)], fill=c_grid, width=4)

    # 2. Dec Grid lines every 10 deg
    for dec in range(-60, 70, 10):
        _, y = ra_dec_to_xy(0, dec)
        width = 8 if dec == 0 else 4
        color = c_grid_eq if dec == 0 else c_grid
        draw.line([(0, y), (W, y)], fill=color, width=width)

    # Fonts
    font_path = r"C:\Windows\Fonts\arialbd.ttf"
    try:
        font_prom  = ImageFont.truetype(font_path, 65)  # 6.5 mm
        font_sec   = ImageFont.truetype(font_path, 48)  # 4.8 mm
        font_ruler = ImageFont.truetype(font_path, 38)  # 3.8 mm
        font_dec   = ImageFont.truetype(font_path, 28)  # 2.8 mm
        font_sub   = ImageFont.truetype(font_path, 22)  # 2.2 mm
    except Exception:
        font_prom = ImageFont.load_default()
        font_sec = font_prom; font_ruler = font_prom; font_dec = font_prom; font_sub = font_prom

    # Dec Labels
    for dec in range(-60, 70, 20):
        dstr = "EQUATOR 0°" if dec == 0 else (f"+{dec}°" if dec > 0 else f"{dec}°")
        _, y = ra_dec_to_xy(0, dec)
        draw.text((35, y - 16), dstr, fill=c_grid_eq, font=font_dec)
        draw.text((W - 240, y - 16), dstr, fill=c_grid_eq, font=font_dec)

    # 3. Ecliptic dashed line
    ecliptic_pts = []
    for deg in range(0, 361, 1):
        l_rad = math.radians(deg)
        eps_rad = math.radians(23.439)
        sin_dec = math.sin(eps_rad) * math.sin(l_rad)
        dec = math.degrees(math.asin(sin_dec))
        ra = math.degrees(math.atan2(math.cos(eps_rad) * math.sin(l_rad), math.cos(l_rad)))
        x, y = ra_dec_to_xy(ra, dec)
        ecliptic_pts.append((x, y))

    ecliptic_pts.sort(key=lambda p: p[0])
    for i in range(len(ecliptic_pts) - 1):
        p1 = ecliptic_pts[i]
        p2 = ecliptic_pts[i+1]
        if abs(p1[0] - p2[0]) < 100:
            if (i // 6) % 2 == 0:
                draw.line([p1, p2], fill=c_ecliptic, width=6)

    # 4. Constellation Lines with SEAMLESS CYLINDER WRAPPING (0.6mm width)
    for feat in lines_data['features']:
        coords = feat['geometry']['coordinates']
        for seg in coords:
            pts = []
            for lon, lat in seg:
                ra = (lon + 360.0) % 360.0
                dec = lat
                pts.append(ra_dec_to_xy(ra, dec))
            for i in range(len(pts) - 1):
                p1 = pts[i]; p2 = pts[i+1]
                x1, y1 = p1; x2, y2 = p2
                if max(y1, y2) < Y_TOP or min(y1, y2) > Y_BOT:
                    continue
                if abs(x1 - x2) < W / 2:
                    draw.line([(x1, y1), (x2, y2)], fill=c_const_line, width=6)
                else:
                    if x1 > x2:
                        dx = (W - x1) + x2
                        frac = (W - x1) / dx
                        y_mid = y1 + (y2 - y1) * frac
                        draw.line([(x1, y1), (W, y_mid)], fill=c_const_line, width=6)
                        draw.line([(0, y_mid), (x2, y2)], fill=c_const_line, width=6)
                    else:
                        dx = x1 + (W - x2)
                        frac = x1 / dx
                        y_mid = y1 + (y2 - y1) * frac
                        draw.line([(x1, y1), (0, y_mid)], fill=c_const_line, width=6)
                        draw.line([(W, y_mid), (x2, y2)], fill=c_const_line, width=6)

    # 5. Constellation Labels (Tracked, Collision-Free)
    seen_ser = False
    for feat in names_data['features']:
        cid = feat['id']
        if cid in EXCLUDE:
            continue
        if cid == 'Ser':
            if seen_ser: continue
            seen_ser = True

        lon, lat = feat['geometry']['coordinates']
        ra = (lon + 360.0) % 360.0
        dec = lat
        x, y = ra_dec_to_xy(ra, dec)
        dx, dy = CUSTOM_OFFSETS.get(cid, (0, 0))
        x += dx; y += dy

        if Y_TOP + 55 <= y <= Y_BOT - 55:
            is_prom = cid in PROMINENT
            name = CONSTELLATION_NAMES.get(cid, cid)
            fnt = font_prom if is_prom else font_sec
            col = c_text_prom if is_prom else c_text_sec
            trk = 13 if is_prom else 10

            tw, th = get_tracked_bbox(draw, name, fnt, trk)
            tx = x - tw / 2
            ty = y - th / 2

            # Background plate for legibility
            draw.rectangle([(tx - 8, ty - 6), (tx + tw + 8, ty + th + 6)], fill=c_bg)
            draw_tracked_text(draw, (tx, ty), name, fnt, fill=col, tracking=trk)

    # 6. Stars (calibrated for 0.4mm nozzle)
    star_list = []
    for feat in stars_data['features']:
        lon, lat = feat['geometry']['coordinates']
        mag = feat['properties']['mag']
        ra = (lon + 360.0) % 360.0
        dec = lat
        if DEC_MIN - 4 <= dec <= DEC_MAX + 4:
            star_list.append((ra, dec, mag))

    star_list.sort(key=lambda s: -s[2])  # faintest first

    for ra, dec, mag in star_list:
        x, y = ra_dec_to_xy(ra, dec)
        if not (Y_TOP + 5 <= y <= Y_BOT - 5):
            continue

        if mag <= 0.0:
            r = 18; col = c_star_bright
        elif mag <= 1.5:
            r = 14; col = c_star_bright
        elif mag <= 2.5:
            r = 11; col = c_star_mid
        elif mag <= 3.5:
            r = 8; col = c_star_mid
        elif mag <= 4.5:
            r = 6; col = c_star_faint
        elif mag <= 5.0:
            r = 4; col = c_star_faint
        else:
            continue

        draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=col)
        if mag <= 1.0:
            draw.ellipse([(x - r - 4, y - r - 4), (x + r + 4, y + r + 4)], outline=col, width=3)

    # 7. Top Header: Calendar Month Ruler
    draw.rectangle([(0, 0), (W, Y_TOP)], fill=c_ruler_bg)
    draw.line([(0, Y_TOP), (W, Y_TOP)], fill=c_ruler_line, width=6)

    months = [
        "DECEMBER", "NOVEMBER", "OCTOBER", "SEPTEMBER", "AUGUST", "JULY",
        "JUNE", "MAY", "APRIL", "MARCH", "FEBRUARY", "JANUARY"
    ]
    month_w = W / 12.0
    for i, mname in enumerate(months):
        mx = i * month_w
        draw.line([(mx, 0), (mx, Y_TOP)], fill=c_ruler_line, width=4)
        draw.line([(mx + month_w / 3.0, Y_TOP - 35), (mx + month_w / 3.0, Y_TOP)], fill=c_ruler_line, width=3)
        draw.line([(mx + 2 * month_w / 3.0, Y_TOP - 35), (mx + 2 * month_w / 3.0, Y_TOP)], fill=c_ruler_line, width=3)

        tw, th = get_tracked_bbox(draw, mname, font_ruler, 6)
        tx = mx + (month_w - tw) / 2.0
        ty = (Y_TOP - 35 - th) / 2.0
        draw_tracked_text(draw, (tx, ty), mname, font_ruler, fill=c_ruler_text, tracking=6)

    # 8. Bottom Footer: Right Ascension Ruler (0h to 24h) & Legend
    draw.rectangle([(0, Y_BOT), (W, H)], fill=c_ruler_bg)
    draw.line([(0, Y_BOT), (W, Y_BOT)], fill=c_ruler_line, width=6)

    for hr in range(24):
        x, _ = ra_dec_to_xy(hr * 15.0, 0)
        draw.line([(x, Y_BOT), (x, Y_BOT + 45)], fill=c_ruler_line, width=4)
        x_half, _ = ra_dec_to_xy((hr + 0.5) * 15.0, 0)
        draw.line([(x_half, Y_BOT), (x_half, Y_BOT + 30)], fill=c_ruler_line, width=3)
        for frac in [1/6, 2/6, 4/6, 5/6]:
            xf, _ = ra_dec_to_xy((hr + frac) * 15.0, 0)
            draw.line([(xf, Y_BOT), (xf, Y_BOT + 18)], fill=c_ruler_line, width=2)

        txt = f"{hr}h"
        tw, th = get_tracked_bbox(draw, txt, font_ruler, 4)
        draw_tracked_text(draw, (x - tw / 2.0, Y_BOT + 52), txt, font_ruler, fill=c_ruler_text, tracking=4)

    # Magnitude Legend
    draw.text((70, Y_BOT + 105), "STAR MAGNITUDE SCALE:", fill=c_ruler_text, font=font_sub)
    leg_x = 380
    mags_legend = [("0", 18), ("1st", 14), ("2nd", 11), ("3rd", 8), ("4th", 6)]
    for label, r_circ in mags_legend:
        draw.ellipse([(leg_x, Y_BOT + 115 - r_circ), (leg_x + 2*r_circ, Y_BOT + 115 + r_circ)], fill=c_star_bright)
        draw.text((leg_x + 2*r_circ + 10, Y_BOT + 105), label, fill=c_ruler_text, font=font_sub)
        leg_x += 2*r_circ + 90

    return img


if __name__ == '__main__':
    print("=== Rendering 180mm x 250mm Sky Maps (0.4mm Nozzle Calibrated) ===")
    print(f"Canvas: {W} x {H} px (10 px/mm scale, 254 DPI)")
    
    print("\nRendering Multicolor map (H2C 5-Color)...")
    img_multi = render_map('multicolor')
    path_multi = os.path.join(workspace, "dewshield_skymap_multicolor_4k.png")
    img_multi.save(path_multi)
    print(f"  [OK] Saved {path_multi}")

    print("\nRendering Lithophane map (pure B&W high contrast)...")
    img_litho = render_map('lithophane')
    path_litho = os.path.join(workspace, "dewshield_skymap_lithophane_4k.png")
    img_litho.save(path_litho)
    print(f"  [OK] Saved {path_litho}")

    print("\nCreating thumbnails...")
    thumb_multi_path = os.path.join(workspace, "thumb_multicolor.png")
    img_multi.resize((1200, int(1200 * H / W)), Image.Resampling.LANCZOS).save(thumb_multi_path)
    
    thumb_litho_path = os.path.join(workspace, "thumb_lithophane.png")
    img_litho.resize((1200, int(1200 * H / W)), Image.Resampling.LANCZOS).save(thumb_litho_path)
    print(f"  [OK] Saved {thumb_multi_path} and {thumb_litho_path}")
    print("\nDone!")
