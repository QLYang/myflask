#!/usr/bin/env python
#-*-coding:utf-8-*-
"""
    检查用户权限的自定义修饰器
"""
from functools import wraps
from flask import abort
from flask_login import current_user
from .model import Permission

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args,**kwargs):#这些参数是给f()的
            if not current_user.can(permission):
                abort(403)#禁止错误
            return f(*args,**kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)

if __name__ == "__main__":
    pass