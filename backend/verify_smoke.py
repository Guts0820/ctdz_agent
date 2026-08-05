"""一键冒烟验证：初始化数据 -> 启动全部服务 -> 走通核心接口。

用法：
    python backend/verify_smoke.py

全部通过时打印 PASS 并以 0 退出；任一环节失败以 1 退出。
若 8000 端口已经有服务在跑，则直接复用现有服务做测试。
"""

import sys
import threading
import time

import requests
import uvicorn

sys.path.insert(0, ".")
sys.path.insert(0, "backend")

from backend.services.analysis_service import app as analysis_app
from backend.services.error_analysis_agent import app as error_analysis_app
from backend.services.knowledge_service import app as knowledge_app
from backend.services.teaching_service import app as teaching_app
from backend.services.state_service import app as state_app
from backend.services.review_scheduler import app as scheduler_app
from backend.insight_service import app as insight_app
from backend.api_gateway import app as gateway_app

from backend.database.init_db import init_database
from backend.init_insight_data import main as init_insight_data


RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))


def main():
    print("== 0/4 初始化数据库 ==")
    try:
        init_database()
        init_insight_data()
        check("初始化数据库（example_db.db + user_data.db）", True)
    except Exception as exc:
        check("初始化数据库", False, str(exc))

    base = "http://127.0.0.1:8000"
    insight = "http://127.0.0.1:8010"
    servers = []
    already_running = False

    try:
        requests.get(f"{base}/health", timeout=2)
        already_running = True
    except Exception:
        already_running = False

    if not already_running:
        print("== 1/4 启动全部服务（本地线程内） ==")
        services = [
            ("analysis", 8081, analysis_app),
            ("error_analysis", 8082, error_analysis_app),
            ("knowledge", 8083, knowledge_app),
            ("teaching", 8084, teaching_app),
            ("state", 8085, state_app),
            ("scheduler", 8086, scheduler_app),
            ("insight", 8010, insight_app),
            ("gateway", 8000, gateway_app),
        ]

        def run_server(port, app):
            server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
            servers.append(server)
            server.run()

        for _name, port, app in services:
            threading.Thread(target=run_server, args=(port, app), daemon=True).start()

        print("  waiting services ready ...")
        for _ in range(60):
            try:
                health = requests.get(f"{base}/health", timeout=2).json()
                if health.get("api_gateway") == "healthy":
                    break
            except Exception:
                pass
            time.sleep(1)
    else:
        print("== 1/4 检测到已有服务在运行，直接复用 ==")

    print("== 2/4 服务健康检查 ==")
    try:
        health = requests.get(f"{base}/health", timeout=5).json()
        up = {svc: st.get("status") for svc, st in health.get("services", {}).items()}
        print("  gateway:", health.get("api_gateway"), up)
        core = ["analysis", "error_analysis", "knowledge", "teaching", "state"]
        check("核心服务健康", all(up.get(s) == "healthy" for s in core), str(up))
    except Exception as exc:
        check("服务健康检查", False, str(exc))

    print("== 3/4 核心提交链路 ==")
    try:
        wrong_payload = {
            "student_id": "S-0001",
            "question_id": "Q-0001",
            "original_question": "小明有25颗糖果，小红有38颗糖果，他们一共有多少颗糖果？",
            "student_write": "25+38=53",
            "grade": "三年级",
        }
        r = requests.post(f"{base}/api/v1/submit", json=wrong_payload, timeout=30)
        data = r.json().get("data", {})
        ok = (
            r.status_code == 200
            and data.get("judge_result") == "wrong"
            and data.get("error_tags")
            and data.get("master_level") is not None
            and data.get("teaching_mode") is not None
        )
        check(
            "错题提交链路（判错+错因+教学+复习计划）",
            ok,
            f"judge={data.get('judge_result')} tags={[t.get('error_id') for t in data.get('error_tags', [])]} mode={data.get('teaching_mode')}",
        )

        correct_payload = dict(wrong_payload, student_write="25+38=63")
        r2 = requests.post(f"{base}/api/v1/submit", json=correct_payload, timeout=30)
        d2 = r2.json().get("data", {})
        check(
            "正确提交链路（判对+掌握度更新）",
            r2.status_code == 200 and d2.get("judge_result") == "correct",
            f"judge={d2.get('judge_result')} next={d2.get('next_action')}",
        )
    except Exception as exc:
        check("提交链路", False, str(exc))

    print("== 4/4 Insight 服务（用户/复习/成长报告） ==")
    try:
        r = requests.post(f"{insight}/api/register", json={"username": "verify_user", "password": "123456"}, timeout=10)
        check("用户注册", r.status_code in (200, 400), str(r.json()))

        r = requests.post(f"{insight}/api/login", json={"username": "verify_user", "password": "123456"}, timeout=10)
        check("用户登录", r.status_code == 200)

        r = requests.post(f"{insight}/api/v1/priority-runs", json={"student_id": "S-0001"}, timeout=10)
        priority_ok = r.status_code == 200 and len(r.json().get("results", [])) > 0
        check("优先级快照", priority_ok)

        r = requests.post(
            f"{insight}/api/v1/review-plans",
            json={"student_id": "S-0001", "mode": "question_count", "question_count": 3},
            timeout=10,
        )
        plan_ok = r.status_code == 200 and r.json().get("items")
        check("复习计划生成", plan_ok)

        r = requests.get(f"{insight}/api/growth_report/1", timeout=10)
        growth_ok = r.status_code == 200 and r.json().get("five_dimension_scores")
        check("成长报告", growth_ok)

        r = requests.get(f"{insight}/api/datahub/statistics/overview", timeout=10)
        check("数据看板概览", r.status_code == 200)
    except Exception as exc:
        check("Insight 服务", False, str(exc))

    print("\n== 汇总 ==")
    failed = [name for name, ok, _ in RESULTS if not ok]
    for name, ok, _ in RESULTS:
        print(f"  {'PASS' if ok else 'FAIL'} {name}")
    print(f"\n通过 {len(RESULTS) - len(failed)}/{len(RESULTS)} 项")

    for server in servers:
        server.should_exit = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
