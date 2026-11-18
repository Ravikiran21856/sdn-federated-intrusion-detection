"""
AEGISNET 1-Click Interactive Demonstration & College Defense Suite.
Launches the PyTorch REST server and opens the real-time glassmorphism web console.
"""

import sys
import os
import time
import subprocess
import webbrowser
import threading
import urllib.request

BANNER = r"""
================================================================================
     _    _____ ____ ___ ____  _   _ _____ _____ 
    / \  | ____/ ___|_ _/ ___|| \ | | ____|_   _|
   / _ \ |  _|| |  _ | |\___ \|  \| |  _|   | |  
  / ___ \| |__| |_| || | ___) | |\  | |___  | |  
 /_/   \_\_____\____|___|____/|_| \_|_____| |_|  
================================================================================
   FEDERATED ZERO-DAY INTRUSION DETECTION & SDN DEFENSE MATRIX (CORE v2.4)
================================================================================
"""

def check_environment():
    print("[+] Checking environment dependencies...")
    try:
        import torch
        import numpy
        import sklearn
        import matplotlib
        import joblib
        print(f"    [OK] Python {sys.version.split()[0]}")
        print(f"    [OK] PyTorch {torch.__version__} (CUDA Available: {torch.cuda.is_available()})")
        print(f"    [OK] NumPy {numpy.__version__}")
        print(f"    [OK] Scikit-Learn {sklearn.__version__}")
        return True
    except ImportError as e:
        print(f"    [!] Missing dependency: {e}")
        print("    [!] Run: pip install torch numpy scikit-learn matplotlib joblib")
        return False

def start_server_daemon(port=8080):
    script_path = os.path.join(os.path.dirname(__file__), "web", "app.py")
    cmd = [sys.executable, script_path, str(port)]
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return process

def wait_for_server(port=8080, timeout=10):
    url = f"http://127.0.0.1:{port}/"
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False

def main():
    print(BANNER)
    if not check_environment():
        input("\nPress Enter to exit...")
        sys.exit(1)

    port = 8080
    print(f"\n[+] Starting AEGISNET SDN Controller & Backend Server on port {port}...")
    server_process = start_server_daemon(port)

    if wait_for_server(port):
        print(f"    [SUCCESS] Server online at: http://127.0.0.1:{port}/")
    else:
        print("    [!] Warning: Server startup taking longer than expected. Proceeding...")

    dashboard_url = f"http://127.0.0.1:{port}/"
    print(f"[+] Launching Cyber Defense Console in browser: {dashboard_url}")
    webbrowser.open(dashboard_url)

    print("\n" + "=" * 80)
    print("                    COLLEGE PROJECT DEMO CONTROLS")
    print("=" * 80)
    print("  * Dashboard URL     : http://127.0.0.1:8080/")
    print("  * Admin Username    : admin")
    print("  * Admin Password    : admin  (or click 'Autofill Demo' in web modal)")
    print("  * Printable Report  : docs/report.html  (Open & press Ctrl+P)")
    print("  * Slide Deck        : docs/presentation.html  (Press 'F' for Fullscreen)")
    print("  * Viva Q&A Guide    : docs/VIVA_VOCE_PREPARATION_GUIDE.md")
    print("=" * 80)
    print("\n[INFO] Backend is actively streaming 1-second telemetry to the browser.")
    print("       Press Ctrl+C in this terminal to shut down the server when finished.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[+] Stopping server...")
        server_process.terminate()
        server_process.wait()
        print("[+] AEGISNET server gracefully stopped. Goodbye!")

if __name__ == "__main__":
    main()
