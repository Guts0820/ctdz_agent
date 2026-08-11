from review.repositories import ReviewRepository
from review.services.plan_service import PlanService
from review.services.priority_calculator import priority_calculator
from review.services.priority_service import PriorityService
from review.services.question_selector import question_selector
from review.services.session_service import SessionService

repository = ReviewRepository()
priority_service = PriorityService(repository, priority_calculator)
plan_service = PlanService(repository, priority_service, question_selector)
session_service = SessionService(repository, plan_service)
