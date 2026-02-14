"""RBAC decorators for route access control.

Role hierarchy: Staff > Technician.
Staff users can access any Technician-protected route.
"""

from functools import wraps

from flask import abort
from flask_login import current_user, login_required

ROLE_HIERARCHY = {'staff': 2, 'technician': 1}


def role_required(role):
    """Restrict route access to users with the given role or higher.

    Args:
        role: Minimum role required ('technician' or 'staff').
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if ROLE_HIERARCHY.get(current_user.role, 0) < ROLE_HIERARCHY.get(role, 0):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
