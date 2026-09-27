// ============================================================================
// Multi-hole slider / mounting plate — OpenSCAD version
// 290 x 60 x 30 overall, dovetail foot on the underside, rows of
// clearance holes and elongated slots.
//
// Same geometry as the CadQuery script (build_plate.py), reimplemented here
// because plain numeric parameters + $fn are much faster to hand-tweak than
// re-running a Python/OCCT script. Open this in OpenSCAD, use Window >
// Customizer to get sliders/fields for every parameter below.
//
// Units: mm.
//
// ----------------------------------------------------------------------
// HOW THE HOLE / SLOT POSITIONS WERE DERIVED (from the dimensioned drawing)
// ----------------------------------------------------------------------
// Outer row (near the long edges), 12 values -> 11 feature centers:
//     13.25, 16.5, 45.5, 16, 25.5, 25.5, 25.5, 16, 50, 16.5, 26.5, 13.25
//     -> the two largest gaps (45.5 and 50) are the elongated slots,
//        the other 9 positions are round Ø6.5 holes (2 rows x 11 = 22,
//        matching the "22-Ø6.5" callout).
//
// Inner row (the big slots), 11 values -> 4 slots of 33 mm + a 35 mm
// center gap that holds the M8 / Ø9.2 holes (symmetric about the
// 145 mm centerline):
//     16, 33, 22.5, 33, 23, 35(+/-0.05), 23, 33, 22.5, 33, 16
//
// ----------------------------------------------------------------------
// ASSUMPTIONS (not explicitly dimensioned in the source drawing — these
// are the first things to change if you have exact reference values):
//   * Y offset of the outer hole/slot rows:   EDGE_ROW_Y = 22
//   * Y offset of the inner big-slot rows:    INNER_ROW_Y = 9
//   * Outer slot length:                      OUTER_SLOT_L = 20
//   * Inner slot width:                       INNER_SLOT_W = 12
//   * Dovetail foot top width (plate side):   FOOT_TOP_W = 20
//   * Underside counterbores (8-Ø12, 2-Ø14, 4-R3, 4-15, 4-2 from the
//     bottom view) are NOT modeled here — see TODO at the bottom.
// ============================================================================

/* [Overall plate] */
L = 290;              // overall length
W = 60;               // overall width
T = 6;                // plate thickness (30 overall - 24 foot height)
CORNER_R = 10;         // 4x R10 corner fillet
EDGE_CHAMFER = 0.5;    // C0.5 edge chamfer (top & bottom perimeter)

/* [Round holes] */
HOLE_D = 6.5;          // 22x Ø6.5 clearance holes
M8_TAP_D = 8.5;        // 2x M8x1.25 (through hole, no thread modeled)
SMALL_HOLE_D = 9.2;    // 2x Ø9.2

/* [Slots] */
OUTER_SLOT_W = 6.5;    // width of the 2 outer-row slots (per side)
OUTER_SLOT_L = 20;     // ASSUMPTION: length of the outer-row slots
INNER_SLOT_W = 12;     // ASSUMPTION: width of the 4 big inner slots
INNER_SLOT_L = 33;     // length of the big inner slots (from dim chain)

/* [Row offsets from centerline] */
EDGE_ROW_Y = 22;       // ASSUMPTION: outer hole/slot row offset
INNER_ROW_Y = 9;       // ASSUMPTION: inner big-slot row offset

/* [Dovetail foot] */
FOOT_HEIGHT = 24;      // (24) in the front view
FOOT_BOTTOM_W = 43.9;  // (43.9) bottom width of the foot
FOOT_TOP_W = 20;       // ASSUMPTION: width where foot meets the plate
FOOT_CHAMFER = 0.5;    // C0.5 chamfer on the foot's bottom edges

/* [Rendering] */
$fn = 48;              // circle smoothness

// ============================================================================
// Derived hole / slot X centers (computed from the drawing's dimension
// chains — do not normally need to edit below this line)
// ============================================================================

// Outer row chain -> 11 feature centers (cumulative sum, centered on 0)
outer_gaps = [13.25, 16.5, 45.5, 16, 25.5, 25.5, 25.5, 16, 50, 16.5, 26.5, 13.25];
outer_slot_idx = [2, 8];   // 0-based indices that are slots, rest are round holes

// Inner row chain -> 10 boundary points -> 4 slots + center hole zone
inner_gaps = [16, 33, 22.5, 33, 23, 35, 23, 33, 22.5, 33, 16];

// cumulative_centers(): running sum of all but the last gap, shifted to
// be centered on the part (returns a vector same length as gaps minus 1)
function cumsum_centered(gaps, total, n, i=0, acc=0, out=[]) =
    (i >= n) ? out :
    let (acc2 = acc + gaps[i])
    cumsum_centered(gaps, total, n, i+1, acc2, concat(out, [acc2 - total/2]));

outer_centers = cumsum_centered(outer_gaps, L, len(outer_gaps)-1);
inner_pts     = cumsum_centered(inner_gaps, L, len(inner_gaps)-1);

// inner_pts = [f1..f10] = slot1_start, slot1_end, slot2_start, slot2_end,
//                          center_start, center_end,
//                          slot3_start, slot3_end, slot4_start, slot4_end
inner_slot_spans = [
    [inner_pts[0], inner_pts[1]],
    [inner_pts[2], inner_pts[3]],
    [inner_pts[6], inner_pts[7]],
    [inner_pts[8], inner_pts[9]],
];
center_zone = [inner_pts[4], inner_pts[5]];

