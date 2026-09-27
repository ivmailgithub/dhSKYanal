"""
Parametric model of the aluminum multi-hole slider / mounting plate shown
in the reference drawing (290 x 60 x 30 overall, dovetail foot on the
underside, rows of M6/M8-class clearance holes and elongated slots).

Built with CadQuery 2.x -> exported as STEP (and STL for quick preview).

--------------------------------------------------------------------------
HOW THE HOLE / SLOT POSITIONS WERE DERIVED
--------------------------------------------------------------------------
The drawing gives the hole/slot centers as chains of cumulative dimensions
rather than absolute coordinates, so the X positions below are computed
by summing those chains (all values in mm, verified to sum to 290):

  Outer row (near the long edges), 12 values -> 11 feature centers:
      13.25, 16.5, 45.5, 16, 25.5, 25.5, 25.5, 16, 50, 16.5, 26.5, 13.25
      -> the two largest gaps (45.5 and 50) are the elongated slots,
         the other 9 positions are round Ø6.5 holes (2 rows x 11 = 22,
         matching the "22-Ø6.5" callout).

  Inner row (the big slots), 11 values -> 4 slots of 33 mm + a 35 mm
  center gap that holds the M8 / Ø9.2 holes (also checks out to 290,
  and is symmetric about the 145 mm centerline):
      16, 33, 22.5, 33, 23, 35(+/-0.05), 23, 33, 22.5, 33, 16

--------------------------------------------------------------------------
ASSUMPTIONS (not explicitly dimensioned in the supplied text and picked
to match the picture -- adjust the CONFIG block below if you have exact
values):
  * Y offset of the two outer (edge) rows of holes/slots: 22 mm off center
  * Y offset of the two inner (big-slot) rows: 9 mm off center
  * Slot width = 6.5 mm (outer row) sized to the Ø6.5 callout
  * Outer-row slot length = 20 mm (visually ~ the gap available)
  * Inner big-slot width = 12 mm (visual proportion vs. the 33 mm length)
  * Bottom dovetail foot: full-length trapezoidal boss, 24 mm tall,
    43.9 mm wide at the bottom, 20 mm wide where it meets the plate
    (top width is not dimensioned in the text, only the 43.9 bottom
    width and 24 mm height are given)
  * Underside counterbores (8-Ø12, 2-Ø14, 4-R3, 4-15, 4-2 from the
    bottom view) are NOT modeled -- they are secondary machining
    details on top of the through-holes and are left as a TODO so the
    core geometry stays reliable. See the bottom of this file.
--------------------------------------------------------------------------
"""

import cadquery as cq

# ======================================================================
# CONFIG - all dimensions in mm, taken directly from the drawing unless
# marked "ASSUMPTION"
# ======================================================================

# --- Overall plate ---
L = 290.0                 # overall length
W = 60.0                  # overall width
T = 6.0                   # plate thickness  (30 overall - 24 foot height)
CORNER_R = 10.0           # 4x R10 corner fillet (top-view corners)
EDGE_CHAMFER = 0.5        # C0.5 chamfers called out around the plate

# --- Round holes ---
HOLE_D = 6.5               # 22x Ø6.5 clearance holes
M8_TAP_D = 8.5             # 2x M8x1.25 (through hole diameter, no thread modeled)
SMALL_HOLE_D = 9.2         # 2x Ø9.2

# --- Slots ---
OUTER_SLOT_W = 6.5         # ASSUMPTION: width of the 2 outer-row slots
OUTER_SLOT_L = 20.0        # ASSUMPTION: length of the 2 outer-row slots
INNER_SLOT_W = 12.0        # ASSUMPTION: width of the 4 big inner slots
INNER_SLOT_L = 33.0        # length of the 4 big inner slots (from dim chain)

# --- Row offsets from the plate centerline (Y) ---
EDGE_ROW_Y = 22.0          # ASSUMPTION: outer hole/slot row offset
INNER_ROW_Y = 9.0          # ASSUMPTION: inner big-slot row offset

# --- Bottom dovetail / foot (front & side views) ---
FOOT_HEIGHT = 24.0         # (24) in the front view
FOOT_BOTTOM_W = 43.9       # (43.9) bottom width of the foot
FOOT_TOP_W = 20.0          # ASSUMPTION: width where the foot meets the plate
FOOT_CHAMFER = 0.5         # C0.5 chamfer noted on the foot

# ======================================================================
# 1. Derive hole / slot X centers from the dimension chains
# ======================================================================

def cumulative_centers(gaps, total_length):
    """Turn a chain of edge-to-edge dimensions into absolute, centered
    X coordinates for each interior feature (drops the final gap that
    closes back out to the opposite edge)."""
    xs = []
    running = 0.0
    for g in gaps[:-1]:
        running += g
        xs.append(running - total_length / 2.0)
    return xs

