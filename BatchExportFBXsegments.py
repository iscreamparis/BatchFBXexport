import csc
import os
import sys

def command_name():
    return "Batch Export FBX Segments"

def run(scene):             
    # Read config file
    config_path = "G:\\Mon Drive\\scripts\\BatchFBXexport\\export_config.txt"
    with open(config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    casc_path = lines[0].strip()
    export_dir = lines[1].strip()
    
    # Ensure paths are properly formatted - Fix Windows path handling
    casc_path = os.path.normpath(casc_path)  # Important: Use normpath not abspath
    export_dir = os.path.normpath(export_dir)
    
    start_frame = int(lines[2].strip())
    end_frame = int(lines[3].strip())
    segment_index = int(lines[4].strip()) if len(lines) > 4 else 0
    
    # Extract base path and name
    base_path = os.path.splitext(casc_path)[0]
    base_name = os.path.basename(base_path)
    
    # Ensure export dir exists
    os.makedirs(export_dir, exist_ok=True)

    # Get application managers
    app = csc.app.get_application()
    scene_manager = app.get_scene_manager()
    ds_manager = app.get_data_source_manager()
    tools_manager = app.get_tools_manager()
    
    # Create scene
    application_scene = scene_manager.create_application_scene()
    scene_manager.set_current_scene(application_scene)
    
    # Load CASC file
    ds_manager.load_scene(casc_path)
    
    # Create filename
    if segment_index == -1:  # Special case for full interval
        fbx_name = f"{base_name}_FULL.fbx"
    else:
        fbx_name = f"{base_name}_{segment_index:02d}.fbx"
    
    # Ensure proper path handling for files with spaces
    fbx_path = os.path.join(export_dir, fbx_name)
    
    # Define the frame selection function - Using the working version from backup
    def mod(model, update, scene, session):
        try:
            # Select the required time range
            ls = session.take_layers_selector()
            layers_with_ids = model.layers_selector()
            selected_layer_ids = layers_with_ids.all_included_layer_ids()
            
            # Make sure we're using the correct selection method for the export_scene approach
            ls.set_full_selection_by_parts(selected_layer_ids, start_frame, end_frame)
            
            # Set the current frame to be within our selected range to ensure proper export
            current_frame = max(start_frame, min(end_frame, (start_frame + end_frame) // 2))
            model.go_to_frame(current_frame)
        except Exception:
            # Silently catch errors to avoid crashing
            pass
    
    # Apply the frame selection
    application_scene.domain_scene().modify_with_session('Set frame range', mod)
    
    # Export the FBX file - WITH FALLBACK MECHANISM
    fbx_scene_loader = tools_manager.get_tool("FbxSceneLoader")
    fbx_loader = fbx_scene_loader.get_fbx_loader(application_scene)
    
    try:
        # First try the original method that was working
        fbx_loader.export_scene_selected_frames(fbx_path)
    except Exception:
        # Fall back to the general export method if the specific one fails
        fbx_loader.export_scene(fbx_path)