import os
import sys
import subprocess
import time
import signal

# Simple print function to replace logging
def print_with_timestamp(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}"
    print(formatted_msg)

def main():
    print_with_timestamp("Starting export_all_segments.py")

    # Get the path to this script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to Cascadeur executable (can be overridden by command line arg)
    cascadeur_path = "C:\\Program Files\\Cascadeur\\cascadeur.exe"
    if len(sys.argv) > 1:
        cascadeur_path = sys.argv[1]
    
    # Configuration options
    SKIP_EXISTING = True  # Skip segments that already have FBX files
    PROCESS_TIMEOUT = 120  # Maximum seconds to wait for Cascadeur (2 minutes)
    
    # Read config file to get CASC file and export directory
    config_path = os.path.join(script_dir, "export_config.txt")
    with open(config_path, 'r') as f:
        lines = f.readlines()
        
    if len(lines) < 2:
        print_with_timestamp("Error: Config file must contain at least 2 lines (casc_path and export_dir)")
        return
        
    casc_path = lines[0].strip()
    export_dir = lines[1].strip()
    print_with_timestamp(f"Processing CASC: {casc_path}")
    print_with_timestamp(f"Export dir: {export_dir}")
    
    # Check if CASC file exists
    if not os.path.exists(casc_path):
        print_with_timestamp(f"Error: CASC file not found: {casc_path}")
        return
    
    # Get keyframes from TXT file
    txt_path = os.path.splitext(casc_path)[0] + ".txt"
    if not os.path.exists(txt_path):
        print_with_timestamp(f"Error: TXT file not found: {txt_path}")
        return
    
    frames = []
    with open(txt_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and line.split()[0].isdigit():
                frames.append(int(line.split()[0]))
    print_with_timestamp(f"Found frames: {frames}")
    
    if len(frames) < 2:
        print_with_timestamp("Error: Not enough frames found")
        return
    
    # Create intervals
    intervals = []
    for i in range(len(frames) - 1):
        intervals.append((frames[i], frames[i+1] - 1, i+1))  # start, end, index
    
    # Add full range
    full_interval = (frames[0], frames[-1] - 1, -1)  # -1 indicates full interval
    intervals.append(full_interval)
    
    print_with_timestamp(f"Created {len(intervals)} intervals to export")
    
    # Process each interval one at a time
    for start_frame, end_frame, segment_index in intervals:
        if segment_index == -1:
            print_with_timestamp(f"Processing FULL interval: frames {start_frame}-{end_frame}")
            fbx_name = f"{os.path.basename(os.path.splitext(casc_path)[0])}_FULL.fbx"
        else:
            print_with_timestamp(f"Processing interval {segment_index}: frames {start_frame}-{end_frame}")
            fbx_name = f"{os.path.basename(os.path.splitext(casc_path)[0])}_{segment_index:02d}.fbx"
        
        # Check if output file already exists
        output_fbx = os.path.join(export_dir, fbx_name)
        if SKIP_EXISTING and os.path.exists(output_fbx):
            print_with_timestamp(f"Skipping - FBX file already exists: {output_fbx}")
            continue
        
        # Update config file with current interval info
        with open(config_path, 'w') as f:
            f.write(f"{casc_path}\n")
            f.write(f"{export_dir}\n")
            f.write(f"{start_frame}\n")
            f.write(f"{end_frame}\n")
            f.write(f"{segment_index}\n")
        
        # Call Cascadeur with command line 
        cmd = [cascadeur_path, "--run-script", "commands.BatchExportFBXsegments"]
        print_with_timestamp(f"Executing: {' '.join(cmd)}")
        
        # Start the process
        process = subprocess.Popen(cmd)
        
        # Wait with timeout
        start_time = time.time()
        while process.poll() is None:
            elapsed = time.time() - start_time
            if elapsed > PROCESS_TIMEOUT:
                print_with_timestamp(f"Process timed out after {PROCESS_TIMEOUT} seconds")
                # Terminate the process gracefully
                if os.name == 'nt':  # Windows
                    process.terminate()
                else:  # Unix-like
                    os.kill(process.pid, signal.SIGTERM)
                time.sleep(2)  # Give it time to terminate
                if process.poll() is None:  # If still running
                    print_with_timestamp("Force killing process...")
                    if os.name == 'nt':
                        process.kill()
                    else:
                        os.kill(process.pid, signal.SIGKILL)
                break
            time.sleep(1)  # Check every second
        
        # Check return code
        if process.returncode is not None:
            if process.returncode == 0:
                print_with_timestamp(f"Cascadeur process completed successfully")
            else:
                print_with_timestamp(f"Cascadeur process completed with error code: {process.returncode}")
        else:
            print_with_timestamp("Cascadeur process was terminated due to timeout")
        
        # Verify if the file was created
        if os.path.exists(output_fbx):
            print_with_timestamp(f"Success! FBX file created: {fbx_name}")
        else:
            print_with_timestamp(f"Error: FBX file was not created: {fbx_name}")
        
        # Wait a moment before starting the next process
        time.sleep(2)
    
    print_with_timestamp("All intervals have been processed")

if __name__ == "__main__":
    main()
