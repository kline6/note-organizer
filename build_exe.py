"""
打包成独立 EXE 软件 - 双击即可运行，无需安装 Python/Node.js

使用方法:
    pip install pyinstaller
    python build_exe.py
    生成文件在 dist/NoteOrganizer.exe

注意事项:
    - 需要先正常启动过一次（确保 backend/data/ 和 node_modules 都存在）
    - 建议在 Python 3.12 环境下运行
"""
import os, sys, shutil, subprocess
from pathlib import Path

BASE = Path(__file__).parent
BACKEND = BASE / "backend"
FRONTEND = BASE / "frontend"
DIST = FRONTEND / "dist"


def step(msg):
    print(f"\n{'='*60}\n  {msg}\n{'='*60}")


def ensure_frontend_built():
    """Build frontend if not already built."""
    if (DIST / "index.html").exists():
        print("[OK] 前端已构建")
        return

    if not (FRONTEND / "node_modules").exists():
        print("[*] 安装前端依赖...")
        subprocess.check_call(["npm", "install"], cwd=str(FRONTEND), shell=True)

    print("[*] 构建前端...")
    subprocess.check_call(["npm", "run", "build"], cwd=str(FRONTEND), shell=True)
    print("[OK] 前端构建完成")


def clean_old_build():
    """Remove old PyInstaller build artifacts."""
    for d in ["build", "dist"]:
        p = BASE / d
        if p.exists():
            shutil.rmtree(p)
    spec = BASE / "NoteOrganizer.spec"
    if spec.exists():
        spec.unlink()


def create_launcher():
    """Create a simple launcher script that PyInstaller will bundle."""
    launcher = BASE / "_launcher.py"
    code = '''"""
NoteOrganizer - 笔记智能整理工具
PyInstaller 入口点
"""
import os, sys, time, subprocess, webbrowser, threading
from pathlib import Path


def get_base():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

BASE = get_base()
BACKEND = BASE / "backend"
FRONTEND_DIST = BASE / "frontend" / "dist"
DATA = Path(sys.executable).parent / "data" if getattr(sys, "frozen", False) else BACKEND / "data"
DATA.mkdir(parents=True, exist_ok=True)


def main():
    print("Starting NoteOrganizer...")
    env = os.environ.copy()
    env["NOTEORGANIZER_DATA_DIR"] = str(DATA)

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(BACKEND), env=env,
    )

    # Wait for startup
    import socket
    for _ in range(30):
        time.sleep(0.5)
        if proc.poll() is not None:
            print(f"Backend failed! Exit code: {proc.returncode}")
            break
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if sock.connect_ex(("127.0.0.1", 8000)) == 0:
            sock.close()
            print("Backend ready: http://127.0.0.1:8000")
            webbrowser.open("http://127.0.0.1:8000")
            break
        sock.close()

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        print("Shutdown.")


if __name__ == "__main__":
    main()
'''
    launcher.write_text(code, encoding="utf-8")
    return launcher


def build_exe():
    step("1/4 清理旧构建")
    clean_old_build()

    step("2/4 构建前端")
    ensure_frontend_built()

    step("3/4 创建启动脚本")
    launcher = create_launcher()

    step("4/4 PyInstaller 打包 (约 2-5 分钟)")
    # Build the spec dynamically
    import PyInstaller.__main__

    args = [
        str(launcher),
        "--name=NoteOrganizer",
        "--onefile",
        "--console",
        "--clean",
        "--noconfirm",
        "--add-data", f"{BACKEND}{os.pathsep}backend",
        "--add-data", f"{DIST}{os.pathsep}frontend/dist",
        "--hidden-import=fastapi",
        "--hidden-import=uvicorn",
        "--hidden-import=sqlalchemy",
        "--hidden-import=aiosqlite",
        "--hidden-import=openai",
        "--hidden-import=pydantic",
        "--hidden-import=pydantic_settings",
        "--hidden-import=httpx",
        "--hidden-import=python_multipart",
        "--hidden-import=docx",
        "--hidden-import=markdown",
        "--hidden-import=bs4",
        "--hidden-import=jieba",
        "--hidden-import=fpdf",
        "--hidden-import=fpdf2",
        "--collect-all", "fpdf2",
        "--collect-all", "fastapi",
        "--collect-all", "uvicorn",
        "--exclude-module=weasyprint",
        "--exclude-module=reportlab",
    ]

    sys.argv = ["pyinstaller"] + [str(a) for a in args]
    PyInstaller.__main__.run()

    # Clean up
    launcher.unlink(missing_ok=True)

    exe = BASE / "dist" / "NoteOrganizer.exe"
    if exe.exists():
        size_mb = exe.stat().st_size / (1024 * 1024)
        print(f"\n{'='*60}")
        print(f"  EXE 构建成功！")
        print(f"  位置: {exe}")
        print(f"  大小: {size_mb:.1f} MB")
        print(f"  将该文件复制到任意位置即可使用")
        print(f"{'='*60}")
    else:
        print("\n[错误] EXE 构建失败")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
