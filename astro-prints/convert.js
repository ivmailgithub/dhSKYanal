/**
 * Cylindrical Multicolor Star Map Lithophane — STEP File Generator (Node.js Version)
 * ==================================================================================
 * Converts an astronomical star map image into a colored cylinder STEP assembly
 * (ISO 10303-21 AP214/AP242) for multicolor 3D printing (Bambu AMS, OrcaSlicer, PrusaSlicer).
 * 
 * Key Design & Engineering Features:
 * - Natural astronomical orientation: Right Ascension wraps 360° circumferentially;
 *   Declination spans the cylinder axis Z with date markings at the bottom (Z approx 0).
 * - Lithophane interior: Wall thickness varies smoothly based on image brightness
 *   (thin wall for bright stars/lines to let light through, thick wall for dark space).
 * - Smooth exterior: Constant outer radius (zero exterior relief bumps) so prints
 *   are smooth to the touch, print reliably without nozzle knocking or wipe-tower collapses.
 * - Multicolor assembly: 4 distinct color parts matching the sky map colors:
 *     1. Space_Background    (Navy: #0a0e27)  — Full lithophane hollow cylinder tube with base flange
 *     2. Stars               (Yellow: #ffd700) — Metric round circular star dots
 *     3. Constellation_Lines (Blue: #2e6fd9)  — Constellation figures & text
 *     4. Index_Lines         (Cyan: #8ab4f8)  — Coordinate grid (RA/Dec) & bottom date ruler
 * - 100% 2-manifold, watertight closed solids natively compatible with all CAD kernels & slicers.
 * - Zero crashes, zero sewing hangs in OpenCASCADE / BambuStudio / OrcaSlicer.
 * 
 * Usage: node convert.js [options]
 *   --input <file>         Input image (default: auto-detect)
 *   --output <file>        Output STEP file (default: image0_cylinder.stp)
 *   --radius <mm>          Outer cylinder radius in mm (default: 35.0)
 *   --height <mm>          Cylinder height in mm (default: auto isotropic ~138mm)
 *   --min-wall <mm>        Thinnest wall section for brightest pixels in mm (default: 0.8)
 *   --max-wall <mm>        Thickest wall section for darkest pixels in mm (default: 2.2)
 *   --base-flange <mm>     Bottom mounting flange height in mm (default: 2.0)
 *   --relief <mm>          Exterior relief height in mm (default: 0.0 = smooth lithophane)
 *   --angle <num>          Circumferential grid resolution (default: 180)
 *   --vert <num>           Axial grid resolution (default: 113)
 *   --color-bg <hex>       Hex color for space background (default: 0a0e27)
 *   --color-stars <hex>    Hex color for stars (default: ffd700)
 *   --color-lines <hex>    Hex color for constellation lines (default: 2e6fd9)
 *   --color-index <hex>    Hex color for index/dates (default: 8ab4f8)
 *   --help                 Show this help
 */

const fs = require('fs');
const path = require('path');
const { Jimp, intToRGBA } = require('jimp');

// ===== CLI PARSER =====
const args = process.argv.slice(2);
function getArg(flags, defaultVal) {
    if (!Array.isArray(flags)) flags = [flags];
    for (const flag of flags) {
        const idx = args.indexOf(flag);
        if (idx !== -1 && idx + 1 < args.length) return args[idx + 1];
    }
    return defaultVal;
}
function hasFlag(flags) {
    if (!Array.isArray(flags)) flags = [flags];
    return flags.some(f => args.includes(f));
}

if (hasFlag(['--help', '-h'])) {
    console.log(`
Cylindrical Multicolor Star Map Lithophane — STEP Generator (Node.js)
=====================================================================
Projects an astronomical star chart onto a 3D printable cylinder in STEP
(ISO 10303-21 AP214/AP242) format for multicolor 3D printing.

The cylinder features a smooth exterior (zero relief bumps) and a lithophane
interior (variable wall thickness based on image brightness).
Different colors of the star chart are generated as 4 distinct solid parts:
  1. Space_Background   (Navy: #0a0e27)
  2. Stars              (Yellow: #ffd700)
  3. Constellation_Lines(Blue: #2e6fd9)
  4. Index_Lines        (Cyan: #8ab4f8)

Options:
  --input <file>         Input image file (default: auto-detect)
  --output <file>        Output STEP file (default: image0_cylinder.stp)
  --radius <mm>          Outer cylinder radius (default: 35.0)
  --height <mm>          Cylinder height (default: auto isotropic)
  --min-wall <mm>        Thinnest wall section for brightest pixels (default: 0.8)
  --max-wall <mm>        Thickest wall section for darkest pixels (default: 2.2)
  --base <mm>            Bottom mounting flange height (default: 2.0)
  --relief <mm>          Exterior relief height (default: 0.0 = smooth lithophane)
  --angle <num>          Circumferential steps (default: 180)
  --vert <num>           Axial steps (default: 113)
  --color-bg <hex>       Color for space background (default: 0a0e27)
  --color-stars <hex>    Color for stars (default: ffd700)
  --color-lines <hex>    Color for constellation lines (default: 2e6fd9)
  --color-index <hex>    Color for index & grid lines (default: 8ab4f8)
  --help                 Show this help
`);
    process.exit(0);
}

function findDefaultImage() {
    const files = fs.readdirSync('.');
    const candidate = files.find(f => f.startsWith('image0.thumb') && f.endsWith('.jpeg'))
        || files.find(f => f.startsWith('image0') && (f.endsWith('.jpeg') || f.endsWith('.jpg') || f.endsWith('.png')))
        || files.find(f => f.endsWith('.jpeg') || f.endsWith('.jpg') || f.endsWith('.png'));
    return candidate || 'image0.thumb.jpeg.aa268959b09fe82e7febe723f0c3ff75.jpeg';
}

