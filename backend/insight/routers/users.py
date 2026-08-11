from fastapi import APIRouter, HTTPException, Body, Query
from typing import Optional, List

from backend.user_database import user_db


router = APIRouter(prefix="/api", tags=["users"])


@router.post("/register", response_model=dict)
def register_user(
    username: str = Body(..., description="用户名"),
    password: str = Body(..., description="密码"),
    grade: Optional[int] = Body(None, description="年级"),
    semester: Optional[str] = Body(None, description="学期")
):
    user_id = user_db.insert_user(username, password, grade, semester)
    if user_id is None:
        raise HTTPException(status_code=400, detail="用户名已存在")
    return {"message": "注册成功", "user_id": user_id}


@router.post("/login", response_model=dict)
def login_user(
    username: str = Body(..., description="用户名"),
    password: str = Body(..., description="密码")
):
    user = user_db.get_user(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {"message": "登录成功", "user": user}


@router.get("/users/{user_id}", response_model=dict)
def get_user(user_id: int):
    user = user_db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.post("/wrong_questions", response_model=dict)
def add_wrong_question(
    user_id: int = Body(..., description="用户ID"),
    question_id: str = Body(..., description="题目ID"),
    wrong_answer: Optional[str] = Body(None, description="错误答案"),
    error_cause_id: Optional[str] = Body(None, description="错因ID")
):
    result = user_db.add_wrong_question(user_id, question_id, wrong_answer, error_cause_id)
    if result:
        return {"message": "错题添加成功", "id": result}
    raise HTTPException(status_code=500, detail="添加失败")


@router.get("/wrong_questions/{user_id}", response_model=List[dict])
def get_wrong_questions(user_id: int):
    return user_db.get_wrong_questions(user_id)


@router.put("/wrong_questions/{user_id}/{question_id}", response_model=dict)
def mark_wrong_reviewed(user_id: int, question_id: str):
    user_db.mark_wrong_question_reviewed(user_id, question_id)
    return {"message": "已标记为已复习"}


@router.post("/learning_progress", response_model=dict)
def update_progress(
    user_id: int = Body(..., description="用户ID"),
    knowledge_id: str = Body(..., description="知识点ID"),
    is_correct: bool = Body(..., description="是否正确")
):
    user_db.update_learning_progress(user_id, knowledge_id, is_correct)
    return {"message": "学习进度更新成功"}


@router.get("/learning_progress/{user_id}", response_model=List[dict])
def get_learning_progress(user_id: int):
    return user_db.get_learning_progress(user_id)


@router.get("/weak_points/{user_id}", response_model=List[dict])
def get_weak_points(
    user_id: int,
    threshold: int = Query(60, description="掌握程度阈值")
):
    return user_db.get_weak_knowledge_points(user_id, threshold)


@router.post("/answer_records", response_model=dict)
def add_answer_record(
    user_id: int = Body(..., description="用户ID"),
    question_id: str = Body(..., description="题目ID"),
    answer: str = Body(..., description="用户答案"),
    is_correct: bool = Body(..., description="是否正确"),
    time_spent: Optional[int] = Body(None, description="答题耗时(秒)")
):
    record_id = user_db.add_answer_record(user_id, question_id, answer, is_correct, time_spent)
    return {"message": "答题记录添加成功", "id": record_id}


@router.get("/answer_records/{user_id}", response_model=List[dict])
def get_answer_records(
    user_id: int,
    limit: int = Query(100, description="返回数量")
):
    return user_db.get_answer_records(user_id, limit)
