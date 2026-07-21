from pydantic_settings import BaseSettings, SettingsConfigDict
import os

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


class Settings(BaseSettings):
    API_KEY: str = ""

    # 赛事指定标准化大模型底座配置
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://api.example.com/v1"
    LLM_MODEL_NAME: str = "default-model"

    # 语音合成（TTS）配置
    TTS_APP_ID: str = ""
    TTS_API_KEY: str = ""
    TTS_API_SECRET: str = ""
    TTS_VOICE: str = "default"
    TTS_SAMPLE_RATE: int = 16000
    TTS_BASE_URL: str = "https://tts-api.example.com/v2/tts"

    # 语音识别（ASR）配置
    ASR_APP_ID: str = ""
    ASR_API_KEY: str = ""
    ASR_API_SECRET: str = ""
    ASR_SAMPLE_RATE: int = 16000
    ASR_BASE_URL: str = "https://asr-api.example.com/v2/asr"

    # MySQL数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "root"
    DB_NAME: str = "demo"
    DATABASE_URL: str = "sqlite:///./database/qingli.db"

    REDIS_URL: str = "redis://localhost:6379/0"

    # Qdrant配置
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8001
    APP_DEBUG: bool = True

    TTS_API_KEY: str = ""
    STT_API_KEY: str = ""

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=_env_path, extra="ignore")


settings = Settings()