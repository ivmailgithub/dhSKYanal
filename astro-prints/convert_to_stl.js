/**
 * Image to Multicolor Stepped Lithophane STL Converter - Improved version
 * 
 * Features:
 * - Even-height distribution of color levels (equal number of pixels per level)
 * - Vertical walls between different height regions for clean color separation
 * - Solid base and outer walls for strength
 * - Optimized geometry size
 */

const jimp = require('jimp');
const { Jimp, intToRGBA } = jimp;
const fs = require('fs');

// ===== CONFIGURATION =====
const INPUT_FILE = 'image0.thumb.jpeg.aa268959b09fe82e7febe723f0c3ff75.jpeg';
const OUTPUT_FILE = 'image0_lithophane.stl';

// Physical model dimensions (mm)
const MODEL_WIDTH_MM = 100;
const MODEL_HEIGHT_MM = 160;
const BASE_THICKNESS_MM = 1.2;
const MAX_RELIEF_MM = 3.5;
const WALL_THICKNESS_MM = 1.5;

// Number of discrete height/color levels
const NUM_COLOR_LEVELS = 5;

// Downsample to this target (width)
// Original is 472x750, we'll scale to ~120 wide for manageable geometry
const TARGET_WIDTH = 100;

// ===== IMPLEMENTATION =====

function writeSTL(triangles, outputPath) {
    let stl = 'solid lithophane\n';
    for (const tri of triangles) {
        const ux = tri[3] - tri[0], uy = tri[4] - tri[1], uz = tri[5] - tri[2];
        const vx = tri[6] - tri[0], vy = tri[7] - tri[1], vz = tri[8] - tri[2];
        const nx = uy * vz - uz * vy;
        const ny = uz * vx - ux * vz;
        const nz = ux * vy - uy * vx;
        const len = Math.sqrt(nx*nx + ny*ny + nz*nz) || 1;
        
        stl += `  facet normal ${(nx/len).toFixed(6)} ${(ny/len).toFixed(6)} ${(nz/len).toFixed(6)}\n`;
        stl += '    outer loop\n';
        stl += `      vertex ${tri[0].toFixed(4)} ${tri[1].toFixed(4)} ${tri[2].toFixed(4)}\n`;
        stl += `      vertex ${tri[3].toFixed(4)} ${tri[4].toFixed(4)} ${tri[5].toFixed(4)}\n`;
        stl += `      vertex ${tri[6].toFixed(4)} ${tri[7].toFixed(4)} ${tri[8].toFixed(4)}\n`;
        stl += '    endloop\n';
        stl += '  endfacet\n';
    }
    stl += 'endsolid lithophane\n';
    fs.writeFileSync(outputPath, stl, 'utf8');
    return triangles.length;
}

function addTriangle(triangles, v1, v2, v3) {
    triangles.push([...v1, ...v2, ...v3]);
}

function addQuad(triangles, v1, v2, v3, v4) {
    addTriangle(triangles, v1, v2, v3);
    addTriangle(triangles, v3, v2, v4);
}

function addVerticalQuad(triangles, x1, y1, x2, y2, zBottom, zTop) {
    // A vertical rectangle wall
    addQuad(triangles,
        [x1, y1, zBottom], [x2, y2, zBottom],
        [x1, y1, zTop], [x2, y2, zTop]);
}

// Check if heightMap[x][y] has a different level on any of its 4 sides
function hasDifferentNeighbor(heightMap, x, y, dsW, dsH) {
    if (x > 0 && heightMap[y][x-1] !== heightMap[y][x]) return true;
    if (x < dsW-1 && heightMap[y][x+1] !== heightMap[y][x]) return true;
    if (y > 0 && heightMap[y-1][x] !== heightMap[y][x]) return true;
    if (y < dsH-1 && heightMap[y+1][x] !== heightMap[y][x]) return true;
    return false;
}

