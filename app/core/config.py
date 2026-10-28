from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "SecureEvent API Backend"
    API_V1_STR: str = "/api/v1"
    
    # Datos de la base de datos PostgreSQL
    POSTGRES_USER: str = "secureuser"
    POSTGRES_PASSWORD: str = "securepass"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "secureevent_db"
    DATABASE_URL: str = "postgresql://secureuser:securepass@localhost:5432/secureevent_db"
    
    # Datos del Broker MQTT EMQX
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883

    # Permite leer el archivo .env e ignorar campos extra si los hubiera
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )

settings = Settings()