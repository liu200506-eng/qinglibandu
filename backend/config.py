from pydantic_settings import BaseSettings, SettingsConfigDict
import os

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


class Settings(BaseSettings):
    API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    MODEL_NAME: str = "gpt-4o-mini"

    # DeepSeek配置
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL_NAME: str = "deepseek-chat"

    # 讯飞星火大模型配置（优先使用）
    SPARK_API_KEY: str = ""
    SPARK_API_SECRET: str = ""
    SPARK_APP_ID: str = ""
    SPARK_API_BASE: str = "https://spark-api-open.xf-yun.com/v1"
    SPARK_MODEL_NAME: str = "spark-4.0-flash"

    # 讯飞TTS配置
    XFYUN_TTS_APP_ID: str = ""
    XFYUN_TTS_API_KEY: str = ""
    XFYUN_TTS_API_SECRET: str = ""
    XFYUN_TTS_VOICE: str = "xiaoyan"
    XFYUN_TTS_SAMPLE_RATE: int = 16000

    # 讯飞ASR配置
    XFYUN_ASR_APP_ID: str = ""
    XFYUN_ASR_API_KEY: str = ""
    XFYUN_ASR_API_SECRET: str = ""
    XFYUN_ASR_SAMPLE_RATE: int = 16000

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