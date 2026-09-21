import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Agentic Employee AI Assistant"
    app_env: str = "development"
    debug: bool = True
    
    # LLM Settings ("gemini", "openai", "lmstudio", "ollama", or "local")
    llm_provider: str = "ollama"
    google_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    
    # LM Studio / Ollama / Local LLM Settings
    lmstudio_base_url: str = "http://localhost:11434/v1"
    lmstudio_model: str = "gemma4:latest"
    llm_timeout: float = 60.0
    
    # RAG & Threshold Settings
    data_dir: Path = Path(__file__).parent.parent / "data"
    chroma_persist_directory: str = "./chroma_db"
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 500
    chunk_overlap: int = 50
    max_vector_distance: float = 1.35
    min_rerank_score: float = 0.0

    # Logging & Observability
    log_level: str = "INFO"

    # Security & Auth Settings
    jwt_secret: str = "dev-secret-key-change-in-production-123456789"
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    demo_employee_password: str = "emp123"
    demo_hr_password: str = "hr123"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
