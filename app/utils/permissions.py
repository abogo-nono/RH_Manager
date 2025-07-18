from functools import wraps
from flask import abort
from flask_login import current_user

def permission_requise (code):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if not current_user.role:
                abort(403)
            permission_codes = [perm.code for perm in current_user.role.permissions]
            if code not in permission_codes:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
