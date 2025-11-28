from typing import Annotated

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GithubContext(BaseSettings):
    """
    Represents GitHub's workflow runtime environment context
    # https://docs.github.com/en/actions/reference/workflows-and-actions/variables
    """
    model_config = SettingsConfigDict(env_prefix='GITHUB_')

    api_url: str = 'https://api.github.com'
    event_name: str
    repository_full_name: Annotated[str, Field(validation_alias='github_repository')]
    repository_owner: str
    ref_name: str
    sha: str

    @computed_field
    @property
    def short_sha(self) -> str:
        return self.sha[:7]

    @computed_field
    @property
    def repository_name(self) -> str:
        return self.repository_full_name.split('/')[-1]

    @computed_field
    @property
    def pull_request_number(self) -> int | None:
        if not self.event_name.startswith('pull_request'):
            return None

        return int(self.ref_name.split('/')[0])


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='MRS_')

    github: GithubContext = Field(default_factory=GithubContext)  # type: ignore

    github_token: str
    config_path: str = '.github/multi-repo-sync-config.json'
    dry_run: bool = False


config = Config()  # type: ignore - https://github.com/pydantic/pydantic/issues/3753
