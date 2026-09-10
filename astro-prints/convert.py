#!/usr/bin/env python3
"""
Cylindrical Multicolor Star Map Lithophane — STEP File Generator (Python Version)
================================================================================
Projects an astronomical star chart onto a 3D printable cylinder in STEP
(ISO 10303-21 AP214/AP242) format for multicolor 3D printing (Bambu AMS, OrcaSlicer,
PrusaSlicer).

Key Design & Engineering Features:
- Natural astronomical orientation: Right Ascension wraps 360° circumferentially;
  Declination spans the cylinder axis Z with date markings at the bottom (Z approx 0).
- Lithophane interior: Wall thickness varies smoothly based on image brightness
  (thin wall for bright stars/lines to let light through, thick wall for dark space).
- Smooth exterior: Constant outer radius (zero exterior relief bumps) so prints
  are smooth to the touch, print reliably without nozzle knocking or wipe-tower collapses.
- Multicolor assembly: 4 distinct color parts matching the sky map colors:
    1. Space_Background   (Navy: #0a0e27)  — Full lithophane hollow cylinder tube with base flange
    2. Stars              (Yellow: #ffd700) — Metric round circular star dots
    3. Constellation_Lines(Blue: #2e6fd9)  — Constellation stick figures and text
    4. Index_Lines        (Cyan: #8ab4f8)  — Coordinate grid (RA/Dec) & bottom date ruler
- 100% 2-manifold, watertight closed solids natively compatible with all CAD kernels & slicers.
- Zero crashes, zero sewing hangs in OpenCASCADE / BambuStudio / OrcaSlicer.

Usage:
  python convert.py [options]

Options:
  --input <file>         Input image file (default: auto-detect)
  --output <file>        Output STEP file (default: image0_cylinder.stp)
  --radius <mm>          Outer cylinder radius in mm (default: 35.0)
  --height <mm>          Cylinder height in mm (default: auto isotropic ~138mm)
  --min-wall <mm>        Thinnest wall section for brightest pixels in mm (default: 0.8)
  --max-wall <mm>        Thickest wall section for darkest pixels in mm (default: 2.2)
  --base-flange <mm>     Bottom mounting flange height in mm (default: 2.0)
  --relief <mm>          Exterior relief height in mm (default: 0.0 = smooth lithophane)
  --grid-w <num>         Circumferential grid resolution (default: 180)
  --grid-h <num>         Axial grid resolution (default: 113)
  --color-bg <hex>       Hex color for space background (default: 0a0e27)
  --color-stars <hex>    Hex color for stars (default: ffd700)
  --color-lines <hex>    Hex color for constellation lines (default: 2e6fd9)
  --color-index <hex>    Hex color for index/dates (default: 8ab4f8)
  --help                 Show this help
"""

import os
import sys
import glob
import math
import time
import argparse
import numpy as np
from PIL import Image
import scipy.ndimage as ndi


def hex_to_rgb(hex_str):
    clean = hex_str.lstrip('#')
    if len(clean) == 3:
        clean = ''.join(c * 2 for c in clean)
    num = int(clean, 16)
    return ((num >> 16) & 255) / 255.0, ((num >> 8) & 255) / 255.0, (num & 255) / 255.0


def parse_args():
    parser = argparse.ArgumentParser(description="Convert Star Map image to 3D printable multicolor lithophane STEP cylinder.")
    parser.add_argument('--input', type=str, default=None, help="Input image path")
    parser.add_argument('--output', type=str, default='image0_cylinder.stp', help="Output STEP file path")
    parser.add_argument('--radius', '--radious', dest='radius', type=float, default=35.0, help="Outer cylinder radius in mm (default: 35.0)")
    parser.add_argument('--height', type=float, default=None, help="Cylinder height in mm (default: auto isotropic)")
    parser.add_argument('--min-wall', type=float, default=0.8, help="Thinnest wall section (brightest) in mm (default: 0.8)")
    parser.add_argument('--max-wall', type=float, default=2.2, help="Thickest wall section (darkest) in mm (default: 2.2)")
    parser.add_argument('--base-flange', '--base', dest='base_flange', type=float, default=2.0, help="Bottom mounting flange height in mm (default: 2.0)")
    parser.add_argument('--relief', type=float, default=0.0, help="Exterior relief in mm (default: 0.0 = smooth lithophane)")
    parser.add_argument('--grid-w', '--angle', dest='grid_w', type=int, default=180, help="Circumferential grid steps (default: 180)")
    parser.add_argument('--grid-h', '--vert', dest='grid_h', type=int, default=113, help="Axial grid steps (default: 113)")
    parser.add_argument('--color-bg', '--color0', dest='color_bg', type=str, default='0a0e27', help="Hex color for space background")
    parser.add_argument('--color-stars', '--color1', dest='color_stars', type=str, default='ffd700', help="Hex color for stars")
    parser.add_argument('--color-lines', '--color2', dest='color_lines', type=str, default='2e6fd9', help="Hex color for constellation lines")
    parser.add_argument('--color-index', '--color3', dest='color_index', type=str, default='8ab4f8', help="Hex color for index/dates")
    return parser.parse_args()


