"""Authentication service layer.

All auth business logic lives here. Views call these functions;
they never query models directly.
"""

from esb.extensions import db
from esb.models.user import User
from esb.utils.exceptions import ValidationError


def authenticate(username: str, password: str) -> User:
    """Authenticate a user by username and password.

    Returns the User object on success.

    Raises:
        ValidationError: if credentials are invalid or account is inactive.
    """
    user = db.session.execute(
        db.select(User).filter_by(username=username)
    ).scalar_one_or_none()

    if user is None or not user.check_password(password):
        raise ValidationError('Invalid username or password')

    if not user.is_active:
        raise ValidationError('Invalid username or password')

    return user


def load_user(user_id: int) -> User | None:
    """Load a user by ID for Flask-Login's user_loader.

    Returns None if user not found or is inactive.
    """
    user = db.session.get(User, int(user_id))
    if user is None or not user.is_active:
        return None
    return user
