import subprocess
import sys
import os
import socket

def run(cmd, cwd=None):
    """Run shell commands and print them"""
    print(f"Running: '{' '.join(cmd)}'...")
    subprocess.run(cmd, check=True, cwd=cwd)

def install_requirements():
    print("Installing Python dependencies from requirements.txt...")
    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def install_playwright():
    print("Installing Playwright and browser dependencies...")
    run([sys.executable, "-m", "pip", "install", "playwright"])
    run(["playwright", "install"])
    
    # The next step requires root privileges
    if os.geteuid() == 0:
        print("🔧 Installing Playwright system dependencies (requires root)...")
        run(["playwright", "install-deps"])
    else:
        print("⚠️ 'playwright install-deps' was skipped (not root).")
        print("Please run manually:")
        print("sudo playwright install-deps")

def init_rag():
    print("Initializing vector stores for RAG...")
    run([sys.executable, "init_rag.py"])

if __name__ == "__main__":
    try:
        install_requirements()
        install_playwright()
        init_rag()
        print("Setup successfully completed!")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"Setup failed: {e}")
        sys.exit(1)
    except socket.gaierror:
        print("Internet unavailable. Check your connection!")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