half_center = (center_zone[1] - center_zone[0]) / 2;
m8_centers_x = [-half_center, half_center];
small_hole_offset = half_center + 23;
small_hole_centers_x = [-small_hole_offset, small_hole_offset];

// ============================================================================
// Helper modules
// ============================================================================

// Rounded-rectangle (2D) used for the corner-filleted plate outline
module rounded_rect2d(l, w, r) {
    hull() {
        for (xs = [-1, 1], ys = [-1, 1])
            translate([xs*(l/2 - r), ys*(w/2 - r)])
                circle(r=r);
    }
}

// A "stadium" slot, extruded through Z, centered at the origin, oriented
// along X
module slot(length, width, depth) {
    straight = max(length - width, 0);
    translate([0, 0, -depth/2])
        linear_extrude(height=depth)
            hull() {
                translate([-straight/2, 0]) circle(d=width);
                translate([ straight/2, 0]) circle(d=width);
            }
}

// Round hole, extruded through Z
module round_hole(dia, depth) {
    translate([0, 0, -depth/2])
        linear_extrude(height=depth)
            circle(d=dia);
}

// ============================================================================
// Main plate body (with corner fillets + top/bottom chamfer)
// ============================================================================

module plate_blank() {
    // chamfer via minkowski-free approach: extrude the rounded rect,
    // then chamfer top/bottom by intersecting with a slightly-shrunk
    // offset shape near each face using a simple two-cylinder-edge trick.
    // For simplicity & reliability we approximate the C0.5 chamfer with a
    // small linear bevel using hull() between a full-size and a slightly
    // inset rounded rectangle at each face.
    bevel = EDGE_CHAMFER;
    hull() {
        translate([0, 0, -T/2 + bevel])
            linear_extrude(height=T - 2*bevel)
                rounded_rect2d(L, W, CORNER_R);
        translate([0, 0, -T/2])
            linear_extrude(height=0.001)
                rounded_rect2d(L - 2*bevel, W - 2*bevel, max(CORNER_R - bevel, 0.1));
        translate([0, 0, T/2 - 0.001])
            linear_extrude(height=0.001)
                rounded_rect2d(L - 2*bevel, W - 2*bevel, max(CORNER_R - bevel, 0.1));
    }
}

// ============================================================================
// Dovetail foot (full-length trapezoidal boss on the underside)
// ============================================================================

module dovetail_foot() {
    profile = [
        [-FOOT_TOP_W/2, 0],
        [ FOOT_TOP_W/2, 0],
        [ FOOT_BOTTOM_W/2, -FOOT_HEIGHT + FOOT_CHAMFER],
        [ FOOT_BOTTOM_W/2 - FOOT_CHAMFER, -FOOT_HEIGHT],
        [-FOOT_BOTTOM_W/2 + FOOT_CHAMFER, -FOOT_HEIGHT],
        [-FOOT_BOTTOM_W/2, -FOOT_HEIGHT + FOOT_CHAMFER],
    ];
    translate([-L/2, 0, -T/2])
        rotate([90, 0, 90])
            linear_extrude(height=L)
                polygon(profile);
}

// ============================================================================
// Assembly
// ============================================================================

module mounting_plate() {
    difference() {
        union() {
            plate_blank();
            dovetail_foot();
        }

        // --- outer row: holes + 2 slots, mirrored top/bottom ---
        for (y = [EDGE_ROW_Y, -EDGE_ROW_Y]) {
            for (i = [0 : len(outer_centers)-1]) {
                x = outer_centers[i];
                is_slot = (i == outer_slot_idx[0] || i == outer_slot_idx[1]);
                translate([x, y, 0]) {
                    if (is_slot)
                        slot(OUTER_SLOT_L, OUTER_SLOT_W, T + 2);
                    else
                        round_hole(HOLE_D, T + 2);
                }
            }
        }

        // --- inner big slots, mirrored top/bottom ---
        for (y = [INNER_ROW_Y, -INNER_ROW_Y]) {
            for (span = inner_slot_spans) {
                cx = (span[0] + span[1]) / 2;
                len_ = span[1] - span[0];
                translate([cx, y, 0])
                    slot(len_, INNER_SLOT_W, T + 2);
            }
        }

        // --- centerline: 2x M8x1.25 ---
        for (x = m8_centers_x)
            translate([x, 0, 0])
                round_hole(M8_TAP_D, T + 2);

        // --- centerline: 2x Ø9.2 ---
        for (x = small_hole_centers_x)
            translate([x, 0, 0])
                round_hole(SMALL_HOLE_D, T + 2);
    }
}

mounting_plate();

// ----------------------------------------------------------------------
// TODO (not modeled — secondary machining details from the bottom view):
//   8x Ø12 counterbore, 2x Ø14 counterbore, 4x R3 fillet, 4-15 / 4-2
//   (likely counterbore diameter/depth for bolt heads on the underside).
//   Add with more round_hole()-style cutters at a shallower depth once
//   you confirm which holes they sit on and how deep they go.
// ----------------------------------------------------------------------
