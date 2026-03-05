from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict


class DatabaseMainSettings(BaseModel):
    engine: str
    host: str
    port: int
    username: str
    password: str
    database: str

    @property
    def dsn(self) -> str:
        if self.engine == "postgresql":
            return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        if self.engine == "mariadb":
            return f"mysql+aiomysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        return f"{self.engine}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class DatabaseSettings(BaseModel):
    main: DatabaseMainSettings


class StorageSettings(BaseModel):
    endpoint: str
    accessKey: str
    secretKey: str
    bucket: str


class MessagingSettings(BaseModel):
    host: str
    port: int
    username: str
    password: str
    vhost: str


class RedisSettings(BaseModel):
    host: str
    port: int
    db: int = 0


class SecuritySettings(BaseModel):
    jwtSecretKey: str
    jwtAlgorithm: str = "HS256"
    accessTokenExpireMinutes: int = 60


class KubernetesSettings(BaseModel):
    namespace: str
    inCluster: bool = False
    kubeconfigPath: Optional[str] = None


class NodeSettings(BaseModel):
    name: str
    cpuMilli: int
    memoryBytes: int
    gpu: int = 0
    capacity: int = 0


class AnalysisToolSettings(BaseModel):
    defaultCpu: int
    defaultGpu: int
    defaultMemory: int
    defaultCapacity: int
    maxExpireDuration: str


class CommonSettings(BaseModel):
    pollingInterval: int = 5000


class FileNodeSettings(BaseModel):
    allowUploadTypes: List[str] = Field(default_factory=list)
    allowPreviewTypes: List[str] = Field(default_factory=list)


class OptionSettings(BaseModel):
    mode: str | None = None
    backupEnabled: bool | None = None
    gpuEnabled: bool | None = None
    storageEnabled: bool | None = None


class LoggingSettings(BaseModel):
    level: str = "INFO"


class ClusterResources(BaseModel):
    total_cpu_milli: int = 0
    total_memory_bytes: int = 0
    total_gpu: int = 0
    total_capacity: int = 0


class UrlSettings(BaseModel):
    graphio: str | None = None
    meta: str | None = None
    containerManagement: str | None = None
    templateAnalysisAdaptor: str | None = None


class TestSettings(BaseModel):
    user: str | None = None
    password: str | None = None


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__", extra="ignore")

    database: DatabaseSettings
    storage: StorageSettings
    messaging: MessagingSettings
    redis: RedisSettings
    security: SecuritySettings
    kubernetes: KubernetesSettings
    nodes: List[NodeSettings] = Field(default_factory=list)
    analysisTool: AnalysisToolSettings
    common: CommonSettings = CommonSettings()
    fileNode: FileNodeSettings = FileNodeSettings()
    option: OptionSettings = OptionSettings()
    logging: LoggingSettings = LoggingSettings()
    url: UrlSettings | None = None
    compat: Dict[str, Any] = Field(default_factory=dict)
    test: TestSettings | None = None

    cluster_resources: ClusterResources = Field(default_factory=ClusterResources)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            YamlConfigSettingsSource(settings_cls=settings_cls),
            env_settings,
            init_settings,
            dotenv_settings,
            file_secret_settings,
        )

    def calc_cluster_resources(self) -> ClusterResources:
        total_cpu = sum(n.cpuMilli for n in self.nodes)
        total_mem = sum(n.memoryBytes for n in self.nodes)
        total_gpu = sum(n.gpu for n in self.nodes)
        total_cap = sum(n.capacity for n in self.nodes)
        self.cluster_resources = ClusterResources(
            total_cpu_milli=total_cpu,
            total_memory_bytes=total_mem,
            total_gpu=total_gpu,
            total_capacity=total_cap,
        )
        return self.cluster_resources


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    def get_yaml_data(self) -> Dict[str, Any]:
        path = Path("application.yaml")
        if not path.exists():
            return {}
        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content) or {}
        if not isinstance(data, dict):
            return {}
        return data

    def get_field_value(
        self,
        field: Any,
        field_name: str,
    ) -> tuple[Any, str, bool]:
        data = self.get_yaml_data()
        return data.get(field_name, self._missing), field_name, False

    def __call__(self) -> Dict[str, Any]:
        return self.get_yaml_data()


@lru_cache
def get_settings() -> AppSettings:
    settings = AppSettings()
    settings.calc_cluster_resources()
    return settings
