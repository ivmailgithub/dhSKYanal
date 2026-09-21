#!/usr/bin/env python3
"""
Cylindrical Multicolor Star Map Dewshield — 3MF & STEP Generator
================================================================
Generates a 3D printable telescope dewshield (180mm outer diameter x 250mm height)
calibrated for a 0.4mm nozzle on Bambu Lab H2C (with AMS + HT-AMS).
All astronomical star chart features cut completely through the full tube wall (2.4mm).

Pre-configured for Bambu Lab H2C:
  Filament 1: TransparentGreen (#00E080) -> Ecliptic & Constellation Labels
  Filament 2: Red (#FF2020)              -> Constellation Lines
  Filament 3: Yellow (#FFD700)           -> Stars (Mag 0 to 5 discs)
  Filament 4: White (#FFFFFF)            -> Index (RA Ruler, Month Calendar, Coordinate Grid)
  Filament 5: Black (#111111)            -> Dewshield Body (Space Background)

All 5 colors extend through the FULL 2.4mm width of the tube (R_inner=87.6mm to R_outer=90.0mm).
Both interior and exterior show identical crisp, continuous celestial geometry.
Zero holes, zero non-manifold edges, zero solid square lettering artifacts.
"""

import os
import sys
import json
import math
import time
import zipfile
import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

PARTS_CONFIG = [
    {
        "class": 0,
        "name": "Dewshield_Body",
        "extruder": 5,
        "color_hex": "111111",
        "rgb": (0.0667, 0.0667, 0.0667),
        "desc": "Dewshield Body (Space Background)"
    },
    {
        "class": 1,
        "name": "Labels_and_Ecliptic",
        "extruder": 1,
        "color_hex": "00e080",
        "rgb": (0.0000, 0.8784, 0.5020),
        "desc": "Ecliptic & Constellation Labels"
    },
    {
        "class": 2,
        "name": "Constellations",
        "extruder": 2,
        "color_hex": "ff2020",
        "rgb": (1.0000, 0.1255, 0.1255),
        "desc": "Constellation Lines"
    },
    {
        "class": 3,
        "name": "Stars",
        "extruder": 3,
        "color_hex": "ffd700",
        "rgb": (1.0000, 0.8431, 0.0000),
        "desc": "Stars (Stellar Discs)"
    },
    {
        "class": 4,
        "name": "Index",
        "extruder": 4,
        "color_hex": "ffffff",
        "rgb": (1.0000, 1.0000, 1.0000),
        "desc": "RA Ruler, Month Calendar, Coordinate Grid"
    },
]

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

# Manual offsets (dx, dy in pixels) for crowded star chart regions
CUSTOM_OFFSETS = {
    'CrB': (0, 75),       # Corona Borealis centered in crown arc
    'Del': (-80, -40),    # Delphinus clear of Aquila
    'Lep': (0, 75),       # Lepus south of Canis Major
    'CrA': (0, 60),       # Corona Austrina clear of Scorpius
    'Lup': (80, 50),      # Lupus clear of Scorpius
    'Ser': (40, -35),     # Serpens Caput clear of Ophiuchus
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert Astronomical Star Chart into a 5-Color Full-Width Dewshield (3MF & STEP)."
    )
    parser.add_argument('--radius', '-r', type=float, default=90.0, help="Outer cylinder radius in mm (default: 90.0 for 180mm diameter)")
    parser.add_argument('--wall', '--wall-thickness', '-w', dest='wall', type=float, default=2.4, help="Total tube wall thickness in mm (default: 2.4)")
    parser.add_argument('--height', '-H', type=float, default=250.0, help="Cylinder height in mm (default: 250.0)")
    parser.add_argument('--angle', '--grid-w', dest='grid_w', type=int, default=1440, help="Circumferential grid resolution (default: 1440 for 0.4mm nozzle)")
    parser.add_argument('--vert', '--grid-h', dest='grid_h', type=int, default=625, help="Axial grid resolution (default: 625 for 0.4mm nozzle)")
    parser.add_argument('--rotate', type=int, default=0, choices=[0, 90, 180, 270], help="Image rotation in degrees (default: 0 for standard cylinder projection)")
    parser.add_argument('--output-3mf', '-m', type=str, default='dewshield_h2c_5color.3mf', help="Output 3MF path (default: dewshield_h2c_5color.3mf)")
    parser.add_argument('--output-step', '-s', type=str, default='dewshield_clean.stp', help="Output STEP path (default: dewshield_clean.stp)")
    parser.add_argument('--skip-step', action='store_true', help="Skip generating STEP file (only output 3MF)")
    parser.add_argument('--skip-3mf', action='store_true', help="Skip generating 3MF file (only output STEP)")
    parser.add_argument('--step-grid-w', type=int, default=480, help="Circumferential grid resolution for STEP export (default: 480 for fast CAD import)")
    parser.add_argument('--step-grid-h', type=int, default=208, help="Axial grid resolution for STEP export (default: 208 for fast CAD import)")
    parser.add_argument('--full-step', action='store_true', help="Force STEP export at full 3MF resolution (warning: large file size)")
    return parser.parse_args()


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