const INPUT_FILE = getArg(['--input', '-i'], findDefaultImage());
const OUTPUT_FILE = getArg(['--output', '-o'], 'image0_cylinder.stp');
const OUTER_R = parseFloat(getArg(['--radius', '--radious', '-r'], '35.0'));
const HEIGHT_PARAM = getArg(['--height', '-h'], null);
const MIN_WALL = parseFloat(getArg(['--min-wall'], '0.8'));
const MAX_WALL = parseFloat(getArg(['--max-wall'], '2.2'));
const BASE_FLANGE = parseFloat(getArg(['--base-flange', '--base'], '2.0'));
const RELIEF = Math.max(0.0, parseFloat(getArg(['--relief'], '0.0')));
const NW = parseInt(getArg(['--angle', '--grid-w'], '180'));
const NH = parseInt(getArg(['--vert', '--grid-h'], '113'));

const COLOR_BG = getArg(['--color-bg', '--color0'], '0a0e27');
const COLOR_STARS = getArg(['--color-stars', '--color1'], 'ffd700');
const COLOR_LINES = getArg(['--color-lines', '--color2'], '2e6fd9');
const COLOR_INDEX = getArg(['--color-index', '--color3'], '8ab4f8');

function hexToRgb(hexStr) {
    let clean = hexStr.replace(/^#/, '');
    if (clean.length === 3) clean = clean.split('').map(c => c + c).join('');
    const num = parseInt(clean, 16);
    return [((num >> 16) & 255) / 255.0, ((num >> 8) & 255) / 255.0, (num & 255) / 255.0];
}

// ===== STEP WRITER =====
class StepAssemblyWriter {
    constructor() {
        this.lines = [];
        this.nextId = 100;
    }

    allocId() {
        return this.nextId++;
    }

    emit(s) {
        this.lines.push(s);
    }

    initContexts() {
        this.appContext = this.allocId();
        this.appProto = this.allocId();
        this.prodContext = this.allocId();
        this.pdefContext = this.allocId();
        this.geomContext = this.allocId();
        this.lenUnit = this.allocId();
        this.angUnit = this.allocId();
        this.sterUnit = this.allocId();
        this.uncert = this.allocId();
        this.originPt = this.allocId();
        this.dirZ = this.allocId();
        this.dirX = this.allocId();
        this.axisPlacement = this.allocId();

        this.emit(`#${this.appContext} = APPLICATION_CONTEXT('core data for automotive mechanical design processes');`);
        this.emit(`#${this.appProto} = APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,#${this.appContext});`);
        this.emit(`#${this.prodContext} = PRODUCT_CONTEXT('',#${this.appContext},'mechanical');`);
        this.emit(`#${this.pdefContext} = PRODUCT_DEFINITION_CONTEXT('part definition',#${this.appContext},'design');`);

        this.emit(`#${this.lenUnit} = ( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.) );`);
        this.emit(`#${this.angUnit} = ( NAMED_UNIT(*) PLANE_ANGLE_UNIT() SI_UNIT($,.RADIAN.) );`);
        this.emit(`#${this.sterUnit} = ( NAMED_UNIT(*) SI_UNIT($,.STERADIAN.) SOLID_ANGLE_UNIT() );`);
        this.emit(`#${this.uncert} = UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-07),#${this.lenUnit},'distance_accuracy_value','confusion accuracy');`);
        this.emit(`#${this.geomContext} = ( GEOMETRIC_REPRESENTATION_CONTEXT(3) GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#${this.uncert})) GLOBAL_UNIT_ASSIGNED_CONTEXT((#${this.lenUnit},#${this.angUnit},#${this.sterUnit})) REPRESENTATION_CONTEXT('Context #1','3D Context with UNIT and UNCERTAINTY') );`);

        this.emit(`#${this.originPt} = CARTESIAN_POINT('',(0.,0.,0.));`);
        this.emit(`#${this.dirZ} = DIRECTION('',(0.,0.,1.));`);
        this.emit(`#${this.dirX} = DIRECTION('',(1.,0.,0.));`);
        this.emit(`#${this.axisPlacement} = AXIS2_PLACEMENT_3D('',#${this.originPt},#${this.dirZ},#${this.dirX});`);

        // Root Assembly Product
        this.rootProd = this.allocId();
        this.rootForm = this.allocId();
        this.rootPdef = this.allocId();
        this.rootPshp = this.allocId();
        this.rootRep = this.allocId();
        this.rootSdr = this.allocId();

        this.emit(`#${this.rootProd} = PRODUCT('StarMap_Cylinder','StarMap_Cylinder','',(#${this.prodContext}));`);
        this.emit(`#${this.rootForm} = PRODUCT_DEFINITION_FORMATION('','',#${this.rootProd});`);
        this.emit(`#${this.rootPdef} = PRODUCT_DEFINITION('design','',#${this.rootForm},#${this.pdefContext});`);
        this.emit(`#${this.rootPshp} = PRODUCT_DEFINITION_SHAPE('','',#${this.rootPdef});`);
        this.emit(`#${this.rootRep} = SHAPE_REPRESENTATION('StarMap_Cylinder',(#${this.axisPlacement}),#${this.geomContext});`);
        this.emit(`#${this.rootSdr} = SHAPE_DEFINITION_REPRESENTATION(#${this.rootPshp},#${this.rootRep});`);
        this.emit(`#${this.allocId()} = PRODUCT_RELATED_PRODUCT_CATEGORY('assembly',$,(#${this.rootProd}));`);
    }

    makeColor(name, rgb) {
        const [r, g, b] = rgb;
        const cId = this.allocId();
        const fasId = this.allocId();
        const sfaId = this.allocId();
        const surfStyleFillId = this.allocId();
        const sideId = this.allocId();
        const usageId = this.allocId();
        const styleId = this.allocId();

        this.emit(`#${cId} = COLOUR_RGB('${name}',${r.toFixed(4)},${g.toFixed(4)},${b.toFixed(4)});`);
        this.emit(`#${fasId} = FILL_AREA_STYLE_COLOUR('',#${cId});`);
        this.emit(`#${sfaId} = FILL_AREA_STYLE('',(#${fasId}));`);
        this.emit(`#${surfStyleFillId} = SURFACE_STYLE_FILL_AREA(#${sfaId});`);
        this.emit(`#${sideId} = SURFACE_SIDE_STYLE('',(#${surfStyleFillId}));`);
        this.emit(`#${usageId} = SURFACE_STYLE_USAGE(.BOTH.,#${sideId});`);
        this.emit(`#${styleId} = PRESENTATION_STYLE_ASSIGNMENT((#${usageId}));`);
        return styleId;
    }

    registerComponent(name, brepIds, styleId) {
        if (!Array.isArray(brepIds)) brepIds = [brepIds];
        const prodId = this.allocId();
        const formId = this.allocId();
        const pdefId = this.allocId();
        const pshpId = this.allocId();
        const repId = this.allocId();
        const sdrId = this.allocId();

        this.emit(`#${prodId} = PRODUCT('${name}','${name}','',(#${this.prodContext}));`);
        this.emit(`#${formId} = PRODUCT_DEFINITION_FORMATION('','',#${prodId});`);
        this.emit(`#${pdefId} = PRODUCT_DEFINITION('design','',#${formId},#${this.pdefContext});`);
        this.emit(`#${pshpId} = PRODUCT_DEFINITION_SHAPE('','',#${pdefId});`);

        const brepItems = brepIds.map(b => '#' + b).join(',');
        this.emit(`#${repId} = SHAPE_REPRESENTATION('${name}',(#${this.axisPlacement},${brepItems}),#${this.geomContext});`);
        this.emit(`#${sdrId} = SHAPE_DEFINITION_REPRESENTATION(#${pshpId},#${repId});`);
        this.emit(`#${this.allocId()} = PRODUCT_RELATED_PRODUCT_CATEGORY('part',$,(#${prodId}));`);

        const styledIds = [];
        for (const b of brepIds) {
            const styledId = this.allocId();
            this.emit(`#${styledId} = STYLED_ITEM('color',(#${styleId}),#${b});`);
            styledIds.push(styledId);
        }

        const styledItems = styledIds.map(s => '#' + s).join(',');
        this.emit(`#${this.allocId()} = MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',(${styledItems}),#${this.geomContext});`);

        const nauoId = this.allocId();
        const relPshpId = this.allocId();
        const cdsrId = this.allocId();
        const relId = this.allocId();
        const transId = this.allocId();

        this.emit(`#${nauoId} = NEXT_ASSEMBLY_USAGE_OCCURRENCE('${name}','${name}','',#${this.rootPdef},#${pdefId},$);`);
        this.emit(`#${relPshpId} = PRODUCT_DEFINITION_SHAPE('','',#${nauoId});`);
        this.emit(`#${cdsrId} = CONTEXT_DEPENDENT_SHAPE_REPRESENTATION(#${relId},#${relPshpId});`);
        this.emit(`#${relId} = ( REPRESENTATION_RELATIONSHIP('','',#${this.rootRep},#${repId}) REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION(#${transId}) SHAPE_REPRESENTATION_RELATIONSHIP() );`);
        this.emit(`#${transId} = ITEM_DEFINED_TRANSFORMATION('','',#${this.axisPlacement},#${this.axisPlacement});`);
    }

    addPlane(pt, norm, tang) {
        let nl = Math.sqrt(norm[0] * norm[0] + norm[1] * norm[1] + norm[2] * norm[2]);
        let n = nl > 1e-9 ? [norm[0] / nl, norm[1] / nl, norm[2] / nl] : [0, 0, 1];
        let dot = tang[0] * n[0] + tang[1] * n[1] + tang[2] * n[2];
        let t = [tang[0] - dot * n[0], tang[1] - dot * n[1], tang[2] - dot * n[2]];
        let tl = Math.sqrt(t[0] * t[0] + t[1] * t[1] + t[2] * t[2]);
        if (tl < 1e-9) {
            let arb = Math.abs(n[0]) < 0.9 ? [1, 0, 0] : [0, 1, 0];
            let adot = arb[0] * n[0] + arb[1] * n[1] + arb[2] * n[2];
            t = [arb[0] - adot * n[0], arb[1] - adot * n[1], arb[2] - adot * n[2]];
            tl = Math.sqrt(t[0] * t[0] + t[1] * t[1] + t[2] * t[2]);
        }
        t = [t[0] / tl, t[1] / tl, t[2] / tl];

        const pid = this.allocId();
        const dz = this.allocId();
        const dx = this.allocId();
        const ax = this.allocId();
        const pl = this.allocId();
        this.emit(`#${pid} = CARTESIAN_POINT('',(${pt[0].toFixed(4)},${pt[1].toFixed(4)},${pt[2].toFixed(4)}));`);
        this.emit(`#${dz} = DIRECTION('',(${n[0].toFixed(4)},${n[1].toFixed(4)},${n[2].toFixed(4)}));`);
        this.emit(`#${dx} = DIRECTION('',(${t[0].toFixed(4)},${t[1].toFixed(4)},${t[2].toFixed(4)}));`);
        this.emit(`#${ax} = AXIS2_PLACEMENT_3D('',#${pid},#${dz},#${dx});`);
        this.emit(`#${pl} = PLANE('',#${ax});`);
        return pl;
    }

    makeTriWithPts(vIds, p0, p1, p2) {
        const d1 = [p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]];
        const d2 = [p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]];
        let n = [
            d1[1] * d2[2] - d1[2] * d2[1],
            d1[2] * d2[0] - d1[0] * d2[2],
            d1[0] * d2[1] - d1[1] * d2[0]
        ];
        const nl = Math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]);
        if (nl > 1e-9) {
            n = [n[0] / nl, n[1] / nl, n[2] / nl];
        } else {
            n = [0, 0, 1];
        }
        const tl = Math.sqrt(d1[0] * d1[0] + d1[1] * d1[1] + d1[2] * d1[2]);
        const t = tl > 1e-9 ? [d1[0] / tl, d1[1] / tl, d1[2] / tl] : [1, 0, 0];

        const pl = this.addPlane(p0, n, t);
        const lid = this.allocId();
        const bid = this.allocId();
        const fid = this.allocId();
        const refs = `#${vIds[0]},#${vIds[1]},#${vIds[2]}`;
        this.emit(`#${lid} = POLY_LOOP('',(${refs}));`);
        this.emit(`#${bid} = FACE_OUTER_BOUND('',#${lid},.T.);`);
        this.emit(`#${fid} = FACE_SURFACE('',(#${bid}),#${pl},.T.);`);
        return fid;
    }

    emitPoint(x, y, z) {
        const id = this.allocId();
        this.emit(`#${id} = CARTESIAN_POINT('',(${x.toFixed(4)},${y.toFixed(4)},${z.toFixed(4)}));`);
        return id;
    }
}

