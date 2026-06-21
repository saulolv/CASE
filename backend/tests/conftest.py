from pathlib import Path


def pytest_sessionstart(session):
    Path("test_vigil.db").unlink(missing_ok=True)
