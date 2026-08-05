from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "小学数学自适应复习引擎"
    api_prefix: str = "/api/v1"
    priority_formula_version: str = "priority-v1.0"
    planning_config_version: str = "planning-demo-v1"


settings = Settings()
