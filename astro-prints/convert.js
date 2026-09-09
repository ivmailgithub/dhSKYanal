/**
 * Cylindrical Multicolor Lithophane — STEP File Generator
 * =======================================================
 * Converts an image to a colored cylinder STEP file for multicolor 3D printing.
 * 
 * DESIGN:
 * - The image is projected onto the exterior of a hollow cylinder.
 * - The image is divided into NUM_BANDS horizontal strips (colored bands).
 * - Each strip is a SEPARATE SOLID BODY with its own color in the STEP file.
 * - The OUTER surface is smooth (same radius for all bands).
 * - The INNER surface varies: brighter pixels = thinner wall (lets light through).
 * - The bands have SLIGHTLY different outer radii (delta 0.01mm) so the slicer
 *   sees them as separate bodies but the step is invisible to the naked eye.
 * - No exterior relief/bumps — the image is purely embedded as wall thickness
 *   for the lithophane effect, and the filament colors provide the multicolor.
 * 
 * Usage: node convert.js [options]
 *   --input <file>     Input image (default: auto-detect)
 *   --output <file>    Output STEP file (default: image0_cylinder.stp)
 *   --radius <mm>      Cylinder outer radius (default: 35)
 *   --height <mm>      Cylinder height (default: 120)
 *   --bands <num>      Number of color bands (default: 5)
 *   --min-wall <mm>    Thinnest wall section (brightest, default: 0.6)
 *   --max-wall <mm>    Thickest wall section (darkest, default: 2.0)
 *   --base <mm>        Solid base thickness (default: 2.0)
 *   --angle <num>      Angular resolution (default: 120)
 *   --vert <num>       Vertical resolution (default: 200)
 *   --color0-4 <hex>   Per-band colors, e.g. --color0 111111
 *   --help             Show this help
 */

const fs = require('fs');
const { Jimp, intToRGBA } = require('jimp');

// ===== CLI =====
const args = process.argv.slice(2);
function getArg(f, d) { const i = args.indexOf(f); return i === -1 || i + 1 >= args.length ? d : args[i + 1]; }
function hasFlag(f) { return args.includes(f); }

if (hasFlag('--help') || hasFlag('-h')) {
    console.log(`
Cylindrical Multicolor Lithophane — STEP Generator
===================================================
Converts an image to a colored cylinder STEP file for multicolor 3D printing.

The image is divided into horizontal color bands (one per filament).
Each band is a separate solid body with its embedded color.
The outer surface is smooth — no exterior bumps. The image appears
through the lithophane effect (variable wall thickness + light).

Options:
  --input <file>     Input image (JPEG/PNG, default: auto-detect)
  --output <file>    Output STEP file (default: image0_cylinder.stp)
  --radius <mm>      Outer cylinder radius (default: 35)
  --height <mm>      Cylinder height (default: 120)
  --bands <num>      Number of color bands (default: 5)
  --min-wall <mm>    Thinnest wall section (brightest, default: 0.6)
  --max-wall <mm>    Thickest wall section (darkest, default: 2.0)
  --base <mm>        Solid base thickness (default: 2.0)
  --angle <num>      Angular resolution — higher = smoother (default: 120)
  --vert <num>       Vertical resolution — higher = more detail (default: 200)
  --color0 <hex>     Color for band 0 (default: 111111)
  --color1 <hex>     Color for band 1 (default: 1a1a5c)
  --color2 <hex>     Color for band 2 (default: 2244aa)
  --color3 <hex>     Color for band 3 (default: 6699dd)
  --color4 <hex>     Color for band 4 (default: bbddee)
  --help             Show this help
`);
    process.exit(0);
}

