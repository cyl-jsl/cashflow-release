from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # cashflow/


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'cashflow.db'}"
    stale_balance_days: int = 7

    class Config:
        env_prefix = "CASHFLOW_"


settings = Settings()
