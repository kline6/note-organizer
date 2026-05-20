"""Start backend and log output."""
import subprocess, sys, os

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
logfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_backend.log")

print(f"Starting backend from: {backend_dir}")
print(f"Log file: {logfile}")

with open(logfile, "w") as log:
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=backend_dir,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    print(f"Backend PID: {proc.pid}")
    print("Backend starting, waiting 3s...")
    import time
    time.sleep(3)
    if proc.poll() is None:
        print("Backend is running!")
    else:
        print(f"Backend exited with code {proc.returncode}")
        with open(logfile) as f:
            print("Log content:")
            print(f.read())