// ===== MAIN =====
async function main() {
    console.log('=== Cylindrical Multicolor Star Map Lithophane Generator (Node.js) ===');
    console.log('Loading image:', INPUT_FILE);
    const img = await Jimp.read(INPUT_FILE);

    // Rotate 90 CCW to natural astronomical orientation:
    // Circumference wraps the 24-hour RA axis (750px),
    // Cylinder axis Z spans Declination (472px) with date markings at the bottom (Z approx 0).
    img.rotate(90);
    const W_orig = img.bitmap.width;
    const H_orig = img.bitmap.height;
    console.log(`Astronomical orientation: ${W_orig}x${H_orig} (RA circumference: ${W_orig}px, Dec height: ${H_orig}px)`);

    const C = 2 * Math.PI * OUTER_R;
    const scale = C / W_orig;
    const H_cyl = HEIGHT_PARAM ? parseFloat(HEIGHT_PARAM) : (H_orig * scale);
    console.log(`Cylinder parameters: Outer R=${OUTER_R.toFixed(2)} mm, Height=${H_cyl.toFixed(2)} mm`);
    console.log(`Lithophane wall thickness: ${MIN_WALL.toFixed(2)} mm (bright) to ${MAX_WALL.toFixed(2)} mm (dark)`);
    console.log(`Exterior relief: ${RELIEF.toFixed(2)} mm (${RELIEF === 0 ? 'Smooth lithophane' : 'Raised relief'})`);
    console.log(`Resolution: ${NW} angular x ${NH} axial grid`);

    // 1. Detect Star Points on full resolution for maximum roundness and precision
    const dateLimFull = Math.floor(50 * H_orig / 472);
    const magLimFull = Math.floor(420 * H_orig / 472);
    const visited = new Uint8Array(W_orig * H_orig);
    const stars = [];

    for (let y = dateLimFull; y < magLimFull; y++) {
        for (let x = 0; x < W_orig; x++) {
            const idx = y * W_orig + x;
            if (visited[idx]) continue;

            const c = intToRGBA(img.getPixelColor(x, y));
            const lum = 0.299 * c.r + 0.587 * c.g + 0.114 * c.b;

            if (lum > 165 && c.r > 120 && c.g > 120) {
                // BFS Connected Components
                const queue = [idx];
                visited[idx] = 1;
                let qHead = 0;
                let sumX = 0, sumY = 0, count = 0;
                let minX = x, maxX = x, minY = y, maxY = y;

                while (qHead < queue.length) {
                    const curr = queue[qHead++];
                    const cy = Math.floor(curr / W_orig);
                    const cx = curr % W_orig;
                    sumX += cx; sumY += cy; count++;
                    if (cx < minX) minX = cx; if (cx > maxX) maxX = cx;
                    if (cy < minY) minY = cy; if (cy > maxY) maxY = cy;

                    const neighbors = [curr - 1, curr + 1, curr - W_orig, curr + W_orig];
                    for (const n of neighbors) {
                        if (n < 0 || n >= W_orig * H_orig) continue;
                        if (visited[n]) continue;
                        const ny = Math.floor(n / W_orig);
                        const nx = n % W_orig;
                        if (ny < dateLimFull || ny >= magLimFull) continue;
                        const nc = intToRGBA(img.getPixelColor(nx, ny));
                        const nlum = 0.299 * nc.r + 0.587 * nc.g + 0.114 * nc.b;
                        if (nlum > 165 && nc.r > 120 && nc.g > 120) {
                            visited[n] = 1;
                            queue.push(n);
                        }
                    }
                }

                const hBox = maxY - minY + 1;
                const wBox = maxX - minX + 1;
                const aspect = wBox / Math.max(hBox, 1);
                if (count >= 4 && aspect >= 0.35 && aspect <= 2.8 && Math.max(hBox, wBox) <= 28) {
                    const cx = sumX / count;
                    const cy = sumY / count;
                    const radPx = Math.max(Math.sqrt(count / Math.PI), 0.8);
                    const radMm = Math.max(radPx * scale, 0.55);
                    const th = (cx / W_orig) * 2 * Math.PI;
                    const z = H_cyl * (cy / H_orig);
                    stars.push({ th, z, radMm });
                }
            }
        }
    }
    console.log(`Detected ${stars.length} prominent round star points`);

    // 2. Downsample for Grid Feature Classification
    const downImg = img.clone().resize({ w: NW, h: NH });
    const lumGrid = [];
    const rGrid = [];
    const gGrid = [];
    const bGrid = [];

    for (let y = 0; y < NH; y++) {
        const lRow = [], rRow = [], gRow = [], bRow = [];
        for (let x = 0; x < NW; x++) {
            const c = intToRGBA(downImg.getPixelColor(x, y));
            const lum = 0.299 * c.r + 0.587 * c.g + 0.114 * c.b;
            lRow.push(lum);
            rRow.push(c.r);
            gRow.push(c.g);
            bRow.push(c.b);
        }
        lumGrid.push(lRow);
        rGrid.push(rRow);
        gGrid.push(gRow);
        bGrid.push(bRow);
    }

    const dateLimDown = Math.floor(50 * NH / H_orig);
    const magLimDown = Math.floor(420 * NH / H_orig);

    const rulerMask = Array.from({ length: NH }, () => new Uint8Array(NW));
    for (let y = 0; y < NH; y++) {
        for (let x = 0; x < NW; x++) {
            if (y < dateLimDown || y >= magLimDown) {
                if (lumGrid[y][x] > 55) rulerMask[y][x] = 1;
            }
        }
    }

    // Grid vertical lines
    const gridV = Array.from({ length: NH }, () => new Uint8Array(NW));
    const xCoords = [7, 36, 56, 83, 111, 138, 166, 194, 222, 250, 277, 305, 333, 360, 388, 416, 443, 471, 498, 526, 553, 581, 609, 636, 664, 691, 719, 746];
    for (const xc of xCoords) {
        const xg = Math.round(xc * NW / W_orig);
        if (xg >= 0 && xg < NW) {
            for (let y = dateLimDown; y < magLimDown; y++) {
                for (let dx = -1; dx <= 1; dx++) {
                    const xx = xg + dx;
                    if (xx >= 0 && xx < NW && lumGrid[y][xx] > 40) gridV[y][xx] = 1;
                }
            }
        }
    }

    // Grid horizontal lines
    const gridH = Array.from({ length: NH }, () => new Uint8Array(NW));
    const yCoords = [61, 92, 123, 154, 186, 217, 249, 280, 311, 343, 374, 405];
    for (const yc of yCoords) {
        const yg = Math.round(yc * NH / H_orig);
        if (yg >= dateLimDown && yg < magLimDown) {
            for (let dy = -1; dy <= 1; dy++) {
                const yy = yg + dy;
                if (yy >= 0 && yy < NH) {
                    for (let x = 0; x < NW; x++) {
                        if (lumGrid[yy][x] > 40) gridH[yy][x] = 1;
                    }
                }
            }
        }
    }

    const indexMask = Array.from({ length: NH }, () => new Uint8Array(NW));
    const linesMask = Array.from({ length: NH }, () => new Uint8Array(NW));
    let numIndex = 0, numLines = 0;

    for (let y = 0; y < NH; y++) {
        for (let x = 0; x < NW; x++) {
            const isSky = (y >= dateLimDown && y < magLimDown);
            if (rulerMask[y][x] || (isSky && (gridV[y][x] || gridH[y][x]) && lumGrid[y][x] > 40)) {
                indexMask[y][x] = 1;
                numIndex++;
            } else if (isSky && lumGrid[y][x] > 35 && lumGrid[y][x] <= 175 && (bGrid[y][x] > rGrid[y][x] + 8)) {
                linesMask[y][x] = 1;
                numLines++;
            }
        }
    }
    console.log(`Classified features: ${numIndex} index/ruler cells, ${numLines} constellation line cells`);

    // Normalized luminance for Lithophane modulation
    const allLum = lumGrid.flat().sort((a, b) => a - b);
    const lumMin = allLum[Math.floor(allLum.length * 0.02)];
    const lumMax = allLum[Math.floor(allLum.length * 0.98)];
    const lumRange = Math.max(lumMax - lumMin, 1.0);

    const normBri = lumGrid.map(row => row.map(v => Math.max(0, Math.min(1, (v - lumMin) / lumRange))));

    // 3. STEP Assembly Generation
    console.log('\nGenerating STEP assembly...');
    const sw = new StepAssemblyWriter();
    sw.initContexts();

    const styleBg = sw.makeColor('navy', hexToRgb(COLOR_BG));
    const styleStars = sw.makeColor('gold', hexToRgb(COLOR_STARS));
    const styleLines = sw.makeColor('blue', hexToRgb(COLOR_LINES));
    const styleIndex = sw.makeColor('cyan', hexToRgb(COLOR_INDEX));

    // =========================================================================
    // Component 1: Space_Background (Full Lithophane Hollow Cylinder Tube)
    // Outer radius is smooth at R_outer.
    // Inner radius varies with brightness: bright -> thin wall, dark -> thick wall.
    // =========================================================================
    console.log('Generating Space_Background solid (Lithophane)...');
    const bgFaces = [];
    const rInGrid = Array.from({ length: NH + 1 }, (_, j) => {
        const rowIdx = Math.min(j, NH - 1);
        return Array.from({ length: NW }, (_, i) => {
            const b = normBri[rowIdx][i];
            const w = MAX_WALL - b * (MAX_WALL - MIN_WALL);
            return OUTER_R - w;
        });
    });

    const bgOutPts = {};
    const bgInPts = {};
    for (let j = 0; j <= NH; j++) {
        const z = (j / NH) * H_cyl;
        for (let i = 0; i < NW; i++) {
            const th = (i / NW) * 2 * Math.PI;
            const rIn = rInGrid[j][i];
            bgOutPts[`${i},${j}`] = sw.emitPoint(OUTER_R * Math.cos(th), OUTER_R * Math.sin(th), z);
            bgInPts[`${i},${j}`] = sw.emitPoint(rIn * Math.cos(th), rIn * Math.sin(th), z);
        }
    }

    function getBgOutCoord(i, j) {
        const th = (i / NW) * 2 * Math.PI;
        const z = (j / NH) * H_cyl;
        return [OUTER_R * Math.cos(th), OUTER_R * Math.sin(th), z];
    }
    function getBgInCoord(i, j) {
        const th = (i / NW) * 2 * Math.PI;
        const z = (j / NH) * H_cyl;
        const rIn = rInGrid[j][i % NW];
        return [rIn * Math.cos(th), rIn * Math.sin(th), z];
    }

    // Outer surface
    for (let j = 0; j < NH; j++) {
        for (let i = 0; i < NW; i++) {
            const iNext = (i + 1) % NW;
            const p00 = getBgOutCoord(i, j), p10 = getBgOutCoord(iNext, j);
            const p11 = getBgOutCoord(iNext, j + 1), p01 = getBgOutCoord(i, j + 1);
            const v00 = bgOutPts[`${i},${j}`], v10 = bgOutPts[`${iNext},${j}`];
            const v11 = bgOutPts[`${iNext},${j + 1}`], v01 = bgOutPts[`${i},${j + 1}`];
            bgFaces.push(sw.makeTriWithPts([v00, v10, v11], p00, p10, p11));
            bgFaces.push(sw.makeTriWithPts([v00, v11, v01], p00, p11, p01));
        }
    }

    // Inner lithophane surface
    for (let j = 0; j < NH; j++) {
        for (let i = 0; i < NW; i++) {
            const iNext = (i + 1) % NW;
            const p00 = getBgInCoord(i, j), p10 = getBgInCoord(iNext, j);
            const p11 = getBgInCoord(iNext, j + 1), p01 = getBgInCoord(i, j + 1);
            const v00 = bgInPts[`${i},${j}`], v10 = bgInPts[`${iNext},${j}`];
            const v11 = bgInPts[`${iNext},${j + 1}`], v01 = bgInPts[`${i},${j + 1}`];
            bgFaces.push(sw.makeTriWithPts([v00, v11, v10], p00, p11, p10));
            bgFaces.push(sw.makeTriWithPts([v00, v01, v11], p00, p01, p11));
        }
    }

    // Top ring cap (z = H_cyl)
    for (let i = 0; i < NW; i++) {
        const iNext = (i + 1) % NW;
        const o0 = getBgOutCoord(i, NH), o1 = getBgOutCoord(iNext, NH);
        const in0 = getBgInCoord(i, NH), in1 = getBgInCoord(iNext, NH);
        const vo0 = bgOutPts[`${i},${NH}`], vo1 = bgOutPts[`${iNext},${NH}`];
        const vi0 = bgInPts[`${i},${NH}`], vi1 = bgInPts[`${iNext},${NH}`];
        bgFaces.push(sw.makeTriWithPts([vo0, vo1, vi1], o0, o1, in1));
        bgFaces.push(sw.makeTriWithPts([vo0, vi1, vi0], o0, in1, in0));
    }

    // Bottom flange or bottom ring cap (z <= 0)
    if (BASE_FLANGE > 0) {
        const rFlange = OUTER_R + 1.2;
        const rInBot = OUTER_R - MAX_WALL;
        const flangeOutPts = {};
        const flangeInPts = {};

        for (let i = 0; i < NW; i++) {
            const th = (i / NW) * 2 * Math.PI;
            flangeOutPts[i] = sw.emitPoint(rFlange * Math.cos(th), rFlange * Math.sin(th), -BASE_FLANGE);
            flangeInPts[i] = sw.emitPoint(rInBot * Math.cos(th), rInBot * Math.sin(th), -BASE_FLANGE);
        }

        const getFlangeOut = (i) => [rFlange * Math.cos((i / NW) * 2 * Math.PI), rFlange * Math.sin((i / NW) * 2 * Math.PI), -BASE_FLANGE];
        const getFlangeIn = (i) => [rInBot * Math.cos((i / NW) * 2 * Math.PI), rInBot * Math.sin((i / NW) * 2 * Math.PI), -BASE_FLANGE];

        for (let i = 0; i < NW; i++) {
            const iNext = (i + 1) % NW;
            const vo0 = bgOutPts[`${i},0`], vo1 = bgOutPts[`${iNext},0`];
            const vi0 = bgInPts[`${i},0`], vi1 = bgInPts[`${iNext},0`];
            const vfo0 = flangeOutPts[i], vfo1 = flangeOutPts[iNext];
            const vfi0 = flangeInPts[i], vfi1 = flangeInPts[iNext];

            const pO0 = getBgOutCoord(i, 0), pO1 = getBgOutCoord(iNext, 0);
            const pI0 = getBgInCoord(i, 0), pI1 = getBgInCoord(iNext, 0);
            const pFo0 = getFlangeOut(i), pFo1 = getFlangeOut(iNext);
            const pFi0 = getFlangeIn(i), pFi1 = getFlangeIn(iNext);

            // Flange outer wall
            bgFaces.push(sw.makeTriWithPts([vo0, vfo0, vfo1], pO0, pFo0, pFo1));
            bgFaces.push(sw.makeTriWithPts([vo0, vfo1, vo1], pO0, pFo1, pO1));
            // Flange bottom ring
            bgFaces.push(sw.makeTriWithPts([vfo0, vfi0, vfi1], pFo0, pFi0, pFi1));
            bgFaces.push(sw.makeTriWithPts([vfo0, vfi1, vfo1], pFo0, pFi1, pFo1));
            // Flange inner wall
            bgFaces.push(sw.makeTriWithPts([vfi0, vi0, vi1], pFi0, pI0, pI1));
            bgFaces.push(sw.makeTriWithPts([vfi0, vi1, vfi1], pFi0, pI1, pFi1));
        }
    } else {
        for (let i = 0; i < NW; i++) {
            const iNext = (i + 1) % NW;
            const o0 = getBgOutCoord(i, 0), o1 = getBgOutCoord(iNext, 0);
            const in0 = getBgInCoord(i, 0), in1 = getBgInCoord(iNext, 0);
            const vo0 = bgOutPts[`${i},0`], vo1 = bgOutPts[`${iNext},0`];
            const vi0 = bgInPts[`${i},0`], vi1 = bgInPts[`${iNext},0`];
            bgFaces.push(sw.makeTriWithPts([vo0, vi1, vo1], o0, in1, o1));
            bgFaces.push(sw.makeTriWithPts([vo0, vi0, vi1], o0, in0, in1));
        }
    }

    const bgShell = sw.allocId();
    const bgBrep = sw.allocId();
    sw.emit(`#${bgShell} = CLOSED_SHELL('',(${bgFaces.map(f => '#' + f).join(',')}));`);
    sw.emit(`#${bgBrep} = FACETED_BREP('Space_Background_Brep',#${bgShell});`);
    sw.registerComponent('Space_Background', bgBrep, styleBg);

    // =========================================================================
    // Component 2: Stars (Watertight circular prisms, yellow filament)
    // Each star is its own CLOSED_SHELL and FACETED_BREP (ISO 10303-42 compliant).
    // All stars are collected under the 'Stars' SHAPE_REPRESENTATION.
    // Outer face is flush with R_outer + 0.02mm (zero relief, smooth!).
    // Inner face reaches through the lithophane wall to R_outer - min_wall.
    // =========================================================================
    console.log('Generating Stars solid (Watertight circular dots)...');
    const nStarSides = 12;
    const rStarTop = OUTER_R + RELIEF + 0.020;
    const rStarBot = OUTER_R - MIN_WALL;
    const starBrepIds = [];

    for (let sIdx = 0; sIdx < stars.length; sIdx++) {
        const star = stars[sIdx];
        const { th: thC, z: zC, radMm: rStar } = star;
        const cTopPt = [rStarTop * Math.cos(thC), rStarTop * Math.sin(thC), zC];
        const cBotPt = [rStarBot * Math.cos(thC), rStarBot * Math.sin(thC), zC];
        const pidCt = sw.emitPoint(...cTopPt);
        const pidCb = sw.emitPoint(...cBotPt);

        const topPids = [], botPids = [];
        const topCoords = [], botCoords = [];

        for (let k = 0; k < nStarSides; k++) {
            const ang = (k / nStarSides) * 2 * Math.PI;
            const ds = rStar * Math.cos(ang);
            const dz = rStar * Math.sin(ang);
            const thK = thC + (ds / OUTER_R);
            const zK = zC + dz;
            const ptT = [rStarTop * Math.cos(thK), rStarTop * Math.sin(thK), zK];
            const ptB = [rStarBot * Math.cos(thK), rStarBot * Math.sin(thK), zK];
            topCoords.push(ptT);
            botCoords.push(ptB);
            topPids.push(sw.emitPoint(...ptT));
            botPids.push(sw.emitPoint(...ptB));
        }

        const thisStarFaces = [];
        for (let k = 0; k < nStarSides; k++) {
            const kn = (k + 1) % nStarSides;
            thisStarFaces.push(sw.makeTriWithPts([pidCt, topPids[k], topPids[kn]], cTopPt, topCoords[k], topCoords[kn]));
            thisStarFaces.push(sw.makeTriWithPts([pidCb, botPids[kn], botPids[k]], cBotPt, botCoords[kn], botCoords[k]));
            const p0 = botCoords[k], p1 = botCoords[kn], p2 = topCoords[kn], p3 = topCoords[k];
            thisStarFaces.push(sw.makeTriWithPts([botPids[k], botPids[kn], topPids[kn]], p0, p1, p2));
            thisStarFaces.push(sw.makeTriWithPts([botPids[k], topPids[kn], topPids[k]], p0, p2, p3));
        }

        const shellId = sw.allocId();
        const brepId = sw.allocId();
        sw.emit(`#${shellId} = CLOSED_SHELL('',(${thisStarFaces.map(f => '#' + f).join(',')}));`);
        sw.emit(`#${brepId} = FACETED_BREP('Star_${sIdx}',#${shellId});`);
        starBrepIds.push(brepId);
    }

    sw.registerComponent('Stars', starBrepIds, styleStars);

    // =========================================================================
    // Components 3 & 4: Inlaid Watertight Shells for Constellation_Lines & Index_Lines
    // Active cells: outer radius is flush at R_outer + delta (smooth, zero relief).
    // Inactive cells: recessed beneath the surface (hidden inside the background wall).
    // =========================================================================
    function buildInlaidComponent(name, mask, deltaSurf, styleId) {
        console.log(`Generating ${name} solid (Inlaid shell)...`);
        const rOutActive = OUTER_R + RELIEF + deltaSurf;
        const rInActive = OUTER_R - 0.50;
        const rOutInactive = OUTER_R - 0.15;
        const rInInactive = OUTER_R - 0.25;

        const rGridOut = Array.from({ length: NH + 1 }, (_, j) => {
            const rowIdx = Math.min(j, NH - 1);
            return Array.from({ length: NW }, (_, i) => mask[rowIdx][i] ? rOutActive : rOutInactive);
        });
        const rGridIn = Array.from({ length: NH + 1 }, (_, j) => {
            const rowIdx = Math.min(j, NH - 1);
            return Array.from({ length: NW }, (_, i) => mask[rowIdx][i] ? rInActive : rInInactive);
        });

        const outPts = {}, inPts = {};
        for (let j = 0; j <= NH; j++) {
            const z = (j / NH) * H_cyl;
            for (let i = 0; i < NW; i++) {
                const th = (i / NW) * 2 * Math.PI;
                const ro = rGridOut[j][i];
                const ri = rGridIn[j][i];
                outPts[`${i},${j}`] = sw.emitPoint(ro * Math.cos(th), ro * Math.sin(th), z);
                inPts[`${i},${j}`] = sw.emitPoint(ri * Math.cos(th), ri * Math.sin(th), z);
            }
        }

        const getOutC = (i, j) => {
            const th = (i / NW) * 2 * Math.PI;
            const z = (j / NH) * H_cyl;
            const ro = rGridOut[j][i % NW];
            return [ro * Math.cos(th), ro * Math.sin(th), z];
        };
        const getInC = (i, j) => {
            const th = (i / NW) * 2 * Math.PI;
            const z = (j / NH) * H_cyl;
            const ri = rGridIn[j][i % NW];
            return [ri * Math.cos(th), ri * Math.sin(th), z];
        };

        const faces = [];
        for (let j = 0; j < NH; j++) {
            for (let i = 0; i < NW; i++) {
                const iNext = (i + 1) % NW;
                const p00 = getOutC(i, j), p10 = getOutC(iNext, j);
                const p11 = getOutC(iNext, j + 1), p01 = getOutC(i, j + 1);
                const v00 = outPts[`${i},${j}`], v10 = outPts[`${iNext},${j}`];
                const v11 = outPts[`${iNext},${j + 1}`], v01 = outPts[`${i},${j + 1}`];
                faces.push(sw.makeTriWithPts([v00, v10, v11], p00, p10, p11));
                faces.push(sw.makeTriWithPts([v00, v11, v01], p00, p11, p01));
            }
        }

        for (let j = 0; j < NH; j++) {
            for (let i = 0; i < NW; i++) {
                const iNext = (i + 1) % NW;
                const p00 = getInC(i, j), p10 = getInC(iNext, j);
                const p11 = getInC(iNext, j + 1), p01 = getInC(i, j + 1);
                const v00 = inPts[`${i},${j}`], v10 = inPts[`${iNext},${j}`];
                const v11 = inPts[`${iNext},${j + 1}`], v01 = inPts[`${i},${j + 1}`];
                faces.push(sw.makeTriWithPts([v00, v11, v10], p00, p11, p10));
                faces.push(sw.makeTriWithPts([v00, v01, v11], p00, p01, p11));
            }
        }

        for (let i = 0; i < NW; i++) {
            const iNext = (i + 1) % NW;
            const o0 = getOutC(i, 0), o1 = getOutC(iNext, 0);
            const in0 = getInC(i, 0), in1 = getInC(iNext, 0);
            const vo0 = outPts[`${i},0`], vo1 = outPts[`${iNext},0`];
            const vi0 = inPts[`${i},0`], vi1 = inPts[`${iNext},0`];
            faces.push(sw.makeTriWithPts([vo0, vi1, vo1], o0, in1, o1));
            faces.push(sw.makeTriWithPts([vo0, vi0, vi1], o0, in0, in1));
        }

        for (let i = 0; i < NW; i++) {
            const iNext = (i + 1) % NW;
            const o0 = getOutC(i, NH), o1 = getOutC(iNext, NH);
            const in0 = getInC(i, NH), in1 = getInC(iNext, NH);
            const vo0 = outPts[`${i},${NH}`], vo1 = outPts[`${iNext},${NH}`];
            const vi0 = inPts[`${i},${NH}`], vi1 = inPts[`${iNext},${NH}`];
            faces.push(sw.makeTriWithPts([vo0, vo1, vi1], o0, o1, in1));
            faces.push(sw.makeTriWithPts([vo0, vi1, vi0], o0, in1, in0));
        }

        const shellId = sw.allocId();
        const brepId = sw.allocId();
        sw.emit(`#${shellId} = CLOSED_SHELL('',(${faces.map(f => '#' + f).join(',')}));`);
        sw.emit(`#${brepId} = FACETED_BREP('${name}_Brep',#${shellId});`);
        sw.registerComponent(name, brepId, styleId);
    }

    buildInlaidComponent('Constellation_Lines', linesMask, 0.010, styleLines);
    buildInlaidComponent('Index_Lines', indexMask, 0.015, styleIndex);

    const now = new Date().toISOString().replace(/\.\d+Z$/, '');
    const headerStr = [
        'ISO-10303-21;',
        'HEADER;',
        "FILE_DESCRIPTION(('Cylindrical Multicolor Lithophane Star Map Assembly'),'2;1');",
        `FILE_NAME('${path.basename(OUTPUT_FILE)}','${now}',('User'),('User'),'Processor','System','');`,
        "FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));",
        'ENDSEC;',
        'DATA;'
    ].join('\n') + '\n';

    console.log(`Writing ${OUTPUT_FILE}...`);
    const fd = fs.openSync(OUTPUT_FILE, 'w');
    fs.writeSync(fd, headerStr);
    for (const line of sw.lines) {
        fs.writeSync(fd, line + '\n');
    }
    fs.writeSync(fd, 'ENDSEC;\nEND-ISO-10303-21;\n');
    fs.closeSync(fd);

    const szMb = (fs.statSync(OUTPUT_FILE).size / (1024 * 1024)).toFixed(2);
    console.log('\n=== COMPLETE ===');
    console.log(`Output: ${OUTPUT_FILE} (${szMb} MB)`);
    console.log('Components: Space_Background, Stars, Constellation_Lines, Index_Lines');
    console.log(`Lithophane: Smooth exterior (R=${OUTER_R}mm), variable wall ${MIN_WALL}-${MAX_WALL}mm`);
    console.log('Ready for OrcaSlicer / Bambu Studio / PrusaSlicer multicolor printing.');
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
