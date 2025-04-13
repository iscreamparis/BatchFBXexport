import os
import sys
import subprocess
import time
import signal

# Log to file with timestamp preserved
def log(message, overwrite=False):
    try:
        # Get timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        
        # Base log path
        log_path = "G:\\Mon Drive\\scripts\\BatchFBXexport\\orchestrator_log.txt"
        
        # Create a session-specific log path using the start time
        if not hasattr(log, "session_log"):
            start_time = time.strftime("%Y%m%d_%H%M%S")
            log_dir = os.path.dirname(log_path)
            log.session_log = os.path.join(log_dir, f"orchestrator_log_{start_time}.txt")
        
        # Write to main log
        mode = "w" if overwrite else "a"
        with open(log_path, mode) as f:
            f.write(formatted_msg + "\n")
            
        # Write to session log
        with open(log.session_log, "a") as f:
            f.write(formatted_msg + "\n")
            
        print(formatted_msg)
        
    except Exception as e:
        print(f"Error writing to log: {str(e)}")

def main():
    # Clear log file
    log("Starting export_all_segments.py", overwrite=True)

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
    try:
        with open(config_path, 'r') as f:
            lines = f.readlines()
            
        if len(lines) < 2:
            log("Error: Config file must contain at least 2 lines (casc_path and export_dir)")
            return
            
        casc_path = lines[0].strip()
        export_dir = lines[1].strip()
        log(f"Processing CASC: {casc_path}")
        log(f"Export dir: {export_dir}")
    except Exception as e:
        log(f"Error reading config: {str(e)}")
        return
    
    # Check if CASC file exists
    if not os.path.exists(casc_path):
        log(f"Error: CASC file not found: {casc_path}")
        return
    
    # Get keyframes from TXT file
    txt_path = os.path.splitext(casc_path)[0] + ".txt"
    if not os.path.exists(txt_path):
        log(f"Error: TXT file not found: {txt_path}")
        return
    
    frames = []
    try:
        with open(txt_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and line.split()[0].isdigit():
                    frames.append(int(line.split()[0]))
        log(f"Found frames: {frames}")
    except Exception as e:
        log(f"Error reading TXT file: {str(e)}")
        return
    
    if len(frames) < 2:
        log("Error: Not enough frames found")
        return
    
    # Create intervals
    intervals = []
    for i in range(len(frames) - 1):
        intervals.append((frames[i], frames[i+1] - 1, i+1))  # start, end, index
    
    # Add full range
    full_interval = (frames[0], frames[-1] - 1, -1)  # -1 indicates full interval
    intervals.append(full_interval)
    
    log(f"Created {len(intervals)} intervals to export")
    
    # Process each interval one at a time
    for start_frame, end_frame, segment_index in intervals:
        if segment_index == -1:
            log(f"Processing FULL interval: frames {start_frame}-{end_frame}")
            fbx_name = f"{os.path.basename(os.path.splitext(casc_path)[0])}_FULL.fbx"
        else:
            log(f"Processing interval {segment_index}: frames {start_frame}-{end_frame}")
            fbx_name = f"{os.path.basename(os.path.splitext(casc_path)[0])}_{segment_index:02d}.fbx"
        
        # Check if output file already exists
        output_fbx = os.path.join(export_dir, fbx_name)
        if SKIP_EXISTING and os.path.exists(output_fbx):
            log(f"Skipping - FBX file already exists: {output_fbx}")
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
        log(f"Executing: {' '.join(cmd)}")
        
        try:
            # Start the process
            process = subprocess.Popen(cmd)
            
            # Wait with timeout
            start_time = time.time()
            while process.poll() is None:
                elapsed = time.time() - start_time
                if elapsed > PROCESS_TIMEOUT:
                    log(f"Process timed out after {PROCESS_TIMEOUT} seconds")
                    # Try to terminate the process gracefully
                    try:
                        log("Attempting to terminate the Cascadeur process...")
                        if os.name == 'nt':  # Windows
                            process.terminate()
                        else:  # Unix-like
                            os.kill(process.pid, signal.SIGTERM)
                        time.sleep(2)  # Give it time to terminate
                        if process.poll() is None:  # If still running
                            log("Force killing process...")
                            if os.name == 'nt':
                                process.kill()
                            else:
                                os.kill(process.pid, signal.SIGKILL)
                    except Exception as term_error:
                        log(f"Error terminating process: {term_error}")
                    break
                time.sleep(1)  # Check every second
            
            # Check return code
            if process.returncode is not None:
                if process.returncode == 0:
                    log(f"Cascadeur process completed successfully")
                else:
                    log(f"Cascadeur process completed with error code: {process.returncode}")
            else:
                log("Cascadeur process was terminated due to timeout")
            
            # Verify if the file was created
            if os.path.exists(output_fbx):
                log(f"Success! FBX file created: {fbx_name}")
            else:
                log(f"Error: FBX file was not created: {fbx_name}")
            
            # Wait a moment before starting the next process
            time.sleep(2)
            
        except KeyboardInterrupt:
            log("Process interrupted by user. Attempting clean shutdown...")
            try:
                if process and process.poll() is None:
                    process.terminate()
                    time.sleep(2)
                    if process.poll() is None:
                        process.kill()
            except Exception as ke:
                log(f"Error during cleanup: {ke}")
            return
        except Exception as e:
            log(f"Error running Cascadeur: {str(e)}")
            continue
    
    log("All intervals have been processed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
    except Exception as e:
        print(f"Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
