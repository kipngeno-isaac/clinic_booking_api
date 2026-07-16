from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.api.deps import get_db


def test_get_db_yields_a_session_and_closes_it_afterwards():
    with patch.object(Session, "close", autospec=True) as mock_close:
        gen = get_db()
        db = next(gen)
        assert isinstance(db, Session)
        mock_close.assert_not_called()

        with pytest.raises(StopIteration):
            next(gen)

        mock_close.assert_called_once_with(db)