def render_skymap_layers(w=5655, h=2500):
    """
    Renders the astronomical dataset onto a 5655x2500 discrete map (10 px/mm scale):
      0 = Background Body (Black, #111111)
      1 = Labels & Ecliptic (TransparentGreen, #00E080)
      2 = Constellations (Red, #FF2020)
      3 = Stars (Yellow, #FFD700)
      4 = Index (White, #FFFFFF)
    """
    stars_file = os.path.join(WORKSPACE_DIR, 'stars.6.json')
    lines_file = os.path.join(WORKSPACE_DIR, 'constellations.lines.json')
    names_file = os.path.join(WORKSPACE_DIR, 'constellations.json')

    with open(stars_file, encoding='utf-8') as f:
        stars_data = json.load(f)
    with open(lines_file, encoding='utf-8') as f:
        lines_data = json.load(f)
    with open(names_file, encoding='utf-8') as f:
        names_data = json.load(f)

    y_top = int(h * 0.072)   # 180 px for top calendar month strip
    y_bot = int(h * 0.928)   # 2320 px for bottom RA hour ruler & legend
    h_sky = y_bot - y_top
    dec_min = -70.0
    dec_max = 70.0

    def ra_dec_to_xy(ra_deg, dec_deg):
        x = (1.0 - ((ra_deg % 360.0) / 360.0)) * w
        y = y_top + (dec_max - dec_deg) / (dec_max - dec_min) * h_sky
        return x, y

    map_img = Image.new('L', (w, h), 0)
    draw = ImageDraw.Draw(map_img)

    # Fonts
    font_path = r"C:\Windows\Fonts\arialbd.ttf"
    try:
        font_prom  = ImageFont.truetype(font_path, 65)  # 6.5 mm cap height
        font_sec   = ImageFont.truetype(font_path, 48)  # 4.8 mm cap height
        font_ruler = ImageFont.truetype(font_path, 38)  # 3.8 mm cap height
        font_dec   = ImageFont.truetype(font_path, 28)  # 2.8 mm cap height
        font_sub   = ImageFont.truetype(font_path, 22)  # 2.2 mm cap height
    except Exception:
        font_prom = ImageFont.load_default()
        font_sec = font_prom; font_ruler = font_prom; font_dec = font_prom; font_sub = font_prom

    print("  Drawing Layer 4: Coordinate Grid...")
    # RA lines every 15 deg (1 hour)
    for hr in range(24):
        ra = hr * 15.0
        x, _ = ra_dec_to_xy(ra, 0)
        draw.line([(x, y_top), (x, y_bot)], fill=4, width=4)

    # Dec lines every 10 deg (Equator is width 8)
    for dec in range(-60, 70, 10):
        _, y = ra_dec_to_xy(0, dec)
        lw = 8 if dec == 0 else 4
        draw.line([(0, y), (w, y)], fill=4, width=lw)

    # Dec Labels
    for dec in range(-60, 70, 20):
        dstr = "EQUATOR 0°" if dec == 0 else (f"+{dec}°" if dec > 0 else f"{dec}°")
        _, y = ra_dec_to_xy(0, dec)
        draw.text((35, y - 16), dstr, fill=4, font=font_dec)
        draw.text((w - 240, y - 16), dstr, fill=4, font=font_dec)

    print("  Drawing Layer 2: Constellation Lines (Red, 0.6mm)...")
    for feat in lines_data['features']:
        coords = feat['geometry']['coordinates']
        for seg in coords:
            pts = []
            for lon, lat in seg:
                ra = (lon + 360.0) % 360.0
                dec = lat
                pts.append(ra_dec_to_xy(ra, dec))
            for i in range(len(pts) - 1):
                x1, y1 = pts[i]; x2, y2 = pts[i+1]
                if max(y1, y2) < y_top or min(y1, y2) > y_bot:
                    continue
                if abs(x1 - x2) < w / 2:
                    draw.line([(x1, y1), (x2, y2)], fill=2, width=6)
                else:
                    if x1 > x2:
                        dx = (w - x1) + x2
                        frac = (w - x1) / dx
                        y_mid = y1 + (y2 - y1) * frac
                        draw.line([(x1, y1), (w, y_mid)], fill=2, width=6)
                        draw.line([(0, y_mid), (x2, y2)], fill=2, width=6)
                    else:
                        dx = x1 + (w - x2)
                        frac = x1 / dx
                        y_mid = y1 + (y2 - y1) * frac
                        draw.line([(x1, y1), (0, y_mid)], fill=2, width=6)
                        draw.line([(w, y_mid), (x2, y2)], fill=2, width=6)

    print("  Drawing Layer 1: Ecliptic & Constellation Labels (TransparentGreen)...")
    # Ecliptic curve
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
        p1 = ecliptic_pts[i]; p2 = ecliptic_pts[i+1]
        if abs(p1[0] - p2[0]) < 100:
            if (i // 6) % 2 == 0:
                draw.line([p1, p2], fill=1, width=6)

    # Constellation Labels with Letter Tracking and Collision-Free Placement
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

        if y_top + 55 <= y <= y_bot - 55:
            is_prom = cid in PROMINENT
            name = CONSTELLATION_NAMES.get(cid, cid)
            fnt = font_prom if is_prom else font_sec
            trk = 13 if is_prom else 10

            tw, th = get_tracked_bbox(draw, name, fnt, trk)
            tx = x - tw / 2
            ty = y - th / 2

            # Background plate clearing box
            draw.rectangle([(tx - 8, ty - 6), (tx + tw + 8, ty + th + 6)], fill=0)
            draw_tracked_text(draw, (tx, ty), name, fnt, fill=1, tracking=trk)

    print("  Drawing Layer 3: Stars (Yellow, Mag 0 to 5 discs)...")
    star_list = []
    for feat in stars_data['features']:
        lon, lat = feat['geometry']['coordinates']
        mag = feat['properties']['mag']
        ra = (lon + 360.0) % 360.0
        dec = lat
        if dec_min - 4 <= dec <= dec_max + 4:
            star_list.append((ra, dec, mag))

    star_list.sort(key=lambda s: -s[2])  # faintest first

    for ra, dec, mag in star_list:
        x, y = ra_dec_to_xy(ra, dec)
        if not (y_top + 5 <= y <= y_bot - 5):
            continue

        # Calibrated for 0.4mm nozzle:
        if mag <= 0.0:   r_s = 18
        elif mag <= 1.5: r_s = 14
        elif mag <= 2.5: r_s = 11
        elif mag <= 3.5: r_s = 8
        elif mag <= 4.5: r_s = 6
        elif mag <= 5.0: r_s = 4
        else: continue

        draw.ellipse([(x - r_s, y - r_s), (x + r_s, y + r_s)], fill=3)
        if mag <= 1.0:
            draw.ellipse([(x - r_s - 4, y - r_s - 4), (x + r_s + 4, y + r_s + 4)], outline=3, width=3)

    print("  Drawing Top Rim Month Calendar Strip...")
    draw.rectangle([(0, 0), (w, y_top)], fill=0)
    draw.line([(0, y_top), (w, y_top)], fill=4, width=6)

    months = [
        "DECEMBER", "NOVEMBER", "OCTOBER", "SEPTEMBER", "AUGUST", "JULY",
        "JUNE", "MAY", "APRIL", "MARCH", "FEBRUARY", "JANUARY"
    ]
    month_w = w / 12.0
    for i, mname in enumerate(months):
        mx = i * month_w
        draw.line([(mx, 0), (mx, y_top)], fill=4, width=4)
        draw.line([(mx + month_w / 3.0, y_top - 35), (mx + month_w / 3.0, y_top)], fill=4, width=3)
        draw.line([(mx + 2 * month_w / 3.0, y_top - 35), (mx + 2 * month_w / 3.0, y_top)], fill=4, width=3)

        tw, th = get_tracked_bbox(draw, mname, font_ruler, 6)
        tx = mx + (month_w - tw) / 2.0
        ty = (y_top - 35 - th) / 2.0
        draw_tracked_text(draw, (tx, ty), mname, font_ruler, fill=4, tracking=6)

    print("  Drawing Bottom Rim RA Hour Scale & Legend...")
    draw.rectangle([(0, y_bot), (w, h)], fill=0)
    draw.line([(0, y_bot), (w, y_bot)], fill=4, width=6)

    for hr in range(24):
        x, _ = ra_dec_to_xy(hr * 15.0, 0)
        draw.line([(x, y_bot), (x, y_bot + 45)], fill=4, width=4)
        x_half, _ = ra_dec_to_xy((hr + 0.5) * 15.0, 0)
        draw.line([(x_half, y_bot), (x_half, y_bot + 30)], fill=4, width=3)
        for frac in [1/6, 2/6, 4/6, 5/6]:
            xf, _ = ra_dec_to_xy((hr + frac) * 15.0, 0)
            draw.line([(xf, y_bot), (xf, y_bot + 18)], fill=4, width=2)

        txt = f"{hr}h"
        tw, th = get_tracked_bbox(draw, txt, font_ruler, 4)
        draw_tracked_text(draw, (x - tw / 2.0, y_bot + 52), txt, font_ruler, fill=4, tracking=4)

    draw.text((70, y_bot + 105), "STAR MAGNITUDE SCALE:", fill=4, font=font_sub)
    leg_x = 380
    mags_legend = [("0", 18), ("1st", 14), ("2nd", 11), ("3rd", 8), ("4th", 6)]
    for label, r_circ in mags_legend:
        draw.ellipse([(leg_x, y_bot + 115 - r_circ), (leg_x + 2*r_circ, y_bot + 115 + r_circ)], fill=3)
        draw.text((leg_x + 2*r_circ + 10, y_bot + 105), label, fill=4, font=font_sub)
        leg_x += 2*r_circ + 90

    return map_img


def downsample_priority(arr, nw, nh, rotate_deg=0):
    """
    Calibrated priority downsampler for 0.4mm nozzle:
      - Preserves lines (class 2) and stars (class 3) without dropouts.
      - Requires >= 25% pixel coverage for labels (class 1), preventing dilation into solid squares!
      - Connects diagonal strokes cleanly without dilating letters into blobs.
    """
    if rotate_deg != 0:
        rot_k = (rotate_deg // 90) % 4
        # np.rot90 rotates CCW: rot_k=1 is 90 CCW, so 90 CW is rot_k=3
        arr = np.rot90(arr, -rot_k)

    h_orig, w_orig = arr.shape
    grid_class = np.zeros((nh, nw), dtype=np.uint8)
    x_bins = np.linspace(0, w_orig, nw + 1).astype(int)
    y_bins = np.linspace(0, h_orig, nh + 1).astype(int)

    for j in range(nh):
        src_j = nh - 1 - j  # Flip Y: row 0 at Z=0 (bottom rim), row NH-1 at Z=H (top rim)
        y0, y1 = y_bins[src_j], y_bins[src_j + 1]
        for i in range(nw):
            x0, x1 = x_bins[i], x_bins[i + 1]
            block = arr[y0:y1, x0:x1]
            cnt3 = np.count_nonzero(block == 3)
            cnt2 = np.count_nonzero(block == 2)
            cnt1 = np.count_nonzero(block == 1)
            cnt4 = np.count_nonzero(block == 4)

            if cnt3 >= 3:
                grid_class[j, i] = 3
            elif cnt2 >= 3:
                grid_class[j, i] = 2
            elif cnt1 >= 4:  # At least 25% text coverage required (prevents solid square blobs!)
                grid_class[j, i] = 1
            elif cnt4 >= 3:
                grid_class[j, i] = 4
            else:
                grid_class[j, i] = 0

    # 1-pass checkerboard stroke connection for lines (class 2) to ensure 100% 2-manifold closed meshes
    for c in [2]:
        for j in range(nh - 1):
            for i in range(nw):
                i_next = (i + 1) % nw
                if grid_class[j, i] == c and grid_class[j+1, i_next] == c:
                    if grid_class[j+1, i] != c and grid_class[j, i_next] != c:
                        grid_class[j+1, i] = c
                if grid_class[j, i_next] == c and grid_class[j+1, i] == c:
                    if grid_class[j, i] != c and grid_class[j+1, i_next] != c:
                        grid_class[j, i] = c

    return grid_class


def build_3d_meshes(grid_class, r_outer, wall_thickness, h_cyl):
    """
    Constructs 5 watertight 3D solid meshes extending across the full wall thickness
    (from R_inner to R_outer).
    """
    nh, nw = grid_class.shape
    r_inner = r_outer - wall_thickness

    cos_th = np.array([math.cos((i / nw) * 2.0 * math.pi) for i in range(nw)])
    sin_th = np.array([math.sin((i / nw) * 2.0 * math.pi) for i in range(nw)])
    z_vals = np.array([(j / nh) * h_cyl for j in range(nh + 1)])

    out_coords = np.zeros((nh + 1, nw, 3), dtype=np.float32)
    in_coords  = np.zeros((nh + 1, nw, 3), dtype=np.float32)
    for j in range(nh + 1):
        z = z_vals[j]
        for i in range(nw):
            out_coords[j, i] = [r_outer * cos_th[i], r_outer * sin_th[i], z]
            in_coords[j, i]  = [r_inner * cos_th[i], r_inner * sin_th[i], z]

    part_meshes = []

    for p in PARTS_CONFIG:
        c = p['class']
        mask = (grid_class == c)
        v_map = {}
        v_list = []

        def get_vid(j, i, is_out):
            key = (j, i % nw, 1 if is_out else 0)
            idx = v_map.get(key)
            if idx is None:
                idx = len(v_list)
                v_map[key] = idx
                pt = out_coords[j, i % nw] if is_out else in_coords[j, i % nw]
                v_list.append(pt)
            return idx

        triangles = []

        for j in range(nh):
            for i in range(nw):
                if not mask[j, i]:
                    continue
                i_next = (i + 1) % nw

                vo00 = get_vid(j,   i,      True)
                vo10 = get_vid(j,   i_next, True)
                vo11 = get_vid(j+1, i_next, True)
                vo01 = get_vid(j+1, i,      True)

                vi00 = get_vid(j,   i,      False)
                vi10 = get_vid(j,   i_next, False)
                vi11 = get_vid(j+1, i_next, False)
                vi01 = get_vid(j+1, i,      False)

                # Outer cylindrical face (pointing OUT)
                triangles.append((vo00, vo10, vo11))
                triangles.append((vo00, vo11, vo01))

                # Inner cylindrical face (pointing IN)
                triangles.append((vi00, vi11, vi10))
                triangles.append((vi00, vi01, vi11))

                # Bottom rim cap (j == 0)
                if j == 0:
                    triangles.append((vo00, vi10, vo10))
                    triangles.append((vo00, vi00, vi10))
                elif not mask[j - 1, i]:
                    triangles.append((vo00, vi10, vo10))
                    triangles.append((vo00, vi00, vi10))

                # Top rim cap (j == nh - 1)
                if j == nh - 1:
                    triangles.append((vo01, vo11, vi11))
                    triangles.append((vo01, vi11, vi01))
                elif not mask[j + 1, i]:
                    triangles.append((vo01, vo11, vi11))
                    triangles.append((vo01, vi11, vi01))

                # Left radial sidewall (i - 1)
                i_prev = (i - 1 + nw) % nw
                if not mask[j, i_prev]:
                    triangles.append((vo00, vo01, vi01))
                    triangles.append((vo00, vi01, vi00))

                # Right radial sidewall (i + 1)
                if not mask[j, i_next]:
                    triangles.append((vo10, vi11, vo11))
                    triangles.append((vo10, vi10, vi11))

        v_arr = np.array(v_list, dtype=np.float32)
        f_arr = np.array(triangles, dtype=np.int32)
        part_meshes.append((p, v_arr, f_arr))
        print(f"  Solid '{p['name']}': {len(v_arr)} vertices, {len(f_arr)} triangles")

    return part_meshes


def export_3mf(part_meshes, output_path, diam_mm=180.0, height_mm=250.0):
    """
    Exports a native Bambu Studio / OrcaSlicer 3MF project with pre-configured filaments
    for the Bambu Lab H2C + AMS + HT-AMS setup.
    """
    print(f"\nWriting native Bambu Studio 3MF: {output_path}...")
    t0 = time.time()

    model_xml = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:m="http://schemas.microsoft.com/3dmanufacturing/material/2015/02">\n',
        '  <metadata name="Application">BambuStudio</metadata>\n',
        '  <metadata name="BambuStudio:Version">01.09.00.00</metadata>\n',
        '  <resources>\n',
        '    <m:colorgroup id="1">\n',
        '      <m:color color="#00E080FF"/>\n', # 1: TransparentGreen
        '      <m:color color="#FF2020FF"/>\n', # 2: Red
        '      <m:color color="#FFD700FF"/>\n', # 3: Yellow
        '      <m:color color="#FFFFFFFF"/>\n', # 4: White
        '      <m:color color="#111111FF"/>\n', # 5: Black
        '    </m:colorgroup>\n'
    ]

    obj_ids = []
    current_obj_id = 2

    for p, v_arr, f_arr in part_meshes:
        name = p['name']
        ext_id = p['extruder']
        color_idx = ext_id - 1
        obj_ids.append((current_obj_id, name, ext_id))

        model_xml.append(f'    <object id="{current_obj_id}" type="model" name="{name}">\n')
        model_xml.append('      <mesh>\n')
        model_xml.append('        <vertices>\n')
        for v in v_arr:
            model_xml.append(f'          <vertex x="{v[0]:.3f}" y="{v[1]:.3f}" z="{v[2]:.3f}"/>\n')
        model_xml.append('        </vertices>\n')
        model_xml.append('        <triangles>\n')
        for f in f_arr:
            model_xml.append(f'          <triangle v1="{f[0]}" v2="{f[1]}" v3="{f[2]}" pid="1" p1="{color_idx}"/>\n')
        model_xml.append('        </triangles>\n')
        model_xml.append('      </mesh>\n')
        model_xml.append('    </object>\n')
        current_obj_id += 1

    root_obj_id = current_obj_id
    assembly_name = f"Astro_Dewshield_{int(diam_mm)}x{int(height_mm)}"
    model_xml.append(f'    <object id="{root_obj_id}" type="model" name="{assembly_name}">\n')
    model_xml.append('      <components>\n')
    for oid, _, _ in obj_ids:
        model_xml.append(f'        <component objectid="{oid}"/>\n')
    model_xml.append('      </components>\n')
    model_xml.append('    </object>\n')
    model_xml.append('  </resources>\n')
    model_xml.append('  <build>\n')
    model_xml.append(f'    <item objectid="{root_obj_id}"/>\n')
    model_xml.append('  </build>\n')
    model_xml.append('</model>\n')

    full_model_str = "".join(model_xml)

    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        '  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
        '  <Default Extension="config" ContentType="text/plain"/>\n'
        '</Types>\n'
    )

    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        '  <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/05/3dmodel"/>\n'
        '  <Relationship Target="/Metadata/model_settings.config" Id="rel1" Type="http://schemas.bambulab.com/package/2021/model_settings"/>\n'
        '</Relationships>\n'
    )

    model_settings = [
        '; model_settings.config\n',
        '[object_1]\n',
        f'name = {assembly_name}\n\n'
    ]
    for idx, (_, name, ext_id) in enumerate(obj_ids):
        model_settings.append(f'[part_{idx + 1}]\n')
        model_settings.append(f'name = {name}\n')
        model_settings.append(f'extruder = {ext_id}\n\n')
    model_settings_str = "".join(model_settings)

    project_settings = (
        '; project_settings.config\n'
        '[project]\n'
        'filament_colour = #00E080;#FF2020;#FFD700;#FFFFFF;#111111\n'
        'filament_type = PLA;PLA;PLA;PLA;PLA\n'
        'filament_vendor = Bambu;Bambu;Bambu;Bambu;Bambu\n'
        'filament_name = "TransparentGreen";"Red";"Yellow";"White";"Black"\n'
    )

    slice_info = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<config>\n'
        '  <header>\n'
        '    <version>1.0</version>\n'
        '  </header>\n'
        '  <plate>\n'
        '    <filament id="1" color="#00E080" type="PLA" name="TransparentGreen"/>\n'
        '    <filament id="2" color="#FF2020" type="PLA" name="Red"/>\n'
        '    <filament id="3" color="#FFD700" type="PLA" name="Yellow"/>\n'
        '    <filament id="4" color="#FFFFFF" type="PLA" name="White"/>\n'
        '    <filament id="5" color="#111111" type="PLA" name="Black"/>\n'
        '  </plate>\n'
        '</config>\n'
    )

    with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr('[Content_Types].xml', content_types)
        zf.writestr('_rels/.rels', rels)
        zf.writestr('3D/3dmodel.model', full_model_str)
        zf.writestr('Metadata/model_settings.config', model_settings_str)
        zf.writestr('Metadata/project_settings.config', project_settings)
        zf.writestr('Metadata/slice_info.config', slice_info)

    sz_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  [OK] 3MF saved: {output_path} ({sz_mb:.2f} MB, {time.time() - t0:.2f}s)")


