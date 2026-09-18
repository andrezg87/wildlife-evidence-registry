import bcrypt
import pytest
from fastapi import HTTPException

from app.presentation.security import CurrentUser, require_lab_director


def test_password_hash_accepts_correct_password_and_rejects_wrong_one():
    password_hash = bcrypt.hashpw("CorrectHorse123!".encode(), bcrypt.gensalt()).decode()

    assert bcrypt.checkpw("CorrectHorse123!".encode(), password_hash.encode())
    assert not bcrypt.checkpw("WrongPassword".encode(), password_hash.encode())


def test_require_lab_director_allows_director_role():
    director = CurrentUser(user_id="1", role="lab_director")

    result = require_lab_director(current_user=director)

    assert result is director


def test_require_lab_director_rejects_analyst_role():
    analyst = CurrentUser(user_id="1", role="analyst")

    with pytest.raises(HTTPException) as exc_info:
        require_lab_director(current_user=analyst)

    assert exc_info.value.status_code == 403
