import base64
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, computed_field


class Repository(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    full_name: str
    owner: str
    topics: tuple[str, ...]


class RepositoryPath(BaseModel):
    repository: Repository
    path: str

    def __str__(self) -> str:
        return f'{self.repository.full_name}:{self.path}'

    def __repr__(self) -> str:
        return str(self)


class ModificationType(StrEnum):
    CREATE = 'create'
    EDIT = 'edit'
    NOOP = 'noop'


class RepositoryPathSyncReport(BaseModel):
    source: RepositoryPath
    source_content: str

    target: RepositoryPath
    target_content: str

    type: ModificationType
    diff: str


class RepositoryFilter(BaseModel):
    patterns: list[str] = Field(default_factory=list)
    regex_patterns: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)


class TargetDiscoverySettings(BaseModel):
    include: RepositoryFilter = Field(default_factory=RepositoryFilter)
    exclude: RepositoryFilter = Field(default_factory=RepositoryFilter)
    # template_dependents_only


class Source(BaseModel):
    path: str
    target_path: str


class SyncSettings(BaseModel):
    sources: list[Source]
    target_discovery: TargetDiscoverySettings

    # Open PR or commit
    # Auto merge if no conflicts
    dry_run: bool = False
