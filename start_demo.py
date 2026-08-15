"""ctdz_agent 一键启动编排：OCR(8087) + 前端(3000) + 后端(8000/8010/8081-8086)。

在同一个控制台窗口内运行。按 Ctrl+C 后，所有子进程会被统一终止，
不留残留进程，控制台窗口可正常关闭。
"""

import os
import subprocess
import sys
import time
import webbrowser

REPO = r"D:\ctdz_agent"
VENV_PY = os.path.join(REPO, ".venv", "Scripts", "python.exe")
OCR_DIR = os.path.join(REPO, "handwriting_ocr_service")
OCR_PY = os.path.join(OCR_DIR, ".venv-vl", "Scripts", "python.exe")
if not os.path.exists(OCR_PY):
    # 复用旧 OCR venv，但跑仓库内代码
    OCR_PY = r"D:\ctdz_agent_backend\handwriting_ocr_service\.venv-vl\Scripts\python.exe"


def kill_tree(proc):
    """强制终止进程及其整棵子进程树（Windows taskkill /T /F）。"""
    if proc and proc.poll() is None:
        subprocess.run(
            ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
            capture_output=True,
            timeout=10,
        )


def main():
    auto_stop = 0.0
    if "--auto-stop-seconds" in sys.argv:
        idx = sys.argv.index("--auto-stop-seconds")
        auto_stop = float(sys.argv[idx + 1])

    ocr = None
    frontend = None
    backend = None
    try:
        if os.path.exists(OCR_PY):
            print("[1/3] 启动 OCR 服务 (8087)...")
            ocr = subprocess.Popen(
                [OCR_PY, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8087"],
                cwd=OCR_DIR,
            )
        else:
            print("[1/3] 未找到 OCR 环境，跳过（拍照功能不可用）")

        print("[2/3] 启动前端 (3000)...")
        frontend = subprocess.Popen(
            [VENV_PY, "-m", "http.server", "3000", "--bind", "127.0.0.1"],
            cwd=os.path.join(REPO, "frontend"),
        )

        time.sleep(2)
        try:
            webbrowser.open("http://localhost:3000")
        except Exception:
            pass

        print("[3/3] 启动后端（网关 + 8 个服务）...")
        env = os.environ.copy()
        env["PYTHONPATH"] = REPO
        backend = subprocess.Popen(
            [VENV_PY, os.path.join(REPO, "backend", "start_all.py")],
            cwd=REPO,
            env=env,
        )

        deadline = time.time() + auto_stop if auto_stop > 0 else None
        while backend.poll() is None:
            if deadline and time.time() > deadline:
                raise KeyboardInterrupt
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n收到停止信号，正在停止所有服务...")
    finally:
        for name, proc in (("后端", backend), ("OCR", ocr), ("前端", frontend)):
            if proc and proc.poll() is None:
                print(f"正在停止 {name}...")
            kill_tree(proc)
        print("全部已停止，可以关闭本窗口。")


if __name__ == "__main__":
    main()
