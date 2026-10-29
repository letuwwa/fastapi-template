from unittest.mock import Mock

import pytest

from app.db import deps


@pytest.mark.parametrize("failure", [False, True])
def test_database_dependency_closes_session(monkeypatch, failure: bool) -> None:
    session = Mock()
    monkeypatch.setattr(deps, "SessionLocal", lambda: session)
    dependency = deps.get_db()
    assert next(dependency) is session

    if failure:
        with pytest.raises(RuntimeError, match="request failed"):
            dependency.throw(RuntimeError("request failed"))
    else:
        with pytest.raises(StopIteration):
            next(dependency)

    session.close.assert_called_once_with()
