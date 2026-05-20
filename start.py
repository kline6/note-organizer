"""
笔记智能整理工具 - 一键启动脚本
用法: python start.py
     双击 启动.bat
"""
import os
import sys
import time
import signal
import shutil
import subprocess
import webbrowser
from pathlib import Path


def get_base_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


BASE = get_base_dir()
BACKEND = BASE / "backend"
FRONTEND = BASE / "frontend"
FRONTEND_DIST = FRONTEND / "dist"

backend_proc = None
frontend_proc = None


# ── helpers ──────────────────────────────────────────────

def banner():
    print("\033[36m")
    print("╔══════════════════════════════════════════════╗")
    print("║      📋 笔记智能整理工具 v1.0.0               ║")
    print("║      AI-Powered Note Organizer               ║")
    print("╚══════════════════════════════════════════════╝")
    print("\033[0m")


def ok(msg):
    print(f"  \033[32m[OK]\033[0m {msg}")


def warn(msg):
    print(f"  \033[33m[提示]\033[0m {msg}")


def fail(msg):
    print(f"  \033[31m[错误]\033[0m {msg}")


def info(msg):
    print(f"  \033[36m[*]\033[0m {msg}")


# ── checks ───────────────────────────────────────────────

def check_python():
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 10):
        fail(f"需要 Python 3.10+，当前: {v.major}.{v.minor}.{v.micro}")
        input("\n按 Enter 退出...")
        sys.exit(1)
    if v.minor >= 14:
        warn(f"Python {v.major}.{v.minor}.{v.micro} 太新，很多包没有预编译版本")
        warn("建议安装 Python 3.12 (https://www.python.org/downloads/)")
        warn("当前尝试继续，但 pip install 可能失败...")
    ok(f"Python {v.major}.{v.minor}.{v.micro}")


def ensure_dirs():
    for d in [BACKEND / "data" / "workspaces", BACKEND / "data"]:
        d.mkdir(parents=True, exist_ok=True)
    ok("数据目录就绪")


def auto_env():
    env_file = BACKEND / ".env"
    env_example = BACKEND / ".env.example"
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        warn("已从 .env.example 创建 .env，如需使用 DeepSeek API 请编辑填入 Key")
        warn(f"   位置: {env_file}")
    elif env_file.exists():
        ok(".env 已存在")


def install_backend_deps():
    """Return True if deps are ready."""
    try:
        import fastapi, uvicorn, sqlalchemy, fpdf  # noqa: F401
        ok("后端依赖已安装")
        return True
    except ImportError:
        info("正在安装后端依赖，请稍候...")
        req = BACKEND / "requirements.txt"
        if not req.exists():
            fail("找不到 requirements.txt")
            return False
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", str(req), "-q"],
                cwd=str(BACKEND),
            )
            ok("后端依赖安装完成")
            return True
        except subprocess.CalledProcessError as e:
            fail(f"依赖安装失败: {e}")
            return False


def check_frontend():
    index = FRONTEND_DIST / "index.html"
    node_mods = FRONTEND / "node_modules"

    if not node_mods.exists():
        info("安装前端依赖...")
        try:
            subprocess.check_call(["npm", "install"], cwd=str(FRONTEND), shell=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ok("前端依赖安装完成")
        except (subprocess.CalledProcessError, FileNotFoundError):
            warn("Node.js 未安装，前端不可用")
            return "none"

    # Always rebuild to pick up latest changes
    if index.exists():
        info("检测到旧构建，正在清理...")
        import shutil
        shutil.rmtree(str(FRONTEND_DIST), ignore_errors=True)

    info("构建前端（约 30-60 秒）...")
    try:
        subprocess.check_call(["npm", "run", "build"], cwd=str(FRONTEND), shell=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if (FRONTEND_DIST / "index.html").exists():
            ok("前端构建完成")
            return "built"
    except subprocess.CalledProcessError:
        pass

    warn("前端构建失败，尝试开发模式")
    return "dev"


# ── start / stop ─────────────────────────────────────────

def start_backend(port=8000):
    global backend_proc
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    # Let stdout/stderr go to the console so errors are visible
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(BACKEND),
        env=env,
        # Don't capture - let it print directly to terminal
        stdout=None,
        stderr=None,
    )
    # Wait for startup
    import socket
    for _ in range(25):
        time.sleep(0.5)
        if backend_proc.poll() is not None:
            fail(f"后端启动失败 (退出码: {backend_proc.returncode})")
            return False
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result == 0:
            ok(f"后端服务已启动: http://127.0.0.1:{port}")
            return True
    fail("后端启动超时")
    return False


def start_frontend(port=5173):
    global frontend_proc
    try:
        frontend_proc = subprocess.Popen(
            ["npx", "vite", "--port", str(port), "--strictPort", "--no-open"],
            cwd=str(FRONTEND),
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(2)
        if frontend_proc.poll() is not None:
            warn("前端开发服务器启动失败")
            return False
        ok(f"前端开发服务器: http://localhost:{port}")
        return True
    except FileNotFoundError:
        warn("Node.js 未安装")
        return False


def cleanup(signum=None, frame=None):
    print("\n\033[33m[关闭]\033[0m 正在停止服务...")
    for p in [backend_proc, frontend_proc]:
        if p:
            try:
                p.terminate()
                p.wait(timeout=5)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                try:
                    p.kill()
                except Exception:
                    pass
    print("\033[33m[关闭]\033[0m 服务已停止")
    sys.exit(0)


# ── main ─────────────────────────────────────────────────

def main():
    signal.signal(signal.SIGINT, cleanup)
    if hasattr(signal, 'SIGBREAK'):
        signal.signal(signal.SIGBREAK, cleanup)

    banner()

    info("检查环境...")
    check_python()
    ensure_dirs()
    auto_env()

    if not install_backend_deps():
        input("\n按 Enter 退出...")
        sys.exit(1)

    fe_status = check_frontend()
    print()

    # Start backend
    info("启动后端...")
    if not start_backend(8000):
        input("\n按 Enter 退出...")
        sys.exit(1)

    # Decide URL
    if fe_status == "built":
        url = "http://127.0.0.1:8000"
        print(f"\n  \033[32m→ 打开浏览器访问: {url}\033[0m\n")
        webbrowser.open(url)
    elif fe_status == "dev":
        if start_frontend(5173):
            url = "http://localhost:5173"
            print(f"\n  \033[32m→ 开发模式\033[0m")
            print(f"    前端: http://localhost:5173")
            print(f"    后端: http://127.0.0.1:8000\n")
            webbrowser.open(url)
        else:
            url = "http://127.0.0.1:8000"
            warn("前端不可用，仅 API 可用")
            print(f"  → {url}\n")
            webbrowser.open(url)
    else:
        url = "http://127.0.0.1:8000"
        warn("前端未构建且 Node.js 不可用，仅后端 API 运行")
        print(f"  → {url}\n")
        webbrowser.open(url)

    print("  按 Ctrl+C 退出\n")
    print("─" * 50)

    try:
        while True:
            if backend_proc and backend_proc.poll() is not None:
                fail("后端进程意外退出")
                break
            if frontend_proc and frontend_proc.poll() is not None:
                warn("前端开发服务器已退出")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
