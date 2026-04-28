"""Application configuration using pydantic-settings."""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change_me_in_production_please"
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "sqlite+aiosqlite:///./nudgeops.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    CORS_ORIGINS: List[str] = ["*"]
    BANDIT_EPSILON: float = 0.15
    BANDIT_UCB_ALPHA: float = 1.0
    BANDIT_THOMPSON_PRIOR_ALPHA: float = 1.0
    BANDIT_THOMPSON_PRIOR_BETA: float = 1.0
    MIN_SAMPLES_FOR_EXPLOITATION: int = 10
    POLICY_RETRAINING_INTERVAL_HOURS: int = 24
    POLICY_EVALUATION_WINDOW_DAYS: int = 7
    POLICY_MIN_FEEDBACK_FOR_RETRAIN: int = 50
    FEATURE_CACHE_TTL_SECONDS: int = 3600
    EMBEDDING_DIM: int = 32
    BEHAVIOR_WINDOW_DAYS: int = 30
    MAX_SINGLE_INTERVENTION_SHARE: float = 0.60
    FAIRNESS_CHECK_WINDOW_DAYS: int = 7
    AB_TEST_MIN_SAMPLE_SIZE: int = 30
    AB_TEST_SIGNIFICANCE_LEVEL: float = 0.05
    ARTIFACTS_PATH: str = "./artifacts"
    RATE_LIMIT_SIGNUP_PER_HOUR: int = 10
    RATE_LIMIT_LOGIN_PER_HOUR: int = 20
    RATE_LIMIT_NUDGE_PER_HOUR: int = 50

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [i.strip() for i in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
