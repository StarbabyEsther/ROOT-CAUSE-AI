"""Per-job isolation and cleanup."""

from __future__ import annotations

from pathlib import Path

import pytest

from api.workspace import cleanup_workspace, create_workspace

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def workspace(tmp_path):
    ws = create_workspace(REPO_ROOT, tmp_path)
    yield ws
    cleanup_workspace(ws)


def test_copies_backend_modules(workspace):
    assert (workspace.path / "workflow.py").is_file()
    assert (workspace.path / "sandbox_verifier.py").is_file()
    assert (workspace.path / "test_workflow.py").is_file()


def test_copies_only_top_level_python(workspace):
    names = {p.name for p in workspace.path.iterdir()}
    assert all(p.is_file() for p in workspace.path.iterdir())
    assert not any(name.endswith(".json") for name in names)
    assert "node_modules" not in names
    assert "web" not in names


def test_never_copies_secrets(workspace):
    names = {p.name for p in workspace.path.iterdir()}
    assert ".env" not in names
    assert not any(name.startswith(".env") for name in names)


def test_no_git_or_pycache(workspace):
    assert not (workspace.path / ".git").exists()
    assert not (workspace.path / "__pycache__").exists()


def test_workspace_permissions_are_private(workspace):
    mode = workspace.path.stat().st_mode & 0o777
    assert mode == 0o700


def test_artifact_resolution_blocks_traversal(workspace):
    assert workspace.resolve_artifact("../etc/passwd") is None
    assert workspace.resolve_artifact("../../../../etc/passwd") is None
    assert workspace.resolve_artifact("nested/file.py") is None
    assert workspace.resolve_artifact("does_not_exist.py") is None


def test_artifact_resolution_allows_real_files(workspace):
    resolved = workspace.resolve_artifact("workflow.py")
    assert resolved is not None and resolved.is_file()


def test_cleanup_is_guaranteed(workspace):
    path = workspace.path
    assert path.exists()
    cleanup_workspace(workspace)
    assert not path.exists()


def test_cleanup_is_idempotent(workspace):
    cleanup_workspace(workspace)
    cleanup_workspace(workspace)  # must not raise


def test_jobs_get_distinct_directories(tmp_path):
    first = create_workspace(REPO_ROOT, tmp_path)
    second = create_workspace(REPO_ROOT, tmp_path)
    assert first.path != second.path
    assert first.job_id != second.job_id
    cleanup_workspace(first)
    cleanup_workspace(second)


def test_missing_backend_dir_raises(tmp_path):
    with pytest.raises(RuntimeError):
        create_workspace(tmp_path / "nope", tmp_path / "work")
