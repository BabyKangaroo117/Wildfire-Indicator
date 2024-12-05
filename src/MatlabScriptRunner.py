import subprocess
import sys
import os
import signal
import time

def cleanup_matlab():
    """Forcefully cleanup all MATLAB processes"""
    try:
        # Kill any MATLAB processes
        subprocess.run(['pkill', '-9', '-f', 'matlab'], check=False)
        # Kill any remaining GStreamer processes
        subprocess.run(['pkill', '-9', '-f', 'gst-launch'], check=False)
        # Small delay to ensure processes are killed
        time.sleep(1)
    except Exception as e:
        print(f"Cleanup error: {e}")

def signal_handler(sig, frame):
    print('\nShutting down...')
    cleanup_matlab()
    print('Cleanup complete. Exiting.')
    sys.exit(0)

def run_matlab_script():
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    matlab_path = "/usr/local/MATLAB/R2024b/bin/matlab"
    
    if not os.path.exists(matlab_path):
        print(f"Could not find MATLAB at {matlab_path}", file=sys.stderr)
        return False
    
    print(f"Found MATLAB at: {matlab_path}")
    print("Press Ctrl+C to exit at any time")
    
    matlab_cmd = ['sudo', matlab_path, '-nodisplay', '-nosplash', 
                  '-r', "try, run('smoke_detection.m'), catch ME, fprintf('Error: %s\\n', ME.message), end, quit"]
    
    process = None
    try:
        process = subprocess.Popen(
            matlab_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            preexec_fn=os.setsid,  # Create new process group
            env=dict(os.environ, MATLAB_JAVA='')
        )
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
                
    except KeyboardInterrupt:
        print("\nReceived interrupt signal...")
        cleanup_matlab()
        sys.exit(0)
    except Exception as e:
        print(f"Failed to run MATLAB script: {str(e)}", file=sys.stderr)
        if process:
            process.kill()
        return False
    finally:
        # Make absolutely sure everything is cleaned up
        cleanup_matlab()
        
    return True

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Script needs to be run with sudo privileges")
        print("Try running: sudo python matlab_runner.py")
        sys.exit(1)
        
    try:
        print("Starting MATLAB script...")
        success = run_matlab_script()
    except KeyboardInterrupt:
        print("\nExiting due to user interrupt...")
        cleanup_matlab()
    finally:
        print("Script terminated.")
