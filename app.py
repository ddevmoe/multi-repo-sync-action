import json

from pydantic import BaseModel

from src import discovery_adapter, github_adapter, sync_report_generator
from src.config import config
from src.models import (
    ModificationType,
    Repository,
    RepositoryPath,
    Source,
    SyncSettings,
    RepositoryPathSyncReport,
    TargetDiscoverySettings,
)


class SyncConfigFile(BaseModel):
    sources: list[str]
    targets: TargetDiscoverySettings


SOURCE_SEPARATOR = ":"
SOURCE_REPOSITORY = Repository(
    name=config.github.repository_name,
    full_name=config.github.repository_full_name,
    owner=config.github.repository_owner,
    topics=tuple(),
)


def _handle_sync_reports(sync_settings: SyncSettings, reports: list[RepositoryPathSyncReport]):
    # Pretty print reports
    pretty_diffs = '\n'.join([sync.diff for sync in reports])
    print(f'[#] Found {len(reports)} syncs to apply:\n{pretty_diffs}')

    # If we are in a PR context, just add a comment
    if config.github.pull_request_number:
        github_adapter.comment_sync_reports_on_pr(reports)
        return

    if sync_settings.dry_run:
        print('[!] Dry run enabled; Doing nothing!')
        return

    github_adapter.sync_targets(reports)


def _generate_reports(sync: SyncSettings, targets: list[Repository]) -> list[RepositoryPathSyncReport]:
    reports: list[RepositoryPathSyncReport] = []
    for target in targets:
        for source in sync.sources:
            source_path = RepositoryPath(repository=SOURCE_REPOSITORY, path=source.path)
            target_path = RepositoryPath(repository=target, path=source.target_path)

            report = sync_report_generator.generate_report(source_path, target_path)
            reports.append(report)

    return reports


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


def _load_sync_definition() -> SyncSettings:
    with open("multi-repo-sync-config.json", encoding="utf-8") as of:
        data: dict = json.load(of)

    config = SyncConfigFile(**data)

    sources = [_parse_source_definition(source_definition) for source_definition in config.sources]

    sync_definition = SyncSettings(sources=sources, target_discovery=config.targets)
    return sync_definition


def main():
    # Read configuration
    sync = _load_sync_definition()
    print(f'[#] Loaded sync settings:\n{sync.model_dump_json(indent=4)}')

    # Discover target repositories
    target_repositories = discovery_adapter.get_target_repositories(sync.target_discovery)
    target_names = '\n'.join([target.name for target in target_repositories])
    print(f'[#] Selected {len(target_repositories)} repositories:\n{target_names}')

    # Generate sync report for each target
    reports = _generate_reports(sync, target_repositories)
    nonempty_syncs = [report for report in reports if report.type != ModificationType.NOOP]

    # Comment / Apply syncs
    _handle_sync_reports(sync, nonempty_syncs)
    print('[#] Done!')


if __name__ == "__main__":
    main()
