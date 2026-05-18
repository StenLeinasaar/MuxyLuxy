from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    admin_username: str = "admin"
    admin_password: str = "admin"
    ansible_root: str = "./ansible"
    ansible_roles_path: str = "./ansible/roles"
    ansible_generated_path: str = "./ansible/generated"
    # Not ANSIBLE_LOG_PATH — that name is reserved by ansible-core for its own log file.
    roller_run_log_dir: str = Field(
        default="./logs",
        validation_alias="ROLLER_RUN_LOG_DIR",
    )
    ansible_run_timeout_seconds: int = 300


settings = Settings()