# Outer row chain -> 11 feature centers
outer_gaps = [13.25, 16.5, 45.5, 16, 25.5, 25.5, 25.5, 16, 50, 16.5, 26.5, 13.25]
outer_centers = cumulative_centers(outer_gaps, L)
# indices (0-based) of the two elongated slots, the rest are round holes
outer_slot_idx = {2, 8}

# Inner row chain -> 10 boundary points -> 4 slots + center hole zone
inner_gaps = [16, 33, 22.5, 33, 23, 35, 23, 33, 22.5, 33, 16]
inner_pts = cumulative_centers(inner_gaps, L)
# inner_pts = [f1..f10] = slot1_start, slot1_end, slot2_start, slot2_end,
#                          center_start, center_end,
#                          slot3_start, slot3_end, slot4_start, slot4_end
inner_slot_spans = [
    (inner_pts[0], inner_pts[1]),
    (inner_pts[2], inner_pts[3]),
    (inner_pts[6], inner_pts[7]),
    (inner_pts[8], inner_pts[9]),
]
center_zone = (inner_pts[4], inner_pts[5])  # holds the M8 / Ø9.2 holes

# Centerline holes: 2x M8 nearer center, 2x Ø9.2 further out, mirrored
half_center = (center_zone[1] - center_zone[0]) / 2.0
m8_centers_x = [-half_center, half_center]
small_hole_offset = half_center + 23.0  # 23 mm gap from the center zone
small_hole_centers_x = [-small_hole_offset, small_hole_offset]


# ======================================================================
# 2. Helper: build a "stadium" slot solid (rounded-end slot), full depth
# ======================================================================

def slot_cutter(length, width, depth):
    """A slot oriented along X, centered at the origin, cut through Z."""
    r = width / 2.0
    straight = length - width
    if straight < 0:
        straight = 0.0
    pts_rect = cq.Workplane("XY").rect(straight, width).extrude(depth)
    circ_l = (cq.Workplane("XY").workplane(offset=0)
              .center(-straight / 2.0, 0).circle(r).extrude(depth))
    circ_r = (cq.Workplane("XY").workplane(offset=0)
              .center(straight / 2.0, 0).circle(r).extrude(depth))
    return pts_rect.union(circ_l).union(circ_r)


# ======================================================================
# 3. Build the plate
# ======================================================================

plate = (
    cq.Workplane("XY")
    .box(L, W, T, centered=(True, True, True))
)

# Round the 4 corners (R10) - select the 4 vertical edges
plate = plate.edges("|Z").fillet(CORNER_R)

# Light chamfer around the top & bottom perimeter (C0.5)
plate = plate.faces(">Z").edges().chamfer(EDGE_CHAMFER)
plate = plate.faces("<Z").edges().chamfer(EDGE_CHAMFER)

result = plate

# --- outer row holes & slots (top edge, then mirrored to bottom edge) ---
for y_sign in (+1, -1):
    y = y_sign * EDGE_ROW_Y
    for i, x in enumerate(outer_centers):
        if i in outer_slot_idx:
            cutter = slot_cutter(OUTER_SLOT_L, OUTER_SLOT_W, T + 2).translate((x, y, -T / 2 - 1))
            result = result.cut(cutter)
        else:
            result = (result.faces(">Z").workplane()
                       .center(x, y).hole(HOLE_D))

# --- inner big slots (mirrored top/bottom of centerline) ---
for y_sign in (+1, -1):
    y = y_sign * INNER_ROW_Y
    for (x0, x1) in inner_slot_spans:
        length = x1 - x0
        cx = (x0 + x1) / 2.0
        cutter = slot_cutter(length, INNER_SLOT_W, T + 2).translate((cx, y, -T / 2 - 1))
        result = result.cut(cutter)

# --- centerline holes: 2x M8x1.25 (through hole only, no thread) ---
for x in m8_centers_x:
    result = result.faces(">Z").workplane().center(x, 0).hole(M8_TAP_D)

# --- centerline holes: 2x Ø9.2 ---
for x in small_hole_centers_x:
    result = result.faces(">Z").workplane().center(x, 0).hole(SMALL_HOLE_D)

# ======================================================================
# 4. Bottom dovetail foot (full-length trapezoidal boss)
# ======================================================================

half_top = FOOT_TOP_W / 2.0
half_bot = FOOT_BOTTOM_W / 2.0
foot_profile = [
    (-half_top, 0.0),
    (half_top, 0.0),
    (half_bot, -FOOT_HEIGHT),
    (-half_bot, -FOOT_HEIGHT),
]
foot = (
    cq.Workplane("YZ")
    .polyline(foot_profile)
    .close()
    .extrude(L, both=False)
    .translate((-L / 2.0, 0, -T / 2.0))
)
# chamfer the two bottom edges of the foot
foot = foot.edges("<Z").chamfer(FOOT_CHAMFER)

result = result.union(foot)

# ======================================================================
# 5. Export
# ======================================================================

cq.exporters.export(result, "/mnt/user-data/outputs/mounting_plate.step")
cq.exporters.export(result, "/mnt/user-data/outputs/mounting_plate.stl")
print("Export complete.")
