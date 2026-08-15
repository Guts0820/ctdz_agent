"""Insight Service（8010）：聚合同事 D:/backend 移植过来的能力。

提供：
- 用户账号体系（注册/登录/错题本/学习进度/答题记录）
- 动态复习引擎（优先级快照 / 按优先级选题 / 复习会话 / 错题订正）
- 成长报告（五维能力 / 薄弱点 / 近期进步 / 学习路径 / 复习计划）
- 数据看板（系统概览 / 班级掌握度 / 复习统计 / 错因分析）
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.user_database import user_db
from insight.routers.users import router as users_router
from insight.routers.growth_report import router as growth_report_router
from insight.routers.datahub import router as datahub_router
from insight.routers.students import router as students_router
from insight.routers.knowledge_points import router as knowledge_points_router
from review.api.priority import router as review_priority_router
from review.api.review_plans import router as review_plans_router
from review.api.review_sessions import router as review_sessions_router
from review.api.corrections import router as review_corrections_router


app = FastAPI(
    title="AI 小学数学错题系统 - Insight Service",
    description="用户体系 / 动态复习引擎 / 成长报告 / 数据看板",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    user_db.connect()
    user_db.seed_demo_users()


@app.get("/")
def root():
    return {"message": "Insight Service 运行中", "features": ["users", "review", "growth_report", "datahub"]}


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Insight Service"}


app.include_router(users_router)
app.include_router(growth_report_router)
app.include_router(datahub_router)
app.include_router(students_router)
app.include_router(knowledge_points_router)
app.include_router(review_priority_router, prefix="/api/v1")
app.include_router(review_plans_router, prefix="/api/v1")
app.include_router(review_sessions_router, prefix="/api/v1")
app.include_router(review_corrections_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