// Config
const INPUT_FILE = getArg('--input', (() => {
    const f = fs.readdirSync('.').find(x => x.startsWith('image0.thumb') && x.endsWith('.jpeg'));
    return f || 'image0.thumb.jpeg.aa268959b09fe82e7febe723f0c3ff75.jpeg';
})());
const OUTPUT_FILE = getArg('--output', 'image0_cylinder.stp');
const OUTER_R = parseFloat(getArg('--radius', '35'));
const HEIGHT = parseFloat(getArg('--height', '120'));
const NUM_BANDS = parseInt(getArg('--bands', '5'));
const MIN_WALL = parseFloat(getArg('--min-wall', '0.6'));
const MAX_WALL = parseFloat(getArg('--max-wall', '2.0'));
const BASE_H = parseFloat(getArg('--base', '2.0'));
const A_STEPS = parseInt(getArg('--angle', '120'));
const V_STEPS = parseInt(getArg('--vert', '200'));

const defaultColors = ['111111', '1a1a5c', '2244aa', '6699dd', 'bbddee'];
const bandColors = [];
for (let i = 0; i < NUM_BANDS; i++) bandColors.push(getArg('--color' + i, defaultColors[i] || '888888'));

const BAND_DELTA = 0.02; // Tiny radius delta per band for slicer body separation

// ===== STEP WRITER =====
class StepWriter {
    constructor() {
        this.lines = [];
        this.nextId = 1;
    }
    freshId() { return '#' + (this.nextId++); }
    emit(s) { this.lines.push(s); }

    header() {
        this.lines.push(
            'ISO-10303-21;\nHEADER;',
            "FILE_DESCRIPTION(('ViewDefinition[CoordinationView]'),'2;1');",
            "FILE_NAME('','2024-01-01',('user'),(''),'SwStep','STEP AP242','');",
            "FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));",
            'ENDSEC;',
            'DATA;'
        );
    }

    finish() {
        this.emit('ENDSEC;');
        this.emit('END-ISO-10303-21;');
        return this.lines.join('\n');
    }

    emitPt(x, y, z) {
        const id = this.freshId();
        this.emit(`${id}=CARTESIAN_POINT('',(${x.toFixed(4)},${y.toFixed(4)},${z.toFixed(4)}));`);
        return id;
    }

    emitDir(dx, dy, dz) {
        const id = this.freshId();
        this.emit(`${id}=DIRECTION('',(${dx.toFixed(6)},${dy.toFixed(6)},${dz.toFixed(6)}));`);
        return id;
    }

    emitAx2p3d(loc, axis, ref) {
        const id = this.freshId();
        this.emit(`${id}=AXIS2_PLACEMENT_3D('',${loc},${axis},${ref});`);
        return id;
    }

    emitPolyLoop(ptIds) {
        const id = this.freshId();
        this.emit(`${id}=POLY_LOOP('',(${ptIds.join(',')}));`);
        return id;
    }

    emitFaceOuterBound(loopId) {
        const id = this.freshId();
        this.emit(`${id}=FACE_OUTER_BOUND('',${loopId},.T.);`);
        return id;
    }

    emitAdvancedFace(boundId) {
        const id = this.freshId();
        this.emit(`${id}=ADVANCED_FACE('',(${boundId}),.T.);`);
        return id;
    }

    emitFace(boundId) {
        // Returns face ID only — no styled_item
        return this.emitAdvancedFace(boundId);
    }

    emitClosedShell(faceIds) {
        const id = this.freshId();
        this.emit(`${id}=CLOSED_SHELL('',(${faceIds.join(',')}));`);
        return id;
    }

    emitBrep(shellId) {
        const id = this.freshId();
        this.emit(`${id}=MANIFOLD_SOLID_BREP('',${shellId});`);
        return id;
    }

    emitColor(name, rFrac, gFrac, bFrac) {
        const id = this.freshId();
        this.emit(`${id}=COLOUR_RGB('${name}',${rFrac.toFixed(6)},${gFrac.toFixed(6)},${bFrac.toFixed(6)});`);
        return id;
    }

