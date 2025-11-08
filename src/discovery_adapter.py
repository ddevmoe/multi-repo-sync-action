import fnmatch
import re

from src import github_adapter
from src.models import TargetDiscoverySettings, Repository, RepositoryFilter


def _does_repository_match(filter: RepositoryFilter, repository: Repository) -> bool:
    if any(fnmatch.fnmatch(repository.name, pattern) for pattern in filter.patterns):
        return True

    if any(re.match(pattern, repository.name) for pattern in filter.regex_patterns):
        return True

    if set(filter.topics).intersection(repository.topics):
        return True

    return False


def get_target_repositories(settings: TargetDiscoverySettings) -> list[Repository]:
    repositories = github_adapter.get_all_repositories()

    targets = [
        repository
        for repository in repositories
        if (
            _does_repository_match(settings.include, repository)
            and not _does_repository_match(settings.exclude, repository)
        )
    ]
    return targets
