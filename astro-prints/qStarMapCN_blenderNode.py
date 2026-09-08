import bpy
import math

# --- CONFIG ---
image_path = "path/to/image0.thumb.jpeg.aa268959b09fe82e7febe723f0c3ff75.jpeg"
output_path = "path/to/star_map_3color_cylindrical.stl"

# Cylinder parameters
radius = 100      # mm
height_scale = 1.0  # vertical scaling factor

# --- STEP 1: Load image ---
img = bpy.data.images.load(image_path)

# --- STEP 2: Create base plane ---
bpy.ops.mesh.primitive_plane_add(size=200)
plane = bpy.context.active_object

# --- STEP 3: Separate color channels ---
bpy.context.scene.use_nodes = True
nodes = bpy.context.scene.node_tree.nodes
links = bpy.context.scene.node_tree.links
nodes.clear()

img_node = nodes.new("CompositorNodeImage")
img_node.image = img
rgb_node = nodes.new("CompositorNodeSeparateRGB")
links.new(img_node.outputs["Image"], rgb_node.inputs["Image"])

# --- STEP 4: Apply displacement for each color ---
for color, depth in [("R", 1.5), ("G", 0.8), ("B", 0.0)]:
    tex = bpy.data.textures.new(f"{color}_mask", type='IMAGE')
    tex.image = img
    disp = plane.modifiers.new(f"Displace_{color}", type='DISPLACE')
    disp.texture = tex
    disp.strength = depth

# Apply modifiers
for mod in plane.modifiers:
    bpy.ops.object.modifier_apply(modifier=mod.name)

# --- STEP 5: Cylindrical projection ---
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.uv_texture_add()
bpy.ops.object.mode_set(mode='OBJECT')

# Convert plane vertices to cylindrical coordinates
import mathutils
for v in plane.data.vertices:
    x, y, z = v.co
    theta = (x / 200.0) * 2 * math.pi
    v.co.x = radius * math.cos(theta)
    v.co.y = radius * math.sin(theta)
    v.co.z = y * height_scale

# --- STEP 6: Export STL ---
bpy.ops.export_mesh.stl(filepath=output_path)
