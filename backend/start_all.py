import subprocess
import sys
import time
import os

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
    time.sleep(3)
    print(f"  日志文件: {log_file_path}")
    return process

def main():
    services = [
        ("Knowledge Graph Service", "kg_service/main.py", 8007),
        ("Analysis Service", "backend/services/analysis_service.py", 8081),
        ("Error Analysis Agent", "backend/services/error_analysis_agent.py", 8082),
        ("Knowledge Service", "backend/services/knowledge_service.py", 8083),
        ("Teaching Service", "backend/services/teaching_service.py", 8084),
        ("State Service", "backend/services/state_service.py", 8085),
        ("Review Scheduler", "backend/services/review_scheduler.py", 8086),
        ("API Gateway", "backend/api_gateway.py", 8000)
    ]
    
    processes = []
    
    try:
        print("Initializing database...")
        subprocess.run([sys.executable, "backend/database/init_db.py"], check=True)
        
        for name, script, port in services:
            process = start_service(name, script, port)
            processes.append((name, process))
        
        print("\nAll services started!")
        print("=" * 60)
        print("API Gateway: http://localhost:8000")
        print("Analysis Service: http://localhost:8081")
        print("Error Analysis Agent: http://localhost:8082")
        print("Knowledge Service: http://localhost:8083")
        print("Teaching Service: http://localhost:8084")
        print("State Service: http://localhost:8085")
        print("Review Scheduler: http://localhost:8086")
        print("Knowledge Graph Service: http://localhost:8007")
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