async function main() {
    console.log('Reading image...');
    const img = await Jimp.read(INPUT_FILE);
    const origW = img.bitmap.width;
    const origH = img.bitmap.height;
    console.log(`Original image: ${origW}x${origH}`);

    // Calculate target dimensions preserving aspect ratio
    const aspect = origW / origH;
    const targetH = Math.round(TARGET_WIDTH / aspect);
    console.log(`Target resolution: ${TARGET_WIDTH}x${targetH}`);

    const downsampled = img.clone().resize({ w: TARGET_WIDTH, h: targetH });

    // Read pixel brightness
    const pixels = [];
    for (let y = 0; y < targetH; y++) {
        const row = [];
        for (let x = 0; x < TARGET_WIDTH; x++) {
            const c = intToRGBA(downsampled.getPixelColor(x, y));
            const brightness = 0.299 * c.r + 0.587 * c.g + 0.114 * c.b;
            row.push(brightness);
        }
        pixels.push(row);
    }

    // Sort all brightness values and divide into equal-sized groups
    const allNormalized = pixels.flat().sort((a, b) => a - b);
    const perLevel = Math.floor(allNormalized.length / NUM_COLOR_LEVELS);
    
    const thresholds = [];
    for (let i = 1; i < NUM_COLOR_LEVELS; i++) {
        thresholds.push(allNormalized[i * perLevel]);
    }
    console.log('Equal-count brightness thresholds:', thresholds.map(t => t.toFixed(1)));

    // Map pixels to levels
    const heightMap = [];
    for (let y = 0; y < targetH; y++) {
        const row = [];
        for (let x = 0; x < TARGET_WIDTH; x++) {
            const b = pixels[y][x];
            let level = 0;
            for (let t = 0; t < thresholds.length; t++) {
                if (b >= thresholds[t]) level = t + 1;
            }
            if (level >= NUM_COLOR_LEVELS) level = NUM_COLOR_LEVELS - 1;
            row.push(level);
        }
        heightMap.push(row);
    }

    // Stats
    const levelCounts = new Array(NUM_COLOR_LEVELS).fill(0);
    for (const row of heightMap) {
        for (const l of row) levelCounts[l]++;
    }
    console.log('Level distribution:', levelCounts.map((c, i) => `L${i}: ${c} (${(c*100/(TARGET_WIDTH*targetH)).toFixed(1)}%)`).join(', '));

    // Physical dimensions
    const scaleX = MODEL_WIDTH_MM / TARGET_WIDTH;
    const scaleY = MODEL_HEIGHT_MM / targetH;
    const modelW = TARGET_WIDTH * scaleX;
    const modelH = targetH * scaleY;

    // Height for each level - evenly spaced
    const levelHeights = [];
    for (let i = 0; i < NUM_COLOR_LEVELS; i++) {
        levelHeights.push(BASE_THICKNESS_MM + (i / (NUM_COLOR_LEVELS - 1)) * MAX_RELIEF_MM);
    }
    console.log('Level heights (mm):', levelHeights.map(h => h.toFixed(2)).join(', '));

    const triangles = [];

    // === TOP SURFACE (stepped) ===
    for (let y = 0; y < targetH - 1; y++) {
        for (let x = 0; x < TARGET_WIDTH - 1; x++) {
            const h00 = levelHeights[heightMap[y][x]];
            const h10 = levelHeights[heightMap[y][x + 1]];
            const h01 = levelHeights[heightMap[y + 1][x]];
            const h11 = levelHeights[heightMap[y + 1][x + 1]];

            const x0 = x * scaleX;
            const x1 = (x + 1) * scaleX;
            const y0 = y * scaleY;
            const y1 = (y + 1) * scaleY;

            // Top surface (all same level)
            if (h00 === h10 && h10 === h01 && h01 === h11) {
                addTriangle(triangles, [x0, y0, h00], [x1, y0, h00], [x0, y1, h00]);
                addTriangle(triangles, [x1, y0, h00], [x1, y1, h00], [x0, y1, h00]);
            } else {
                // Split into two triangles, each at their actual heights
                addTriangle(triangles, [x0, y0, h00], [x1, y0, h10], [x0, y1, h01]);
                addTriangle(triangles, [x1, y0, h10], [x1, y1, h11], [x0, y1, h01]);
            }
        }
    }

    // === VERTICAL WALLS between different height regions ===
    // Horizontal edges (between adjacent cells)
    for (let y = 0; y < targetH; y++) {
        for (let x = 0; x < TARGET_WIDTH - 1; x++) {
            const leftLevel = heightMap[y][x];
            const rightLevel = heightMap[y][x + 1];
            if (leftLevel !== rightLevel) {
                const hLeft = levelHeights[leftLevel];
                const hRight = levelHeights[rightLevel];
                const lowerH = Math.min(hLeft, hRight);
                const upperH = Math.max(hLeft, hRight);
                const xPos = (x + 1) * scaleX;
                const yPos0 = y * scaleY;
                const yPos1 = (y + 1) * scaleY;
                
                addVerticalQuad(triangles, xPos, yPos0, xPos, yPos1, lowerH, upperH);
            }
        }
    }

    // Vertical edges (between adjacent rows)
    for (let y = 0; y < targetH - 1; y++) {
        for (let x = 0; x < TARGET_WIDTH; x++) {
            const topLevel = heightMap[y][x];
            const bottomLevel = heightMap[y + 1][x];
            if (topLevel !== bottomLevel) {
                const hTop = levelHeights[topLevel];
                const hBottom = levelHeights[bottomLevel];
                const lowerH = Math.min(hTop, hBottom);
                const upperH = Math.max(hTop, hBottom);
                const xPos0 = x * scaleX;
                const xPos1 = (x + 1) * scaleX;
                const yPos = (y + 1) * scaleY;
                
                addVerticalQuad(triangles, xPos0, yPos, xPos1, yPos, lowerH, upperH);
            }
        }
    }

    // === OUTER PERIMETER WALLS (connect top surface down to base) ===
    // Top edge (y=0)
    for (let x = 0; x < TARGET_WIDTH; x++) {
        const h = levelHeights[heightMap[0][x]];
        if (h > BASE_THICKNESS_MM) {
            const x0 = x * scaleX;
            const x1 = (x + 1) * scaleX;
            addVerticalQuad(triangles, x0, 0, x1, 0, BASE_THICKNESS_MM, h);
        }
    }

    // Bottom edge (y=modelH)
    for (let x = 0; x < TARGET_WIDTH; x++) {
        const h = levelHeights[heightMap[targetH-1][x]];
        if (h > BASE_THICKNESS_MM) {
            const x0 = x * scaleX;
            const x1 = (x + 1) * scaleX;
            addVerticalQuad(triangles, x1, modelH, x0, modelH, BASE_THICKNESS_MM, h);
        }
    }

    // Left edge (x=0)
    for (let y = 0; y < targetH; y++) {
        const h = levelHeights[heightMap[y][0]];
        if (h > BASE_THICKNESS_MM) {
            const y0 = y * scaleY;
            const y1 = (y + 1) * scaleY;
            addVerticalQuad(triangles, 0, y0, 0, y1, BASE_THICKNESS_MM, h);
        }
    }

    // Right edge (x=modelW)
    for (let y = 0; y < targetH; y++) {
        const h = levelHeights[heightMap[y][TARGET_WIDTH-1]];
        if (h > BASE_THICKNESS_MM) {
            const y0 = y * scaleY;
            const y1 = (y + 1) * scaleY;
            addVerticalQuad(triangles, modelW, y0, modelW, y1, BASE_THICKNESS_MM, h);
        }
    }

    // === SOLID BASE ===
    // Bottom face
    addQuad(triangles,
        [0, 0, 0], [modelW, 0, 0],
        [0, modelH, 0], [modelW, modelH, 0]);

    // Base outer walls (from z=0 to z=BASE_THICKNESS_MM)
    addVerticalQuad(triangles, 0, 0, modelW, 0, 0, BASE_THICKNESS_MM);  // front
    addVerticalQuad(triangles, modelW, modelH, 0, modelH, 0, BASE_THICKNESS_MM);  // back
    addVerticalQuad(triangles, 0, 0, 0, modelH, 0, BASE_THICKNESS_MM);  // left
    addVerticalQuad(triangles, modelW, 0, modelW, modelH, 0, BASE_THICKNESS_MM);  // right

    // Write STL
    const numTriangles = writeSTL(triangles, OUTPUT_FILE);
    const fileSize = fs.statSync(OUTPUT_FILE).size;

    console.log(`\n=== Conversion Complete ===`);
    console.log(`Output: ${OUTPUT_FILE}`);
    console.log(`Triangles: ${numTriangles}`);
    console.log(`File size: ${(fileSize / 1024).toFixed(1)} KB`);
    console.log(`\nModel dimensions: ${modelW.toFixed(1)} x ${modelH.toFixed(1)} x ${(BASE_THICKNESS_MM + MAX_RELIEF_MM).toFixed(1)} mm`);
    console.log(`Base thickness: ${BASE_THICKNESS_MM} mm`);
    console.log(`Max relief: ${MAX_RELIEF_MM} mm`);
    console.log(`Color levels: ${NUM_COLOR_LEVELS}`);
    console.log(`\n=== Printing Instructions ===`);
    console.log(`For multicolor FDM printing, do filament changes at these heights:`);
    for (let i = 0; i < NUM_COLOR_LEVELS; i++) {
        const z = levelHeights[i];
        const layer = Math.round(z / 0.2);
        console.log(`  Color ${i}: z=${z.toFixed(2)} mm (layer ~${layer})`);
    }
    console.log(`\nPrint with 0.2mm layer height, no supports needed.`);
    console.log(`For best results, use a dark filament for the base (level 0) and`);
    console.log(`gradually lighter filaments for higher levels to create contrast.`);
    console.log(`Or use: Level 0=black, 1=dark blue, 2=blue, 3=light blue, 4=white`);
}

main().catch(e => { console.error(e); process.exit(1); });
