from collections import defaultdict
from functools import lru_cache

from github import Auth, Github
from github.GithubException import UnknownObjectException, GithubException
from github.Repository import Repository as GithubRepository

from src.config import config
from src.exceptions import RepositoryPathNotFoundError
from src.models import ModificationType, Repository, RepositoryPathSyncReport


_client = Github(base_url=config.github.api_url, auth=Auth.Token(config.input.github_token))


def _get_reports_by_repository(reports: list[RepositoryPathSyncReport]):
    reports_by_repository: dict[Repository, list[RepositoryPathSyncReport]] = defaultdict(list)
    for report in reports:
        reports_by_repository[report.target.repository].append(report)
    return reports_by_repository


def get_all_repositories() -> list[Repository]:
    repositories_cursor = _client.get_user().get_repos()

    repositories: list[Repository] = []
    for repository in repositories_cursor:
        result = Repository(
            name=repository.name,
            full_name=repository.full_name,
            owner=repository.owner.name or '',
            topics=tuple(repository.topics),
        )
        repositories.append(result)

    return repositories


@lru_cache()
def get_file_contents(repository_full_name: str, path: str) -> str:
    try:
        content = _client.get_repo(repository_full_name).get_contents(path)
    except UnknownObjectException as _error:
        raise RepositoryPathNotFoundError(repository_full_name, path) from None

    if isinstance(content, list):
        raise ValueError('Provided target path must be a file, received a path to a folder')

    decoded_content = content.decoded_content.decode()
    return decoded_content


def comment_sync_reports_on_pr(reports: list[RepositoryPathSyncReport]):
    if not config.github.pull_request_number:
        raise ValueError('[X] Not a PR!')

    reports_by_repository = _get_reports_by_repository(reports)

    content = ''
    for repository, reports in reports_by_repository.items():
        content += f'# {repository.full_name}\n'

        for report in reports:
            formatted_report = (
                '<details>\n'
                f'<summary>{report.source} -> {report.target}</summary>\n'
                '\n'
                '```diff\n'
                f'{report.diff}\n'
                '```\n'
                '</details>\n\n'
            )
            content += formatted_report

    pr = _client.get_repo(config.github.repository_full_name).get_pull(config.github.pull_request_number)
    pr.create_issue_comment(content)


def _commit_reports(
    repository_handle: GithubRepository,
    branch_name: str,
    reports: list[RepositoryPathSyncReport],
):
    for report in reports:
        if report.type == ModificationType.CREATE:
            repository_handle.create_file(
                path=report.target.path,
                message=f'Create {report.target.path} by [{branch_name}]',
                content=report.source_content,
                branch=branch_name,
            )
            continue

        old_content = repository_handle.get_contents(report.target.path, ref=branch_name)

        if isinstance(old_content, list):
            raise ValueError('Something horrible happened! There should not be folders around here...')

        repository_handle.update_file(
            path=report.target.path,
            message=f'Create {report.target.path} by [{branch_name}]',
            content=report.encoded_source_content,
            sha=old_content.sha,
            branch=branch_name,
        )


def sync_targets(reports: list[RepositoryPathSyncReport]):
    reports_by_repository = _get_reports_by_repository(reports)

    for repository, reports in reports_by_repository.items():
        repository_handle = _client.get_repo(repository.full_name)

        # Create new branch on target repository
        target_head_sha = repository_handle.get_git_ref(f'heads/{repository_handle.default_branch}').object.sha
        sync_branch_name = f'sync-{config.github.repository_name}-{config.github.short_sha}'

        try:
            repository_handle.create_git_ref(f'refs/heads/{sync_branch_name}', target_head_sha)
        except GithubException as error:
            # 422 is when ref already exists, probably from a previous iteration
            if error.status != 422:
                raise

        _commit_reports(repository_handle, sync_branch_name, reports)

        pr_title = f'Incoming sync from {config.github.repository_name}-{config.github.short_sha}'
        pull_request = repository_handle.create_pull(
            base=repository_handle.default_branch,
            head=sync_branch_name,
            title=pr_title,
        )
