"""Configuración del proyecto, resuelta desde .env o el entorno."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # El SDK también la resuelve solo desde el entorno; se declara aquí para
    # poder avisar al arrancar si falta.
    anthropic_api_key: str = ""

    model: str = "claude-opus-5"
    effort: str = "low"
    max_tokens: int = 8000
    max_tool_iterations: int = 5

    # --- Índice ---------------------------------------------------------
    index_dir: Path = DATA_DIR / "index"
    cache_dir: Path = DATA_DIR / "cache"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # Troceado. 700 caracteres entran holgados en el contexto sin partir un
    # párrafo típico del blog por la mitad.
    chunk_size: int = 700
    chunk_overlap: int = 120

    # --- Entrega de leads -----------------------------------------------
    leads_file: Path = DATA_DIR / "leads.jsonl"
    # Ronald confirmó info@ y adelantó que más adelante querrá añadir una o dos
    # direcciones más, así que esto acepta lista separada por comas desde el
    # principio: añadir un destinatario no debe requerir tocar código.
    lead_email_to: str = "info@rgwallcovering.com"

    # --- API ------------------------------------------------------------
    allowed_origins: str = "*"

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def destinatarios_lead(self) -> list[str]:
        return [d.strip() for d in self.lead_email_to.split(",") if d.strip()]

    @property
    def embeddings_path(self) -> Path:
        return self.index_dir / "embeddings.npy"

    @property
    def chunks_path(self) -> Path:
        return self.index_dir / "chunks.jsonl"


settings = Settings()
