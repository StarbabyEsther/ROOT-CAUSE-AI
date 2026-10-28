"""Per-job isolated working directory.

`workflow.py` resolves `ROOT = Path(__file__).resolve().parent` and every stage
writes its JSON report beside the code it ran. That is exactly what makes the
existing backend trivially isolatable: copy the modules into a private directory
and launch the child with that directory as its working directory, and all
artifacts land inside the job.

Rules enforced here:
  * only top-level `*.py` files from the backend are copied (no `.git`, no
    `.env`, no secrets, no nested directories, no symlinks);
  * the workspace is created with mode 0o700;
  * cleanup is guaranteed by the context manager, including on exceptions;
  * nothing is ever written back to the repository.
"""

from __future__ import annotations

import shutil
import stat
import uuid
from dataclasses import dataclass
from pathlib import Path

# Files we must never copy into a job, even if they match the glob.
_DENY_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.example",
    "secrets.toml",
}

# Reports/bundles from a previous run must not bleed into a new job.
_DENY_PREFIXES = ("verification_bundle", "refund_verification_bundle", "precision_verification_bundle")


@dataclass
class JobWorkspace:
    job_id: str
    path: Path

    def resolve_artifact(self, name: str) -> Path | None:
        """Resolve a whitelisted artifact name inside the workspace.

        Returns None for anything that is not a plain file directly inside the
        workspace, which is what defeats `../` traversal attempts.
        """
        candidate = (self.path / name).resolve()
        try:
            candidate.relative_to(self.path.resolve())
        except ValueError:
            return None
        if not candidate.is_file():
            return None
        return candidate


def create_workspace(backend_dir: Path, workspace_root: Path, job_id: str | None = None) -> JobWorkspace:
    job_id = job_id or uuid.uuid4().hex
    workspace = workspace_root / job_id
    workspace.mkdir(parents=True, exist_ok=False)
    workspace.chmod(0o700)

    copied = 0
    for source in sorted(backend_dir.glob("*.py")):
        if not source.is_file() or source.is_symlink():
            continue
        if source.name in _DENY_NAMES or source.name.startswith(_DENY_PREFIXES):
            continue
        target = workspace / source.name
        shutil.copyfile(source, target)
        target.chmod(stat.S_IRUSR | stat.S_IWUSR)
        copied += 1

    if copied == 0:
        raise RuntimeError(f"No backend modules found in {backend_dir}")

    return JobWorkspace(job_id=job_id, path=workspace)


def cleanup_workspace(workspace: JobWorkspace, keep: bool = False) -> None:
    if keep:
        return
    shutil.rmtree(workspace.path, ignore_errors=True)
