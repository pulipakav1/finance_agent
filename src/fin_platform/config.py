"""Typed configuration for the financial intelligence platform."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PlatformSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    app_name: str = "Multi-Agent Financial Intelligence Platform"
    env: str = Field(default="dev", alias="APP_ENV")
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    streamlit_api_base_url: str = Field(
        default="http://127.0.0.1:8000",
        alias="STREAMLIT_API_BASE_URL",
    )

    model_name: str = Field(default="gpt-4o-mini", alias="MODEL_NAME")
    supervisor_timeout_s: float = 7.0
    specialist_timeout_s: float = 10.0
    retry_attempts: int = 2

    data_mode: str = Field(default="mock", alias="DATA_MODE")
    enable_live_data: bool = Field(default=False, alias="ENABLE_LIVE_DATA")

    log_level: str = "INFO"
    include_response_metadata: bool = True

    max_history_turns: int = 12
    summarize_history: bool = True

    ui_theme: str = "dark"
    ui_show_diagnostics: bool = True


settings = PlatformSettings()
