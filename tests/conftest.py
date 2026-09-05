import os

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://login_plans:login_plans_dev_password@localhost:5432/login_plans_test"
)
