"""
NoteOrganizer EXE Entry - PyInstaller packaged
"""
import os, sys, time, webbrowser, socket, asyncio, threading
from pathlib import Path


def get_base():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


BASE = get_base()
BACKEND = BASE / "backend"
DATA = Path(sys.executable).parent / "data" if getattr(sys, "frozen", False) else BACKEND / "data"
DATA.mkdir(parents=True, exist_ok=True)
os.environ["NOTEORGANIZER_DATA_DIR"] = str(DATA)
sys.path.insert(0, str(BACKEND))


def is_port_open(port=8000):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    r = s.connect_ex(("127.0.0.1", port)) == 0
    s.close()
    return r


def run_server():
    os.chdir(str(BACKEND))
    import uvicorn
    config = uvicorn.Config("app.main:app", host="127.0.0.1", port=8000, log_level="warning")
    server = uvicorn.Server(config)

    async def serve():
        await server.serve()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(serve())
    except Exception as e:
        print(f"Server error: {e}")


def main():
    print("=" * 50)
    print("  NoteOrganizer v1.0")
    print(f"  Data: {DATA}")
    print("=" * 50)
    print()

    if is_port_open(8000):
        print("Port 8000 already in use. Opening browser...")
        webbrowser.open("http://127.0.0.1:8000")
        print("An instance is already running.")
        input("Press Enter to exit...")
        return

    if not (BACKEND / "app" / "main.py").exists():
        print(f"ERROR: Backend not found!")
        print(f"  Path: {BACKEND}")
        input("Press Enter to exit...")
        return

    print("Starting server...")
    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    # Wait for server to be ready
    for i in range(40):
        time.sleep(0.5)
        if is_port_open(8000):
            print(f"Ready: http://127.0.0.1:8000")
            print("Minimize this window and use the browser.")
            print()
            webbrowser.open("http://127.0.0.1:8000")
            break
    else:
        print("ERROR: Server did not start within 20 seconds.")
        print("Check:", DATA / "backend.log")
        input("Press Enter to exit...")
        return

    try:
        while t.is_alive():
            t.join(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        os._exit(0)


if __name__ == "__main__":
    main()
