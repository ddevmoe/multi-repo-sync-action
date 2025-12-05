import json

from pydantic import BaseModel

from src.config import config
from src.exceptions import MultiRootRepositorySyncErrorBase
from src.models import Source, SyncConfig, TargetDiscoverySettings

SOURCE_SEPARATOR = ":"


class InvalidSourceError(MultiRootRepositorySyncErrorBase):
    def __init__(self, raw_source: str, cause: str) -> None:
        self.raw_source = raw_source
        self.message = f"Source '{raw_source}' is invalid because {cause}"

    def __str__(self) -> str:
        return self.message


class RawSyncConfig(BaseModel):
    sources: list[str]
    targets: TargetDiscoverySettings


def _parse_raw_source(raw_source: str) -> Source:
    if SOURCE_SEPARATOR not in raw_source:
        source = Source(path=raw_source, target_path=raw_source)
        return source

    parts = raw_source.split(SOURCE_SEPARATOR)

    if len(parts) > 2:
        raise InvalidSourceError(raw_source, "source contains too many parts")

    if not all(parts):
        raise InvalidSourceError(raw_source, "Some source parts are undefined")

    source = Source(path=parts[0], target_path=parts[1])
    return source


def load_sync_config() -> SyncConfig:
    with open(config.config_path, encoding="utf-8") as of:
        data: dict = json.load(of)

    raw_sync_config = RawSyncConfig(**data)

    sources = [_parse_raw_source(raw_source) for raw_source in raw_sync_config.sources]

    sync_config = SyncConfig(sources=sources, target_discovery=raw_sync_config.targets)
    return sync_config