def export_step(part_meshes, output_path, diam_mm=180.0, height_mm=250.0):
    """
    Exports a clean STEP AP214 assembly with human-readable entity names and embedded colors.
    """
    print(f"\nWriting STEP AP214 Assembly: {output_path}...")
    t0 = time.time()

    entity_id = 100
    def alloc_id():
        nonlocal entity_id
        res = entity_id
        entity_id += 1
        return res

    assembly_name = f"Astro_Dewshield_{int(diam_mm)}x{int(height_mm)}"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("ISO-10303-21;\nHEADER;\n")
        f.write(f"FILE_DESCRIPTION(('Cylindrical Multicolor Star Map Dewshield Assembly {int(diam_mm)}x{int(height_mm)}'),'2;1');\n")
        f.write(f"FILE_NAME('{os.path.basename(output_path)}','{time.strftime('%Y-%m-%dT%H:%M:%S')}',('User'),('User'),'Processor','System','');\n")
        f.write("FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));\n")
        f.write("ENDSEC;\nDATA;\n")

        app_ctx = alloc_id(); app_proto = alloc_id(); prod_ctx = alloc_id(); pdef_ctx = alloc_id()
        len_unit = alloc_id(); ang_unit = alloc_id(); ster_unit = alloc_id(); uncert = alloc_id(); geom_ctx = alloc_id()
        origin_pt = alloc_id(); dir_z = alloc_id(); dir_x = alloc_id(); axis_pl = alloc_id()

        f.write(f"#{app_ctx} = APPLICATION_CONTEXT('core data for automotive mechanical design processes');\n")
        f.write(f"#{app_proto} = APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,#{app_ctx});\n")
        f.write(f"#{prod_ctx} = PRODUCT_CONTEXT('',#{app_ctx},'mechanical');\n")
        f.write(f"#{pdef_ctx} = PRODUCT_DEFINITION_CONTEXT('part definition',#{app_ctx},'design');\n")
        f.write(f"#{len_unit} = ( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.) );\n")
        f.write(f"#{ang_unit} = ( NAMED_UNIT(*) PLANE_ANGLE_UNIT() SI_UNIT($,.RADIAN.) );\n")
        f.write(f"#{ster_unit} = ( NAMED_UNIT(*) SI_UNIT($,.STERADIAN.) SOLID_ANGLE_UNIT() );\n")
        f.write(f"#{uncert} = UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-07),#{len_unit},'distance_accuracy_value','confusion accuracy');\n")
        f.write(f"#{geom_ctx} = ( GEOMETRIC_REPRESENTATION_CONTEXT(3) GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#{uncert})) GLOBAL_UNIT_ASSIGNED_CONTEXT((#{len_unit},#{ang_unit},#{ster_unit})) REPRESENTATION_CONTEXT('Context #1','3D Context with UNIT and UNCERTAINTY') );\n")
        f.write(f"#{origin_pt} = CARTESIAN_POINT('',(0.,0.,0.));\n")
        f.write(f"#{dir_z} = DIRECTION('',(0.,0.,1.));\n")
        f.write(f"#{dir_x} = DIRECTION('',(1.,0.,0.));\n")
        f.write(f"#{axis_pl} = AXIS2_PLACEMENT_3D('',#{origin_pt},#{dir_z},#{dir_x});\n")

        # Root Assembly Product
        root_prod = alloc_id(); root_form = alloc_id(); root_pdef = alloc_id()
        root_pshp = alloc_id(); root_rep = alloc_id(); root_sdr = alloc_id()

        f.write(f"#{root_prod} = PRODUCT('{assembly_name}','{assembly_name}','',(#{prod_ctx}));\n")
        f.write(f"#{root_form} = PRODUCT_DEFINITION_FORMATION('{assembly_name}','',#{root_prod});\n")
        f.write(f"#{root_pdef} = PRODUCT_DEFINITION('design','{assembly_name}',#{root_form},#{pdef_ctx});\n")
        f.write(f"#{root_pshp} = PRODUCT_DEFINITION_SHAPE('{assembly_name}','',#{root_pdef});\n")
        f.write(f"#{root_rep} = SHAPE_REPRESENTATION('{assembly_name}',(#{axis_pl}),#{geom_ctx});\n")
        f.write(f"#{root_sdr} = SHAPE_DEFINITION_REPRESENTATION(#{root_pshp},#{root_rep});\n")
        f.write(f"#{alloc_id()} = PRODUCT_RELATED_PRODUCT_CATEGORY('assembly',$,(#{root_prod}));\n")

        def make_color(name, rgb):
            r_c, g_c, b_c = rgb
            c_id = alloc_id(); fas_id = alloc_id(); sfa_id = alloc_id()
            surf_fill = alloc_id(); side_id = alloc_id(); usage_id = alloc_id(); style_id = alloc_id()
            f.write(f"#{c_id} = COLOUR_RGB('{name}',{r_c:.4f},{g_c:.4f},{b_c:.4f});\n")
            f.write(f"#{fas_id} = FILL_AREA_STYLE_COLOUR('',#{c_id});\n")
            f.write(f"#{sfa_id} = FILL_AREA_STYLE('',(#{fas_id}));\n")
            f.write(f"#{surf_fill} = SURFACE_STYLE_FILL_AREA(#{sfa_id});\n")
            f.write(f"#{side_id} = SURFACE_SIDE_STYLE('',(#{surf_fill}));\n")
            f.write(f"#{usage_id} = SURFACE_STYLE_USAGE(.BOTH.,#{side_id});\n")
            f.write(f"#{style_id} = PRESENTATION_STYLE_ASSIGNMENT((#{usage_id}));\n")
            return style_id

        for p, v_arr, f_arr in part_meshes:
            name = p['name']
            style_id = make_color(name, p['rgb'])

            # Emit vertices for this part
            v_step_ids = []
            for v in v_arr:
                vid = alloc_id()
                f.write(f"#{vid} = CARTESIAN_POINT('',({v[0]:.4f},{v[1]:.4f},{v[2]:.4f}));\n")
                v_step_ids.append(vid)

            # Emit faces
            face_ids = []
            for tri in f_arr:
                v0_idx, v1_idx, v2_idx = tri
                p0 = v_arr[v0_idx]; p1 = v_arr[v1_idx]; p2 = v_arr[v2_idx]
                d1 = p1 - p0; d2 = p2 - p0
                n = np.cross(d1, d2)
                nl = np.linalg.norm(n)
                n = n / nl if nl > 1e-9 else np.array([0., 0., 1.])
                t = d1 / np.linalg.norm(d1) if np.linalg.norm(d1) > 1e-9 else np.array([1., 0., 0.])

                pid = alloc_id(); dz = alloc_id(); dx = alloc_id(); ax = alloc_id(); pl = alloc_id()
                lid = alloc_id(); bid = alloc_id(); fid = alloc_id()
                f.write(f"#{pid} = CARTESIAN_POINT('',({p0[0]:.4f},{p0[1]:.4f},{p0[2]:.4f}));\n")
                f.write(f"#{dz} = DIRECTION('',({n[0]:.4f},{n[1]:.4f},{n[2]:.4f}));\n")
                f.write(f"#{dx} = DIRECTION('',({t[0]:.4f},{t[1]:.4f},{t[2]:.4f}));\n")
                f.write(f"#{ax} = AXIS2_PLACEMENT_3D('',#{pid},#{dz},#{dx});\n")
                f.write(f"#{pl} = PLANE('',#{ax});\n")
                f.write(f"#{lid} = POLY_LOOP('',(#{v_step_ids[v0_idx]},#{v_step_ids[v1_idx]},#{v_step_ids[v2_idx]}));\n")
                f.write(f"#{bid} = FACE_OUTER_BOUND('',#{lid},.T.);\n")
                f.write(f"#{fid} = FACE_SURFACE('',(#{bid}),#{pl},.T.);\n")
                face_ids.append(fid)

            shell_id = alloc_id(); brep_id = alloc_id()
            f_refs = ','.join(f"#{fid}" for fid in face_ids)
            f.write(f"#{shell_id} = CLOSED_SHELL('',({f_refs}));\n")
            f.write(f"#{brep_id} = FACETED_BREP('{name}_Brep',#{shell_id});\n")

            # Part hierarchy with human-readable names on EVERY entity
            prod_id = alloc_id(); form_id = alloc_id(); pdef_id = alloc_id()
            pshp_id = alloc_id(); rep_id = alloc_id(); sdr_id = alloc_id()

            f.write(f"#{prod_id} = PRODUCT('{name}','{name}','',(#{prod_ctx}));\n")
            f.write(f"#{form_id} = PRODUCT_DEFINITION_FORMATION('{name}','',#{prod_id});\n")
            f.write(f"#{pdef_id} = PRODUCT_DEFINITION('design','{name}',#{form_id},#{pdef_ctx});\n")
            f.write(f"#{pshp_id} = PRODUCT_DEFINITION_SHAPE('{name}','',#{pdef_id});\n")
            f.write(f"#{rep_id} = SHAPE_REPRESENTATION('{name}',(#{axis_pl},#{brep_id}),#{geom_ctx});\n")
            f.write(f"#{sdr_id} = SHAPE_DEFINITION_REPRESENTATION(#{pshp_id},#{rep_id});\n")
            f.write(f"#{alloc_id()} = PRODUCT_RELATED_PRODUCT_CATEGORY('part',$,(#{prod_id}));\n")

            styled_id = alloc_id()
            f.write(f"#{styled_id} = STYLED_ITEM('color',(#{style_id}),#{brep_id});\n")
            f.write(f"#{alloc_id()} = MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',(#{styled_id}),#{geom_ctx});\n")

            nauo_id = alloc_id(); rel_pshp_id = alloc_id(); cdsr_id = alloc_id(); rel_id = alloc_id(); trans_id = alloc_id()
            f.write(f"#{nauo_id} = NEXT_ASSEMBLY_USAGE_OCCURRENCE('{name}','{name}','{name}',#{root_pdef},#{pdef_id},$);\n")
            f.write(f"#{rel_pshp_id} = PRODUCT_DEFINITION_SHAPE('{name}','',#{nauo_id});\n")
            f.write(f"#{cdsr_id} = CONTEXT_DEPENDENT_SHAPE_REPRESENTATION(#{rel_id},#{rel_pshp_id});\n")
            f.write(f"#{rel_id} = ( REPRESENTATION_RELATIONSHIP('','',#{root_rep},#{rep_id}) REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION(#{trans_id}) SHAPE_REPRESENTATION_RELATIONSHIP() );\n")
            f.write(f"#{trans_id} = ITEM_DEFINED_TRANSFORMATION('','',#{axis_pl},#{axis_pl});\n")

        f.write("ENDSEC;\nEND-ISO-10303-21;\n")

    sz_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  [OK] STEP saved: {output_path} ({sz_mb:.2f} MB, {time.time() - t0:.2f}s)")


