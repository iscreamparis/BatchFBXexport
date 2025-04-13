import bpy
import os
import sys
import traceback

# Function to log messages to file
def log(message):
    with open("G:\\Mon Drive\\scripts\\BatchFBXexport\\blender_log.txt", "a") as f:
        f.write(str(message) + "\n")
    print(message)

# Clear log for this file
def clear_log():
    with open("G:\\Mon Drive\\scripts\\BatchFBXexport\\blender_log.txt", "w") as f:
        f.write("Starting Blender render process for single FBX\n")

clear_log()
log(f"Python version: {sys.version}")
log(f"Blender version: {bpy.app.version_string}")

# Get FBX file path from command line arguments
if "--" in sys.argv:
    argv = sys.argv[sys.argv.index("--") + 1:]
    fbx_path = argv[0] if len(argv) > 0 else None
else:
    fbx_path = None

if not fbx_path or not os.path.isfile(fbx_path):
    log(f"Error: Invalid FBX file path: {fbx_path}")
    sys.exit(1)

log(f"Processing FBX file: {fbx_path}")

def setup_scene():
    """Set up a basic scene with an armature"""
    try:
        log("Setting up scene")
        # Clear existing scene
        #bpy.ops.wm.read_factory_settings(use_empty=True)
        
        # Create a simple armature
        bpy.ops.object.armature_add()
        armature = bpy.context.active_object
        armature.name = "BaseArmature"
        log("Created base armature")
        
        # Add a camera
        #bpy.ops.object.camera_add(location=(0, -5, 1), rotation=(1.57, 0, 0))
        #camera = bpy.context.active_object
        #bpy.context.scene.camera = camera
        
        # Add a light
        #bpy.ops.object.light_add(type='SUN', location=(0, 0, 5))
        
        # Setup render settings
        scene = bpy.context.scene
        scene.render.image_settings.file_format = 'FFMPEG'
        scene.render.ffmpeg.format = 'MPEG4'
        scene.render.ffmpeg.codec = 'H264'
        scene.render.resolution_x = 1280  # Reduced resolution for faster rendering
        scene.render.resolution_y = 720
        
        return armature
    except Exception as e:
        log(f"ERROR in setup_scene: {e}")
        traceback.print_exc()
        return None

def import_and_render_fbx(fbx_path):
    """Import an FBX file and render to MP4"""
    try:
        # Create fresh scene
        base_armature = setup_scene()
        if base_armature is None:
            log("ERROR: Failed to set up scene")
            return False
        
        # Ensure path is absolute and valid
        abs_fbx_path = os.path.abspath(fbx_path)
        if not os.path.exists(abs_fbx_path):
            log(f"ERROR: FBX file does not exist: {abs_fbx_path}")
            return False
            
        log(f"Importing FBX file: {abs_fbx_path}")
        
        # Import FBX with error handling
        try:
            # First try to use the CASCADEUR preset
            preset_used = False
            try:
                log("Attempting to use CASCADEUR preset")
                bpy.ops.import_scene.fbx(
                    filepath=abs_fbx_path,
                    use_preset=True,
                    preset_name="CASCADEUR"
                )
                preset_used = True
                log("Successfully used CASCADEUR preset for import")
            except Exception as preset_error:
                log(f"CASCADEUR preset not found or failed: {preset_error}")
                log("Falling back to explicit FBX import settings")
                
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
                
            log("FBX import successful")
        except Exception as import_error:
            log(f"ERROR importing FBX: {import_error}")
            traceback.print_exc()
            return False
        
        # Find imported armature(s)
        imported_armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE' and obj != base_armature]
        
        if not imported_armatures:
            log(f"No armature found in {fbx_path}")
            return False
        
        # Use the first imported armature
        imported_armature = imported_armatures[0]
        log(f"Found imported armature: {imported_armature.name}")
        
        # Set animation frame range
        scene = bpy.context.scene
        frame_start = 9999
        frame_end = 0
        
        # Determine animation length from actions
        if len(bpy.data.actions) == 0:
            log("No actions found in the imported file")
        
        for action in bpy.data.actions:
            log(f"Found action: {action.name} with range {action.frame_range}")
            if action.frame_range[0] < frame_start:
                frame_start = action.frame_range[0]
            if action.frame_range[1] > frame_end:
                frame_end = action.frame_range[1]
        
        if frame_end > 0:
            scene.frame_start = max(1, int(frame_start))
            scene.frame_end = int(frame_end)
            log(f"Animation range: {scene.frame_start} - {scene.frame_end}")
        else:
            log(f"No animation found in {fbx_path}")
            return False
        
        # Set output path
        output_path = os.path.splitext(fbx_path)[0] + ".mp4"
        scene.render.filepath = output_path
        log(f"Output path: {output_path}")
        
        # Set imported armature as active for rendering
        try:
            bpy.ops.object.select_all(action='DESELECT')
            imported_armature.select_set(True)
            bpy.context.view_layer.objects.active = imported_armature
        except Exception as e:
            log(f"ERROR setting active object: {e}")
            traceback.print_exc()
        
        # Set up a basic material if needed
        try:
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    if len(obj.material_slots) == 0:
                        mat = bpy.data.materials.new(name="BasicMaterial")
                        if hasattr(mat, 'use_nodes'):
                            mat.use_nodes = True
                        obj.data.materials.append(mat)
        except Exception as e:
            log(f"ERROR setting up materials: {e}")
            # Continue anyway, not critical
        
        # Render animation
        log(f"Starting render: {os.path.basename(fbx_path)} from frame {scene.frame_start} to {scene.frame_end}")
        try:
            bpy.ops.render.render(animation=True)
            log(f"Finished rendering: {os.path.basename(output_path)}")
            return True
        except Exception as render_error:
            log(f"ERROR during rendering: {render_error}")
            traceback.print_exc()
            return False
            
    except Exception as e:
        log(f"ERROR in import_and_render_fbx: {e}")
        traceback.print_exc()
        return False

# Main execution
try:
    import_and_render_fbx(fbx_path)
except Exception as e:
    log(f"Unhandled exception: {e}")
    traceback.print_exc()
    sys.exit(1)
