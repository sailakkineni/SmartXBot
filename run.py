import os
import sys
import subprocess

def main():
    """Launcher script to run the Streamlit frontend application."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(project_root, "frontend", "app.py")
    
    cmd = [sys.executable, "-m", "streamlit", "run", app_path]
    print(f"🚀 Launching SmartXBot from frontend/app.py...")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nApplication stopped.")

if __name__ == "__main__":
    main()
