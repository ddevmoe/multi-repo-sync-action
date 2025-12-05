# Multi Repo Sync Action
`multi-repo-sync-action` helps you synchronize between multiple repositories.

The action runs on a single "upstream" repository and takes a dedicated sync configuration as input.
It will compare the state of selected files in the upstream repository and push changes to downstream repositories if changes are detected.

## Features
- Synchronize files from a single, central repository to multiple targets in a single action
- Targets discovery supports regex, glob patterns, topic match
- Exclude targets from discovery using negative filters
- Show changes before applying when running the action in a PR

## Example use cases
- Synchronize common configurations across entire teams, such as `.editorconfig`, `ruff.toml`, `tsconfig.json`.
- Keep repositories up-to-date with their originating template repository.
- Push modifications team-wide for different tooling (ever needed to update a common `Dockerfile`?).

## The configuration file
```json
{
    // List of source files
    // Each item must be a path to a single file in the repository
    // Files can be moved / renamed when being synced by using the form "path/to/file:path/to/destination"
    "sources": [
        // Regular file sync
        "ruff.toml",
        // We want the workflow to run on downstream repositories so we place it in .github/workflows
        "custom-workflows/test-workflow.yaml:.github/workflows/tests.yaml"
    ],
    // Target discovery rules
    "targets": {
        // Rules to include a repository
        // Repository is included if it fits AT LEAST ONE rule (filters are OR'd)
        "include": {
            // List of glob patterns (Python `fnmatch.fnmatch`)
            "patterns": ["targetrepo*"],
            // List of regex patterns (Python `re.match`), use anchors (^/$) for full match
            "regex": ["^team-(backend|sre)-.*$"],
            // List of repository topics to match, at least one topic needs to match
            "topics": ["python"],
        },
        // Rules to exclude a repository
        // Repository is excluded if it fits AT LEAST ONE rule (filters are OR'd)
        // Rules behave the same as "include" rules.
        // If a repository matches both "include" and "exclude" rules it will be EXCLUDED.
        "exclude": {
            "patterns": [],
            "regex": [],
            "topics": ["no-ruff", "skip-sync"]
        }
    }
}
```

## Example workflow
```yaml
on:
  - push

jobs:
  main:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - uses: ddevmoe/multi-repo-sync-action@v1
        with:
          github_token: ${{ secrets.MRS_TOKEN }}
          config_path: ${{ github.workspace }}/.github/multi-repo-sync-config.json
          dry_run: false
```

## Planned Features
- Define labels for opened PRs
- Skip PR for create / add only syncs
- Include template descendants
- Delete path on targets if source not found
- Support wildcards for sources
- Support folders