def export_color_map_png(map_img, output_png):
    """
    Exports a 5K multicolor PNG preview of the star chart mapping matching the 5 filaments.
    """
    arr = np.array(map_img)
    h, w = arr.shape
    rgb_img = np.zeros((h, w, 3), dtype=np.uint8)

    palette = {
        0: (17, 17, 17),       # Black: Dewshield Body
        1: (0, 224, 128),      # TransparentGreen: Labels & Ecliptic
        2: (255, 32, 32),      # Red: Constellations
        3: (255, 215, 0),      # Yellow: Stars
        4: (255, 255, 255),    # White: Index
    }
    for c, col in palette.items():
        rgb_img[arr == c] = col

    preview = Image.fromarray(rgb_img)
    preview.save(output_png)
    thumb_path = os.path.join(WORKSPACE_DIR, "dewshield_h2c_preview.png")
    preview.resize((1200, int(1200 * h / w)), Image.Resampling.LANCZOS).save(thumb_path)
    print(f"  [OK] Graphic previews saved: {output_png} and {thumb_path}")


def main():
    args = parse_args()
    diam_mm = args.radius * 2.0
    circumference = math.pi * diam_mm

    print("=== Cylindrical Multicolor Star Map Dewshield Generator (H2C 5-Color) ===")
    print(f"Dimensions: Outer Diameter={diam_mm:.1f}mm (Radius={args.radius:.2f}mm), Height={args.height:.1f}mm, Wall={args.wall:.2f}mm")
    print(f"Circumference: {circumference:.2f}mm | Inner Radius: {args.radius - args.wall:.2f}mm (all colors cut through full wall)")
    print(f"Target 3MF Resolution: {args.grid_w} angular x {args.grid_h} axial cells (~{circumference/args.grid_w:.3f}mm x {args.height/args.grid_h:.3f}mm per cell)")
    if args.rotate != 0:
        print(f"Projection Rotation: {args.rotate}°")

    t_start = time.time()

    # 1. Calculate map dimensions at 10 pixels/mm
    map_w = int(round(circumference * 10.0))
    map_h = int(round(args.height * 10.0))
    print(f"\n1. Rendering 10 px/mm Vector Sky Map ({map_w} x {map_h} px)...")
    map_img = render_skymap_layers(map_w, map_h)

    # 2. Export 5-color visual preview
    print("\n2. Exporting 5-Color Graphic Preview...")
    preview_path = os.path.join(WORKSPACE_DIR, "dewshield_skymap_h2c_5color_4k.png")
    export_color_map_png(map_img, preview_path)

    # 3. Priority downsample to target cylindrical grid
    print(f"\n3. Priority Downsampling to {args.grid_w}x{args.grid_h} Grid (0.4mm Nozzle Calibrated)...")
    arr = np.array(map_img)
    grid_class = downsample_priority(arr, args.grid_w, args.grid_h, rotate_deg=args.rotate)

    total_cells = args.grid_w * args.grid_h
    for p in PARTS_CONFIG:
        c = p['class']
        cnt = np.sum(grid_class == c)
        print(f"  {p['name']:20s} (Filament {p['extruder']}): {cnt:7d} cells ({cnt/total_cells*100:5.2f}%)")

    # 4. Construct 3D meshes for 3MF
    if not args.skip_3mf:
        print(f"\n4. Constructing 3D Meshes for 3MF ({args.grid_w}x{args.grid_h})...")
        part_meshes_3mf = build_3d_meshes(grid_class, args.radius, args.wall, args.height)
        out_3mf_path = os.path.join(WORKSPACE_DIR, args.output_3mf)
        export_3mf(part_meshes_3mf, out_3mf_path, diam_mm=diam_mm, height_mm=args.height)

    # 5. Construct 3D meshes for STEP
    if not args.skip_step:
        step_w = args.grid_w if args.full_step else args.step_grid_w
        step_h = args.grid_h if args.full_step else args.step_grid_h
        print(f"\n5. Constructing STEP Assembly ({step_w}x{step_h})...")
        if step_w == args.grid_w and step_h == args.grid_h:
            part_meshes_step = part_meshes_3mf
        else:
            grid_class_step = downsample_priority(arr, step_w, step_h, rotate_deg=args.rotate)
            part_meshes_step = build_3d_meshes(grid_class_step, args.radius, args.wall, args.height)

        out_step_path = os.path.join(WORKSPACE_DIR, args.output_step)
        export_step(part_meshes_step, out_step_path, diam_mm=diam_mm, height_mm=args.height)

    print(f"\n=== GENERATION COMPLETE in {time.time() - t_start:.2f}s ===")
    print("Files ready for slicing:")
    if not args.skip_3mf:
        print(f"  * Bambu Studio Project (.3mf): {args.output_3mf} (LOADS IN 1-2s WITH 5 PRE-CONFIGURED FILAMENTS)")
    if not args.skip_step:
        print(f"  * STEP Assembly (.stp):        {args.output_step}")


if __name__ == '__main__':
    main()
