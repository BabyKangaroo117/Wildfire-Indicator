import subprocess
import sys
import os
import signal
import time
from typing import Optional

class MatlabRunner:
    def __init__(self, matlab_path: str = "/usr/local/MATLAB/R2024b/bin/matlab"):
        """Initialize the MATLAB runner with configurable path"""
        self.matlab_path = matlab_path
        self.process: Optional[subprocess.Popen] = None
        

    def cleanup_matlab(self) -> None:
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

    def _signal_handler(self, sig: int, frame) -> None:
        """Handle interrupt signals"""
        print('\nShutting down...')
        self.cleanup_matlab()
        print('Cleanup complete. Exiting.')
        sys.exit(0)

    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        # Check for sudo privileges
        if os.geteuid() != 0:
            print("Script needs to be run with sudo privileges")
            print("Try running: sudo python matlab_runner.py")
            return False

        # Check if MATLAB exists
        if not os.path.exists(self.matlab_path):
            print(f"Could not find MATLAB at {self.matlab_path}", file=sys.stderr)
            return False

        return True

    def run_script(self, script_name: str = 'smoke_detection.m') -> bool:
        """Run the specified MATLAB script"""
        if not self.check_prerequisites():
            return False

        print(f"Found MATLAB at: {self.matlab_path}")
        print("Press Ctrl+C to exit at any time")

        matlab_cmd = [
            'sudo',
            self.matlab_path,
            '-nodisplay',
            '-nosplash',
            '-r',
            f"try, run('{script_name}'), catch ME, fprintf('Error: %s\\n', ME.message), end, quit"
        ]

        try:
            self.process = subprocess.Popen(
                matlab_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                preexec_fn=os.setsid,  # Create new process group
                env=dict(os.environ, MATLAB_JAVA='')
            )

            while True:
                output = self.process.stdout.readline()
                if output == '' and self.process.poll() is not None:
                    break
                if output:
                    print(output.strip())

        except KeyboardInterrupt:
            print("\nReceived interrupt signal...")
            self.cleanup_matlab()
            sys.exit(0)
        except Exception as e:
            print(f"Failed to run MATLAB script: {str(e)}", file=sys.stderr)
            if self.process:
                self.process.kill()
            return False
        finally:
            # Make absolutely sure everything is cleaned up
            self.cleanup_matlab()

        return True

def main():
    """Main function to demonstrate usage"""
    runner = MatlabRunner()
    
    try:
        print("Starting MATLAB script...")
        success = runner.run_script()
    except KeyboardInterrupt:
        print("\nExiting due to user interrupt...")
        runner.cleanup_matlab()
    finally:
        print("Script terminated.")

if __name__ == "__main__":
    main()
