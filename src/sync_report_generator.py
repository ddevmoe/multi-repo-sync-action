import difflib

from src import github_adapter
from src.config import config
from src.exceptions import RepositoryPathNotFoundError
from src.models import ModificationType, RepositoryPath, RepositoryPathSyncReport


def generate_report(source: RepositoryPath, target: RepositoryPath) -> RepositoryPathSyncReport:
    try:
        source_content = github_adapter.get_file_contents(source.repository.full_name, source.path, config.github.source_ref)
    except RepositoryPathNotFoundError as _error:
        raise  # TODO: Fail with config error when the source does not exist

    try:
        target_content = github_adapter.get_file_contents(target.repository.full_name, target.path)
    except RepositoryPathNotFoundError as _error:
        differences = difflib.unified_diff(
            [""],
            source_content.splitlines(keepends=True),
            fromfile=str(target),
            tofile=str(source),
        )
        diff = "".join(differences)

        report = RepositoryPathSyncReport(
            source=source,
            source_content=source_content,
            target=target,
            target_content="",
            type=ModificationType.CREATE,
            diff=diff,
        )
        return report

    differences = difflib.unified_diff(
        target_content.splitlines(keepends=True),
        source_content.splitlines(keepends=True),
        fromfile=str(target),
        tofile=str(source),
    )
    diff = "".join(differences)

    if not diff:
        report = RepositoryPathSyncReport(
            source=source,
            source_content=source_content,
            target=target,
            target_content=target_content,
            type=ModificationType.NOOP,
            diff=diff,
        )
        return report

    report = RepositoryPathSyncReport(
        source=source,
        source_content=source_content,
        target=target,
        target_content=target_content,
        type=ModificationType.EDIT,
        diff=diff,
    )
    return report
