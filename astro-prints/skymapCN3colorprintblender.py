import bpy

# --- CONFIG ---
image_path = "path/to/image0.thumb.jpeg.aa268959b09fe82e7febe723f0c3ff75.jpeg"
output_path = "path/to/star_map_3color.stl"

# --- STEP 1: Load image ---
img = bpy.data.images.load(image_path)

# --- STEP 2: Create base plane ---
bpy.ops.mesh.primitive_plane_add(size=200)
plane = bpy.context.active_object

# --- STEP 3: Separate color masks ---
# (Simplified: use compositor nodes for precise masking)
bpy.context.scene.use_nodes = True
nodes = bpy.context.scene.node_tree.nodes
links = bpy.context.scene.node_tree.links
nodes.clear()

img_node = nodes.new("CompositorNodeImage")
img_node.image = img
rgb_node = nodes.new("CompositorNodeSeparateRGB")

links.new(img_node.outputs["Image"], rgb_node.inputs["Image"])

# --- STEP 4: Create displacement modifiers ---
for color, depth in [("R", 1.5), ("G", 0.8), ("B", 0.0)]:
    tex = bpy.data.textures.new(f"{color}_mask", type='IMAGE')
    tex.image = img
    disp = plane.modifiers.new(f"Displace_{color}", type='DISPLACE')
    disp.texture = tex
    disp.strength = depth

# --- STEP 5: Apply modifiers and export ---
bpy.ops.object.modifier_apply(modifier="Displace_R")
bpy.ops.object.modifier_apply(modifier="Displace_G")
bpy.ops.object.modifier_apply(modifier="Displace_B")
bpy.ops.export_mesh.stl(filepath=output_path)
