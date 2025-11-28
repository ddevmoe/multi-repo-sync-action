import json

from pydantic import BaseModel

from src.config import config
from src.models import Source, SyncDefinition, TargetDiscoverySettings


SOURCE_SEPARATOR = ":"


class SyncConfigFile(BaseModel):
    sources: list[str]
    targets: TargetDiscoverySettings


def _parse_source_definition(source_definition: str) -> Source:
    if SOURCE_SEPARATOR not in source_definition:
        source = Source(path=source_definition, target_path=source_definition)
        return source

    parts = source_definition.split(SOURCE_SEPARATOR)

    if len(parts) > 3:
        raise ValueError(f'Supplied source "{source_definition}" contains too many parts')

    if not all(parts):
        raise ValueError(f"Some source parts are undefined ({source_definition})")

    source = Source(path=parts[0], target_path=parts[1])
    return source


def load_sync_definition() -> SyncDefinition:
    with open(config.input.config_path, encoding="utf-8") as of:
        data: dict = json.load(of)

    sync_config = SyncConfigFile(**data)

    sources = [_parse_source_definition(source_definition) for source_definition in sync_config.sources]

    sync_definition = SyncDefinition(sources=sources, target_discovery=sync_config.targets)
    return sync_definition
