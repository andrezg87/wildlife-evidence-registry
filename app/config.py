from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str

    jwt_secret_key: str
    jwt_expiration_minutes: int

    gemini_api_key: str

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_s3_bucket: str
    aws_region: str

    currency_exchange_api_base_url: str

    class Config:
        env_file = ".env"


settings = Settings()
