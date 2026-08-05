from dataclasses import dataclass


@dataclass
class KnowledgeState:
    student_id: str
    knowledge_point_id: str
    correct_count: int
    wrong_count: int


@dataclass
class Question:
    question_id: str
    knowledge_ids: list[str]
