"""RootCause AI — Phase 2 API adapter.

An additive FastAPI layer that exposes the existing, unmodified Python backend
(`workflow.run_workflow`) over HTTP for the React frontend.

Nothing in this package imports the model clients or the sandbox verifier into
the server process: they only ever run inside a per-job subprocess working on a
disposable copy of the repository.
"""

__version__ = "0.1.0-m1"
