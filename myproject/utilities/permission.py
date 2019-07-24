import functools
from flask import abort
from flask_login import current_user, logout_user
from myproject.models import Role


def user_permission(rolename):
    def my_decorator(func):
        @functools.wraps(func)
        def permission(*args, **kwargs):
            role = Role.query.filter_by(role=rolename).first()
            if role in current_user.role:
                return func(*args, **kwargs)
            else:
                logout_user()
                abort(403)
        return permission
    return my_decorator