    emitStyle(colorId) {
        const sr = this.freshId();
        this.emit(`${sr}=SURFACE_STYLE_RENDERING(${colorId},(.FILLED.),.ON.,.LAMBERT.);`);
        const ss = this.freshId();
        this.emit(`${ss}=SURFACE_SIDE_STYLE('',(${sr}));`);
        const su = this.freshId();
        this.emit(`${su}=SURFACE_STYLE_USAGE(.BOTH.,${ss});`);
        const ps = this.freshId();
        this.emit(`${ps}=PRESENTATION_STYLE_ASSIGNMENT((${su}));`);
        return ps;
    }

    emitStyledItem(styleId, refId) {
        const id = this.freshId();
        this.emit(`${id}=STYLED_ITEM('',(${styleId}),${refId});`);
        return id;
    }

    emitProduct(name) {
        const ctx = this.freshId();
        this.emit(`${ctx}=PRODUCT_CONTEXT('','model','mechanical');`);
        const prod = this.freshId();
        this.emit(`${prod}=PRODUCT('${name}','${name}','',(${ctx}));`);
        const pdf = this.freshId();
        this.emit(`${pdf}=PRODUCT_DEFINITION_FORMATION('','',${prod});`);
        const pd = this.freshId();
        this.emit(`${pd}=PRODUCT_DEFINITION('','',${pdf});`);
        const pds = this.freshId();
        this.emit(`${pds}=PRODUCT_DEFINITION_SHAPE('','',${pd});`);
        return { product: prod, shape: pds };
    }

    emitShapeRep(brepId, placementId) {
        const id = this.freshId();
        this.emit(`${id}=SHAPE_REPRESENTATION('',(${brepId}),${placementId});`);
        return id;
    }

    emitSDR(srId, pdsId) {
        const id = this.freshId();
        this.emit(`${id}=SHAPE_DEFINITION_REPRESENTATION('',(${srId}),${pdsId});`);
        return id;
    }

    emitPresentationRep(styledItemId, placementId) {
        const id = this.freshId();
        this.emit(`${id}=MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',(${styledItemId}),${placementId});`);
        return id;
    }

    emitCDSR(presId, pdsId) {
        const id = this.freshId();
        this.emit(`${id}=CONTEXT_DEPENDENT_SHAPE_REPRESENTATION('',(${presId}),${pdsId});`);
        return id;
    }

    /**
     * Write a complete product with embedded color for one band.
     * Returns the placement ID (reusable for geometry).
     */
    writeColoredBand(name, faceIds, rFrac, gFrac, bFrac, origin) {
        // Helper: write placement
        const loc = this.emitPt(0, origin, 0);
        const axis = this.emitDir(0, 1, 0);
        const ref = this.emitDir(1, 0, 0);
        const place = this.emitAx2p3d(loc, axis, ref);

        // Shell + Brep
        const shell = this.emitClosedShell(faceIds);
        const brep = this.emitBrep(shell);

        // Color + Style
        const col = this.emitColor(name + '_color', rFrac, gFrac, bFrac);
        const style = this.emitStyle(col);

        // Styled item on the brep
        const si = this.emitStyledItem(style, brep);

        // Presentation representation (color for OrcaSlicer)
        const pres = this.emitPresentationRep(si, place);

        // Product hierarchy
        const prodInfo = this.emitProduct(name);
        const sr = this.emitShapeRep(brep, place);
        const sdr = this.emitSDR(sr, prodInfo.shape);
        const cdsr = this.emitCDSR(pres, prodInfo.shape);

        return place;
    }
}

// ===== GEOMETRY HELPERS =====
function cylPt(r, th, y) { return [r * Math.cos(th), y, r * Math.sin(th)]; }

