import bpy
import os
import sys

# Get script directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Get FBX file path from command line arguments
if "--" in sys.argv:
    argv = sys.argv[sys.argv.index("--") + 1:]
    fbx_path = argv[0] if len(argv) > 0 else None
else:
    fbx_path = None

if not fbx_path or not os.path.isfile(fbx_path):
    print(f"Error: Invalid FBX file path: {fbx_path}")
    sys.exit(1)

print(f"Processing FBX file: {fbx_path}")

def setup_scene():
    """Set up a basic scene with an armature"""
    print("Setting up scene")
    # Clear existing scene
    
    # Create a simple armature
    bpy.ops.object.armature_add()
    armature = bpy.context.active_object
    armature.name = "BaseArmature"
    
    # Setup render settings
    scene = bpy.context.scene
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    
    return armature

def import_and_render_fbx(fbx_path):
    """Import an FBX file and render to MP4"""
    # Create fresh scene
    base_armature = setup_scene()
    
    # Ensure path is absolute and valid
    abs_fbx_path = os.path.abspath(fbx_path)
    
    print(f"Importing FBX file: {abs_fbx_path}")
    
    # Import FBX
    preset_used = False
    try:
        print("Attempting to use CASCADEUR preset")
        bpy.ops.import_scene.fbx(
            filepath=abs_fbx_path,
            use_preset=True,
            preset_name="CASCADEUR"
        )
        preset_used = True
        print("Successfully used CASCADEUR preset for import")
    except:
        print("CASCADEUR preset not found or failed")
        print("Falling back to explicit FBX import settings")
    
    # If preset failed, use explicit settings
    if not preset_used:
        bpy.ops.import_scene.fbx(
            filepath=abs_fbx_path,
            use_manual_orientation=True,
            global_scale=1.0,
            bake_space_transform=False,
            use_custom_normals=True,
            colors_type='SRGB',
            use_image_search=True,
            use_alpha_decals=False,
            decal_offset=0.0,
            use_anim=True,
            anim_offset=1.0,
            use_subsurf=False,
            use_custom_props=True,
            use_custom_props_enum_as_string=True,
            ignore_leaf_bones=False,
            force_connect_children=False,
            automatic_bone_orientation=True,
            primary_bone_axis='Y',                
            secondary_bone_axis='X',
            use_prepost_rot=False,
            axis_forward='Y',
            axis_up='Z'
        )
    
    print("FBX import successful")
    
    # Find imported armature(s)
    imported_armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE' and obj != base_armature]
    
    if not imported_armatures:
        print(f"No armature found in {fbx_path}")
        return False
    
    # Use the first imported armature
    imported_armature = imported_armatures[0]
    print(f"Found imported armature: {imported_armature.name}")
    
    # Set animation frame range
    scene = bpy.context.scene
    frame_start = 9999
    frame_end = 0
    
    # Determine animation length from actions
    if len(bpy.data.actions) == 0:
        print("No actions found in the imported file")
    
    for action in bpy.data.actions:
        print(f"Found action: {action.name} with range {action.frame_range}")
        if action.frame_range[0] < frame_start:
            frame_start = action.frame_range[0]
        if action.frame_range[1] > frame_end:
            frame_end = action.frame_range[1]
    
    if frame_end > 0:
        scene.frame_start = max(1, int(frame_start))
        scene.frame_end = int(frame_end)
        print(f"Animation range: {scene.frame_start} - {scene.frame_end}")
    else:
        print(f"No animation found in {fbx_path}")
        return False
    
    # Set output path
    output_path = os.path.splitext(fbx_path)[0] + ".mp4"
    scene.render.filepath = output_path
    print(f"Output path: {output_path}")
    
    # Set imported armature as active for rendering
    bpy.ops.object.select_all(action='DESELECT')
    imported_armature.select_set(True)
    bpy.context.view_layer.objects.active = imported_armature
    
    # Set up a basic material if needed
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            if len(obj.material_slots) == 0:
                mat = bpy.data.materials.new(name="BasicMaterial")
                if hasattr(mat, 'use_nodes'):
                    mat.use_nodes = True
                obj.data.materials.append(mat)
    
    # Render animation
    print(f"Starting render: {os.path.basename(fbx_path)} from frame {scene.frame_start} to {scene.frame_end}")
    bpy.ops.render.render(animation=True)
    print(f"Finished rendering: {os.path.basename(output_path)}")
    return True

# Main execution
import_and_render_fbx(fbx_path)
