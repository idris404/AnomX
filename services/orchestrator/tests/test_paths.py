"""Tests for repo path resolution."""

from anomx_orchestrator.paths import repo_path, repo_root


def test_repo_root_contains_workspace_markers() -> None:
    root = repo_root()
    assert (root / "config" / "settings.yaml").is_file()
    assert (root / "packages" / "anomx").is_dir()


def test_repo_path_resolves_sample_csv_config() -> None:
    assert repo_path("config/sources/sample_csv.yaml").is_file()
