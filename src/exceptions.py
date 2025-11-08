class MultiRootRepositorySyncErrorBase(Exception):
    ...


class RepositoryPathNotFoundError(MultiRootRepositorySyncErrorBase):
    def __init__(self, repository_full_name: str, path: str):
        self.message = f'Requested repository path was not found {repository_full_name}:{path}'
        self.repository_full_name = repository_full_name
        self.path = path
        super().__init__(self.message)