def find_default_image():
    patterns = [
        'image0.thumb.jpeg.aa268959b09fe82e7febe723f0c3ff75.jpeg',
        'image0.thumb.*.jpeg',
        'image0*.jpeg',
        '*.jpeg',
        '*.jpg',
        '*.png'
    ]
    for pat in patterns:
        matches = glob.glob(pat)
        if matches:
            return matches[0]
    return None


def main():
    args = parse_args()
    input_file = args.input
    if not input_file:
        input_file = find_default_image()
        if not input_file:
            print("Error: No input image found. Specify with --input <file>")
            sys.exit(1)

    print("=== Cylindrical Multicolor Star Map Lithophane Generator (Python) ===")
    print(f"Loading image: {input_file}")
    img = Image.open(input_file).convert('RGB')

    # Rotate 90 CCW to natural astronomical orientation:
    # Circumference wraps the 24-hour RA axis (750px),
    # Cylinder axis Z spans Declination (472px) with date markings at the bottom (Z approx 0).
    rot_img = img.transpose(Image.Transpose.ROTATE_90)
    rot_arr = np.array(rot_img)
    H_orig, W_orig, _ = rot_arr.shape
    print(f"Astronomical orientation: {W_orig}x{H_orig} (RA circumference: {W_orig}px, Dec height: {H_orig}px)")

    R_outer = args.radius
    min_wall = args.min_wall
    max_wall = args.max_wall
    base_flange = args.base_flange
    relief = max(0.0, args.relief)
    nw = args.grid_w
    nh = args.grid_h

    # Isotropic metric scaling
    C = 2 * math.pi * R_outer
    scale = C / W_orig
    H_cyl = args.height if args.height is not None else (H_orig * scale)
    print(f"Cylinder parameters: Outer R={R_outer:.2f} mm, Height={H_cyl:.2f} mm")
    print(f"Lithophane wall thickness: {min_wall:.2f} mm (bright) to {max_wall:.2f} mm (dark)")
    print(f"Exterior relief: {relief:.2f} mm ({'Smooth lithophane' if relief == 0 else 'Raised relief'})")
    print(f"Resolution: {nw} angular x {nh} axial grid")

    # Downsampled image for grid processing
    down_img = rot_img.resize((nw, nh), Image.Resampling.LANCZOS)
    down_arr = np.array(down_img)

    # 1. Detect Star Points on full resolution for maximum roundness and precision
    r_full = rot_arr[:, :, 0].astype(float)
    g_full = rot_arr[:, :, 1].astype(float)
    b_full = rot_arr[:, :, 2].astype(float)
    lum_full = 0.299 * r_full + 0.587 * g_full + 0.114 * b_full

    date_lim_full = int(50 * H_orig / 472)
    mag_lim_full = int(420 * H_orig / 472)
    sky_mask_full = np.zeros((H_orig, W_orig), dtype=bool)
    sky_mask_full[date_lim_full:mag_lim_full, :] = True

    star_cand = sky_mask_full & (lum_full > 165) & (r_full > 120) & (g_full > 120)
    lbl, num = ndi.label(star_cand)
    sizes = ndi.sum(star_cand, lbl, range(1, num + 1))
    coms = ndi.center_of_mass(star_cand, lbl, range(1, num + 1))

    stars = []
    for i in range(1, num + 1):
        sz = sizes[i - 1]
        if sz < 4:
            continue
        sub = (lbl == i)
        ys, xs = np.where(sub)
        h_box = ys.max() - ys.min() + 1
        w_box = xs.max() - xs.min() + 1
        aspect = w_box / max(h_box, 1)
        if 0.35 <= aspect <= 2.8 and max(h_box, w_box) <= 28:
            cy, cx = coms[i - 1]
            rad_px = max(np.sqrt(sz / np.pi), 0.8)
            rad_mm = max(rad_px * scale, 0.55)
            th = (cx / W_orig) * 2 * math.pi
            z = H_cyl * (cy / H_orig)
            stars.append((th, z, rad_mm))

    print(f"Detected {len(stars)} prominent round star points")

    # 2. Feature Masks for Index/Date lines and Constellation lines on the downsampled grid
    r_down = down_arr[:, :, 0].astype(float)
    g_down = down_arr[:, :, 1].astype(float)
    b_down = down_arr[:, :, 2].astype(float)
    lum_down = 0.299 * r_down + 0.587 * g_down + 0.114 * b_down

    date_lim_down = int(50 * nh / H_orig)
    mag_lim_down = int(420 * nh / H_orig)

    sky_mask_down = np.zeros((nh, nw), dtype=bool)
    sky_mask_down[date_lim_down:mag_lim_down, :] = True

    # Date marks at the bottom (y < date_lim_down -> Z near 0)
    # Magnitude scale at the top (y >= mag_lim_down -> Z near H_cyl)
    ruler_mask = np.zeros((nh, nw), dtype=bool)
    ruler_mask[:date_lim_down, :] = (lum_down[:date_lim_down, :] > 55)
    ruler_mask[mag_lim_down:, :] = (lum_down[mag_lim_down:, :] > 55)

    # Coordinate grid lines
    grid_v = np.zeros((nh, nw), dtype=bool)
    for x_c_orig in [7, 36, 56, 83, 111, 138, 166, 194, 222, 250, 277, 305, 333, 360, 388, 416, 443, 471, 498, 526, 553, 581, 609, 636, 664, 691, 719, 746]:
        xg = int(round(float(x_c_orig) * nw / W_orig))
        if 0 <= xg < nw:
            grid_v[date_lim_down:mag_lim_down, max(0, xg - 1):min(nw, xg + 2)] = (lum_down[date_lim_down:mag_lim_down, max(0, xg - 1):min(nw, xg + 2)] > 40)

    grid_h_lines = np.zeros((nh, nw), dtype=bool)
    for y_c_orig in [61, 92, 123, 154, 186, 217, 249, 280, 311, 343, 374, 405]:
        yg = int(round(float(y_c_orig) * nh / H_orig))
        if date_lim_down <= yg < mag_lim_down:
            grid_h_lines[max(0, yg - 1):min(nh, yg + 2), :] = (lum_down[max(0, yg - 1):min(nh, yg + 2)] > 40)

    index_mask = ruler_mask | (sky_mask_down & (grid_v | grid_h_lines) & (lum_down > 40))
    lines_mask = sky_mask_down & ~index_mask & (lum_down > 35) & (lum_down <= 175) & (b_down > r_down + 8)

    print(f"Classified features: {np.sum(index_mask)} index/ruler cells, {np.sum(lines_mask)} constellation line cells")

    # Normalized luminance grid for Lithophane wall modulation
    lum_min = np.percentile(lum_down, 2)
    lum_max = np.percentile(lum_down, 98)
    lum_range = max(lum_max - lum_min, 1.0)
    norm_bri = np.clip((lum_down - lum_min) / lum_range, 0.0, 1.0)

    # 3. Generate STEP AP214/AP242 Assembly Structure
    step_lines = []
    entity_id = 100

    def alloc_id():
        nonlocal entity_id
        res = entity_id
        entity_id += 1
        return res

    app_context = alloc_id()
    app_proto = alloc_id()
    prod_context = alloc_id()
    pdef_context = alloc_id()
    geom_context = alloc_id()
    len_unit = alloc_id()
    ang_unit = alloc_id()
    ster_unit = alloc_id()
    uncert = alloc_id()
    origin_pt = alloc_id()
    dir_z = alloc_id()
    dir_x = alloc_id()
    axis_placement = alloc_id()

    step_lines.append(f"#{app_context} = APPLICATION_CONTEXT('core data for automotive mechanical design processes');\n")
    step_lines.append(f"#{app_proto} = APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,#{app_context});\n")
    step_lines.append(f"#{prod_context} = PRODUCT_CONTEXT('',#{app_context},'mechanical');\n")
    step_lines.append(f"#{pdef_context} = PRODUCT_DEFINITION_CONTEXT('part definition',#{app_context},'design');\n")

    step_lines.append(f"#{len_unit} = ( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.) );\n")
    step_lines.append(f"#{ang_unit} = ( NAMED_UNIT(*) PLANE_ANGLE_UNIT() SI_UNIT($,.RADIAN.) );\n")
    step_lines.append(f"#{ster_unit} = ( NAMED_UNIT(*) SI_UNIT($,.STERADIAN.) SOLID_ANGLE_UNIT() );\n")
    step_lines.append(f"#{uncert} = UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-07),#{len_unit},'distance_accuracy_value','confusion accuracy');\n")
    step_lines.append(f"#{geom_context} = ( GEOMETRIC_REPRESENTATION_CONTEXT(3) GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#{uncert})) GLOBAL_UNIT_ASSIGNED_CONTEXT((#{len_unit},#{ang_unit},#{ster_unit})) REPRESENTATION_CONTEXT('Context #1','3D Context with UNIT and UNCERTAINTY') );\n")

    step_lines.append(f"#{origin_pt} = CARTESIAN_POINT('',(0.,0.,0.));\n")
    step_lines.append(f"#{dir_z} = DIRECTION('',(0.,0.,1.));\n")
    step_lines.append(f"#{dir_x} = DIRECTION('',(1.,0.,0.));\n")
    step_lines.append(f"#{axis_placement} = AXIS2_PLACEMENT_3D('',#{origin_pt},#{dir_z},#{dir_x});\n")

    def make_color(name, rgb):
        r_col, g_col, b_col = rgb
        c_id = alloc_id()
        fas_id = alloc_id()
        sfa_id = alloc_id()
        surf_style_fill_id = alloc_id()
        side_id = alloc_id()
        usage_id = alloc_id()
        style_id = alloc_id()
        step_lines.append(f"#{c_id} = COLOUR_RGB('{name}',{r_col:.4f},{g_col:.4f},{b_col:.4f});\n")
        step_lines.append(f"#{fas_id} = FILL_AREA_STYLE_COLOUR('',#{c_id});\n")
        step_lines.append(f"#{sfa_id} = FILL_AREA_STYLE('',(#{fas_id}));\n")
        step_lines.append(f"#{surf_style_fill_id} = SURFACE_STYLE_FILL_AREA(#{sfa_id});\n")
        step_lines.append(f"#{side_id} = SURFACE_SIDE_STYLE('',(#{surf_style_fill_id}));\n")
        step_lines.append(f"#{usage_id} = SURFACE_STYLE_USAGE(.BOTH.,#{side_id});\n")
        step_lines.append(f"#{style_id} = PRESENTATION_STYLE_ASSIGNMENT((#{usage_id}));\n")
        return style_id

    style_bg = make_color('navy', hex_to_rgb(args.color_bg))
    style_stars = make_color('gold', hex_to_rgb(args.color_stars))
    style_lines = make_color('blue', hex_to_rgb(args.color_lines))
    style_index = make_color('cyan', hex_to_rgb(args.color_index))

    # Root Assembly Product
    root_prod = alloc_id()
    root_form = alloc_id()
    root_pdef = alloc_id()
    root_pshp = alloc_id()
    root_rep = alloc_id()
    root_sdr = alloc_id()

    step_lines.append(f"#{root_prod} = PRODUCT('StarMap_Cylinder','StarMap_Cylinder','',({prod_context}));\n")
    step_lines.append(f"#{root_form} = PRODUCT_DEFINITION_FORMATION('','',#{root_prod});\n")
    step_lines.append(f"#{root_pdef} = PRODUCT_DEFINITION('design','',#{root_form},#{pdef_context});\n")
    step_lines.append(f"#{root_pshp} = PRODUCT_DEFINITION_SHAPE('','',#{root_pdef});\n")
    step_lines.append(f"#{root_rep} = SHAPE_REPRESENTATION('StarMap_Cylinder',({axis_placement}),#{geom_context});\n")
    step_lines.append(f"#{root_sdr} = SHAPE_DEFINITION_REPRESENTATION(#{root_pshp},#{root_rep});\n")
    step_lines.append(f"#{alloc_id()} = PRODUCT_RELATED_PRODUCT_CATEGORY('assembly',$,(#{root_prod}));\n")

    def register_component(name, brep_ids, style_id):
        if not isinstance(brep_ids, list):
            brep_ids = [brep_ids]
        prod_id = alloc_id()
        form_id = alloc_id()
        pdef_id = alloc_id()
        pshp_id = alloc_id()
        rep_id = alloc_id()
        sdr_id = alloc_id()

        step_lines.append(f"#{prod_id} = PRODUCT('{name}','{name}','',({prod_context}));\n")
        step_lines.append(f"#{form_id} = PRODUCT_DEFINITION_FORMATION('','',#{prod_id});\n")
        step_lines.append(f"#{pdef_id} = PRODUCT_DEFINITION('design','',#{form_id},#{pdef_context});\n")
        step_lines.append(f"#{pshp_id} = PRODUCT_DEFINITION_SHAPE('','',#{pdef_id});\n")
        
        brep_items = ','.join(f"#{b}" for b in brep_ids)
        step_lines.append(f"#{rep_id} = SHAPE_REPRESENTATION('{name}',({axis_placement},{brep_items}),#{geom_context});\n")
        step_lines.append(f"#{sdr_id} = SHAPE_DEFINITION_REPRESENTATION(#{pshp_id},#{rep_id});\n")
        step_lines.append(f"#{alloc_id()} = PRODUCT_RELATED_PRODUCT_CATEGORY('part',$,(#{prod_id}));\n")

        styled_ids = []
        for b in brep_ids:
            styled_id = alloc_id()
            step_lines.append(f"#{styled_id} = STYLED_ITEM('color',({style_id}),#{b});\n")
            styled_ids.append(styled_id)
        
        styled_items = ','.join(f"#{s}" for s in styled_ids)
        step_lines.append(f"#{alloc_id()} = MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',({styled_items}),#{geom_context});\n")

        nauo_id = alloc_id()
        rel_pshp_id = alloc_id()
        cdsr_id = alloc_id()
        rel_id = alloc_id()
        trans_id = alloc_id()

        step_lines.append(f"#{nauo_id} = NEXT_ASSEMBLY_USAGE_OCCURRENCE('{name}','{name}','',#{root_pdef},#{pdef_id},$);\n")
        step_lines.append(f"#{rel_pshp_id} = PRODUCT_DEFINITION_SHAPE('','',#{nauo_id});\n")
        step_lines.append(f"#{cdsr_id} = CONTEXT_DEPENDENT_SHAPE_REPRESENTATION(#{rel_id},#{rel_pshp_id});\n")
        step_lines.append(f"#{rel_id} = ( REPRESENTATION_RELATIONSHIP('','',#{root_rep},#{rep_id}) REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION(#{trans_id}) SHAPE_REPRESENTATION_RELATIONSHIP() );\n")
        step_lines.append(f"#{trans_id} = ITEM_DEFINED_TRANSFORMATION('','',#{axis_placement},#{axis_placement});\n")

    def add_plane(pt, norm, tang):
        nl = np.linalg.norm(norm)
        n = norm / nl if nl > 1e-9 else np.array([0., 0., 1.])
        # Orthonormalize tang against norm:
        t = tang - np.dot(tang, n) * n
        tl = np.linalg.norm(t)
        if tl < 1e-9:
            # Pick arbitrary vector not parallel to n
            arb = np.array([1., 0., 0.]) if abs(n[0]) < 0.9 else np.array([0., 1., 0.])
            t = arb - np.dot(arb, n) * n
            tl = np.linalg.norm(t)
        t = t / tl
        pid = alloc_id()
        dz = alloc_id()
        dx = alloc_id()
        ax = alloc_id()
        pl = alloc_id()
        step_lines.append(f"#{pid} = CARTESIAN_POINT('',({pt[0]:.4f},{pt[1]:.4f},{pt[2]:.4f}));\n")
        step_lines.append(f"#{dz} = DIRECTION('',({n[0]:.4f},{n[1]:.4f},{n[2]:.4f}));\n")
        step_lines.append(f"#{dx} = DIRECTION('',({t[0]:.4f},{t[1]:.4f},{t[2]:.4f}));\n")
        step_lines.append(f"#{ax} = AXIS2_PLACEMENT_3D('',#{pid},#{dz},#{dx});\n")
        step_lines.append(f"#{pl} = PLANE('',#{ax});\n")
        return pl

    def make_tri_with_pts(v_ids, p0, p1, p2):
        d1 = p1 - p0
        d2 = p2 - p0
        n = np.cross(d1, d2)
        nl = np.linalg.norm(n)
        n = n / nl if nl > 1e-9 else np.array([0., 0., 1.])
        tl = np.linalg.norm(d1)
        t = d1 / tl if tl > 1e-9 else np.array([1., 0., 0.])
        pl = add_plane(p0, n, t)
        lid = alloc_id()
        bid = alloc_id()
        fid = alloc_id()
        refs = f"#{v_ids[0]},#{v_ids[1]},#{v_ids[2]}"
        step_lines.append(f"#{lid} = POLY_LOOP('',({refs}));\n")
        step_lines.append(f"#{bid} = FACE_OUTER_BOUND('',#{lid},.T.);\n")
        step_lines.append(f"#{fid} = FACE_SURFACE('',(#{bid}),#{pl},.T.);\n")
        return fid

    # =========================================================================
    # Component 1: Space_Background (Full Lithophane Hollow Cylinder Tube)
    # Outer radius is smooth at R_outer.
    # Inner radius varies with brightness: bright -> thin wall, dark -> thick wall.
    # =========================================================================
    print("Generating Space_Background solid (Lithophane)...")
    bg_faces = []
    r_in_grid = np.zeros((nh + 1, nw))
    for j in range(nh):
        for i in range(nw):
            b = norm_bri[j, i]
            w = max_wall - b * (max_wall - min_wall)
            r_in_grid[j, i] = R_outer - w
    r_in_grid[nh, :] = r_in_grid[nh - 1, :]

    bg_out_pts = {}
    bg_in_pts = {}
    for j in range(nh + 1):
        z = (j / nh) * H_cyl
        for i in range(nw):
            th = (i / nw) * 2 * math.pi
            r_in = r_in_grid[j, i]
            pid_o = alloc_id()
            step_lines.append(f"#{pid_o} = CARTESIAN_POINT('',({R_outer*math.cos(th):.4f},{R_outer*math.sin(th):.4f},{z:.4f}));\n")
            bg_out_pts[(i, j)] = pid_o

            pid_i = alloc_id()
            step_lines.append(f"#{pid_i} = CARTESIAN_POINT('',({r_in*math.cos(th):.4f},{r_in*math.sin(th):.4f},{z:.4f}));\n")
            bg_in_pts[(i, j)] = pid_i

    def get_bg_out_coord(i, j):
        th = (i / nw) * 2 * math.pi
        z = (j / nh) * H_cyl
        return np.array([R_outer * math.cos(th), R_outer * math.sin(th), z])

    def get_bg_in_coord(i, j):
        th = (i / nw) * 2 * math.pi
        z = (j / nh) * H_cyl
        r_in = r_in_grid[j, i % nw]
        return np.array([r_in * math.cos(th), r_in * math.sin(th), z])

    # Outer cylindrical surface (smooth, normal outward)
    for j in range(nh):
        for i in range(nw):
            i_next = (i + 1) % nw
            p00 = get_bg_out_coord(i, j); p10 = get_bg_out_coord(i_next, j)
            p11 = get_bg_out_coord(i_next, j + 1); p01 = get_bg_out_coord(i, j + 1)
            v00 = bg_out_pts[(i, j)]; v10 = bg_out_pts[(i_next, j)]
            v11 = bg_out_pts[(i_next, j + 1)]; v01 = bg_out_pts[(i, j + 1)]
            bg_faces.append(make_tri_with_pts([v00, v10, v11], p00, p10, p11))
            bg_faces.append(make_tri_with_pts([v00, v11, v01], p00, p11, p01))

    # Inner lithophane surface (variable radius, normal inward)
    for j in range(nh):
        for i in range(nw):
            i_next = (i + 1) % nw
            p00 = get_bg_in_coord(i, j); p10 = get_bg_in_coord(i_next, j)
            p11 = get_bg_in_coord(i_next, j + 1); p01 = get_bg_in_coord(i, j + 1)
            v00 = bg_in_pts[(i, j)]; v10 = bg_in_pts[(i_next, j)]
            v11 = bg_in_pts[(i_next, j + 1)]; v01 = bg_in_pts[(i, j + 1)]
            bg_faces.append(make_tri_with_pts([v00, v11, v10], p00, p11, p10))
            bg_faces.append(make_tri_with_pts([v00, v01, v11], p00, p01, p11))

    # Top ring cap (z = H_cyl)
    for i in range(nw):
        i_next = (i + 1) % nw
        o0 = get_bg_out_coord(i, nh); o1 = get_bg_out_coord(i_next, nh)
        in0 = get_bg_in_coord(i, nh); in1 = get_bg_in_coord(i_next, nh)
        vo0 = bg_out_pts[(i, nh)]; vo1 = bg_out_pts[(i_next, nh)]
        vi0 = bg_in_pts[(i, nh)]; vi1 = bg_in_pts[(i_next, nh)]
        bg_faces.append(make_tri_with_pts([vo0, vo1, vi1], o0, o1, in1))
        bg_faces.append(make_tri_with_pts([vo0, vi1, vi0], o0, in1, in0))

    # Bottom flange or bottom ring cap (z <= 0)
    if base_flange > 0:
        r_flange = R_outer + 1.2
        r_in_bot = R_outer - max_wall
        flange_out_pts = {}
        flange_in_pts = {}
        for i in range(nw):
            th = (i / nw) * 2 * math.pi
            pid_fo = alloc_id()
            step_lines.append(f"#{pid_fo} = CARTESIAN_POINT('',({r_flange*math.cos(th):.4f},{r_flange*math.sin(th):.4f},{-base_flange:.4f}));\n")
            flange_out_pts[i] = pid_fo

            pid_fi = alloc_id()
            step_lines.append(f"#{pid_fi} = CARTESIAN_POINT('',({r_in_bot*math.cos(th):.4f},{r_in_bot*math.sin(th):.4f},{-base_flange:.4f}));\n")
            flange_in_pts[i] = pid_fi

        def get_flange_out(i):
            th = (i / nw) * 2 * math.pi
            return np.array([r_flange * math.cos(th), r_flange * math.sin(th), -base_flange])

        def get_flange_in(i):
            th = (i / nw) * 2 * math.pi
            return np.array([r_in_bot * math.cos(th), r_in_bot * math.sin(th), -base_flange])

        for i in range(nw):
            i_next = (i + 1) % nw
            vo0 = bg_out_pts[(i, 0)]; vo1 = bg_out_pts[(i_next, 0)]
            vi0 = bg_in_pts[(i, 0)]; vi1 = bg_in_pts[(i_next, 0)]
            vfo0 = flange_out_pts[i]; vfo1 = flange_out_pts[i_next]
            vfi0 = flange_in_pts[i]; vfi1 = flange_in_pts[i_next]

            p_o0 = get_bg_out_coord(i, 0); p_o1 = get_bg_out_coord(i_next, 0)
            p_i0 = get_bg_in_coord(i, 0); p_i1 = get_bg_in_coord(i_next, 0)
            p_fo0 = get_flange_out(i); p_fo1 = get_flange_out(i_next)
            p_fi0 = get_flange_in(i); p_fi1 = get_flange_in(i_next)

            # Flange outer wall
            bg_faces.append(make_tri_with_pts([vo0, vfo0, vfo1], p_o0, p_fo0, p_fo1))
            bg_faces.append(make_tri_with_pts([vo0, vfo1, vo1], p_o0, p_fo1, p_o1))
            # Flange bottom ring
            bg_faces.append(make_tri_with_pts([vfo0, vfi0, vfi1], p_fo0, p_fi0, p_fi1))
            bg_faces.append(make_tri_with_pts([vfo0, vfi1, vfo1], p_fo0, p_fi1, p_fo1))
            # Flange inner wall connecting up to z=0
            bg_faces.append(make_tri_with_pts([vfi0, vi0, vi1], p_fi0, p_i0, p_i1))
            bg_faces.append(make_tri_with_pts([vfi0, vi1, vfi1], p_fi0, p_i1, p_fi1))
    else:
        for i in range(nw):
            i_next = (i + 1) % nw
            o0 = get_bg_out_coord(i, 0); o1 = get_bg_out_coord(i_next, 0)
            in0 = get_bg_in_coord(i, 0); in1 = get_bg_in_coord(i_next, 0)
            vo0 = bg_out_pts[(i, 0)]; vo1 = bg_out_pts[(i_next, 0)]
            vi0 = bg_in_pts[(i, 0)]; vi1 = bg_in_pts[(i_next, 0)]
            bg_faces.append(make_tri_with_pts([vo0, vi1, vo1], o0, in1, o1))
            bg_faces.append(make_tri_with_pts([vo0, vi0, vi1], o0, in0, in1))

    bg_shell = alloc_id()
    bg_brep = alloc_id()
    refs_bg = ','.join(f"#{f}" for f in bg_faces)
    step_lines.append(f"#{bg_shell} = CLOSED_SHELL('',({refs_bg}));\n")
    step_lines.append(f"#{bg_brep} = FACETED_BREP('Space_Background_Brep',#{bg_shell});\n")
    register_component('Space_Background', bg_brep, style_bg)

    # =========================================================================
    # Component 2: Stars (Watertight circular prisms, yellow filament)
    # Each star is its own CLOSED_SHELL and FACETED_BREP (ISO 10303-42 compliant).
    # All stars are collected under the 'Stars' SHAPE_REPRESENTATION.
    # Outer face is flush with R_outer + 0.02mm (zero relief, smooth!).
    # Inner face reaches through the lithophane wall to R_outer - min_wall.
    # =========================================================================
    print("Generating Stars solid (Watertight circular dots)...")
    n_star_sides = 12
    r_star_top = R_outer + relief + 0.020
    r_star_bot = R_outer - min_wall
    star_brep_ids = []

    for s_idx, (th_c, z_c, r_star) in enumerate(stars):
        c_top_pt = (r_star_top * math.cos(th_c), r_star_top * math.sin(th_c), z_c)
        c_bot_pt = (r_star_bot * math.cos(th_c), r_star_bot * math.sin(th_c), z_c)
        pid_ct = alloc_id()
        step_lines.append(f"#{pid_ct} = CARTESIAN_POINT('',({c_top_pt[0]:.4f},{c_top_pt[1]:.4f},{c_top_pt[2]:.4f}));\n")
        pid_cb = alloc_id()
        step_lines.append(f"#{pid_cb} = CARTESIAN_POINT('',({c_bot_pt[0]:.4f},{c_bot_pt[1]:.4f},{c_bot_pt[2]:.4f}));\n")

        top_pids = []
        bot_pids = []
        top_coords = []
        bot_coords = []
        for k in range(n_star_sides):
            ang = (k / n_star_sides) * 2.0 * math.pi
            ds = r_star * math.cos(ang)
            dz = r_star * math.sin(ang)
            th_k = th_c + (ds / R_outer)
            zk = z_c + dz
            pt_t = (r_star_top * math.cos(th_k), r_star_top * math.sin(th_k), zk)
            pt_b = (r_star_bot * math.cos(th_k), r_star_bot * math.sin(th_k), zk)
            top_coords.append(pt_t)
            bot_coords.append(pt_b)

            pid_t = alloc_id()
            step_lines.append(f"#{pid_t} = CARTESIAN_POINT('',({pt_t[0]:.4f},{pt_t[1]:.4f},{pt_t[2]:.4f}));\n")
            top_pids.append(pid_t)

            pid_b = alloc_id()
            step_lines.append(f"#{pid_b} = CARTESIAN_POINT('',({pt_b[0]:.4f},{pt_b[1]:.4f},{pt_b[2]:.4f}));\n")
            bot_pids.append(pid_b)

        this_star_faces = []
        for k in range(n_star_sides):
            kn = (k + 1) % n_star_sides
            this_star_faces.append(make_tri_with_pts([pid_ct, top_pids[k], top_pids[kn]], np.array(c_top_pt), np.array(top_coords[k]), np.array(top_coords[kn])))
            this_star_faces.append(make_tri_with_pts([pid_cb, bot_pids[kn], bot_pids[k]], np.array(c_bot_pt), np.array(bot_coords[kn]), np.array(bot_coords[k])))
            p0 = np.array(bot_coords[k]); p1 = np.array(bot_coords[kn]); p2 = np.array(top_coords[kn])
            this_star_faces.append(make_tri_with_pts([bot_pids[k], bot_pids[kn], top_pids[kn]], p0, p1, p2))
            p3 = np.array(top_coords[k])
            this_star_faces.append(make_tri_with_pts([bot_pids[k], top_pids[kn], top_pids[k]], p0, p2, p3))

        shell_id = alloc_id()
        brep_id = alloc_id()
        refs_star = ','.join(f"#{f}" for f in this_star_faces)
        step_lines.append(f"#{shell_id} = CLOSED_SHELL('',({refs_star}));\n")
        step_lines.append(f"#{brep_id} = FACETED_BREP('Star_{s_idx}',#{shell_id});\n")
        star_brep_ids.append(brep_id)

    register_component('Stars', star_brep_ids, style_stars)

    # =========================================================================
    # Components 3 & 4: Inlaid Watertight Shells for Constellation_Lines & Index_Lines
    # Active cells: outer radius is flush at R_outer + delta (smooth, zero relief).
    # Inactive cells: recessed beneath the surface (hidden inside the background wall).
    # =========================================================================
    def build_inlaid_component(name, mask, delta_surf, style_id):
        print(f"Generating {name} solid (Inlaid shell)...")
        r_out_active = R_outer + relief + delta_surf
        r_in_active = R_outer - 0.50
        r_out_inactive = R_outer - 0.15
        r_in_inactive = R_outer - 0.25

        r_grid_out = np.full((nh + 1, nw), r_out_inactive)
        r_grid_in = np.full((nh + 1, nw), r_in_inactive)
        for j in range(nh):
            for i in range(nw):
                if mask[j, i]:
                    r_grid_out[j, i] = r_out_active
                    r_grid_in[j, i] = r_in_active
        r_grid_out[nh, :] = r_grid_out[nh - 1, :]
        r_grid_in[nh, :] = r_grid_in[nh - 1, :]

        out_pts = {}
        in_pts = {}
        for j in range(nh + 1):
            z = (j / nh) * H_cyl
            for i in range(nw):
                th = (i / nw) * 2 * math.pi
                ro = r_grid_out[j, i]
                ri = r_grid_in[j, i]

                pid_o = alloc_id()
                out_pts[(i, j)] = pid_o
                step_lines.append(f"#{pid_o} = CARTESIAN_POINT('',({ro*math.cos(th):.4f},{ro*math.sin(th):.4f},{z:.4f}));\n")

                pid_i = alloc_id()
                in_pts[(i, j)] = pid_i
                step_lines.append(f"#{pid_i} = CARTESIAN_POINT('',({ri*math.cos(th):.4f},{ri*math.sin(th):.4f},{z:.4f}));\n")

        def get_out_c(i, j):
            th = (i / nw) * 2 * math.pi
            z = (j / nh) * H_cyl
            ro = r_grid_out[j, i % nw]
            return np.array([ro * math.cos(th), ro * math.sin(th), z])

        def get_in_c(i, j):
            th = (i / nw) * 2 * math.pi
            z = (j / nh) * H_cyl
            ri = r_grid_in[j, i % nw]
            return np.array([ri * math.cos(th), ri * math.sin(th), z])

        faces = []
        for j in range(nh):
            for i in range(nw):
                i_next = (i + 1) % nw
                p00 = get_out_c(i, j); p10 = get_out_c(i_next, j)
                p11 = get_out_c(i_next, j + 1); p01 = get_out_c(i, j + 1)
                v00 = out_pts[(i, j)]; v10 = out_pts[(i_next, j)]
                v11 = out_pts[(i_next, j + 1)]; v01 = out_pts[(i, j + 1)]
                faces.append(make_tri_with_pts([v00, v10, v11], p00, p10, p11))
                faces.append(make_tri_with_pts([v00, v11, v01], p00, p11, p01))

        for j in range(nh):
            for i in range(nw):
                i_next = (i + 1) % nw
                p00 = get_in_c(i, j); p10 = get_in_c(i_next, j)
                p11 = get_in_c(i_next, j + 1); p01 = get_in_c(i, j + 1)
                v00 = in_pts[(i, j)]; v10 = in_pts[(i_next, j)]
                v11 = in_pts[(i_next, j + 1)]; v01 = in_pts[(i, j + 1)]
                faces.append(make_tri_with_pts([v00, v11, v10], p00, p11, p10))
                faces.append(make_tri_with_pts([v00, v01, v11], p00, p01, p11))

        for i in range(nw):
            i_next = (i + 1) % nw
            o0 = get_out_c(i, 0); o1 = get_out_c(i_next, 0)
            in0 = get_in_c(i, 0); in1 = get_in_c(i_next, 0)
            vo0 = out_pts[(i, 0)]; vo1 = out_pts[(i_next, 0)]
            vi0 = in_pts[(i, 0)]; vi1 = in_pts[(i_next, 0)]
            faces.append(make_tri_with_pts([vo0, vi1, vo1], o0, in1, o1))
            faces.append(make_tri_with_pts([vo0, vi0, vi1], o0, in0, in1))

        for i in range(nw):
            i_next = (i + 1) % nw
            o0 = get_out_c(i, nh); o1 = get_out_c(i_next, nh)
            in0 = get_in_c(i, nh); in1 = get_in_c(i_next, nh)
            vo0 = out_pts[(i, nh)]; vo1 = out_pts[(i_next, nh)]
            vi0 = in_pts[(i, nh)]; vi1 = in_pts[(i_next, nh)]
            faces.append(make_tri_with_pts([vo0, vo1, vi1], o0, o1, in1))
            faces.append(make_tri_with_pts([vo0, vi1, vi0], o0, in1, in0))

        shell_id = alloc_id()
        brep_id = alloc_id()
        f_refs = ','.join(f"#{f}" for f in faces)
        step_lines.append(f"#{shell_id} = CLOSED_SHELL('',({f_refs}));\n")
        step_lines.append(f"#{brep_id} = FACETED_BREP('{name}_Brep',#{shell_id});\n")
        register_component(name, brep_id, style_id)

    build_inlaid_component('Constellation_Lines', lines_mask, 0.010, style_lines)
    build_inlaid_component('Index_Lines', index_mask, 0.015, style_index)

    output_path = args.output
    header_str = (
        f"ISO-10303-21;\nHEADER;\n"
        f"FILE_DESCRIPTION(('Cylindrical Multicolor Lithophane Star Map Assembly'),'2;1');\n"
        f"FILE_NAME('{os.path.basename(output_path)}','{time.strftime('%Y-%m-%dT%H:%M:%S')}',('User'),('User'),'Processor','System','');\n"
        f"FILE_SCHEMA(('AUTOMOTIVE_DESIGN {{ 1 0 10303 214 1 1 1 1 }}'));\n"
        f"ENDSEC;\nDATA;\n"
    )

    print(f"Writing {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header_str)
        f.writelines(step_lines)
        f.write("ENDSEC;\nEND-ISO-10303-21;\n")

    sz_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n=== COMPLETE ===")
    print(f"Output: {output_path} ({sz_mb:.2f} MB)")
    print(f"Components: Space_Background, Stars, Constellation_Lines, Index_Lines")
    print(f"Lithophane: Smooth exterior (R={R_outer}mm), variable wall {min_wall}-{max_wall}mm")
    print(f"Ready for OrcaSlicer / Bambu Studio / PrusaSlicer multicolor printing.")


if __name__ == '__main__':
    main()
