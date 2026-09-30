from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/legal_metrology"
    jwt_secret_key: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    frontend_url: str = "http://localhost:3000"
    public_base_url: str = "http://localhost:8000"
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10
    demo_certificate_validity_days: int = 365
    demo_reminder_windows_days: str = "30,7"
    demo_allowed_attachment_types: str = "image/jpeg,image/png,application/pdf"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def allowed_attachment_types_list(self) -> List[str]:
        return [t.strip() for t in self.demo_allowed_attachment_types.split(",")]

    @property
    def reminder_windows_list(self) -> List[int]:
        return [int(d.strip()) for d in self.demo_reminder_windows_days.split(",")]


settings = Settings()