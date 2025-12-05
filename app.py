from src import discovery_adapter, github_adapter, sync_configuration_loader, sync_report_generator
from src.config import config
from src.models import (
    ModificationType,
    RepositoryMeta,
    RepositoryPath,
    RepositoryPathSyncReport,
    SyncConfig,
)

SOURCE_REPOSITORY = RepositoryMeta(
    name=config.github.repository_name,
    full_name=config.github.repository_full_name,
    owner=config.github.repository_owner,
    topics=(),
)


def _handle_sync_reports(reports: list[RepositoryPathSyncReport]) -> None:
    # Pretty print reports
    pretty_diffs = "\n".join([sync.diff for sync in reports])
    print(f"[#] Found {len(reports)} syncs to apply:\n{pretty_diffs}")

    # If we are in a PR context, just add a comment
    if config.github.pull_request_number:
        github_adapter.comment_sync_reports_on_pr(reports)
        return

    if config.dry_run:
        print("[!] Dry run enabled; Doing nothing!")
        return

    github_adapter.sync_targets(reports)


def _generate_reports(sync: SyncConfig, targets: list[RepositoryMeta]) -> list[RepositoryPathSyncReport]:
    reports: list[RepositoryPathSyncReport] = []
    for target in targets:
        for source in sync.sources:
            source_path = RepositoryPath(repository=SOURCE_REPOSITORY, path=source.path)
            target_path = RepositoryPath(repository=target, path=source.target_path)

            report = sync_report_generator.generate_report(source_path, target_path)
            reports.append(report)

    return reports


def main() -> None:
    # Read configuration
    sync_config = sync_configuration_loader.load_sync_config()
    print(f"[#] Loaded sync settings:\n{sync_config.model_dump_json(indent=4)}")

    # Discover target repositories
    target_repositories = discovery_adapter.find_target_repositories(sync_config.target_discovery)
    target_names = "\n".join([target.name for target in target_repositories])
    print(f"[#] Selected {len(target_repositories)} repositories:\n{target_names}")

    # Generate sync report for each target
    reports = _generate_reports(sync_config, target_repositories)
    nonempty_syncs = [report for report in reports if report.type != ModificationType.NOOP]

    # Comment / Apply syncs
    _handle_sync_reports(nonempty_syncs)
    print("[#] Done!")


if __name__ == "__main__":
    main()