// ===== MAIN =====
async function main() {
    console.log('=== Cylindrical Multicolor Lithophane — STEP Generator ===');
    console.log('Input:', INPUT_FILE);
    console.log('Output:', OUTPUT_FILE);
    console.log(`Outer radius: ${OUTER_R}mm, Height: ${HEIGHT}mm, Bands: ${NUM_BANDS}`);
    console.log(`Wall: ${MIN_WALL}–${MAX_WALL}mm, Base: ${BASE_H}mm`);
    console.log(`Resolution: ${A_STEPS}×${V_STEPS}`);
    console.log('Band colors:', bandColors.map((c, i) => `#${c}`).join(', '));

    const img = await Jimp.read(INPUT_FILE);
    console.log('Image:', img.bitmap.width, '×', img.bitmap.height);

    const resized = img.clone().resize({ w: A_STEPS, h: V_STEPS });

    // Extract brightness
    const bri = [];
    for (let y = 0; y < V_STEPS; y++) {
        const row = [];
        for (let x = 0; x < A_STEPS; x++) {
            const c = intToRGBA(resized.getPixelColor(x, y));
            row.push(0.299 * c.r + 0.587 * c.g + 0.114 * c.b);
        }
        bri.push(row);
    }

    // Brightness range for mapping
    const allB = bri.flat().sort((a, b) => a - b);
    const bMin = allB[Math.floor(allB.length * 0.02)];
    const bMax = allB[Math.floor(allB.length * 0.98)];
    const bRange = bMax - bMin || 1;
    console.log('Brightness range:', bMin.toFixed(0) + '–' + bMax.toFixed(0));

    // Band configuration
    const rowsPerBand = Math.floor(V_STEPS / NUM_BANDS);
    const bandH = HEIGHT / NUM_BANDS;
    const dTh = (2 * Math.PI) / A_STEPS;
    const dH = HEIGHT / V_STEPS;
    const Ri = OUTER_R - MAX_WALL - 0.5;  // Inner radius (allows max wall thickness + clearance)
    const baseBot = -BASE_H;

    function nb(v) { return Math.max(0, Math.min(1, (v - bMin) / bRange)); }

    console.log('\nGenerating geometry...');
    const sw = new StepWriter();
    sw.header();

    // For each band, generate faces and emit as a colored product
    for (let band = 0; band < NUM_BANDS; band++) {
        const bandStartRow = band * rowsPerBand;
        const bandEndRow = Math.min((band + 1) * rowsPerBand, V_STEPS);
        const hex = bandColors[band];
        const rCol = parseInt(hex.substring(0, 2), 16);
        const gCol = parseInt(hex.substring(2, 4), 16);
        const bCol = parseInt(hex.substring(4, 6), 16);

        // Slightly different outer radius per band for slicer body separation
        // delta is tiny (0.02mm) — invisible to the eye but enough for slicer
        const R_outer = OUTER_R + band * BAND_DELTA;

        // Wall thickness range for this band
        // Darker bands get thicker walls (more material), brighter get thinner
        const wallRange = MAX_WALL - MIN_WALL;
        const bandBrightness = band / (NUM_BANDS - 1); // 0 = bottom, 1 = top
        // Invert brightness mapping: bottom bands (darker image area) = thicker
        // Top bands (brighter) = thinner
        const maxWallForBand = MAX_WALL - bandBrightness * wallRange * 0.2;
        const minWallForBand = MIN_WALL + (1 - bandBrightness) * wallRange * 0.2;

        // Collect all face IDs for this band
        const faceIds = [];

        for (let y = bandStartRow; y < bandEndRow; y++) {
            const y0 = y * dH;
            const y1 = (y + 1) * dH;
            const isBoundary = (y === bandStartRow && band > 0);

            for (let x = 0; x < A_STEPS; x++) {
                const xN = (x + 1) % A_STEPS;
                const t0 = x * dTh;
                const t1 = (x + 1) * dTh;
                const yN = Math.min(y + 1, V_STEPS - 1);

                // Wall thickness at this pixel
                // Bright pixel → thin wall (near minWallForBand)
                // Dark pixel → thick wall (near maxWallForBand)
                const wallScale = nb(bri[y][x]);   // 0 = dark, 1 = bright
                const w00 = maxWallForBand - wallScale * (maxWallForBand - minWallForBand);
                const w10 = maxWallForBand - nb(bri[y][xN]) * (maxWallForBand - minWallForBand);
                const w01 = maxWallForBand - nb(bri[yN][x]) * (maxWallForBand - minWallForBand);
                const w11 = maxWallForBand - nb(bri[yN][xN]) * (maxWallForBand - minWallForBand);

                // Outer surface: constant radius R_outer (smooth!)
                // Inner surface: variable radius based on wall thickness
                const rOuter = R_outer;
                const rInner00 = R_outer - w00;
                const rInner10 = R_outer - w10;
                const rInner01 = R_outer - w01;
                const rInner11 = R_outer - w11;

                // At band boundary, snap inner to max thickness for clean seam
                const ri00 = isBoundary ? (R_outer - maxWallForBand) : rInner00;
                const ri10 = isBoundary ? (R_outer - maxWallForBand) : rInner10;
                const ri01 = rInner01;
                const ri11 = rInner11;

                // === OUTER surface (smooth, constant radius) ===
                const e00 = sw.emitPt(...cylPt(rOuter, t0, y0));
                const e10 = sw.emitPt(...cylPt(rOuter, t1, y0));
                const e01 = sw.emitPt(...cylPt(rOuter, t0, y1));
                const e11 = sw.emitPt(...cylPt(rOuter, t1, y1));

                // === INNER surface (variable radius = lithophane) ===
                const i00 = sw.emitPt(...cylPt(ri00, t0, y0));
                const i10 = sw.emitPt(...cylPt(ri10, t1, y0));
                const i01 = sw.emitPt(...cylPt(ri01, t0, y1));
                const i11 = sw.emitPt(...cylPt(ri11, t1, y1));

                // Outer face (normal outward)
                let loop = sw.emitPolyLoop([e00, e10, e11, e01]);
                let bound = sw.emitFaceOuterBound(loop);
                faceIds.push(sw.emitFace(bound));

                // Inner face (normal inward — reversed winding)
                loop = sw.emitPolyLoop([i01, i11, i10, i00]);
                bound = sw.emitFaceOuterBound(loop);
                faceIds.push(sw.emitFace(bound));

                // Left radial wall (theta = t0)
                loop = sw.emitPolyLoop([e00, e01, i01, i00]);
                bound = sw.emitFaceOuterBound(loop);
                faceIds.push(sw.emitFace(bound));

                // Bottom wall (y = y0)
                loop = sw.emitPolyLoop([e00, i00, i10, e10]);
                bound = sw.emitFaceOuterBound(loop);
                faceIds.push(sw.emitFace(bound));
            }
        }

        // === TOP RING (only for top band) ===
        if (band === NUM_BANDS - 1) {
            for (let x = 0; x < A_STEPS; x++) {
                const t0 = x * dTh;
                const t1 = ((x + 1) % A_STEPS) * dTh;
                const yT = HEIGHT;
                const w = maxWallForBand - nb(bri[V_STEPS - 1][x]) * (maxWallForBand - minWallForBand);
                const wn = maxWallForBand - nb(bri[V_STEPS - 1][(x + 1) % A_STEPS]) * (maxWallForBand - minWallForBand);
                const ri = R_outer - w;
                const rin = R_outer - wn;

                const to = sw.emitPt(...cylPt(R_outer, t0, yT));
                const tn = sw.emitPt(...cylPt(R_outer, t1, yT));
                const ti = sw.emitPt(...cylPt(ri, t0, yT));
                const tin = sw.emitPt(...cylPt(rin, t1, yT));

                const loop = sw.emitPolyLoop([to, tn, tin, ti]);
                const bound = sw.emitFaceOuterBound(loop);
                faceIds.push(sw.emitFace(bound));
            }
        }

        // === BOTTOM RING (only for band 0) ===
        if (band === 0) {
            const baseRimR = OUTER_R + 2; // slightly wider base rim
            for (let x = 0; x < A_STEPS; x++) {
                const t0 = x * dTh;
                const t1 = ((x + 1) % A_STEPS) * dTh;
                const xN = (x + 1) % A_STEPS;

                const innerBotR = OUTER_R - MAX_WALL;  // thickest at bottom

                // Inner wall at bottom
                const ib0 = sw.emitPt(...cylPt(innerBotR, t0, 0));
                const ib1 = sw.emitPt(...cylPt(innerBotR, t1, 0));
                const ib_bot0 = sw.emitPt(...cylPt(innerBotR, t0, baseBot));
                const ib_bot1 = sw.emitPt(...cylPt(innerBotR, t1, baseBot));

                // Outer at bottom
                const eb0 = sw.emitPt(...cylPt(R_outer, t0, 0));
                const eb1 = sw.emitPt(...cylPt(R_outer, t1, 0));

                // Close bottom ring: outer → inner at y=0
                let loop = sw.emitPolyLoop([eb0, eb1, ib1, ib0]);
                let bound = sw.emitFaceOuterBound(loop);
                faceIds.push(sw.emitFace(bound));

                // Outer rim wall (base)
                const rb0 = sw.emitPt(...cylPt(baseRimR, t0, 0));
                const rb1 = sw.emitPt(...cylPt(baseRimR, t1, 0));
                const rb_bot0 = sw.emitPt(...cylPt(baseRimR, t0, baseBot));
                const rb_bot1 = sw.emitPt(...cylPt(baseRimR, t1, baseBot));

                loop = sw.emitPolyLoop([rb0, rb1, rb_bot1, rb_bot0]);
                bound = sw.emitFaceOuterBound(loop);
                faceIds.push(sw.emitFace(bound));

                // Bottom disc surface
                const center = sw.emitPt(0, baseBot, 0);
                loop = sw.emitPolyLoop([rb1, rb0, center]);
                bound = sw.emitFaceOuterBound(loop);
                faceIds.push(sw.emitFace(bound));

                loop = sw.emitPolyLoop([ib_bot0, ib_bot1, center]);
                bound = sw.emitFaceOuterBound(loop);
                faceIds.push(sw.emitFace(bound));

                // Inner wall of base
                loop = sw.emitPolyLoop([ib1, ib0, ib_bot0, ib_bot1]);
                bound = sw.emitFaceOuterBound(loop);
                faceIds.push(sw.emitFace(bound));
            }
        }

        // Emit this band as a colored product
        const bandName = 'band_' + band;
        const originY = band * bandH;
        sw.writeColoredBand(bandName, faceIds, rCol / 255, gCol / 255, bCol / 255, originY);

        const zTop = (band + 1) * bandH;
        console.log(`  Band ${band}: z=0–${zTop.toFixed(0)}mm, ${faceIds.length} faces, color #${hex}`);
    }

    // Write file
    const content = sw.finish();
    fs.writeFileSync(OUTPUT_FILE, content, 'utf8');
    const size = fs.statSync(OUTPUT_FILE).size;

    console.log('\n=== COMPLETE ===');
    console.log('Output:', OUTPUT_FILE);
    console.log('Size:', (size / 1024).toFixed(1), 'KB');
    console.log('Lines: ~', content.split('\n').length);

    console.log('\n=== FILAMENT CHANGES ===');
    for (let b = 0; b < NUM_BANDS; b++) {
        const zTop = (b + 1) * bandH;
        console.log(`Band ${b}: z=0–${zTop.toFixed(0)}mm, color #${bandColors[b]}`);
        if (b < NUM_BANDS - 1) console.log(`  >>> CHANGE FILAMENT at layer ${Math.round(zTop / 0.2)} (z=${zTop.toFixed(0)}mm)`);
    }
    console.log('\nThe outer surface is smooth. The image appears as variable wall thickness.');
    console.log('Place an LED tealight inside — bright areas glow through, dark areas stay opaque.');
}

main().catch(e => { console.error(e); process.exit(1); });
