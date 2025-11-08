class MultiRootRepositorySyncErrorBase(Exception):
    ...


class RepositoryPathNotFoundError(MultiRootRepositorySyncErrorBase):
    MESSAGE = 'Requested repository file was not found'

    def __init__(self, repository_full_name: str, path: str):
        super().__init__(self.MESSAGE)
        self.repository_full_name = repository_full_name
        self.path = path
