import subprocess
import sys
import time
import os

from backend.config import SERVICE_STARTUP_WAIT_SECONDS, API_GATEWAY_HOST, API_GATEWAY_PORT, service_urls

def start_service(name, script_path, port, log_dir="backend/logs"):
    print(f"Starting {name} on port {port}...")
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, f"{name.replace(' ', '_')}.log")
    log_file = open(log_file_path, "w", encoding="utf-8")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    process = subprocess.Popen(
        [sys.executable, script_path],
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True
    )
    time.sleep(SERVICE_STARTUP_WAIT_SECONDS)
    print(f"  日志文件: {log_file_path}")
    return process


def start_ocr_service(processes):
    """OCR 服务需要独立的 Python 3.12 + PaddlePaddle 环境（handwriting_ocr_service/.venv-vl）。"""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ocr_dir = os.path.join(repo_root, "handwriting_ocr_service")
    ocr_python = os.path.join(ocr_dir, ".venv-vl", "Scripts", "python.exe")
    if not os.path.exists(ocr_python):
        # 兼容旧路径：D:\ctdz_agent_backend\handwriting_ocr_service\.venv-vl
        alt_dir = r"D:\ctdz_agent_backend\handwriting_ocr_service"
        alt_python = os.path.join(alt_dir, ".venv-vl", "Scripts", "python.exe")
        if os.path.exists(alt_python):
            ocr_dir = alt_dir
            ocr_python = alt_python
    if not os.path.exists(ocr_python):
        print("未检测到 handwriting_ocr_service/.venv-vl，跳过 OCR 服务（主流程将回退到模拟 OCR / 文本输入）")
        return

    os.makedirs("backend/logs", exist_ok=True)
    log_file = open("backend/logs/OCR_Service.log", "w", encoding="utf-8")
    print("Starting Handwriting OCR Service on port 8087...")
    process = subprocess.Popen(
        [ocr_python, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8087"],
        cwd=ocr_dir,
        env=os.environ.copy(),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )
    time.sleep(SERVICE_STARTUP_WAIT_SECONDS)
    print("  OCR 日志文件: backend/logs/OCR_Service.log（首次启动需下载约 1.9GB 模型，耗时数分钟）")
    processes.append(("OCR Service", process))


def main():
    services = [
        ("Analysis Service", "backend/services/analysis_service.py", 8081),
        ("Error Analysis Agent", "backend/services/error_analysis_agent.py", 8082),
        ("Knowledge Service", "backend/services/knowledge_service.py", 8083),
        ("Teaching Service", "backend/services/teaching_service.py", 8084),
        ("State Service", "backend/services/state_service.py", 8085),
        ("Review Scheduler", "backend/services/review_scheduler.py", 8086),
        ("Insight Service", "backend/insight_service.py", 8010),
        ("API Gateway", "backend/api_gateway.py", 8000)
    ]
    
    processes = []
    
    try:
        print("Initializing database...")
        subprocess.run([sys.executable, "backend/database/init_db.py"], check=True)

        start_ocr_service(processes)

        for name, script, port in services:
            process = start_service(name, script, port)
            processes.append((name, process))
        
        print("\nAll services started!")
        print("=" * 60)
        print(f"API Gateway: {API_GATEWAY_HOST}:{API_GATEWAY_PORT}")
        for service, url in service_urls().items():
            print(f"{service}: {url}")
        print("=" * 60)
        print(f"\n各服务日志保存在: backend/logs/ 目录下，如需调试请查看对应文件")
        print("\nPress Ctrl+C to stop all services...")
        
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nStopping all services...")
        for name, process in processes:
            process.terminate()
            process.wait()
            print(f"{name} stopped")
        print("All services stopped")

if __name__ == "__main__":
    main()
